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
            ui.button("refresh", label="Refresh", send="refresh", request=True)

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
    send="refresh"               -> action fired on tap/change (broadcast)
    request=True                 -> make that action a request (await reply)
    payload={"v": "{{value}}"}   -> action payload
For anything fancier (multiple syncs, custom shapes) pass `sync=[...]` / `action={...}`
built with `carterkit.bind` directly — they win over the sugar.

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
              send=None, request: bool = False, payload=None,
              sync=None, action=None, visible=None, pulse=None, **props) -> Control:
        syncs = list(sync) if sync else []
        if listen is not None:
            for v in ([listen] if isinstance(listen, str) else listen):
                syncs.append(_bind.listen(v, event=event, filter=when))
        if syncs:
            props["sync"] = syncs
        if action is not None:
            props["action"] = action
        elif send is not None:
            props["action"] = _bind.action(
                send, mode="request" if request else "broadcast", payload=payload)
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
              hide_background=None) -> "GroupHandle":
        """Add a group container and return a handle you can `with`-enter to fill.

        `dynamic="event"` makes the group's children runtime-injectable (replaced by a
        broadcast with matching `msg_type` — build that payload with :class:`Fragment`)."""
        gid = self._owner._unique_id(id or "group")
        g: dict = {"type": "group", "id": gid,
                   "grid": {"columns": cols, "rows": rows}, "children": []}
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
        self._tab_index = 0
        self._first_tab_used = False
        self._scope = self._scope_for_tab(0)

    # ─── internals ───────────────────────────────────────────────────────────
    def _scope_for_tab(self, i: int) -> _GridScope:
        tab = self._buf.tabs[i]
        cols, rows = self._buf._grid_dims(tab)
        return _GridScope(tab.setdefault("children", []), cols, rows, self)

    def _unique_id(self, base: str) -> str:
        return self._buf.unique_id(base)

    # ─── structure ───────────────────────────────────────────────────────────
    def connect(self, url: str, **identity) -> "Layout":
        """Attach a `connection` block (see bind.connection for the identity kwargs)."""
        self._buf.layout["connection"] = _bind.connection(url, **identity)
        return self

    def tab(self, title: str, *, icon: str = "square.grid.2x2",
            cols: int = None, rows: int = 6, columns: int = None) -> TabHandle:
        """Start a tab and make it current. First call configures the default tab;
        later calls append. `with ui.tab(...)` scopes controls to it; the flat form
        ``ui.tab("Main"); ui.gauge(...)`` works too."""
        cols = cols if cols is not None else (columns if columns is not None else 4)
        if not self._first_tab_used:
            t = self._buf.tabs[0]
            t["title"], t["icon"] = title, icon
            t["grid"] = {"columns": cols, "rows": rows}
            self._tab_index = 0
            self._first_tab_used = True
        else:
            self._tab_index = self._buf.add_tab(title, icon=icon, columns=cols, rows=rows)
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
