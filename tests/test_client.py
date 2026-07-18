"""Tests for CarterClient — async context manager, transparent E2EE seal/open, notify."""

import asyncio
import base64
import io
import json

import pytest

import urllib.error

import carterkit.client as ckclient
from carterkit import (CarterClient, CarterNotifyError, notify_http,
                       device_refresh_http, CarterDeviceRevoked)
from carterkit.e2ee import E2EESession

K = base64.b64encode(bytes([1]) * 32).decode()


class _FakeSock:
    def __init__(self):
        self.sent = []
        self.handlers = {}
        self.reply = None
        self.events = []
        self.auth_token = "tok"  # device refresh updates this in place

    def on(self, t, f):
        self.handlers[t] = f

    async def send(self, t, payload=None, reply_to=None):
        self.sent.append((t, payload))

    async def request(self, t, payload=None, timeout=5.0):
        self.sent.append(("REQ:" + t, payload))
        return self.reply

    async def start(self):
        self.events.append("start")

    async def wait_until_ready(self):
        self.events.append("ready")

    async def stop(self):
        self.events.append("stop")


def _client(key=K, **kw):
    c = CarterClient("ws://x", "tok", "home", role="device", e2ee_key=key, **kw)
    c._sock = _FakeSock()  # swap the real MeshSocket for a recorder
    return c


def test_async_context_manager_connects_and_closes():
    c = _client()

    async def run():
        async with c as ctx:
            assert ctx is c
        return c._sock.events

    assert asyncio.run(run()) == ["start", "ready", "stop"]


def test_broadcast_sealed_peer_opens():
    async def run():
        c = _client()
        await c.broadcast("hello", {"v": 1})
        t, payload = c._sock.sent[0]
        assert t == "broadcast_request"
        assert E2EESession.is_envelope(payload)
        peer = E2EESession(bytes([1]) * 32, is_device_side=False)
        assert peer.open(payload) == {"msg_type": "hello", "v": 1}

    asyncio.run(run())


def test_on_handler_decrypts_and_seals_reply():
    async def run():
        c = _client()
        got = {}
        c.on("toggle", lambda data: (got.update(data) or {"status": "ok"}))
        peer = E2EESession(bytes([1]) * 32, is_device_side=False)
        reply = await c._sock.handlers["toggle"](peer.seal({"key": "lamp", "value": True}))
        assert got == {"key": "lamp", "value": True}
        assert E2EESession.is_envelope(reply)
        assert peer.open(reply) == {"status": "ok"}

    asyncio.run(run())


def test_cleartext_when_no_key():
    async def run():
        c = _client(key=None)
        await c.broadcast("hello", {"v": 1})
        _, payload = c._sock.sent[0]
        assert payload == {"msg_type": "hello", "v": 1}
        assert not E2EESession.is_envelope(payload)

    asyncio.run(run())


def _room_client():
    c = CarterClient("ws://x", "tok", "home", role="device", e2ee_key=K, room=True)
    c._sock = _FakeSock()
    return c


def test_room_broadcast_uses_group_cipher():
    async def run():
        c = _room_client()
        await c.broadcast("metrics", {"cpu": 7})
        _, payload = c._sock.sent[0]
        assert E2EESession.is_envelope(payload)
        peer = E2EESession.group(bytes([1]) * 32)  # a room member opens the hub's broadcast
        assert peer.open(payload) == {"msg_type": "metrics", "cpu": 7}

    asyncio.run(run())


def test_authority_answers_control_sync_request():
    async def run():
        c = _room_client()
        c.set_control_state("thermostat", 68)
        c.set_control_state("lamp", True)
        c.enable_state_authority()
        peer = E2EESession.group(bytes([1]) * 32)
        await c._sock.handlers["broadcast"](peer.seal({"msg_type": "control_sync_request", "from": "guest-abc12"}))
        snaps = [p for (t, p) in c._sock.sent if t == "broadcast_request"]
        assert snaps, "authority sent no snapshot"
        data = peer.open(snaps[-1])
        assert data["msg_type"] == "control_snapshot"
        assert data["to"] == "guest-abc12"
        assert data["v"] == 1
        assert data["controls"] == {"thermostat": 68, "lamp": True}

    asyncio.run(run())


def test_authority_silent_without_state():
    async def run():
        c = _room_client()
        c.enable_state_authority()
        peer = E2EESession.group(bytes([1]) * 32)
        await c._sock.handlers["broadcast"](peer.seal({"msg_type": "control_sync_request", "from": "g"}))
        assert c._sock.sent == []  # nothing recorded to snapshot

    asyncio.run(run())


