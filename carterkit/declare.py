"""Declarative layouts — a class veneer over the flat builder.

For static, hand-written dashboards this reads like a schema: a control's id is its
attribute name, tabs and groups are nested classes, and cross-control visibility falls
out of comparing handles. It compiles to exactly the same `Layout`/`LayoutBuffer` the
flat builder uses (so `.layout` is an ordinary layout dict) — pick whichever front door
fits: generated/dynamic UIs read better flat, fixed ones read better here.

    from carterkit.declare import Screen, Tab, Group, Connect, Ref, Gauge, Button, Slider, StatusLight

    class Bench(Screen, cols=4, rows=4):
        relay = Connect("ws://192.168.1.50:8765", channel="lab")

        class Main(Tab, icon="gauge"):
            cpu  = Gauge(label="CPU", min=0, max=100, span=(2, 2),
                         listen="cpu", when={"msg_type": "metrics"})
            warn = StatusLight(visible=cpu > 90)          # handle -> visibility cond
            refresh = Button(label="Refresh", send="refresh", request=True)

            class Motors(Group, span=(2, 2), cols=2, rows=2):
                m0 = Slider(min=0, max=255)
                m1 = Slider(min=0, max=255)

    layout = Bench.layout          # the dict
    Bench.save("bench.json")

Control classes (`Gauge`, `Button`, `StatusLight`, `ColorPicker`, …) are generated from
the bundled catalog: a PascalCase name maps to its control type, so `from
carterkit.declare import *` (or attribute access) exposes one per placeable control.
Kwargs are the same sugar the flat builder takes (`listen=/when=/send=/request=/span=/
visible=`). For a reference to a control by literal id (forward refs, other tabs) use
`Ref("id") > 90`. `==`/`!=` keep normal Python semantics — use `.eq()`/`.neq()`.
"""
from __future__ import annotations

from functools import lru_cache

from . import controls as _controls
from .layout import Layout


class DeclareError(Exception):
    """Raised when a declarative Screen is shaped in a way that can't compile."""


# ─── references & conditions ─────────────────────────────────────────────────
class _Cmp:
    """A pending visibility condition: a handle/Ref compared to a value, resolved to
    `{when, operator, value}` once attribute-name ids are known."""

    def __init__(self, target, op: str, value):
        self.target, self.op, self.value = target, op, value

    def resolve(self, idmap: dict) -> dict:
        if isinstance(self.target, Ref):
            when = self.target.id
        else:
            when = idmap.get(id(self.target))
            if when is None:
                raise DeclareError(
                    "a visibility condition references a control that isn't a named "
                    "attribute in this Screen — use Ref('id') to point at it by id")
        return {"when": when, "operator": self.op, "value": self.value}


class _Comparable:
    def __gt__(self, o): return _Cmp(self, "gt", o)
    def __ge__(self, o): return _Cmp(self, "gte", o)
    def __lt__(self, o): return _Cmp(self, "lt", o)
    def __le__(self, o): return _Cmp(self, "lte", o)
    def eq(self, o): return _Cmp(self, "eq", o)
    def neq(self, o): return _Cmp(self, "neq", o)


class Ref(_Comparable):
    """Reference another control by literal id, for visibility conditions:
    ``hidden = Label(visible=Ref("power").eq(True))``."""

    def __init__(self, id: str):
        self.id = id


class Connect:
    """A connection declaration: ``relay = Connect(url, channel=..., role=..., token=...)``."""

    def __init__(self, url: str, **identity):
        self.url, self.identity = url, identity


# ─── control specs ───────────────────────────────────────────────────────────
class _Spec(_Comparable):
    """A deferred control: its catalog `_ctype` plus the kwargs to build it. The id is
    filled in from the attribute name at compile time."""

    _ctype: str = ""

    def __init__(self, **kwargs):
        self._kwargs = kwargs


@lru_cache(maxsize=None)
def _spec_class(ctype: str, clsname: str) -> type:
    return type(clsname, (_Spec,), {"_ctype": ctype,
                                    "__doc__": f"Declarative {ctype} control."})


@lru_cache(maxsize=1)
def _catalog() -> dict:
    from . import controldocs_dir
    from . import catalog as _catmod
    return _catmod.build_catalog(controldocs_dir())


def _type_for(clsname: str):
    """PascalCase class name -> catalog control type, or None if not a control."""
    if not clsname[:1].isupper():
        return None
    ctype = clsname[0].lower() + clsname[1:]
    return ctype if ctype in _catalog() else None


# ─── compile helpers ─────────────────────────────────────────────────────────
def _members(klass):
    """Ordered (name, value) of a class body, skipping dunders and internals."""
    for name, value in vars(klass).items():
        if name.startswith("_"):
            continue
        yield name, value


def _is_sub(value, base) -> bool:
    return isinstance(value, type) and issubclass(value, base)


def _collect_ids(klass, idmap: dict) -> None:
    """Map every spec object (by identity) to its attribute-name id, recursively."""
    for name, value in _members(klass):
        if isinstance(value, _Spec):
            idmap[id(value)] = name
        elif _is_sub(value, (Tab, Group)):
            _collect_ids(value, idmap)


