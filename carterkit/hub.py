"""Hub — drive the layout you just built, through the layout itself.

A layout already declares every control's wire contract: what each display control
listens for (`sync`: filter + valuePath) and what each interactive control emits
(`action`: broadcast_request + msg_type). Hub inverts those bindings at runtime, so
the same object that authored the UI also drives it — no hand-written frames, no
msg_type strings duplicated between the layout and the server:

    from carterkit import Layout

    with Layout("Thermostat") as ui:
        with ui.tab("Main"):
            temp   = ui.gauge("temp", label="Temp", min=0, max=40,
                              listen="temp", when={"msg_type": "climate"})
            target = ui.slider("target", min=10, max=30, send="set_target")

    async with ui.serve() as hub:          # zero config: embedded LocalRelay + QR
        @hub.on(target)                    # demux derived from the action binding
        async def _(data):
            heater.set(data["value"])

        while True:
            await temp.push(read_temp())   # frame derived from the sync binding
            await asyncio.sleep(2)

The same surface works cross-process off the saved JSON — the layout file is the
contract: ``Hub("dashboard.json", connection="device.json")`` then ``hub.push("temp",
21.5)`` / ``hub.on("set_target", fn)``.

Connection-wise a Hub takes anything :class:`carterkit.connection.Connection` parses:
nothing (embedded LocalRelay), a ``ws://`` relay URL (self-hosted), or the Connect+
*Add Device* credential JSON (token self-refresh + room E2EE come along
automatically, via CarterClient).
"""
from __future__ import annotations

import asyncio
import json as _json

from .client import CarterClient
from .connection import Connection


class HubError(RuntimeError):
    """A driving call that cannot work — wrong binding shape, no device, etc."""


def _set_path(frame: dict, dotted: str, value) -> None:
    parts = dotted.split(".")
    cur = frame
    for p in parts[:-1]:
        nxt = cur.get(p)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[p] = nxt
        cur = nxt
    cur[parts[-1]] = value


def _walk_children(layout: dict):
    """Every control in the layout, recursing through groups, container pages
    (carousel/flipCard/accordion `panels`), and canvas-hosted controls — the same
    nesting the app's own sync collection walks, so a nested control is as
    pushable/handleable as a top-level one."""
    def walk(children):
        for ch in children or []:
            if not isinstance(ch, dict):
                continue
            yield ch
            if ch.get("type") == "group":
                yield from walk(ch.get("children"))
            for panel in ch.get("panels") or []:
                if isinstance(panel, dict):
                    yield from walk(panel.get("children"))
            cfg = ch.get("canvasConfig")
            if isinstance(cfg, dict):
                for item in cfg.get("items") or []:
                    if isinstance(item, dict) and isinstance(item.get("control"), dict):
                        yield item["control"]
    for tab in layout.get("tabs", []):
        yield from walk(tab.get("children"))