def test_authority_consumes_sync_frames_not_forwarded():
    async def run():
        c = _room_client()
        c.set_control_state("x", 1)
        got = []
        c.on_broadcast(lambda d: got.append(d))
        c.enable_state_authority()
        peer = E2EESession.group(bytes([1]) * 32)
        # protocol frames are consumed (answered), never handed to the app handler
        await c._sock.handlers["broadcast"](peer.seal({"msg_type": "control_sync_request", "from": "g"}))
        await c._sock.handlers["broadcast"](peer.seal({"msg_type": "control_snapshot", "to": "g", "v": 1, "controls": {}}))
        assert got == []
        # a normal app broadcast is forwarded
        await c._sock.handlers["broadcast"](peer.seal({"msg_type": "evt", "v": 2}))
        assert {"msg_type": "evt", "v": 2} in got

    asyncio.run(run())


def test_non_authority_never_answers():
    async def run():
        c = _room_client()
        c.set_control_state("x", 1)        # recorded, but authority not enabled
        c.on_broadcast(lambda d: None)     # arm the listener without becoming authority
        peer = E2EESession.group(bytes([1]) * 32)
        await c._sock.handlers["broadcast"](peer.seal({"msg_type": "control_sync_request", "from": "g"}))
        assert c._sock.sent == []          # consumed but never answered

    asyncio.run(run())


def test_notify_http_maps_args_to_request():
    captured = {}

    def fake_send(url, headers, body_bytes):
        captured["url"] = url
        captured["headers"] = headers
        captured["payload"] = json.loads(body_bytes.decode())
        return {"sent": 2, "stale": 0}

    out = notify_http("https://v.example.com/", "jwt-123", "Garage", "Door open",
                      channel="home", data={"ruleId": "test"}, _send=fake_send)
    assert out == {"sent": 2, "stale": 0}
    assert captured["url"] == "https://v.example.com/alerts/notify"
    assert captured["headers"]["Authorization"] == "jwt-123"
    p = captured["payload"]
    assert p["title"] == "Garage" and p["body"] == "Door open"
    assert p["channel"] == "home" and p["sound"] == "default"
    assert p["data"] == {"ruleId": "test"}
    assert "badge" not in p and "category" not in p


def test_notify_http_validates_title_body():
    for bad in [("", "b"), ("t", ""), ("x" * 257, "b"), ("t", "y" * 257)]:
        with pytest.raises(ValueError):
            notify_http("https://v/", "jwt", bad[0], bad[1], _send=lambda *a: {})


def test_client_notify_requires_validator_creds():
    async def run():
        c = _client()  # no validator_url / session_jwt
        with pytest.raises(CarterNotifyError) as ei:
            await c.notify("t", "b")
        assert ei.value.status == 0

    asyncio.run(run())


def test_device_refresh_http_maps_args_to_request():
    captured = {}

    def fake_send(url, headers, body_bytes):
        captured["url"] = url
        captured["payload"] = json.loads(body_bytes.decode())
        return {"deviceToken": "fresh-tok", "expiresAt": 123}

    out = device_refresh_http("https://v.example.com/", "dv_1", "secret-9", _send=fake_send)
    assert out == {"deviceToken": "fresh-tok", "expiresAt": 123}
    assert captured["url"] == "https://v.example.com/devices/sessions/refresh"
    assert captured["payload"] == {"deviceId": "dv_1", "refreshToken": "secret-9"}


def test_device_refresh_http_raises_on_revoke():
    def revoked_send(url, headers, body_bytes):
        raise urllib.error.HTTPError(url, 403, "Forbidden", {}, io.BytesIO(b"device revoked"))

    with pytest.raises(CarterDeviceRevoked):
        device_refresh_http("https://v/", "dv_1", "secret", _send=revoked_send)


def test_refresh_device_token_updates_socket_token():
    async def run():
        c = _client(key=None, validator_url="https://v/", device_id="dv_1", refresh_token="secret")
        orig = ckclient.device_refresh_http
        ckclient.device_refresh_http = lambda *a, **k: {"deviceToken": "fresh-tok", "expiresAt": 9}
        try:
            await c.refresh_device_token()
        finally:
            ckclient.device_refresh_http = orig
        assert c._sock.auth_token == "fresh-tok"  # reconnects now use the fresh token

    asyncio.run(run())


