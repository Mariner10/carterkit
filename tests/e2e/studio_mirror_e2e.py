#!/usr/bin/env python3
"""Studio Mirror end-to-end — the protocol, without a simulator.

Stands up a real `carterkit explore` Explorer on an embedded LocalRelay, joins a
**fake phone** (a plain `CarterClient` identifying the way the app does during a
Studio Session), and replays the exact `studio.event` sequence the app emits:

    hello → layout → tab → action → value → bye

then asserts, over HTTP, that the explorer tracked it:

* ``/api/status`` → ``mirror`` reflects device / layout / active tab / alive
* ``/events``     → each frame arrives as an SSE ``{"kind": "studio", ...}``
* ``/api/contract`` → re-pulled and re-rendered for the layout the phone opened
  (the fake phone answers the routed ``get-current-layout`` read-back)

This is the wire contract both repos must agree on; the real-simulator smoke test
(AUTO_PAIR + AUTO_LAYOUT) is a separate, manual pass.

Run:  cd carterkit && .venv/bin/python tests/e2e/studio_mirror_e2e.py
Exits 0 on success, 1 on the first failed assertion.
"""

from __future__ import annotations

import asyncio
import json
import socket
import sys
import threading
import urllib.request

from carterkit.client import CarterClient
from carterkit.explore import Explorer
from carterkit.hub import Hub

# ── the layout the fake phone claims to have open ────────────────────────────
PHONE_LAYOUT = {
    "name": "Rack Monitor",
    "version": 1,
    "tabs": [
        {"title": "Power", "icon": "bolt.fill",
         "grid": {"columns": 4, "rows": 8},
         "children": [
             {"type": "toggle", "id": "lamp", "position": [0, 0], "label": "Lamp",
              "action": {"method": "meshsocket", "mode": "broadcast",
                         "event": "broadcast_request",
                         "payload": {"msg_type": "set-lamp", "on": "{{value}}"}}},
             {"type": "gauge", "id": "cpu", "position": [0, 1], "label": "CPU",
              "min": 0, "max": 100,
              "sync": [{"method": "meshsocket", "type": "listen", "event": "broadcast",
                        "filter": {"msg_type": "metrics"}, "valuePath": "cpu"}]},
             # A group exactly as an OLDER app echoes it: children, but NO "type".
             # The app's GroupDefinition has no `type` field, so a re-encoded layout
             # used to emit this shape — and a walker keyed on type == "group" stopped
             # here, losing every nested control and leaking the group as a "?" row.
             # Echoing the lossy shape on purpose keeps that regression caught.
             {"id": "rack", "position": [0, 2], "label": "Rack",
              "grid": {"columns": 2, "rows": 2},
              "children": [
                  {"type": "statusLight", "id": "psu", "position": [0, 0], "label": "PSU"},
              ]},
         ]},
        {"title": "Network", "icon": "wifi",
         "grid": {"columns": 4, "rows": 8}, "children": []},
    ],
}

TABS = [{"id": t["title"], "title": t["title"]} for t in PHONE_LAYOUT["tabs"]]

#: The scripted session, in emission order.
SCRIPT = [
    {"event": "hello", "device": "Fake iPhone", "appVersion": "1.0", "layout": None},
    {"event": "layout", "layout": "Rack Monitor", "layoutId": "rack-monitor.json",
     "tabs": TABS, "controls": 3, "tab": "Power"},
    {"event": "tab", "tab": "Network", "title": "Network", "index": 1},
    {"event": "action", "control": "lamp", "controlType": "toggle",
     "payload": {"msg_type": "set-lamp", "on": True}},
    {"event": "value", "control": "lamp", "value": True},
]


# ── tiny assertion + HTTP helpers ────────────────────────────────────────────
_checks = 0


def check(cond, what):
    global _checks
    _checks += 1
    if not cond:
        raise AssertionError(what)
    print(f"  ✓ {what}")


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def get_json(port, path):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as r:
        return json.loads(r.read())


def _post_json_blocking(port, path, body):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


async def post_json(port, path, body):
    """POST off the loop thread. Endpoints that talk to the device hop onto this
    same event loop (`run_coroutine_threadsafe(...).result()`), so calling them
    synchronously from a coroutine would deadlock the loop against itself."""
    return await asyncio.to_thread(_post_json_blocking, port, path, body)


