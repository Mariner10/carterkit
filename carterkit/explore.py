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
import json
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .codegen import generate_service_stub
from .contract import extract_contract
from .explore_html import PAGE
from .hub import Hub

_PULL_VERBS = {"current": ("get-current-layout", {"include": "full"})}


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
                self.publish({"kind": "broadcast",
                              "command": (data or {}).get("msg_type"),
                              "data": data})

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
        return True

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
        return {"connected": self.connected, "kind": conn.kind,
                "channel": conn.channel, "connectError": self.connect_error,
                "url": conn.url, "port": getattr(conn, "port", None),
                "peers": self.peers, "hasLayout": self.hub.layout is not None,
                "qr": self.hub.qr_json() if conn.kind in ("local", "selfhosted") else None,
                "device": self.device_info}

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
            self.contract = extract_contract(self.hub.layout)
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
