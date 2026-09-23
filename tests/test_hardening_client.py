import base64
import pytest
from carterkit import client as ckclient
from carterkit.client import CarterClient, device_refresh_http


class _FakeSock:
    def __init__(self, **kw):
        self.handlers = {}
        self.sent = []
        self.auth_token = kw.get("auth_token")
    def on(self, t, f): self.handlers[t] = f
    async def send(self, t, payload=None, reply_to=None): self.sent.append((t, payload))
    async def start(self): pass
    async def wait_until_ready(self): pass
    async def stop(self): pass


def _room_client(monkeypatch, **kw):
    monkeypatch.setattr(ckclient, "MeshSocket", _FakeSock)
    key = base64.b64encode(bytes([3]) * 32).decode()
    return CarterClient("ws://x", "tok", "home", e2ee_key=key, room=True, **kw)


def test_room_client_drops_cleartext_frames(monkeypatch):
    # fail-closed is the default
    c = _room_client(monkeypatch)
    assert c._open({"msg_type": "command", "text": "rm -rf /"}) is None
    assert c.dropped["plaintext"] == 1
    # relay control frames are plaintext by nature and always pass
    assert c._open({"type": "node_status", "clients": []}) == {"type": "node_status", "clients": []}


def test_room_client_rejects_short_key(monkeypatch):
    monkeypatch.setattr(ckclient, "MeshSocket", _FakeSock)
    with pytest.raises(ValueError):
        CarterClient("ws://x", "tok", "home", e2ee_key=base64.b64encode(b"abcd").decode(), room=True)


def test_room_client_open_never_raises_into_socket_task(monkeypatch):
    c = _room_client(monkeypatch)
    garbage = {"e2ee": 2, "s": "AA==", "n": -1, "ct": "AA=="}
    assert c._open(garbage) is None                     # struct.error propagates today


def test_refresh_secret_only_travels_over_https():
    captured = {}
    def fake_send(url, headers, body):
        captured["url"] = url
        return {"deviceToken": "t", "expiresAt": 1}
    with pytest.raises(ValueError):
        device_refresh_http("http://validator.example", "dv_1", "refresh-secret", _send=fake_send)
    assert "url" not in captured                        # sent in the clear today


def _rotating_validator(calls, new_secret="rot-2"):
    def fake(url, device_id, refresh_token, **kw):
        calls.append(refresh_token)
        return {"deviceToken": f"tok-{len(calls)}", "expiresAt": 1, "refreshToken": new_secret}
    return fake


def test_rotated_refresh_secret_is_persisted_to_device_json(monkeypatch, tmp_path):
    import asyncio, json, os, stat
    from carterkit.connection import Connection
    monkeypatch.setattr(ckclient, "MeshSocket", _FakeSock)
    p = tmp_path / "device.json"
    p.write_text(json.dumps({"url": "wss://relay.example", "channel": "home", "role": "hub",
                             "token": "old-tok", "refresh": "rot-1", "did": "dv_1",
                             "validator": "https://v.example", "note": "keep me"}))
    calls = []
    monkeypatch.setattr(ckclient, "device_refresh_http", _rotating_validator(calls))
    c = CarterClient(**Connection.parse(str(p)).client_kwargs(name="hub"))

    async def run():
        await c.refresh_device_token()
        await c.refresh_device_token()          # second call uses the rotated secret
    asyncio.run(run())

    assert calls == ["rot-1", "rot-2"]
    assert c._refresh_token == "rot-2" and c._sock.auth_token == "tok-2"
    doc = json.loads(p.read_text())
    assert doc["refresh"] == "rot-2" and doc["note"] == "keep me" and doc["did"] == "dv_1"
    assert stat.S_IMODE(os.stat(p).st_mode) == 0o600
    assert not [f for f in os.listdir(tmp_path) if f.endswith(".tmp")]   # no temp litter


def test_rotated_secret_snake_case_and_inline_credential_warns(monkeypatch, caplog):
    import asyncio, logging
    monkeypatch.setattr(ckclient, "MeshSocket", _FakeSock)
    monkeypatch.setattr(ckclient, "device_refresh_http",
                        lambda *a, **k: {"deviceToken": "t", "refresh_token": "rot-9"})
    c = CarterClient("wss://x", "tok", "home", validator_url="https://v.example",
                     device_id="dv_1", refresh_token="rot-1")          # inline: no file
    with caplog.at_level(logging.WARNING, logger="carterkit.client"):
        asyncio.run(c.refresh_device_token())
    assert c._refresh_token == "rot-9"                                  # adopted in memory
    assert any("could not be persisted" in r.message or "lives only in memory" in r.message
               for r in caplog.records)


def test_unchanged_refresh_response_does_not_touch_the_file(monkeypatch, tmp_path):
    import asyncio, json
    from carterkit.connection import Connection
    monkeypatch.setattr(ckclient, "MeshSocket", _FakeSock)
    p = tmp_path / "device.json"
    p.write_text(json.dumps({"refresh": "rot-1", "did": "dv_1", "url": "wss://r", "token": "t"}))
    before = p.stat().st_mtime_ns
    monkeypatch.setattr(ckclient, "device_refresh_http", lambda *a, **k: {"deviceToken": "t2"})
    c = CarterClient(**Connection.parse(str(p)).client_kwargs())
    asyncio.run(c.refresh_device_token())
    assert p.stat().st_mtime_ns == before and c._refresh_token == "rot-1"
