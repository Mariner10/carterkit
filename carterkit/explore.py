"""Layout Link — a live, typed endpoint explorer for a layout.

`carterkit explore` turns the layout on your phone into a browsable API:

* **Triggers** — every action the layout's controls fire, with its wire shape
  and the native type of each ``{{token}}``; fires flash live as you tap them.
* **Data feeds** — every sync binding, with the scalar type it expects and a
  typed input to push values straight onto the phone.
* **Live wire** — every frame crossing the channel, both directions.
* A downloadable typed server stub (`bridge.py`) and contract JSON.

Zero-config flow: ``carterkit explore`` starts an embedded LocalRelay, prints
the pairing QR JSON, and the moment the phone scans in (Studio Session → scan) the
explorer pulls the phone's current layout over the mesh (`get-current-layout`)
and renders its contract. Point it at a saved layout instead with
``--device my-layout.json``, or explore a local file offline with
``carterkit explore my-layout.json``.

Stdlib only (http.server + SSE) — the HTTP side runs in threads and hops onto
the Hub's asyncio loop with ``run_coroutine_threadsafe``.
"""

from __future__ import annotations

import asyncio
import functools
import json
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .codegen import generate_service_stub
from .contract import extract_contract, is_group, walk_with_location
from .explore_html import PAGE
from .hub import Hub
from .qr import encode as _qr_encode

_PULL_VERBS = {"current": ("get-current-layout", {"include": "full"})}

#: Studio Mirror — the phone's narration of what the user is doing during a Studio
#: Session. Every frame is a broadcast carrying this ``msg_type`` plus a flat ``event``
#: discriminator (``hello``/``layout``/``layout-closed``/``tab``/``action``/``value``/
#: ``bye``). The session's socket is authoritative on the phone, so the user can
#: navigate to any layout and it stays wired to *this* explorer — these events are how
#: we find out. See the app's ``AppState+StudioMirror.swift`` for the emitting side.
STUDIO_EVENT = "studio.event"


def extract_controls(layout: dict) -> list[dict]:
    """Every control the layout renders, flat and in document order.

    The Triggers/Data-feeds view is the *wire contract* — only controls with a
    meshsocket binding appear there, so a demo-style layout (no `connection`, no
    `sync`) shows an empty page and nothing to drive. This is the *device* view: it
    lists controls whether or not they are wired to anything, because the routed
    `set-control-state` verb can drive any of them by id.
    """
    out = []
    for ctrl, tab, crumb in walk_with_location(layout):
        cid, ctype = ctrl.get("id"), ctrl.get("type", "?")
        # `is_group` also catches the implicit shape (children, no `type`) an older
        # app echoes — those are containers, not rows to drive.
        if not cid or is_group(ctrl):
            continue
        out.append({
            "id": cid,
            "type": ctype,
            "label": ctrl.get("label") or cid,
            "where": " › ".join([tab] + crumb),
            # What the app will accept for this control, so the page can pick an input.
            "expects": _control_input_type(ctrl),
            "options": ctrl.get("options"),
            "min": ctrl.get("min"),
            "max": ctrl.get("max"),
            "step": ctrl.get("step"),
        })
    return out


#: Controls whose value is a *buffer* the device appends to rather than a scalar.
_ARRAY_CONTROLS = {"sparkline", "list", "cardList", "logConsole"}
_BOOL_CONTROLS = {"toggle", "statusLight"}
_NUMBER_CONTROLS = {"slider", "gauge", "progressRing", "stepper", "compass"}
#: Scalar-valued controls whose value is a JSON *document* string (graph nodes, board
#: columns, chart series …) rather than a plain scalar.
_JSON_CONTROLS = {"graph", "chart", "pieChart", "heatmap", "radar", "boxPlot", "gantt",
                  "sankey", "treemap", "chord", "map", "sortboard", "pinboard", "canvas"}


def _control_input_type(ctrl: dict) -> str:
    """The input widget kind for a control: ``boolean``/``number``/``enum``/``array``/
    ``json``/``string``. Mirrors how the app routes an incoming value by declared type."""
    ctype = ctrl.get("type")
    if ctrl.get("options"):
        return "enum"
    if ctype in _BOOL_CONTROLS:
        return "boolean"
    if ctype in _NUMBER_CONTROLS:
        return "number"
    if ctype in _ARRAY_CONTROLS:
        return "array"
    if ctype in _JSON_CONTROLS:
        return "json"
    return "string"


