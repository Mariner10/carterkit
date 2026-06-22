"""Tests for CarterClient — async context manager, transparent E2EE seal/open, notify."""

import asyncio
import base64
import json

import pytest

import carterkit.client as ckclient
from carterkit import CarterClient, CarterNotifyError, notify_http
from carterkit.e2ee import E2EESession

K = base64.b64encode(bytes([1]) * 32).decode()


class _FakeSock:
    def __init__(self):
        self.sent = []
        self.handlers = {}
        self.reply = None
        self.events = []

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