class Hub:
    """The driving side of a layout: push values into syncs, handle actions.

    ``layout`` may be a :class:`carterkit.Layout`, a layout dict, or a path to a
    layout JSON; ``connection`` is anything :meth:`Connection.parse` accepts and
    defaults to the layout's own ``connection`` block (or, failing that, an
    embedded LocalRelay). Use as an async context manager; handlers registered
    before entry arm on connect.

    By default the hub declares itself the control-state authority: every
    :meth:`push` is snapshotted, and replicas that join late (or reconnect) get the
    current values via the app's control-sync handshake. Pass
    ``state_authority=False`` to opt out."""

    def __init__(self, layout=None, connection=None, *, name: str | None = None,
                 state_authority: bool = True, **conn_overrides):
        self._layout_obj = None
        if layout is not None and not isinstance(layout, (dict, str)):
            # a carterkit.Layout — bind its handles so ctrl.push()/ctrl.on() work
            self._layout_obj = layout
            layout = layout.layout
        elif isinstance(layout, str):
            with open(layout) as f:
                layout = _json.load(f)
        self.layout = layout

        source = connection
        if source is None and layout:
            source = layout.get("connection")
        self.connection = Connection.parse(source, **conn_overrides)

        hub_name = (name or self.connection.hub
                    or (layout or {}).get("connection", {}).get("hub") or "hub")
        self.client = CarterClient(can_route=True, can_monitor=True,
                                   **self.connection.client_kwargs(name=hub_name))
        self.name = hub_name

        self._index: dict[str, dict] = {}
        if layout:
            for ch in _walk_children(layout):
                if ch.get("id"):
                    self._index[ch["id"]] = ch

        self._demux: dict[str, list] = {}      # broadcast msg_type -> [handlers]
        self._user_broadcast = None
        self._relay = None                     # embedded LocalRelay (kind "local")
        if state_authority:
            self.client.enable_state_authority()
        # The layout's `state.acks` opts its controls into ack'd commands — the
        # serving side of that contract is ours to honour automatically.
        if isinstance((layout or {}).get("state"), dict) and layout["state"].get("acks"):
            self.client.enable_command_acks()
        self.client.on_broadcast(self._dispatch)
        if self._layout_obj is not None:
            self._layout_obj._active_hub = self

    # ─── lifecycle ───────────────────────────────────────────────────────────
    async def start(self) -> "Hub":
        if self.connection.kind == "local":
            from .relay import LocalRelay, port_in_use
            # An already-listening port means a relay is running (the CLI's, another
            # script's) — join it rather than failing the way a second relay would.
            if not port_in_use(self.connection.port):
                self._relay = await LocalRelay(port=self.connection.port,
                                               key=self.connection.key).start()
        await self.client.connect()
        return self

    async def close(self) -> None:
        await self.client.close()
        if self._relay is not None:
            await self._relay.stop()
            self._relay = None

    async def __aenter__(self) -> "Hub":
        return await self.start()

    async def __aexit__(self, *exc) -> bool:
        await self.close()
        return False

    def adopt_layout(self, layout: dict) -> None:
        """Adopt a layout after construction — e.g. one pulled off a paired
        device via `get-layout` — reindexing controls so push()/on()/frame_for()
        resolve against it."""
        self.layout = layout
        self._index = {ch["id"]: ch for ch in _walk_children(layout or {})
                       if ch.get("id")}

    # ─── the pairing hand-off ────────────────────────────────────────────────
    def qr_json(self, *, role: str = "controller") -> str:
        """The pairing JSON for the app (paste or QR-encode; the app scans it)."""
        return self.connection.qr_json(role=role)

    async def wait_for_device(self, timeout: float = 120.0, poll: float = 1.0) -> dict:
        """Block until another channel member appears; returns its roster entry.
        (Polls get_nodes — the pushed roster races joins.)"""
        deadline = asyncio.get_running_loop().time() + timeout
        while True:
            peer = await self._first_peer()
            if peer:
                return peer
            if asyncio.get_running_loop().time() >= deadline:
                raise HubError(f"no device joined channel '{self.connection.channel}' "
                               f"within {timeout:.0f}s")
            await asyncio.sleep(poll)

    async def _first_peer(self):
        res = await self.client._sock.request("get_nodes", None, timeout=5.0)
        for c in (res or {}).get("clients", []):
            if c.get("name") != self.name:
                return c
        return None

    async def push_layout(self) -> dict:
        """Send this hub's layout to the paired device (routed apply-layout; the
        reply echoes what actually rendered). Requires a device on the channel."""
        if not self.layout:
            raise HubError("this hub has no layout to push")
        peer = await self._first_peer()
        if not peer:
            raise HubError("no device on the channel — have the phone connect first "
                           "(hub.qr_json() prints the pairing JSON) or wait_for_device()")
        req = dict(self.layout)
        req.pop("msg_type", None)
        res = await self.client._sock.request(
            "route_msg", {"target_id": peer.get("id"), "type": "apply-layout",
                          "payload": req}, timeout=10.0)
        if not isinstance(res, dict) or not res.get("ok"):
            raise HubError(f"device rejected the layout: "
                           f"{(res or {}).get('error', 'no reply')}")
        return res

    # ─── drive: server -> controls ───────────────────────────────────────────
    def _control(self, target) -> dict:
        if isinstance(target, dict):
            return target
        d = getattr(target, "ref", None)
        if isinstance(d, dict):
            return d
        h = getattr(target, "control", None)          # GroupHandle → its Control
        if isinstance(getattr(h, "ref", None), dict):
            return h.ref
        if isinstance(target, str):
            try:
                return self._index[target]
            except KeyError:
                raise HubError(f"no control with id {target!r} in this layout") from None
        raise HubError(f"can't resolve {target!r} to a control")

    def frame_for(self, target, value) -> dict:
        """The broadcast frame that drives `target`'s sync binding — exposed for
        tests and dry runs; `push` sends it."""
        ctrl = self._control(target)
        syncs = [s for s in ctrl.get("sync") or [] if isinstance(s, dict)]
        broadcasts = [s for s in syncs if s.get("event", "broadcast") == "broadcast"]
        if not broadcasts:
            if syncs:
                raise HubError(
                    f"control '{ctrl.get('id')}' only listens on routed event(s) "
                    f"{[s.get('event') for s in syncs]!r} — Hub.push drives broadcast "
                    f"syncs; route those frames yourself via hub.client")
            raise HubError(f"control '{ctrl.get('id')}' has no sync binding — "
                           f"nothing listens for a pushed value")
        s = broadcasts[0]
        frame = dict(s.get("filter") or {})
        path = s.get("valuePath")
        if path:
            _set_path(frame, path, value)
        elif isinstance(value, dict):
            frame.update(value)
        else:
            raise HubError(
                f"control '{ctrl.get('id')}' has no valuePath (it takes the whole "
                f"payload) — push a dict for it")
        return frame

    async def push(self, target, value) -> dict:
        """Drive a control: broadcast the frame its sync binding listens for.
        `target` is a Control handle or an id string. Returns the sent frame."""
        ctrl = self._control(target)
        frame = self.frame_for(ctrl, value)
        self.client.set_control_state(ctrl.get("id"), value)
        await self.client.broadcast_frame(frame)
        return frame

    async def fill(self, group, children) -> dict:
        """Replace a dynamic group's children live. `group` is a group handle or id
        (must carry `dynamic="event"`); `children` is a Fragment, a children list,
        or a prebuilt `{msg_type, children}` payload."""
        g = self._control(group)
        event = g.get("dynamic")
        if not event:
            raise HubError(f"group '{g.get('id')}' has no dynamic= event — only "
                           f"dynamic groups take runtime children")
        if isinstance(children, dict) and "children" in children:
            payload = {**children, "msg_type": event}
        else:
            kids = getattr(children, "children", children)
            payload = {"msg_type": event, "children": list(kids)}
        await self.client.broadcast_frame(payload)
        return payload

    # ─── drive: controls -> server ───────────────────────────────────────────
    def on(self, target, fn=None):
        """Handle a control's action (or a raw command name). Derives the demux
        from the control's action binding: broadcast_request actions match on their
        payload msg_type; routed actions register the inner routed type. Usable as
        a decorator: ``@hub.on(button)``. Handlers get the (decrypted) payload dict
        and may be sync or async."""
        if fn is None:
            return lambda f: self.on(target, f) or f
        if isinstance(target, str) and target not in self._index:
            # A raw command name: demux broadcasts on msg_type AND accept it as a
            # routed frame type, so the handler works whichever transport the
            # layout (or a legacy layout) uses.
            self._demux.setdefault(target, []).append(fn)
            self.client.on(target, fn)
            return fn
        ctrl = self._control(target)
        events = []
        for akey in ("action", "longPressAction"):
            a = ctrl.get(akey)
            if isinstance(a, dict) and a.get("event"):
                events.append(a)
        if not events:
            raise HubError(f"control '{ctrl.get('id')}' has no action binding — "
                           f"it never emits anything to handle")
        for a in events:
            ev, payload = a.get("event"), a.get("payload")
            if ev == "broadcast_request":
                mt = isinstance(payload, dict) and payload.get("msg_type")
                if not mt:
                    raise HubError(
                        f"control '{ctrl.get('id')}' broadcasts without a payload "
                        f"msg_type — nothing to demux on (author it with send=)")
                self._demux.setdefault(mt, []).append(fn)
            elif ev in ("route_msg", "route_msg_noreply"):
                inner = isinstance(payload, dict) and payload.get("type")
                if not inner:
                    raise HubError(f"control '{ctrl.get('id')}' routes without an "
                                   f"inner type — nothing to register")
                self.client.on(inner, fn)
            else:
                # Legacy custom event: dead through a relay, but arriving frames
                # would carry this type — register it, and demux broadcasts too in
                # case the layout gets fixed to send= later.
                self.client.on(ev, fn)
                self._demux.setdefault(ev, []).append(fn)
        return fn

    def on_broadcast(self, fn):
        """Raw hook: every broadcast that no `on()` demux consumed."""
        self._user_broadcast = fn
        return fn

    def on_sync_request(self, fn):
        """A replica joined / reconnected (the app's `control_sync_request`). The
        frame's `dynamic` field lists the slot events the layout carries, so a
        server can `fill()` exactly the requested decks instead of everything."""
        self.client.on_sync_request(fn)
        return fn

    async def _dispatch(self, data):
        # Returns True iff a demux handler actually ran — the client's ack'd-command
        # layer gates command_ack on that, so a hub that matched nothing stays
        # silent (the raw on_broadcast hook is an observer, not a handler).
        handlers = None
        if isinstance(data, dict):
            handlers = self._demux.get(data.get("msg_type"))
        if handlers:
            for fn in handlers:
                r = fn(data)
                if asyncio.iscoroutine(r):
                    await r
            return True
        if self._user_broadcast is not None:
            r = self._user_broadcast(data)
            if asyncio.iscoroutine(r):
                await r
        return False

    # ─── passthroughs ────────────────────────────────────────────────────────
    async def broadcast(self, msg_type, data):
        await self.client.broadcast(msg_type, data)

    async def chat(self, text, **kw):
        kw.setdefault("name", self.name)
        return await self.client.chat(text, **kw)

    async def notify(self, title, body, **kw):
        return await self.client.notify(title, body, **kw)

    def on_notif_action(self, handler):
        self.client.on_notif_action(handler)

    def __repr__(self) -> str:
        n = len(self._index)
        return f"<Hub {self.name!r} {self.connection!r} {n} control(s)>"