def test_client_notify_forwards_to_helper():
    async def run():
        captured = {}

        def fake_send(url, headers, body_bytes):
            captured["payload"] = json.loads(body_bytes.decode())
            return {"sent": 1, "stale": 0}

        c = _client(key=None, validator_url="https://v/", session_jwt="jwt-9")
        orig = ckclient.notify_http
        ckclient.notify_http = lambda *a, **k: orig(*a, _send=fake_send, **k)
        try:
            out = await c.notify("Garage", "Door open", channel="home")
        finally:
            ckclient.notify_http = orig
        assert out == {"sent": 1, "stale": 0}
        assert captured["payload"]["title"] == "Garage"

    asyncio.run(run())


# ─── join signal + ack'd commands ────────────────────────────────────────────


def test_on_sync_request_fires_for_control_sync_request_only():
    async def run():
        c = _client(key=None)
        seen = []
        c.on_sync_request(seen.append)
        handler = c._sock.handlers["broadcast"]
        await handler({"msg_type": "control_sync_request", "from": "Phone",
                       "dynamic": ["ui.rooms"]})
        await handler({"msg_type": "telemetry", "v": 1})   # data, not a join
        assert len(seen) == 1 and seen[0]["from"] == "Phone"
        assert seen[0]["dynamic"] == ["ui.rooms"]          # deck scoping survives

    asyncio.run(run())


def test_authority_answer_and_sync_request_handler_share_the_request():
    async def run():
        c = _client(key=None)
        c.enable_state_authority()
        c.set_control_state("master", 80)
        joined = []
        c.on_sync_request(joined.append)
        await c._sock.handlers["broadcast"](
            {"msg_type": "control_sync_request", "from": "Phone"})
        assert [p.get("msg_type") for _, p in c._sock.sent] == ["control_snapshot"]
        assert len(joined) == 1

    asyncio.run(run())


def test_command_ack_ok_when_handler_reports_handled():
    async def run():
        c = _client(key=None)
        got = []

        def handle(data):
            got.append(data)
            return True                                    # "this was mine"

        c.on_broadcast(handle)
        c.enable_command_acks()
        await c._sock.handlers["broadcast"](
            {"msg_type": "light.power", "on": True, "_cmd": "c-1", "_from": "Phone"})
        assert got[0]["msg_type"] == "light.power"
        t, ack = c._sock.sent[0]
        assert t == "broadcast_request"
        assert ack == {"msg_type": "command_ack", "cmd_id": "c-1",
                       "to": "Phone", "ok": True}

    asyncio.run(run())


def test_no_ack_when_handler_reports_unhandled():
    async def run():
        c = _client(key=None)
        c.on_broadcast(lambda d: None)     # observed, but not handled
        c.enable_command_acks()
        await c._sock.handlers["broadcast"](
            {"msg_type": "someone.elses", "_cmd": "c-9", "_from": "Phone"})
        assert c._sock.sent == []          # silence → the app times out + reverts

    asyncio.run(run())


def test_command_ack_not_ok_when_handler_raises_and_still_raises():
    async def run():
        c = _client(key=None)

        def boom(_data):
            raise RuntimeError("handler exploded")

        c.on_broadcast(boom)
        c.enable_command_acks()
        with pytest.raises(RuntimeError):
            await c._sock.handlers["broadcast"](
                {"msg_type": "x", "_cmd": "c-2", "_from": "Phone"})
        _, ack = c._sock.sent[0]
        assert ack["ok"] is False and ack["cmd_id"] == "c-2"

    asyncio.run(run())


def test_unstamped_frames_get_no_ack():
    async def run():
        c = _client(key=None)
        c.on_broadcast(lambda d: True)
        c.enable_command_acks()
        await c._sock.handlers["broadcast"]({"msg_type": "light.power", "on": False})
        assert c._sock.sent == []

    asyncio.run(run())


def test_command_ack_frames_are_protocol_not_data():
    async def run():
        c = _client(key=None)
        got = []
        c.on_broadcast(got.append)
        await c._sock.handlers["broadcast"](
            {"msg_type": "command_ack", "cmd_id": "c-1", "to": "Phone", "ok": True})
        assert got == []                   # another hub's ack never leaks as data

    asyncio.run(run())


