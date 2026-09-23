"""Confirms the first-pass CSRF / status-leak issue on `carterkit explore` and
encodes the desired Host/Origin gating + redaction."""
import base64
import json
import urllib.error
import urllib.request

from carterkit.explore import Explorer
from carterkit.hub import Hub
from test_explore import LAYOUT, _free_port, _wait_connected

KEY_B64 = base64.b64encode(bytes([9]) * 32).decode()


def _run(test_body):
    import asyncio, threading
    web, relay = _free_port(), _free_port()
    hub = Hub(LAYOUT, None, name="layout-link", port=relay, key="lan-shared-secret",
              e2ee_key=KEY_B64)
    global EX
    ex = EX = Explorer(hub, port=web, pull=None)
    errors = []

    async def run():
        started = asyncio.Event()
        task = asyncio.ensure_future(ex.run(ready=lambda _e: started.set()))
        await asyncio.wait_for(started.wait(), timeout=10)
        def worker():
            try:
                test_body(web)
            except Exception as e:
                errors.append(e)
        t = threading.Thread(target=worker); t.start()
        while t.is_alive():
            await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    asyncio.run(run())
    if errors:
        raise errors[0]


def _req(port, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data,
                                 headers={"Content-Type": "application/json", **(headers or {})},
                                 method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def test_cross_site_post_is_refused():
    def body(port):
        _wait_connected(port)
        evil = {"Origin": "http://evil.example", "Referer": "http://evil.example/",
                "Host": f"evil.example:{port}"}
        status, raw = _req(port, "/api/push", {"id": "cpu", "value": 99}, evil)
        assert status == 403, f"cross-site push accepted: {status} {raw[:120]!r}"
    _run(body)


def test_status_does_not_leak_relay_key_or_room_key():
    def body(port):
        s = _wait_connected(port)
        qr = json.loads(s["qr"]) if s.get("qr") else {}
        assert "token" not in qr and "k" not in qr, f"pairing secrets in /api/status: {sorted(qr)}"
        # DNS-rebinding shape: a foreign Host header must not be served at all
        status, _ = _req(port, "/api/status", headers={"Host": f"rebound.example:{port}"})
        assert status in (400, 403, 421)
    _run(body)


def test_layout_endpoint_redacts_connection_secrets():
    def body(port):
        _wait_connected(port)
        # a layout pulled off a phone carries its connection block verbatim
        EX.hub.layout["connection"] = {"url": "wss://relay.example", "token": "eyJhY2N0.secret",
                                       "mode": "room", "e2eeKey": KEY_B64,
                                       "identity": {"name": "n", "channel": "home", "role": "controller"}}
        status, raw = _req(port, "/api/layout")
        conn = json.loads(raw).get("connection") or {}
        assert conn.get("token") in (None, "••• redacted")
        assert conn.get("e2eeKey") in (None, "••• redacted")
    _run(body)
