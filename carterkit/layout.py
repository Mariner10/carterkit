"""A flat layout builder with live control handles — the ergonomic front door.

Controls are methods on the layout, ids are positional, bindings fold into kwargs,
and tabs/groups are context managers, so nesting reads the way Python nests:

    from carterkit import Layout

    with Layout("Bench", cols=4, rows=4) as ui:
        ui.connect("ws://192.168.1.50:8765", channel="lab")

        with ui.tab("Main", icon="gauge"):
            cpu = ui.gauge("cpu", label="CPU", min=0, max=100, span=(2, 2),
                           listen="cpu", when={"msg_type": "metrics"})
            ui.status_light("warn", visible=cpu > 90)  # handle -> visibility cond
            ui.button("refresh", label="Refresh", send="refresh")

            with ui.group("Motors", span=(4, 2)) as motors:   # dynamic generation
                for i in range(4):
                    motors.slider(f"m{i}", min=0, max=255)

    ui.save("bench.json")

Every control method returns a :class:`Control` handle — use it as a binding target
(``visible=cpu > 90``) or to patch the control later (``cpu.update(max=200)``).

Binding sugar (folded into any control method):
    listen="cpu"                 -> sync that subscribes to the `cpu` value path
    when={"msg_type": "metrics"} -> filter on that listen
    event="telemetry"            -> the listen event (default "broadcast")
    send="refresh"               -> named command: compiles to a broadcast_request
                                    tagged msg_type="refresh" (the only shape the
                                    relay forwards; `Hub.on` demuxes it back)
    payload={"v": "{{value}}"}   -> command payload (default {"value": "{{value}}"})
For anything fancier (multiple syncs, custom shapes) pass `sync=[...]` / `action={...}`
built with `carterkit.bind` directly — they win over the sugar. There is no
request/reply sugar: replies can't ride the relay's fan-out, so use the round-trip
idiom (send= the command, listen= for the state broadcast the server answers with).

Dynamic groups have two senses, both first-class here:
  • author-time generation — build groups/controls in `for`/`if` (see above);
  • runtime injection — a group with ``dynamic="event"`` whose children are replaced
    live by a broadcast. Build that replacement payload with :class:`Fragment`.

Back-compat: the old fluent chain (``.connect().tab().add(build.x(), default_span=)``)
still works; the new style is just nicer. Auto-placement, id de-dup, and grid
bookkeeping come from LayoutBuffer; `.validate()` lints against the bundled catalog.
"""
from __future__ import annotations

import json

from . import bind as _bind
from . import controls as _controls
from . import grid as _grid
from . import validate as _validate
from .buffer import LayoutBuffer, BufferError

_OPS = {"gt": "gt", "ge": "gte", "lt": "lt", "le": "lte"}


class Condition:
    """A visibility condition: show/hide a control based on another's value.

    Usually built by comparing a control handle (``power > 50``, ``mode.eq("auto")``);
    serialises to the device's ``visible`` shape ``{when, operator, value}``."""

    def __init__(self, when: str, operator: str, value):
        self.when, self.operator, self.value = when, operator, value

    def to_dict(self) -> dict:
        return {"when": self.when, "operator": self.operator, "value": self.value}

    def __repr__(self) -> str:
        return f"<Condition {self.when} {self.operator} {self.value!r}>"


