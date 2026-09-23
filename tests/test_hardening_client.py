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
    # strict_e2ee=True is the fail-closed mode; 0.13 makes it the default.
    c = _room_client(monkeypatch, strict_e2ee=True)
    assert c._open({"msg_type": "command", "text": "rm -rf /"}) is None
    assert c.dropped["plaintext"] == 1
    # relay control frames are plaintext by nature and always pass
    assert c._open({"type": "node_status", "clients": []}) == {"type": "node_status", "clients": []}


def test_room_client_default_passes_cleartext_with_one_warning(monkeypatch, caplog):
    # 0.12 default (strict_e2ee=False): the TestFlight app still answers routed requests
    # in plaintext, so pass through — but warn exactly once per msg_type.
    import logging
    c = _room_client(monkeypatch)
    frame = {"msg_type": "command", "text": "x"}
    with caplog.at_level(logging.WARNING, logger="carterkit.client"):
        assert c._open(frame) == frame
        assert c._open(frame) == frame
    assert sum("plaintext frame" in r.message for r in caplog.records) == 1


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