def _resolve_kwargs(kwargs: dict, idmap: dict) -> dict:
    return {k: (v.resolve(idmap) if isinstance(v, _Cmp) else v) for k, v in kwargs.items()}


def _populate(scope, klass, idmap: dict) -> None:
    """Materialise a class body into a layout scope (a tab or group handle)."""
    for name, value in _members(klass):
        if isinstance(value, _Spec):
            make = getattr(scope, value._ctype)
            make(name, **_resolve_kwargs(value._kwargs, idmap))
        elif _is_sub(value, Group):
            gm = value._group_meta
            gh = scope.group(gm["label"], id=name, span=gm["span"], cols=gm["cols"],
                             rows=gm["rows"], dynamic=gm["dynamic"], pulse=gm["pulse"],
                             hide_background=gm["hide_background"],
                             visible=(gm["visible"].resolve(idmap)
                                      if isinstance(gm["visible"], _Cmp) else gm["visible"]))
            with gh:
                _populate(gh, value, idmap)


# ─── declarative bases ───────────────────────────────────────────────────────
class Tab:
    """Base for a nested tab class: ``class Main(Tab, icon="gauge", cols=4, rows=6): ...``"""

    @classmethod
    def __init_subclass__(cls, *, title: str = None, icon: str = "square.grid.2x2",
                          cols: int = None, rows: int = 6, columns: int = None, **rest):
        super().__init_subclass__(**rest)
        cls._tab_meta = {"title": title or cls.__name__, "icon": icon,
                         "cols": cols if cols is not None else (columns or 4), "rows": rows}


class Group:
    """Base for a nested group class. Class kwargs mirror `Layout.group`:
    ``class Motors(Group, span=(2,2), cols=2, rows=2, dynamic="motor_state"): ...``"""

    @classmethod
    def __init_subclass__(cls, *, label: str = None, span=None, cols: int = 4, rows: int = 4,
                          dynamic: str = None, visible=None, pulse=None,
                          hide_background: bool = None, **rest):
        super().__init_subclass__(**rest)
        cls._group_meta = {"label": label if label is not None else cls.__name__,
                           "span": span, "cols": cols, "rows": rows, "dynamic": dynamic,
                           "visible": visible, "pulse": pulse, "hide_background": hide_background}


class _ScreenMeta(type):
    @property
    def layout(cls) -> dict:
        return cls.build().layout


class Screen(metaclass=_ScreenMeta):
    """Base for a declarative layout. Subclass kwargs: ``name=``, ``cols=``, ``rows=``,
    ``accent=``. Access the result via ``.layout`` / ``.build()`` / ``.json()`` /
    ``.save(path)`` / ``.validate()`` / ``.findings()``."""

    @classmethod
    def __init_subclass__(cls, *, name: str = None, cols: int = None, rows: int = 6,
                          columns: int = None, accent: str = "#667eea", **rest):
        super().__init_subclass__(**rest)
        cls._screen_meta = {"name": name or cls.__name__,
                            "cols": cols if cols is not None else (columns or 4),
                            "rows": rows, "accent": accent}
        cls._compiled = None

    @classmethod
    def _compile(cls) -> Layout:
        meta = cls._screen_meta
        lay = Layout(meta["name"], cols=meta["cols"], rows=meta["rows"], accent=meta["accent"])

        idmap: dict = {}
        _collect_ids(cls, idmap)

        for _n, value in _members(cls):
            if isinstance(value, Connect):
                lay.connect(value.url, **value.identity)

        tabs = [(n, v) for n, v in _members(cls) if _is_sub(v, Tab)]
        loose = [(n, v) for n, v in _members(cls)
                 if isinstance(v, _Spec) or _is_sub(v, Group)]
        if tabs:
            if any(isinstance(v, _Spec) for _n, v in loose):
                raise DeclareError(
                    "controls are defined directly on the Screen alongside Tab classes — "
                    "move them inside a Tab (controls must live in a tab)")
            for _n, tabcls in tabs:
                tm = tabcls._tab_meta
                handle = lay.tab(tm["title"], icon=tm["icon"], cols=tm["cols"], rows=tm["rows"])
                with handle:
                    _populate(handle, tabcls, idmap)
        else:
            _populate(lay, cls, idmap)
        return lay

    @classmethod
    def build(cls) -> Layout:
        """Compile (once) to a `Layout`. Cached on the class."""
        if cls.__dict__.get("_compiled") is None:
            cls._compiled = cls._compile()
        return cls._compiled

    @classmethod
    def json(cls, indent: int = 2) -> str:
        return cls.build().json(indent)

    @classmethod
    def save(cls, path: str, indent: int = 2) -> str:
        return cls.build().save(path, indent)

    @classmethod
    def validate(cls) -> list:
        return cls.build().validate()

    @classmethod
    def findings(cls) -> str:
        return cls.build().findings()


# ─── module-level control-class access (PEP 562) ─────────────────────────────
_STATIC = {"Screen", "Tab", "Group", "Connect", "Ref", "DeclareError"}


def __getattr__(name: str):
    ctype = _type_for(name)
    if ctype is not None:
        return _spec_class(ctype, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    pascal = [t[0].upper() + t[1:] for t in _catalog()]
    return sorted(_STATIC | set(pascal))


__all__ = sorted(_STATIC | {t[0].upper() + t[1:] for t in _catalog()})