class Control:
    """A handle to a placed control. Use it as a binding target or to patch the
    control after the fact. `==`/`!=` keep normal Python semantics on purpose —
    use `.eq()`/`.neq()` to build equality visibility conditions."""

    def __init__(self, scope: "_GridScope", d: dict):
        self._scope, self._d = scope, d

    @property
    def id(self) -> str:
        return self._d["id"]

    @property
    def ref(self) -> dict:
        """The underlying control dict (live — edits show in the layout)."""
        return self._d

    def update(self, **props) -> "Control":
        """Patch props in place (``None`` removes a key). Returns self."""
        for k, v in props.items():
            if v is None:
                self._d.pop(k, None)
            else:
                self._d[k] = v
        return self

    def _cond(self, op: str, other) -> Condition:
        return Condition(self.id, op, other)

    def __gt__(self, o):  return self._cond("gt", o)
    def __ge__(self, o):  return self._cond("gte", o)
    def __lt__(self, o):  return self._cond("lt", o)
    def __le__(self, o):  return self._cond("lte", o)

    def eq(self, o) -> Condition:  return self._cond("eq", o)
    def neq(self, o) -> Condition: return self._cond("neq", o)

    # ─── driving (live, via the layout's active Hub) ─────────────────────────
    def _hub(self):
        hub = getattr(self._scope._owner, "_active_hub", None)
        if hub is None:
            raise RuntimeError(
                "no active hub for this layout — create one with ui.serve(...) and "
                "enter it (`async with ui.serve() as hub:`) before driving controls")
        return hub

    async def push(self, value):
        """Drive this control live: broadcast the frame its sync binding listens
        for (needs an active `ui.serve()` hub)."""
        return await self._hub().push(self, value)

    def on(self, fn=None):
        """Handle this control's action (decorator-friendly): the demux is derived
        from the action binding (needs an active `ui.serve()` hub)."""
        return self._hub().on(self, fn)

    def __repr__(self) -> str:
        return f"<Control {self._d.get('type','?')} {self.id!r}>"


class _GridScope:
    """A placeable grid (a tab's children, a group's children, or a Fragment).

    Control methods resolve off the bundled catalog via attribute access
    (``scope.gauge(...)``); `owner` supplies global id de-dup."""

    def __init__(self, children: list, cols: int, rows: int, owner):
        self._children, self._cols, self._rows, self._owner = children, cols, rows, owner

    # ─── placement ───────────────────────────────────────────────────────────
    def _place(self, node: dict, position, span) -> None:
        sp = [int(span[0]), int(span[1])] if span else (node.get("span") or [1, 1])
        if span:
            node["span"] = sp
        if position is not None:
            node["position"] = [int(position[0]), int(position[1])]
            return
        slot = _grid.find_slot(self._children, self._cols, self._rows, sp)
        if slot is None:
            raise BufferError(
                f"no free {sp} slot in this {self._rows}x{self._cols} grid — grow it "
                f"(cols=/rows=) or pass position=")
        node["position"] = slot

    # ─── controls ────────────────────────────────────────────────────────────
    def _make(self, ctype: str, *, id=None, position=None, span=None,
              listen=None, when=None, event: str = "broadcast",
              send=None, request: bool = False, payload=None, sensor=None,
              sync=None, action=None, visible=None, pulse=None, **props) -> Control:
        syncs = list(sync) if sync else []
        if listen is not None:
            for v in ([listen] if isinstance(listen, str) else listen):
                syncs.append(_bind.listen(v, event=event, filter=when))
        if sensor is not None:
            # Bind to a device sensor (no backend). `sensor="heading"` / "motion.roll".
            for s in ([sensor] if isinstance(sensor, str) else sensor):
                syncs.append(_bind.sensor(s))
        if syncs:
            props["sync"] = syncs
        if action is not None:
            props["action"] = action
        elif send is not None:
            if send in _bind.WIRE_VERBS or send in _bind.RELAY_SERVICE_VERBS:
                # Raw wire/service verb: pass through untouched (power users own the
                # payload; service verbs like "ping" are answered by the relay itself).
                props["action"] = _bind.action(
                    send, mode="request" if request else "broadcast", payload=payload)
            elif request:
                raise ValueError(
                    f"request=True can't ride a broadcast: the relay only routes replies "
                    f"for route_msg, which needs a live target_id no layout can know at "
                    f"author time. Use the round-trip idiom — send={send!r} and listen= "
                    f"for the state broadcast the server answers with — or pass a raw "
                    f"action=bind.action(...) if you really hold a target_id.")
            else:
                props["action"] = _bind.command(send, payload=payload)
        if visible is not None:
            props["visible"] = visible.to_dict() if isinstance(visible, Condition) else visible
        if pulse is not None:
            props["pulse"] = pulse
        cid = self._owner._unique_id(id or ctype)
        ctrl = _controls.control(ctype, id=cid, **props)   # validates type + enums
        self._place(ctrl, position, span)
        self._children.append(ctrl)
        return Control(self, ctrl)

    def group(self, label=None, *, id=None, span=None, position=None, cols: int = 4,
              rows: int = 4, dynamic=None, visible=None, pulse=None,
              hide_background=None, mode: str = None, row_height: int = None) -> "GroupHandle":
        """Add a group container and return a handle you can `with`-enter to fill.

        `dynamic="event"` makes the group's children runtime-injectable (replaced by a
        broadcast with matching `msg_type` — build that payload with :class:`Fragment`).
        `mode="flow"` opts this group out of the default 2-D grid; `row_height` sets the
        2-D row unit in points (default 56)."""
        gid = self._owner._unique_id(id or "group")
        grid: dict = {"columns": cols, "rows": rows}
        if mode is not None:
            grid["mode"] = mode
        if row_height is not None:
            grid["rowHeight"] = row_height
        g: dict = {"type": "group", "id": gid, "grid": grid, "children": []}
        if label is not None:
            g["label"] = label
        if dynamic is not None:
            g["dynamic"] = dynamic
        if visible is not None:
            g["visible"] = visible.to_dict() if isinstance(visible, Condition) else visible
        if pulse is not None:
            g["pulse"] = pulse
        if hide_background is not None:
            g["hideBackground"] = hide_background
        self._place(g, position, span)
        self._children.append(g)
        gscope = _GridScope(g["children"], cols, rows, self._owner)
        return GroupHandle(self._owner, gscope, Control(self, g))

    def add(self, control: dict, *, position=None, span=None, default_span=None) -> "_GridScope":
        """Back-compat: place a pre-built control dict (from `build.x()`)."""
        control = dict(control)
        control["id"] = self._owner._unique_id(control.get("id") or control.get("type", "control"))
        sp = span or default_span
        self._place(control, position, sp)
        self._children.append(control)
        return self

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        ctype = _controls._resolve_type(name)
        if ctype is None:
            raise AttributeError(f"no control type {name!r}")

        def make(id=None, **kw) -> Control:
            return self._make(ctype, id=id, **kw)
        make.__name__ = ctype
        return make