def test_connect_pre_refreshes_expired_device_token():
    async def run():
        c = _client(key=None, validator_url="https://v/", device_id="dv_1",
                    refresh_token="secret")
        orig = ckclient.device_refresh_http
        ckclient.device_refresh_http = lambda *a, **k: {"deviceToken": "fresh-tok",
                                                        "expiresAt": 9}
        try:
            await c.connect()
        finally:
            ckclient.device_refresh_http = orig
            if c._refresh_task:
                c._refresh_task.cancel()
        # the socket dialed WITH the freshly minted token, not the stale one
        assert c._sock.auth_token == "fresh-tok"
        assert c._sock.events[:2] == ["start", "ready"]

    asyncio.run(run())


def test_connect_survives_transient_refresh_failure():
    async def run():
        c = _client(key=None, validator_url="https://v/", device_id="dv_1",
                    refresh_token="secret")
        orig = ckclient.device_refresh_http

        def boom(*a, **k):
            raise CarterNotifyError(500, "validator down")
        ckclient.device_refresh_http = boom
        try:
            await c.connect()          # falls through to the stored token
        finally:
            ckclient.device_refresh_http = orig
            if c._refresh_task:
                c._refresh_task.cancel()
        assert c._sock.events[:2] == ["start", "ready"]

    asyncio.run(run())


# ─── notification personalization (notify v2) ────────────────────────────────


def test_notify_http_maps_rich_fields():
    captured = {}

    def fake_send(url, headers, body_bytes):
        captured["payload"] = json.loads(body_bytes.decode())
        return {"sent": 1, "stale": 0}

    notify_http("https://v/", "jwt", "Garage", "Door open",
                subtitle="Bay 2", interruption="time-sensitive", relevance=0.8,
                thread_id="layout-abc", image="https://x/img.jpg",
                sender=("Monroe", "https://x/ava.jpg"),
                actions=[{"id": "ack", "title": "Acknowledge"},
                         {"id": "del", "title": "Delete", "destructive": True}],
                notif_id="n123", _send=fake_send)
    p = captured["payload"]
    assert p["subtitle"] == "Bay 2"
    assert p["interruption"] == "time-sensitive"
    assert p["relevance"] == 0.8
    assert p["threadId"] == "layout-abc"
    assert p["imageURL"] == "https://x/img.jpg"
    assert p["sender"] == {"name": "Monroe", "avatarURL": "https://x/ava.jpg"}
    assert p["actions"] == [{"id": "ack", "title": "Acknowledge"},
                            {"id": "del", "title": "Delete", "destructive": True}]
    assert p["notifId"] == "n123"


def test_notify_http_rejects_bad_fields():
    ok = lambda *a: {}
    with pytest.raises(ValueError, match="Apple approval"):
        notify_http("https://v/", "jwt", "t", "b", interruption="critical", _send=ok)
    with pytest.raises(ValueError):
        notify_http("https://v/", "jwt", "t", "b", interruption="loud", _send=ok)
    with pytest.raises(ValueError):
        notify_http("https://v/", "jwt", "t", "b", relevance=1.5, _send=ok)
    with pytest.raises(ValueError, match="at most 4"):
        notify_http("https://v/", "jwt", "t", "b", _send=ok,
                    actions=[{"id": str(i), "title": "x"} for i in range(5)])
    with pytest.raises(ValueError, match="CarterClient.notify"):
        notify_http("https://v/", "jwt", "t", "b", _send=ok,
                    actions={"ack": ("Acknowledge", lambda d: None)})
    with pytest.raises(ValueError):
        notify_http("https://v/", "jwt", "t", "b", sender=("Monroe", "x", "y"), _send=ok)


def test_notify_sender_forms():
    from carterkit.client import _normalize_sender
    assert _normalize_sender("Monroe") == {"name": "Monroe"}
    assert _normalize_sender(("Monroe", "https://a")) == {"name": "Monroe", "avatarURL": "https://a"}
    assert _normalize_sender({"name": "Monroe", "avatar_url": "https://a"}) == \
        {"name": "Monroe", "avatarURL": "https://a"}


def _notify_client(**kw):
    c = _client(key=None, validator_url="https://v/", session_jwt="jwt-9", **kw)
    return c


def _capture_notify(monkeypatch_target_module, captured):
    def fake_send(url, headers, body_bytes):
        captured["payload"] = json.loads(body_bytes.decode())
        return {"sent": 1, "stale": 0}
    orig = monkeypatch_target_module.notify_http
    monkeypatch_target_module.notify_http = lambda *a, **k: orig(*a, _send=fake_send, **k)
    return orig


