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
        assert s["qrMatrix"] and len(s["qrMatrix"]) == len(s["qrMatrix"][0])

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


# ── Studio Mirror ────────────────────────────────────────────────────────────
# The phone narrates its navigation with `studio.event` broadcasts during a Studio
# Session (see the app's AppState+StudioMirror.swift). The explorer demuxes them out
# of the generic broadcast passthrough, folds them into `mirror`, and follows the
# phone by re-pulling the contract whenever it opens a different layout.


def _studio(event, **fields):
    return {"msg_type": "studio.event", "event": event, **fields}


def _fresh_explorer():
    hub = Hub(LAYOUT, None, name="layout-link", port=_free_port())
    return Explorer(hub, port=_free_port(), pull="current")


def test_studio_event_demux_publishes_studio_kind():
    ex = _fresh_explorer()
    q = ex.subscribe()
    ex.on_studio_event(_studio("hello", device="Carter's iPhone",
                               appVersion="1.0", layout=None))
    evt = q.get_nowait()
    assert evt["kind"] == "studio" and evt["event"] == "hello"
    assert evt["data"]["device"] == "Carter's iPhone"
    assert "ts" in evt                      # the SSE layer stamps time, not the wire


def test_studio_events_track_mirror_state():
    ex = _fresh_explorer()
    assert ex.mirror["alive"] is False

    ex.on_studio_event(_studio("hello", device="iPhone", appVersion="1.0", layout=None))
    assert ex.mirror["device"] == "iPhone" and ex.mirror["alive"] is True

    ex.on_studio_event(_studio("layout", layout="Rack", layoutId="rack.json",
                               tabs=[{"id": "One", "title": "One"},
                                     {"id": "Two", "title": "Two"}],
                               controls=7, tab="One"))
    assert ex.mirror["layout"] == "Rack" and ex.mirror["layoutId"] == "rack.json"
    assert ex.mirror["controls"] == 7 and ex.mirror["tab"] == "One"
    assert [t["id"] for t in ex.mirror["tabs"]] == ["One", "Two"]

    ex.on_studio_event(_studio("tab", tab="Two", title="Two", index=1))
    assert ex.mirror["tab"] == "Two"

    ex.on_studio_event(_studio("action", control="lamp", controlType="toggle",
                               payload={"msg_type": "set-lamp", "on": True}))
    assert ex.mirror["lastEvent"] == "action"
    assert ex.mirror["layout"] == "Rack"     # activity doesn't disturb the layout

    ex.on_studio_event(_studio("layout-closed"))
    assert ex.mirror["layout"] is None and ex.mirror["tabs"] == []
    assert ex.mirror["alive"] is True        # closing a layout doesn't end the session

    ex.on_studio_event(_studio("bye"))
    assert ex.mirror["alive"] is False


def test_studio_layout_event_requests_a_repull():
    """The phone navigated, so the contract on screen is the wrong one."""
    ex = _fresh_explorer()

    async def run():
        ex.loop = asyncio.get_running_loop()
        ex._repull = asyncio.Event()
        ex.on_studio_event(_studio("tab", tab="Two", title="Two", index=1))
        await asyncio.sleep(0)
        assert not ex._repull.is_set(), "a tab switch is not a new contract"
        ex.on_studio_event(_studio("layout", layout="Rack", layoutId="rack.json",
                                   tabs=[], controls=0, tab=""))
        await asyncio.sleep(0)
        assert ex._repull.is_set()

    asyncio.run(run())


def test_status_carries_mirror():
    def body(port):
        _wait_connected(port)
        s = json.loads(_get(port, "/api/status")[1])
        assert "mirror" in s
        assert s["mirror"]["alive"] is False and s["mirror"]["layout"] is None

    _run_explorer(body)


def test_prime_mirror_fills_a_blank_mirror_from_the_pull():
    """A late/restarted explorer missed the phone's hello, so the Device Mirror would
    sit empty forever. The routed pull carries the same facts — derive them."""
    ex = _fresh_explorer()
    ex.peers = ["Carter's iPhone"]
    ex.device_info = {"ok": True, "appVersion": "1.0", "build": "42"}

    ex.prime_mirror(LAYOUT)

    assert ex.mirror["device"] == "Carter's iPhone"
    assert ex.mirror["appVersion"] == "1.0"
    assert ex.mirror["layout"] == "Explore Test"
    assert ex.mirror["tabs"] == [{"id": "Main", "title": "Main"}]
    assert ex.mirror["tab"] == "Main"
    assert ex.mirror["controls"] == 2          # slider + gauge, groups excluded