def _blank_mirror() -> dict:
    """The mirror state before the phone has said anything."""
    return {"device": None, "appVersion": None, "layout": None, "layoutId": None,
            "tabs": [], "tab": None, "controls": None,
            "alive": False, "lastEvent": None, "ts": None}


@functools.lru_cache(maxsize=4)
def _qr_matrix_for(payload: str) -> list[list[bool]]:
    """The pairing QR's module matrix for `payload` — cached, since `status()`
    is polled every few seconds but the pairing payload never changes mid-run."""
    return _qr_encode(payload, ecc="M").matrix


class Explorer:
    """Serve the explorer for ``hub``. ``pull`` names what to fetch off the
    first device that joins: ``"current"``, ``{"file": …}``, ``{"name": …}``,
    or ``None`` (the hub already has its layout)."""

    def __init__(self, hub: Hub, *, port: int = 8770, pull=None):
        self.hub = hub
        self.port = port
        self.pull = pull
        self.loop: asyncio.AbstractEventLoop | None = None
        self.contract: dict | None = None
        self.connected = False
        self.connect_error: str | None = None
        self.peers: list[str] = []
        self.device_info: dict | None = None
        #: Live Studio Mirror state, fed by `studio.event` frames and surfaced in
        #: `status()["mirror"]` for the web UI's Device Mirror panel.
        self.mirror: dict = _blank_mirror()
        #: The device view: every control in the layout (not just wire-bound ones),
        #: with the last value we know for each. Drives the Controls section.
        self.controls: list[dict] = []
        self.control_values: dict = {}
        self._armed: set[str] = set()
        self._subs: list[queue.Queue] = []
        self._httpd: ThreadingHTTPServer | None = None
        self._repull = asyncio.Event()

    # ── event bus (loop thread → HTTP/SSE threads) ───────────────────────────
    def publish(self, evt: dict) -> None:
        evt.setdefault("ts", time.time())
        for q in list(self._subs):
            try:
                q.put_nowait(evt)
            except queue.Full:
                pass

    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=500)
        self._subs.append(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        try:
            self._subs.remove(q)
        except ValueError:
            pass

    # ── contract / observers ─────────────────────────────────────────────────
    def _adopt(self, layout: dict) -> None:
        self.hub.adopt_layout(layout)
        self.contract = extract_contract(layout)
        self.controls = extract_controls(layout)
        self.control_values = {}          # re-seeded from the device by _seed_control_values
        self._arm()
        self.publish({"kind": "contract"})

    def _arm(self) -> None:
        """Register an observer for every trigger command (idempotent), plus a
        catch-all for everything else on the wire."""
        for trig in (self.contract or {}).get("triggers", []):
            cmd = trig["command"]
            if cmd in self._armed:
                continue
            self._armed.add(cmd)

            def observer(data, _cmd=cmd):
                self.publish({"kind": "trigger", "command": _cmd, "data": data})
                return {"ok": True}       # resolves request-mode routed actions

            self.hub.on(cmd, observer)

        if "\0catchall" not in self._armed:
            self._armed.add("\0catchall")

            @self.hub.on_broadcast
            def _rest(data):
                # Studio Mirror frames are navigation narration, not layout data —
                # demux them out before the generic broadcast passthrough so the
                # mirror panel gets typed events and the wire log stays honest.
                if isinstance(data, dict) and data.get("msg_type") == STUDIO_EVENT:
                    self.on_studio_event(data)
                    return
                self.publish({"kind": "broadcast",
                              "command": (data or {}).get("msg_type"),
                              "data": data})

    # ── studio mirror ────────────────────────────────────────────────────────
    def on_studio_event(self, frame: dict) -> None:
        """Fold one `studio.event` frame into `self.mirror` and republish it as an
        SSE `studio` event. A `layout` event also asks the watcher to re-pull
        `get-current-layout`: the phone navigated, so the contract on screen is now
        the wrong one — this is what makes the explorer follow the user around."""
        event = frame.get("event")
        m = self.mirror
        m["lastEvent"] = event
        m["ts"] = time.time()
        if event == "hello":
            m.update(device=frame.get("device"), appVersion=frame.get("appVersion"),
                     layout=frame.get("layout"), alive=True)
        elif event == "layout":
            m.update(layout=frame.get("layout"), layoutId=frame.get("layoutId"),
                     tabs=frame.get("tabs") or [], controls=frame.get("controls"),
                     tab=frame.get("tab"), alive=True)
        elif event == "layout-closed":
            m.update(layout=None, layoutId=None, tabs=[], tab=None, controls=None)
        elif event == "tab":
            m["tab"] = frame.get("tab")
        elif event == "value" and frame.get("control"):
            # The user just moved it on the phone — keep the Controls row in step.
            self.control_values[frame["control"]] = frame.get("value")
        elif event == "bye":
            m["alive"] = False
        self.publish({"kind": "studio", "event": event, "data": frame})
        # Follow the phone: re-render the contract for whatever it just opened. The
        # last contract is deliberately kept on close/bye — a blank page would lose
        # the work in progress for what is usually a momentary state.
        if event == "layout" and self.loop is not None:
            self.loop.call_soon_threadsafe(self._repull.set)

    # ── device pull ──────────────────────────────────────────────────────────
    async def _routed(self, verb: str, payload, timeout: float = 10.0):
        peer = await self.hub._first_peer()
        if not peer:
            raise RuntimeError("no device on the channel")
        return await self.hub.client._sock.request(
            "route_msg", {"target_id": peer.get("id"), "type": verb,
                          "payload": payload}, timeout=timeout)

    async def _pull_layout(self) -> bool:
        if isinstance(self.pull, dict):
            verb, payload = "get-layout", self.pull
        else:
            verb, payload = _PULL_VERBS["current"]
        res = await self._routed(verb, payload)
        if not (isinstance(res, dict) and res.get("ok") and res.get("layout")):
            err = (res or {}).get("error") if isinstance(res, dict) else "no reply"
            self.publish({"kind": "status", "data": {"pullError": err or "empty reply"}})
            return False
        self._adopt(res["layout"])
        try:
            info = await self._routed("get-device-info", None, timeout=5.0)
            if isinstance(info, dict) and info.get("ok"):
                self.device_info = info
        except Exception:
            pass
        # Name the device we actually pulled from, not just "some peer" — on a channel
        # with more than one member `peers[0]` need not be the phone.
        try:
            peer = await self.hub._first_peer()
        except Exception:
            peer = None
        self.prime_mirror(res["layout"], device=(peer or {}).get("name"))
        await self._seed_control_values()
        return True

    async def _seed_control_values(self) -> None:
        """Fill the Controls section with what the device currently shows. Best-effort:
        an app too old to answer `get-control-state` just leaves the rows blank."""
        try:
            res = await self._routed("get-control-state", None, timeout=5.0)
        except Exception:
            return
        if isinstance(res, dict) and isinstance(res.get("values"), dict):
            self.control_values = dict(res["values"])
            self.publish({"kind": "controls", "data": {"values": self.control_values}})

    async def set_control_values(self, values: dict) -> dict:
        """Drive controls on the device by id — the routed dual of `get-control-state`,
        and the only path that reaches a control with no `sync` binding. Returns the
        device's truthful `{ok, applied, skipped}` reply."""
        res = await self._routed("set-control-state", {"values": values})
        if not isinstance(res, dict):
            raise RuntimeError("no reply from the device")
        if res.get("error") and not res.get("ok"):
            raise RuntimeError(res["error"])
        # Trust the device about what it actually took: only `applied` ids move here.
        for cid in res.get("applied") or []:
            if cid in values:
                self.control_values[cid] = values[cid]
        return res

    def prime_mirror(self, layout: dict, *, device: str | None = None) -> None:
        """Fill blank mirror fields from what the routed pull already told us.

        The mirror is normally fed by `studio.event` broadcasts, but those are
        fire-and-forget: an explorer started (or restarted) after the phone already
        said hello would show an empty Device Mirror until the user happened to
        navigate. The pull gives us the same facts by request/response, so derive
        them here. Only *empty* fields are filled — anything the phone actually told
        us is the truth and must not be overwritten by an inference.
        """
        m = self.mirror
        if m["device"] is None:
            m["device"] = device or (self.peers[0] if self.peers else None)
        if m["appVersion"] is None and isinstance(self.device_info, dict):
            m["appVersion"] = self.device_info.get("appVersion")
        if m["layout"] is None:
            m["layout"] = layout.get("name")
        if not m["tabs"]:
            # The app keys a tab by its title (`TabDefinition.id == title`).
            m["tabs"] = [{"id": t.get("title"), "title": t.get("title")}
                         for t in layout.get("tabs", []) if isinstance(t, dict)]
        if m["tab"] is None and m["tabs"]:
            m["tab"] = m["tabs"][0]["id"]
        if m["controls"] is None:
            m["controls"] = len(extract_controls(layout))

    async def _watch(self) -> None:
        """Roster poll + auto-pull: notice the phone joining, pull the layout
        when asked to, honour re-pull requests."""
        while True:
            try:
                res = await self.hub.client._sock.request("get_nodes", None, timeout=5.0)
                roster = [c.get("name", "?") for c in (res or {}).get("clients", [])
                          if c.get("name") != self.hub.name]
                if roster != self.peers:
                    self.peers = roster
                    self.publish({"kind": "status", "data": {"peers": roster}})
                want_pull = (self.pull is not None
                             and (self.hub.layout is None or self._repull.is_set()))
                if want_pull and roster:
                    self._repull.clear()
                    await self._pull_layout()
            except Exception:
                pass
            try:
                await asyncio.wait_for(self._repull.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                pass

    # ── HTTP plumbing ────────────────────────────────────────────────────────
    def _call(self, coro, timeout: float = 15.0):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout)

    def status(self) -> dict:
        conn = self.hub.connection
        pairing = self.hub.qr_json() if conn.kind in ("local", "selfhosted") else None
        return {"connected": self.connected, "kind": conn.kind,
                "channel": conn.channel, "connectError": self.connect_error,
                "url": conn.url, "port": getattr(conn, "port", None),
                "peers": self.peers, "hasLayout": self.hub.layout is not None,
                "qr": pairing,
                "qrMatrix": _qr_matrix_for(pairing) if pairing else None,
                "device": self.device_info,
                "mirror": dict(self.mirror)}

    def start_http(self) -> None:
        explorer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, body, ctype="application/json", status=200, download=None):
                if isinstance(body, (dict, list)):
                    body = json.dumps(body, indent=1)
                data = body.encode() if isinstance(body, str) else body
                self.send_response(status)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                if download:
                    self.send_header("Content-Disposition",
                                     f'attachment; filename="{download}"')
                self.end_headers()
                self.wfile.write(data)

            def _err(self, msg, status=400):
                self._send({"error": str(msg)}, status=status)

            def do_GET(self):
                path = self.path.split("?")[0]
                if path == "/":
                    return self._send(PAGE, "text/html; charset=utf-8")
                if path == "/api/status":
                    return self._send(explorer.status())
                if path == "/api/contract":
                    if explorer.contract is None:
                        return self._err("no layout yet", 404)
                    return self._send(explorer.contract)
                if path == "/api/controls":
                    return self._send({"controls": explorer.controls,
                                       "values": explorer.control_values})
                if path == "/api/layout":
                    if explorer.hub.layout is None:
                        return self._err("no layout yet", 404)
                    return self._send(explorer.hub.layout)
                if path == "/api/stub":
                    if explorer.hub.layout is None:
                        return self._err("no layout yet", 404)
                    stub = generate_service_stub(explorer.hub.layout)
                    return self._send(stub, "text/x-python", download="bridge.py")
                if path == "/events":
                    return self._sse()
                self._err("not found", 404)

            def do_POST(self):
                length = int(self.headers.get("Content-Length") or 0)
                try:
                    body = json.loads(self.rfile.read(length) or b"{}")
                except json.JSONDecodeError:
                    return self._err("body must be JSON")
                path = self.path.split("?")[0]
                try:
                    if path == "/api/push":
                        frame = explorer._call(
                            explorer.hub.push(body["id"], body.get("value")))
                        explorer.publish({"kind": "push", "command": body["id"],
                                          "data": frame})
                        return self._send({"ok": True, "frame": frame})
                    if path == "/api/fill":
                        payload = explorer._call(
                            explorer.hub.fill(body["id"], body.get("children") or []))
                        explorer.publish({"kind": "push", "command": body["id"],
                                          "data": payload})
                        return self._send({"ok": True})
                    if path == "/api/set":
                        # {"values": {...}} or the single-control sugar {"id":…,"value":…}
                        values = body.get("values")
                        if values is None:
                            values = {body["id"]: body.get("value")}
                        res = explorer._call(explorer.set_control_values(values))
                        explorer.publish({"kind": "set", "command": ",".join(values),
                                          "data": {"values": values, "reply": res}})
                        return self._send({"ok": True, **res})
                    if path == "/api/repull":
                        explorer.loop.call_soon_threadsafe(explorer._repull.set)
                        return self._send({"ok": True})
                except KeyError as e:
                    return self._err(f"missing field {e}")
                except Exception as e:
                    return self._err(e, 500)
                self._err("not found", 404)

            def _sse(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                q = explorer.subscribe()
                try:
                    while True:
                        try:
                            evt = q.get(timeout=15)
                            self.wfile.write(
                                f"data: {json.dumps(evt)}\n\n".encode())
                        except queue.Empty:
                            self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    pass
                finally:
                    explorer.unsubscribe(q)

        self._httpd = ThreadingHTTPServer(("127.0.0.1", self.port), Handler)
        threading.Thread(target=self._httpd.serve_forever, daemon=True).start()

    # ── lifecycle ────────────────────────────────────────────────────────────
    async def run(self, *, ready=None) -> None:
        """Serve until cancelled. The web UI comes up immediately; the mesh
        connection happens in the background with retries, so a slow or
        unreachable relay (e.g. a layout whose connection block points at a
        production gateway) never blanks the page. ``ready`` is an optional
        callback invoked once the web server is listening."""
        self.loop = asyncio.get_running_loop()
        self._repull = asyncio.Event()
        if self.hub.layout is not None:
            # The hub was handed a layout up front (`explore my-layout.json`), so it
            # never goes through `_adopt` — build both views here too.
            self.contract = extract_contract(self.hub.layout)
            self.controls = extract_controls(self.hub.layout)
        self.start_http()
        if ready:
            ready(self)
        started = False
        try:
            while not started:
                try:
                    await self.hub.start()
                    started = True
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    self.connect_error = str(e) or type(e).__name__
                    self.publish({"kind": "status",
                                  "data": {"connectError": self.connect_error}})
                    await asyncio.sleep(3.0)
            self.connected = True
            self.connect_error = None
            self._arm()
            self.publish({"kind": "status", "data": {"connected": True}})
            await self._watch()
        except asyncio.CancelledError:
            pass
        finally:
            self.connected = False
            if started:
                try:
                    await self.hub.close()
                except Exception:
                    pass
            if self._httpd:
                self._httpd.shutdown()


def build_explorer(source: str | None = None, *, device: str | None = None,
                   port: int = 8770, **conn_overrides) -> Explorer:
    """Wire up an Explorer from CLI-ish arguments.

    ``source`` is a layout JSON path, a connection artifact (pairing/device
    JSON path or ws:// URL), or None. ``device`` asks to pull off the phone:
    ``"current"``, or a saved layout's ``file``/``name``.
    """
    layout = None
    connection = None
    if source:
        if source.endswith(".json") or source.endswith(".carter"):
            try:
                with open(source) as f:
                    doc = json.load(f)
            except (OSError, json.JSONDecodeError):
                doc = None
            if isinstance(doc, dict) and "tabs" in doc:
                layout = doc              # a layout file
            else:
                connection = source       # a pairing / device credential file
        else:
            connection = source           # a ws:// URL etc.

    pull = None
    if device is not None:
        pull = ("current" if device in ("", "current")
                else {"file": device} if device.endswith(".json")
                else {"name": device})
    elif layout is None:
        pull = "current"                  # zero-config: pull whatever is live

    hub = Hub(layout, connection, name="layout-link", **conn_overrides)
    return Explorer(hub, port=port, pull=pull)