class _ScopeProxy:
    """Shared base for tab/group handles: a context manager that activates its scope,
    forwarding control-method calls to it."""

    def __init__(self, layout: "Layout", scope: "_GridScope"):
        self._layout, self._scope, self._prev = layout, scope, None

    def __enter__(self):
        self._prev = self._layout._scope
        self._layout._scope = self._scope
        return self

    def __exit__(self, *exc):
        if self._prev is not None:
            self._layout._scope = self._prev
        return False

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        self._layout._scope = self._scope     # keep flat (non-`with`) usage targeting us
        return getattr(self._scope, name)


class GroupHandle(_ScopeProxy):
    def __init__(self, layout, scope, handle: Control):
        super().__init__(layout, scope)
        self._handle = handle

    @property
    def id(self) -> str:
        return self._handle.id

    @property
    def control(self) -> Control:
        return self._handle


class TabHandle(_ScopeProxy):
    def __init__(self, layout, scope, index: int):
        super().__init__(layout, scope)
        self._index = index

    # chaining / back-compat (return types preserved for the old fluent style)
    def add(self, control, **kw):
        self._layout._scope = self._scope
        self._scope.add(control, **kw)
        return self

    def tab(self, *a, **kw):
        return self._layout.tab(*a, **kw)

    def connect(self, *a, **kw):
        self._layout.connect(*a, **kw)
        return self

    @property
    def layout(self) -> dict:
        return self._layout.layout

    def validate(self):
        return self._layout.validate()

    def findings(self) -> str:
        return self._layout.findings()

    def json(self, indent: int = 2) -> str:
        return self._layout.json(indent)