def test_prime_mirror_never_overwrites_what_the_phone_said():
    """An inference must never beat a fact: whatever arrived over `studio.event`
    wins, and priming only fills the gaps around it."""
    ex = _fresh_explorer()
    ex.peers = ["Some Other Phone"]
    ex.on_studio_event(_studio("hello", device="Carter's iPhone",
                               appVersion="9.9", layout=None))
    ex.on_studio_event(_studio("layout", layout="Rack", layoutId="rack.json",
                               tabs=[{"id": "Power", "title": "Power"}],
                               controls=7, tab="Power"))

    ex.prime_mirror(LAYOUT)

    assert ex.mirror["device"] == "Carter's iPhone"
    assert ex.mirror["appVersion"] == "9.9"
    assert ex.mirror["layout"] == "Rack"
    assert ex.mirror["tabs"] == [{"id": "Power", "title": "Power"}]
    assert ex.mirror["controls"] == 7
    assert ex.mirror["alive"] is True


def test_generic_broadcast_passthrough_is_unchanged():
    """Regression guard: only studio.event is demuxed; every other frame still
    publishes as a generic broadcast on the wire log."""
    ex = _fresh_explorer()
    published = []
    ex.publish = published.append
    ex._arm()
    ex.hub._user_broadcast({"msg_type": "metrics", "cpu": 12})
    assert published[-1]["kind"] == "broadcast"
    assert published[-1]["command"] == "metrics"
    assert ex.mirror["lastEvent"] is None

    ex.hub._user_broadcast(_studio("hello", device="x", appVersion="1", layout=None))
    assert published[-1]["kind"] == "studio"
    assert ex.mirror["device"] == "x"


# ── Controls (the device view) ───────────────────────────────────────────────
# Triggers/Feeds only surface meshsocket-bound controls, so a demo-style layout has
# nothing to drive. The Controls section lists EVERY control and drives it by id over
# the routed `set-control-state` verb.

DEMO_LAYOUT = {                      # no connection, no sync — nothing on the wire
    "name": "Demo",
    "tabs": [{
        "title": "Main",
        "children": [
            {"type": "toggle", "id": "lamp", "label": "Lamp"},
            {"type": "gauge", "id": "cpu", "label": "CPU", "min": 0, "max": 100},
            {"type": "group", "id": "g", "label": "G", "children": [
                {"type": "sparkline", "id": "trend", "label": "Trend"},
            ]},
        ],
    }],
}


def test_extract_controls_lists_every_control_wired_or_not():
    from carterkit.explore import extract_controls

    controls = extract_controls(DEMO_LAYOUT)
    assert [c["id"] for c in controls] == ["lamp", "cpu", "trend"]
    assert [c["type"] for c in controls] == ["toggle", "gauge", "sparkline"]
    # Typed inputs are inferred from the control kind.
    assert [c["expects"] for c in controls] == ["boolean", "number", "array"]
    assert controls[2]["where"] == "Main › G", "nested controls carry their location"
    # The wire-contract view is empty for this layout — that is the whole point.
    from carterkit.contract import extract_contract
    c = extract_contract(DEMO_LAYOUT)
    assert not c["triggers"] and not c["feeds"]


def test_adopting_a_layout_builds_the_controls_list():
    ex = _fresh_explorer()
    ex._adopt(DEMO_LAYOUT)
    assert [c["id"] for c in ex.controls] == ["lamp", "cpu", "trend"]
    assert ex.control_values == {}, "values are re-seeded from the device, not guessed"


