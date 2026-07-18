import asyncio
import json
import socket
import threading
import urllib.error
import urllib.request

from carterkit.explore import Explorer, build_explorer
from carterkit.hub import Hub


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


LAYOUT = {
    "name": "Explore Test",
    "tabs": [{
        "title": "Main",
        "children": [
            {"type": "slider", "id": "bright", "label": "Brightness",
             "min": 0, "max": 255,
             "action": {"method": "meshsocket", "mode": "broadcast",
                        "event": "broadcast_request",
                        "payload": {"msg_type": "set-brightness", "level": "{{value}}"}}},
            {"type": "gauge", "id": "cpu", "label": "CPU", "min": 0, "max": 100,
             "sync": [{"method": "meshsocket", "type": "listen", "event": "broadcast",
                       "filter": {"msg_type": "metrics"}, "valuePath": "cpu"}]},
        ],
    }],
}


def _get(port, path):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as r:
        return r.status, r.read()


def _post(port, path, body):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, json.loads(r.read())


def _run_explorer(test_body):
    """Start an Explorer on a free relay+web port, run `test_body(port)` in a
    thread, tear down."""
    web = _free_port()
    relay = _free_port()
    hub = Hub(LAYOUT, None, name="layout-link", port=relay)
    ex = Explorer(hub, port=web, pull=None)
    errors = []

    async def run():
        started = asyncio.Event()
        task = asyncio.ensure_future(ex.run(ready=lambda _e: started.set()))
        await asyncio.wait_for(started.wait(), timeout=10)

        def worker():
            try:
                test_body(web)
            except Exception as e:          # surface into the main thread
                errors.append(e)

        t = threading.Thread(target=worker)
        t.start()
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


def _wait_connected(port, tries=100):
    import time
    for _ in range(tries):
        s = json.loads(_get(port, "/api/status")[1])
        if s["connected"]:
            return s
        time.sleep(0.1)
    raise AssertionError("hub never connected")


def test_endpoints_and_push():
    def body(port):
        status, page = _get(port, "/")
        assert status == 200 and b"Layout Link" in page

        s = _wait_connected(port)
        assert s["hasLayout"] is True and s["kind"] == "local"
        assert s["qr"] and "ws://" in s["qr"]

        status, raw = _get(port, "/api/contract")
        c = json.loads(raw)
        assert c["triggers"][0]["command"] == "set-brightness"
        assert c["feeds"][0]["expects"]["type"] == "number"

        status, raw = _get(port, "/api/stub")
        assert b"carterkit" in raw and b"set_brightness" in raw

        status, raw = _get(port, "/api/layout")
        assert json.loads(raw)["name"] == "Explore Test"

        # SSE: subscribe, then push, and expect the push event on the stream
        got = {}

        def listen():
            req = urllib.request.Request(f"http://127.0.0.1:{port}/events")
            with urllib.request.urlopen(req, timeout=15) as r:
                for line in r:
                    if line.startswith(b"data: "):
                        got["evt"] = json.loads(line[6:])
                        return

        lt = threading.Thread(target=listen)
        lt.start()
        import time
        time.sleep(0.3)                      # let the SSE subscription arm
        status, res = _post(port, "/api/push", {"id": "cpu", "value": 55})
        assert res["ok"] and res["frame"] == {"msg_type": "metrics", "cpu": 55}
        lt.join(timeout=10)
        assert got["evt"]["kind"] == "push" and got["evt"]["data"]["cpu"] == 55

        # error path: slider has no sync binding -> hub refuses -> JSON 500
        try:
            _post(port, "/api/push", {"id": "bright", "value": 1})
            raise AssertionError("expected HTTPError")
        except urllib.error.HTTPError as e:
            assert "no sync binding" in json.loads(e.read())["error"]

    _run_explorer(body)


def test_post_error_is_json():
    def body(port):
        try:
            _post(port, "/api/push", {"value": 1})       # missing id
            raise AssertionError("expected HTTPError")
        except urllib.error.HTTPError as e:
            assert json.loads(e.read())["error"]

    _run_explorer(body)


def test_build_explorer_modes(tmp_path):
    lay = tmp_path / "l.json"
    lay.write_text(json.dumps(LAYOUT))
    ex = build_explorer(str(lay))
    assert ex.hub.layout["name"] == "Explore Test" and ex.pull is None

    ex = build_explorer(None)
    assert ex.hub.layout is None and ex.pull == "current"
    assert ex.hub.connection.kind == "local"

    ex = build_explorer(None, device="my-dash.json")
    assert ex.pull == {"file": "my-dash.json"}
    ex = build_explorer(None, device="My Dash")
    assert ex.pull == {"name": "My Dash"}

    ex = build_explorer("ws://192.168.1.9:8765", channel="lab")
    assert ex.hub.connection.kind == "selfhosted"
    assert ex.hub.connection.channel == "lab"