class Layout:
    def __init__(self, name: str = "Layout", *, cols: int = None, rows: int = 6,
                 columns: int = None, accent: str = "#667eea"):
        cols = cols if cols is not None else (columns if columns is not None else 4)
        self._buf = LayoutBuffer.blank(name=name, columns=cols, rows=rows, accent=accent)
        # Remember the layout's grid so tabs inherit it unless they override — otherwise
        # `Layout(rows=12)` would be silently ignored and every tab would fall back to a
        # fixed 6-row grid, surprising callers who sized the grid on the Layout.
        self._default_cols = cols
        self._default_rows = rows
        self._tab_index = 0
        self._first_tab_used = False
        self._active_hub = None          # set by Hub when this layout is served
        self._scope = self._scope_for_tab(0)

    # ─── internals ───────────────────────────────────────────────────────────
    def _scope_for_tab(self, i: int) -> _GridScope:
        tab = self._buf.tabs[i]
        cols, rows = self._buf._grid_dims(tab)
        return _GridScope(tab.setdefault("children", []), cols, rows, self)

    def _unique_id(self, base: str) -> str:
        return self._buf.unique_id(base)

    # ─── structure ───────────────────────────────────────────────────────────
    def connect(self, source: str = None, **identity) -> "Layout":
        """Attach a `connection` block. `source` is a relay URL (identity kwargs as
        in bind.connection, including `hub=` to name the serving side) — or anything
        `Connection.parse` accepts: a pairing/Add-Device JSON path or dict, an
        existing Connection, or nothing at all for the embedded local relay."""
        if isinstance(source, str) and source.startswith(("ws://", "wss://")):
            self._buf.layout["connection"] = _bind.connection(source, **identity)
            return self
        from .connection import Connection
        name = identity.pop("name", "CAR-TER")
        role = identity.pop("role", None)
        conn = Connection.parse(source, **identity)
        self._buf.layout["connection"] = conn.layout_block(name=name, role=role)
        return self

    def state(self, *, sync: bool = True, authority: str = None,
              acks: bool = None, ack_timeout_ms: int = None) -> "Layout":
        """Attach the layout `state` block — the app's device-held shared-state
        opt-in. With `sync` on, the app broadcasts a `control_sync_request` when the
        layout loads and on every reconnect (the deterministic join signal servers
        catch with `CarterClient.on_sync_request` / `Hub.on_sync_request`), and
        adopts the authority's `control_snapshot` of current control values.
        `authority` names the source-of-truth node (match the serving hub's mesh
        name or role); `acks=True` additionally opts every control action into
        ack'd commands — the app stamps `_cmd`/`_from` onto each fired payload and
        reverts the control unless a `command_ack` arrives within `ack_timeout_ms`
        (emitted as `ackTimeoutMs`, app default 2000 — raise it for slow links).
        Serve with `CarterClient.enable_command_acks` (`Hub` does it for you)."""
        block: dict = {"sync": sync}
        if authority is not None:
            block["authority"] = authority
        if acks is not None:
            block["acks"] = acks
        if ack_timeout_ms is not None:
            block["ackTimeoutMs"] = int(ack_timeout_ms)
        self._buf.layout["state"] = block
        return self

    # ─── data sources (MQTT / HTTP — app-side runtimes, no server code) ─────────
    def source_mqtt(self, name: str, url: str, *, username: str = None,
                    password: str = None, client_id: str = None) -> "Layout":
        """Declare an MQTT broker source. Controls bind topics with
        ``bind.mqtt("home/temp")`` (sync) / ``bind.mqtt_publish("home/lamp/set")``
        (action). The app speaks MQTT directly — no server code. See sources.md."""
        src: dict = {"type": "mqtt", "url": url}
        if username is not None:
            src["username"] = username
        if password is not None:
            src["password"] = password
        if client_id is not None:
            src["clientId"] = client_id
        self._buf.layout.setdefault("sources", {})[name] = src
        return self

    def source_http(self, name: str, base_url: str, *, headers: dict = None,
                    interval: float = None) -> "Layout":
        """Declare an HTTP API source. Controls poll it with
        ``bind.http("/status", interval=5)`` and act with ``bind.http_request(...)``.
        The app polls directly — no server code. See sources.md."""
        src: dict = {"type": "http", "baseURL": base_url}
        if headers is not None:
            src["headers"] = headers
        if interval is not None:
            src["interval"] = interval
        self._buf.layout.setdefault("sources", {})[name] = src
        return self

    # ─── publishers (stream this device's sensors over the connection) ──────────
    def publisher(self, sensor: str, *, interval: float = None) -> "Layout":
        """Stream a device [[sensors]] pipeline over the layout's connection, so a hub
        device or server can watch this phone's compass/speed/sound live. `sensor` is a
        pipeline name (heading, motion, barometer, device, audio, location). See publishers.md."""
        pub: dict = {"sensor": sensor}
        if interval is not None:
            pub["interval"] = interval
        self._buf.layout.setdefault("publishers", []).append(pub)
        return self

    # ─── alerts (relay-watcher push rules) ──────────────────────────────────────
    def alert(self, *, event: str, value_path: str, operator: str, value,
              title: str, body: str, id: str = None, cooldown: int = None,
              acknowledge_server_readable: bool = None) -> "Layout":
        """Add a relay-side alert rule: when a broadcast on `event` whose `value_path`
        `operator`-compares to `value` lands, the relay's alert-watcher pushes a
        notification (`title`/`body`) — even with the app closed. `operator` is one of
        eq/neq/gt/lt/gte/lte. `cooldown` (seconds) rate-limits repeats. See AlertRule."""
        ops = {"eq", "neq", "gt", "lt", "gte", "lte"}
        if operator not in ops:
            raise ValueError(f"operator must be one of {sorted(ops)}, got {operator!r}")
        rule: dict = {"id": id or f"alert-{len(self._buf.layout.get('alerts', []))}",
                      "event": event, "valuePath": value_path, "operator": operator,
                      "value": value, "title": title, "body": body}
        if cooldown is not None:
            rule["cooldown"] = int(cooldown)
        if acknowledge_server_readable is not None:
            rule["acknowledgeServerReadable"] = acknowledge_server_readable
        self._buf.layout.setdefault("alerts", []).append(rule)
        return self

    # ─── glance (widgets / lock screen / Dynamic Island / Live Activity) ────────
    def glance(self, *, enabled: bool = None, title: str = None, icon: str = None,
               tint: str = None, hero: str = None, slots: list = None,
               live_activity: bool = None, controls: list = None) -> "Layout":
        """Project this layout onto glance surfaces (widgets, lock screen, Dynamic
        Island, Live Activities). `hero`/`slots` are control ids to surface; enabling
        `live_activity` lets the relay push updates to a running Live Activity. See
        GlanceConfig / glance.md."""
        block: dict = {}
        for k, v in (("enabled", enabled), ("title", title), ("icon", icon),
                     ("tint", tint), ("hero", hero), ("slots", slots),
                     ("liveActivity", live_activity), ("controls", controls)):
            if v is not None:
                block[k] = v
        self._buf.layout["glance"] = block
        return self

    # ─── poll groups (server-timer polling) ─────────────────────────────────────
    def poll_group(self, name: str, *, event: str, interval: float, payload=None) -> "Layout":
        """Fire `event` (with optional `payload`) every `interval` seconds so a server
        answers on a timer — a layout-driven poll. Servers catch it like any broadcast."""
        grp: dict = {"event": event, "interval": interval}
        if payload is not None:
            grp["payload"] = payload
        self._buf.layout.setdefault("pollGroups", {})[name] = grp
        return self

    # ─── dynamic tabs (runtime-injected tabs) ───────────────────────────────────
    def dynamic_tab(self, event: str) -> "Layout":
        """Register an `event` that can inject a whole tab at runtime (the tab analog of
        a dynamic group). A server broadcasts a matching payload to add the tab live."""
        self._buf.layout.setdefault("dynamicTabs", []).append({"event": event})
        return self

    # ─── appearance (chrome overrides) ──────────────────────────────────────────
    def appearance(self, *, color_scheme: str = None, show_header: bool = None,
                   status_bar_style: str = None, background_image: str = None) -> "Layout":
        """Set the layout's `appearance` chrome: `color_scheme` ("light"/"dark"/"system"),
        whether the header shows, status-bar style, and a background image URL."""
        block: dict = {}
        for k, v in (("colorScheme", color_scheme), ("showHeader", show_header),
                     ("statusBarStyle", status_bar_style), ("backgroundImage", background_image)):
            if v is not None:
                block[k] = v
        self._buf.layout["appearance"] = block
        return self

    def serve(self, connection=None, *, name: str = None, **overrides) -> "Hub":
        """The driving side of THIS layout: a Hub bound to these control handles
        (`async with ui.serve() as hub:` connects; then `ctrl.push(v)` /
        `@ctrl.on`). `connection` defaults to the layout's own connection block,
        else an embedded LocalRelay. Also stamps the connection into the layout so
        the saved JSON dials the same relay the hub serves on."""
        from .hub import Hub
        hub = Hub(self, connection=connection, name=name, **overrides)
        if "connection" not in self.layout:
            self._buf.layout["connection"] = hub.connection.layout_block()
        return hub

    async def notify(self, title, body, **kw):
        """Send a push scoped to THIS layout, through its serving hub:

            await ui.notify("Door open", "Bay 2 since 14:02",
                            image="https://…/door.jpg", criticality="time-sensitive",
                            sender=("Monroe", "https://…/monroe.jpg"),
                            actions={"ack": ("Acknowledge", on_ack)})

        Defaults that make the push *belong* to the layout: `thread_id` is the layout
        name (all of this layout's notifications stack together on the lock screen)
        and `channel` is the layout's connection channel (tapping the push opens this
        layout, and action-button taps come back to this hub). Everything else —
        subtitle, image, sender persona, criticality, sound, relevance, actions with
        callbacks, E2EE — as in `CarterClient.notify`. Requires the hub's connection
        to carry Connect+ validator credentials (`validator_url` + `session_jwt`)."""
        if self._active_hub is None:
            raise RuntimeError("layout.notify() sends through the layout's hub — serve "
                               "it first (`async with ui.serve() as hub:`) or use "
                               "CarterClient.notify / notify_http directly")
        kw.setdefault("thread_id", self._buf.layout.get("name"))
        return await self._active_hub.notify(title, body, **kw)

    def tab(self, title: str, *, icon: str = "square.grid.2x2",
            cols: int = None, rows: int = None, columns: int = None,
            mode: str = None, row_height: int = None) -> TabHandle:
        """Start a tab and make it current. First call configures the default tab;
        later calls append. `with ui.tab(...)` scopes controls to it; the flat form
        ``ui.tab("Main"); ui.gauge(...)`` works too. `mode="flow"` opts the tab out of
        the default 2-D grid; `row_height` sets the 2-D row unit (points, default 56).

        Grid size defaults to the Layout's own `cols`/`rows`; pass `cols=`/`rows=` here
        to override for just this tab."""
        cols = cols if cols is not None else (columns if columns is not None else self._default_cols)
        rows = rows if rows is not None else self._default_rows
        grid = {"columns": cols, "rows": rows}
        if mode is not None:
            grid["mode"] = mode
        if row_height is not None:
            grid["rowHeight"] = row_height
        if not self._first_tab_used:
            t = self._buf.tabs[0]
            t["title"], t["icon"] = title, icon
            t["grid"] = grid
            self._tab_index = 0
            self._first_tab_used = True
        else:
            self._tab_index = self._buf.add_tab(title, icon=icon, columns=cols, rows=rows,
                                                mode=mode, row_height=row_height)
        self._scope = self._scope_for_tab(self._tab_index)
        return TabHandle(self, self._scope, self._tab_index)

    def group(self, label=None, **kw):
        """New style: ``with ui.group("Motors", span=(4,2)) as g:`` returns a GroupHandle.
        Back-compat: ``ui.group(prebuilt_dict)`` places a group dict and returns self."""
        if isinstance(label, dict):
            self._buf.add_group(label, tab_index=self._tab_index, position=kw.get("position"))
            return self
        return self._scope.group(label, **kw)

    def add(self, control: dict, *, position=None, span=None, default_span=None) -> "Layout":
        """Back-compat: add a pre-built control (from `build.x()`) to the current tab."""
        self._buf.add_control(control, tab_index=self._tab_index, position=position,
                              default_span=default_span or span)
        return self

    # ─── outputs ─────────────────────────────────────────────────────────────
    @property
    def layout(self) -> dict:
        """The composed layout dict (ready to push/save)."""
        return self._buf.layout

    @property
    def buffer(self) -> LayoutBuffer:
        """The underlying LayoutBuffer, for advanced ops (update/move/remove)."""
        return self._buf

    def validate(self) -> list:
        """Lint against the bundled control catalog."""
        import carterkit
        return carterkit.validate_layout(self.layout)

    def findings(self) -> str:
        """Human-readable lint report."""
        return _validate.format_findings(self.validate())

    def json(self, indent: int = 2) -> str:
        return json.dumps(self.layout, indent=indent)

    def save(self, path: str, indent: int = 2) -> str:
        """Write the layout JSON to `path` (live push to a device is the app/MCP's job —
        `push_layout` — not this offline builder). Returns the path."""
        with open(path, "w") as f:
            f.write(self.json(indent))
        return path

    # context-manager sugar so `with Layout(...) as ui:` reads cleanly
    def __enter__(self) -> "Layout":
        return self

    def __exit__(self, *exc) -> bool:
        return False

    def __getattr__(self, name: str):
        # delegate control-method calls (ui.gauge(...)) to the active scope
        if name.startswith("_"):
            raise AttributeError(name)
        scope = self.__dict__.get("_scope")
        if scope is None:
            raise AttributeError(name)
        return getattr(scope, name)

    def __repr__(self) -> str:
        n = sum(len(t.get("children", [])) for t in self._buf.tabs)
        return (f"<Layout {self.layout.get('name')!r}: "
                f"{len(self._buf.tabs)} tab(s), {n} control(s)>")