def test_set_control_values_routes_the_verb_and_tracks_applied():
    """/api/set → routed `set-control-state` with the exact wire payload; only ids the
    device says it applied move in our local copy."""
    ex = _fresh_explorer()
    ex._adopt(DEMO_LAYOUT)
    sent = {}

    async def fake_routed(verb, payload, timeout=10.0):
        sent["verb"], sent["payload"] = verb, payload
        return {"ok": True, "applied": ["lamp"], "skipped": ["ghost"]}

    ex._routed = fake_routed
    res = asyncio.run(ex.set_control_values({"lamp": True, "ghost": 1}))

    assert sent["verb"] == "set-control-state"
    assert sent["payload"] == {"values": {"lamp": True, "ghost": 1}}
    assert res["applied"] == ["lamp"] and res["skipped"] == ["ghost"]
    assert ex.control_values == {"lamp": True}, "a skipped id must not be recorded"


def test_seed_control_values_from_the_device():
    ex = _fresh_explorer()
    ex._adopt(DEMO_LAYOUT)
    published = []
    ex.publish = published.append

    async def fake_routed(verb, payload, timeout=10.0):
        assert verb == "get-control-state"
        return {"ok": True, "values": {"lamp": True, "cpu": 42}}

    ex._routed = fake_routed
    asyncio.run(ex._seed_control_values())

    assert ex.control_values == {"lamp": True, "cpu": 42}
    assert published[-1]["kind"] == "controls"


def test_mirror_value_event_updates_the_control_store():
    """The user moved it on the phone — the Controls row must follow."""
    ex = _fresh_explorer()
    ex._adopt(DEMO_LAYOUT)
    ex.on_studio_event(_studio("value", control="lamp", value=True))
    assert ex.control_values["lamp"] is True


# The app's `get-current-layout` echo re-encodes its own model, and older builds emit
# group nodes with NO `type` (the Swift GroupDefinition has no such field). Walkers that
# keyed on `type == "group"` stopped there: nested controls vanished and the group itself
# leaked through as a `type: "?"` row. Every walker must accept the implicit shape.

ECHOED_LAYOUT = {                    # exactly what an older app echoes back
    "name": "Echoed",
    "tabs": [{
        "title": "Main",
        "children": [
            {"type": "gauge", "id": "cpu", "label": "CPU"},
            {"id": "rack", "label": "Rack", "children": [          # ← no "type"
                {"type": "toggle", "id": "lamp", "label": "Lamp"},
                {"id": "inner", "label": "Inner", "children": [    # ← nested, no "type"
                    {"type": "label", "id": "deep", "label": "Deep"},
                ]},
            ]},
        ],
    }],
}


def test_is_group_accepts_the_implicit_shape():
    from carterkit.contract import is_group

    assert is_group({"type": "group", "children": []})
    assert is_group({"id": "rack", "children": []}), "children + no type is a group"
    assert not is_group({"type": "gauge", "id": "cpu"})
    assert not is_group({"type": "carousel", "id": "c", "panels": []}), \
        "container controls nest under `panels`, not `children`"


def test_walk_descends_into_untyped_groups():
    from carterkit.contract import walk_with_location

    seen = {c.get("id"): (tab, crumb) for c, tab, crumb in walk_with_location(ECHOED_LAYOUT)}
    assert set(seen) == {"cpu", "rack", "lamp", "inner", "deep"}
    assert seen["deep"] == ("Main", ["Rack", "Inner"]), "breadcrumbs survive both groups"


def test_extract_controls_skips_untyped_groups():
    from carterkit.explore import extract_controls

    controls = extract_controls(ECHOED_LAYOUT)
    assert [c["id"] for c in controls] == ["cpu", "lamp", "deep"]
    assert not [c for c in controls if c["type"] == "?"], \
        "a group must never leak through as an unknown-type row"
    assert controls[2]["where"] == "Main › Rack › Inner"


def test_prime_mirror_counts_controls_not_groups():
    ex = _fresh_explorer()
    ex.prime_mirror(ECHOED_LAYOUT)
    assert ex.mirror["controls"] == 3, "groups are containers, not controls"


def test_hub_indexes_controls_under_untyped_groups():
    """The push/handle index must find nested controls in an echoed layout too."""
    hub = Hub(ECHOED_LAYOUT, None, name="layout-link", port=_free_port())
    assert set(hub._index) == {"cpu", "rack", "lamp", "inner", "deep"}


def test_controls_endpoint_serves_the_device_view():
    def body(port):
        _wait_connected(port)
        d = json.loads(_get(port, "/api/controls")[1])
        assert "controls" in d and "values" in d
        assert [c["id"] for c in d["controls"]] == ["bright", "cpu"]

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