def test_client_notify_defaults_channel_and_thread():
    async def run():
        captured = {}
        c = _notify_client()  # mesh channel "home"
        orig = _capture_notify(ckclient, captured)
        try:
            await c.notify("T", "B", sender="Monroe", criticality="active")
        finally:
            ckclient.notify_http = orig
        p = captured["payload"]
        assert p["channel"] == "home"           # tap-routing key from the mesh channel
        assert p["threadId"] == "Monroe"        # persona implies a stable thread
        assert p["interruption"] == "active"    # criticality alias
        assert p["sender"] == {"name": "Monroe"}

    asyncio.run(run())


def test_client_notify_action_callbacks_dispatch():
    async def run():
        captured = {}
        taps = []
        c = _notify_client()
        orig = _capture_notify(ckclient, captured)
        try:
            out = await c.notify("T", "B", actions={
                "ack": ("Acknowledge", lambda d: taps.append(("cb", d["actionId"]))),
                "info": "Details"})  # no callback for this one
        finally:
            ckclient.notify_http = orig
        p = captured["payload"]
        notif_id = p["notifId"]
        assert notif_id  # minted because a callback was registered
        assert {a["id"] for a in p["actions"]} == {"ack", "info"}

        seen = []
        c.on_notif_action(lambda d: seen.append(d["actionId"]))
        tap = {"msg_type": "notif_action", "notifId": notif_id, "actionId": "ack"}
        await c._sock.handlers["broadcast"](tap)
        assert taps == [("cb", "ack")]
        assert seen == ["ack"]
        # unknown action id: only the catch-all fires
        await c._sock.handlers["broadcast"](
            {"msg_type": "notif_action", "notifId": notif_id, "actionId": "zzz"})
        assert taps == [("cb", "ack")] and seen == ["ack", "zzz"]

    asyncio.run(run())


def test_notif_action_consumed_not_forwarded_to_on_broadcast():
    async def run():
        c = _notify_client()
        got = []
        c.on_broadcast(lambda d: got.append(d))
        await c._sock.handlers["broadcast"](
            {"msg_type": "notif_action", "notifId": "n1", "actionId": "a"})
        assert got == []  # kit plane, like control_sync_request

    asyncio.run(run())


def test_room_client_notify_seals_content_fields():
    async def run():
        captured = {}
        c = CarterClient("ws://x", "tok", "home", role="device", e2ee_key=K, room=True,
                         validator_url="https://v/", session_jwt="jwt-9")
        c._sock = _FakeSock()
        orig = _capture_notify(ckclient, captured)
        try:
            await c.notify("Secret title", "Secret body", subtitle="Secret sub",
                           image="https://x/i.jpg", sender=("Monroe", "https://x/a.jpg"),
                           thread_id="th", relevance=0.5)
        finally:
            ckclient.notify_http = orig
        p = captured["payload"]
        # placeholders in the clear, content sealed
        assert p["title"] == "CAR-TER" and p["body"] == "New notification"
        assert "subtitle" not in p and "imageURL" not in p and "sender" not in p
        # delivery hints stay clear
        assert p["threadId"] == "th" and p["relevance"] == 0.5 and p["channel"] == "home"
        env = p["data"]["enc"]
        assert E2EESession.is_envelope(env)
        clear = E2EESession.group(bytes([1]) * 32).open(env)
        assert clear == {"title": "Secret title", "body": "Secret body",
                         "subtitle": "Secret sub", "imageURL": "https://x/i.jpg",
                         "sender": {"name": "Monroe", "avatarURL": "https://x/a.jpg"}}

    asyncio.run(run())


def test_notify_encrypt_true_requires_room_cipher():
    async def run():
        c = _notify_client()  # no e2ee at all
        with pytest.raises(CarterNotifyError, match="room"):
            await c.notify("T", "B", encrypt=True)
        d = _client(validator_url="https://v/", session_jwt="jwt")  # directional cipher
        with pytest.raises(CarterNotifyError, match="room"):
            await d.notify("T", "B", encrypt=True)

    asyncio.run(run())


def test_room_client_notify_encrypt_false_stays_clear():
    async def run():
        captured = {}
        c = CarterClient("ws://x", "tok", "home", role="device", e2ee_key=K, room=True,
                         validator_url="https://v/", session_jwt="jwt-9")
        c._sock = _FakeSock()
        orig = _capture_notify(ckclient, captured)
        try:
            await c.notify("Plain", "Text", encrypt=False)
        finally:
            ckclient.notify_http = orig
        p = captured["payload"]
        assert p["title"] == "Plain" and "data" not in p

    asyncio.run(run())