class SSEReader:
    """Collect `/events` frames on a background thread."""

    def __init__(self, port):
        self.events: list[dict] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, args=(port,), daemon=True)

    def start(self):
        self._thread.start()
        return self

    def _run(self, port):
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/events")
            with urllib.request.urlopen(req, timeout=60) as r:
                for line in r:
                    if self._stop.is_set():
                        return
                    if line.startswith(b"data: "):
                        self.events.append(json.loads(line[6:]))
        except Exception:
            pass

    def stop(self):
        self._stop.set()

    def studio(self, event):
        return [e for e in self.events
                if e.get("kind") == "studio" and e.get("event") == event]


async def wait_for(predicate, what, timeout=15.0, interval=0.1):
    """Poll `predicate` (sync, called off the loop's critical path) until true."""
    waited = 0.0
    while waited < timeout:
        if predicate():
            return
        await asyncio.sleep(interval)
        waited += interval
    raise AssertionError(f"timed out waiting for {what}")


# ── the run ──────────────────────────────────────────────────────────────────
async def main() -> int:
    web_port, relay_port = free_port(), free_port()
    hub = Hub(None, None, name="layout-link", port=relay_port)
    explorer = Explorer(hub, port=web_port, pull="current")

    started = asyncio.Event()
    task = asyncio.ensure_future(explorer.run(ready=lambda _e: started.set()))
    await asyncio.wait_for(started.wait(), timeout=10)
    await wait_for(lambda: explorer.connected, "the explorer to reach the relay")

    sse = SSEReader(web_port).start()
    await asyncio.sleep(0.4)                       # let the SSE subscription arm

    # The fake phone joins exactly as the app does after a QR pair: same channel,
    # broadcast rights on (Studio Mirror events are broadcasts), routing off.
    pairing = json.loads(hub.qr_json())
    phone = CarterClient(pairing["url"], pairing.get("token") or "",
                         pairing["channel"], role=pairing.get("role", "viewer"),
                         name="Fake iPhone")

    # The routed read-back the explorer's auto-pull calls — the app's
    # `get-current-layout` responder.
    phone.on("get-current-layout", lambda _p: {"ok": True, "layout": PHONE_LAYOUT})
    phone.on("get-device-info", lambda _p: {"ok": True, "appVersion": "1.0",
                                            "build": "1", "protocolVersion": 1})

    # The device's control state, and the `get`/`set` duals over it. `set-control-state`
    # answers truthfully: unknown ids come back as skipped, never as an error.
    device_state = {"lamp": False, "cpu": 12, "psu": "green"}
    known = {"lamp", "cpu", "psu"}

    phone.on("get-control-state", lambda _p: {"ok": True, "values": dict(device_state)})

    def _set_control_state(payload):
        values = (payload or {}).get("values") or {}
        applied = sorted(k for k in values if k in known)
        skipped = sorted(k for k in values if k not in known)
        for k in applied:
            device_state[k] = values[k]
        return {"ok": True, "applied": applied, "skipped": skipped}

    phone.on("set-control-state", _set_control_state)
    await phone.connect()

    try:
        print("\nStudio Mirror E2E")
        print("─────────────────")

        await wait_for(lambda: explorer.peers, "the phone to appear on the roster")

        # ── priming: the phone has said nothing yet, but the routed pull already
        # told us everything the mirror needs. This is the "explorer started late /
        # restarted" case, which otherwise showed a permanently blank panel. ──
        await wait_for(lambda: explorer.contract is not None,
                       "the explorer's auto-pull of the phone's layout")
        primed = explorer.mirror
        check(primed["device"] == "Fake iPhone", "primed the device from the pull")
        check(primed["appVersion"] == "1.0", "primed the app version from get-device-info")
        check(primed["layout"] == "Rack Monitor", "primed the layout name from the pull")
        check([t["id"] for t in primed["tabs"]] == ["Power", "Network"],
              "primed the tabs from the pulled layout")
        check(primed["tab"] == "Power", "primed the initial tab")
        check(primed["controls"] == 3,
              "primed the control count — controls only, groups excluded")
        check(primed["alive"] is False,
              "priming is an inference — it does not claim the session said hello")

        for frame in SCRIPT:
            await phone.broadcast_frame({"msg_type": "studio.event", **frame})
            await asyncio.sleep(0.15)

        # ── /events: every frame arrived typed, not as a generic broadcast ──
        await wait_for(lambda: len(sse.studio("value")) >= 1,
                       "the value event on the SSE stream")
        for event in ("hello", "layout", "tab", "action", "value"):
            check(len(sse.studio(event)) >= 1, f"SSE carried the '{event}' event")
        check(not [e for e in sse.events
                   if e.get("kind") == "broadcast"
                   and (e.get("data") or {}).get("msg_type") == "studio.event"],
              "studio frames are demuxed, never published as generic broadcasts")
        action = sse.studio("action")[0]["data"]
        check(action["control"] == "lamp" and action["controlType"] == "toggle",
              "the action event names the control and its type")
        check(action["payload"] == {"msg_type": "set-lamp", "on": True},
              "the action event carries the substituted payload as sent")

        # ── /api/status: the mirror tracked the session ──
        status = get_json(web_port, "/api/status")
        m = status["mirror"]
        check(m["device"] == "Fake iPhone", "mirror knows the device")
        check(m["appVersion"] == "1.0", "mirror knows the app version")
        check(m["layout"] == "Rack Monitor", "mirror knows the open layout")
        check(m["layoutId"] == "rack-monitor.json", "mirror knows the layout file")
        check(m["controls"] == 3, "mirror knows the control count")
        check([t["id"] for t in m["tabs"]] == ["Power", "Network"], "mirror knows the tabs")
        check(m["tab"] == "Network", "mirror followed the tab switch")
        check(m["alive"] is True, "mirror is alive between hello and bye")
        check(m["lastEvent"] == "value" and m["ts"], "mirror stamps the last event")

        # ── /api/contract: the `layout` event made the explorer re-pull ──
        await wait_for(lambda: explorer.contract is not None,
                       "the explorer to re-pull the phone's layout")
        contract = get_json(web_port, "/api/contract")
        check(contract["layout"]["name"] == "Rack Monitor",
              "the contract followed the phone to the layout it opened")
        check(any(t["command"] == "set-lamp" for t in contract["triggers"]),
              "the re-rendered contract exposes the layout's trigger")
        check(any(f["id"] == "cpu" for f in contract["feeds"]),
              "the re-rendered contract exposes the layout's feed")

        # ── Controls: the device view, drivable even with no wire bindings ──
        controls = get_json(web_port, "/api/controls")
        ids = [c["id"] for c in controls["controls"]]
        check(ids == ["lamp", "cpu", "psu"],
              "the Controls section lists every control, including one nested in a "
              "group the phone echoed WITHOUT a type")
        check([c["expects"] for c in controls["controls"]] == ["boolean", "number", "boolean"],
              "each control gets a typed input inferred from its kind")
        check(not [c for c in controls["controls"] if c["type"] == "?"],
              "a group never leaks through as an unknown-type row")
        check([c["where"] for c in controls["controls"]][2] == "Power › Rack",
              "a nested control carries its group breadcrumb")
        check(controls["values"]["cpu"] == 12,
              "control values are seeded from the device via get-control-state")
        check(controls["values"]["lamp"] is True,
              "a mirrored `value` event moved the row past its seeded value")

        res = await post_json(web_port, "/api/set", {"id": "cpu", "value": 87})
        check(res["applied"] == ["cpu"] and res["skipped"] == [],
              "/api/set round-trips through the routed set-control-state verb")
        check(device_state["cpu"] == 87, "the value actually reached the device")
        check(get_json(web_port, "/api/controls")["values"]["cpu"] == 87,
              "the explorer's copy tracks what the device took")

        res = await post_json(web_port, "/api/set", {"values": {"ghost": 1}})
        check(res["skipped"] == ["ghost"] and res["applied"] == [],
              "an unknown id surfaces as skipped, not as an error")

        # ── closing down: layout-closed keeps the contract, bye ends the session ──
        await phone.broadcast_frame({"msg_type": "studio.event", "event": "layout-closed"})
        await phone.broadcast_frame({"msg_type": "studio.event", "event": "bye"})
        await wait_for(lambda: get_json(web_port, "/api/status")["mirror"]["alive"] is False,
                       "the mirror to go inert on bye")
        final = get_json(web_port, "/api/status")["mirror"]
        check(final["layout"] is None and final["tabs"] == [],
              "layout-closed clears the open layout")
        check(get_json(web_port, "/api/contract")["layout"]["name"] == "Rack Monitor",
              "the last contract is kept after close (the work in progress survives)")

        print(f"\nPASS — {_checks} checks\n")
        return 0
    except AssertionError as e:
        print(f"\nFAIL — {e}\n", file=sys.stderr)
        return 1
    finally:
        sse.stop()
        await phone.close()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