class Fragment:
    """A detached grid of controls whose `.children` array is what you broadcast to
    fill a ``dynamic=`` group at runtime. Same control methods as a layout scope:

        frag = Fragment(cols=4, rows=3)
        frag.label("title", text="Now Playing", span=(1, 4))
        for t in tracks:
            frag.button(t.id, label=t.name, send="play", payload={"id": t.id})
        await client.broadcast("player_state", {"children": frag.children})
        # or: frag.payload("player_state")  ->  {"msg_type", "children"}

    Keep injected ids STABLE across re-pushes of the same surface: the app diffs a
    dynamic group's children by id and preserves the live value (and container
    state) of every id it already has — a renamed id is a brand-new control that
    resets to its defaultValue.
    """

    def __init__(self, *, cols: int = 4, rows: int = 4):
        self._children: list = []
        self._scope = _GridScope(self._children, cols, rows, self)

    def _unique_id(self, base: str) -> str:
        ids = self._ids()
        if base not in ids:
            return base
        i = 2
        while f"{base}-{i}" in ids:
            i += 1
        return f"{base}-{i}"

    def _ids(self) -> set:
        out: set = set()

        def walk(children):
            for c in children or []:
                if isinstance(c, dict):
                    if "id" in c:
                        out.add(c["id"])
                    if c.get("type") == "group":
                        walk(c.get("children"))
        walk(self._children)
        return out

    @property
    def children(self) -> list:
        return self._children

    def payload(self, msg_type: str) -> dict:
        """The broadcast body to replace a dynamic group's children: `{msg_type, children}`."""
        return {"msg_type": msg_type, "children": self._children}

    def json(self, indent: int = 2) -> str:
        return json.dumps(self._children, indent=indent)

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self._scope, name)

    def __repr__(self) -> str:
        return f"<Fragment: {len(self._children)} child(ren)>"
