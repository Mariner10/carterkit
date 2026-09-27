"""Layout patch ops — the app's ``LayoutOp`` vocabulary, applied and diffed in Python.

A patch is a batch of id-addressed edit ops (``{"ops": [...], "base"?, "author"?}``)
that the app runs through ``LayoutOps.apply`` (``CAR-TER/Services/LayoutOps.swift``,
carter-c1n.8). This module is the kit's twin (carter-n4x.10, K11): a pure, stdlib-only
port of the applier plus a differ that turns ``old`` → ``new`` into ops, so the MCP and
``carterkit dev`` can send small patches instead of whole layouts. The shared goldens are
``tests/fixtures/layout-ops/*.json``.

Public API::

    decode_op(obj) -> dict           one op in canonical wire form (aliases resolved)
    decode_batch(obj) -> dict        {"ops": [...], "base"?, "author"?, "label"?}
    apply(layout, ops_or_batch, *, base=None, mint=None) -> PatchResult
    diff(old, new) -> list[dict] | None
    layout_hash(layout) -> "sha256:<hex>"   (= carterkit.canonical.content_digest)

Wire vocabulary (``"op"`` → payload). Aliases are accepted on input, never written:

    setProp  {id,key,value,config?}            aliases set, unset{id,key}
    update   {id,set:{},unset:[]}              (K11)
    setSync  {id,sync}     setAction {id,action,slot?: action|longPressAction}
    add      {parent,panel?,index?,control,position?,span?}   aliases child→control, tab→parent
    remove   {id}          duplicate {id,position?}
    move     {id,position?,parent?,panel?,index?}             alias tab→parent
    resize   {id,span}
    place    {id,presentation: default|landscape|regular,position?,span?,hidden?}
    renameId {from,to}     rewrites visible.when + glance hero/slots/control refs
    layout   {set:{},unset:[]}                 alias setLayout{key,value}; never ``tabs``
    setTheme {key,value,scheme?}
    addTab   {title?,icon?,id?,grid?,index?} | {tab:{...},index?} (verbatim)
    removeTab {tab}        moveTab {tab,index}
    setTab   {tab,key,value}                   alias renameTab{from,to} (K11)
    upsertSource {sourceId,def}                removeSource {sourceId}

A ``parent``/``tab`` ref is a tab index (int), a tab id, a group/page/container id, or a
tab title (checked last). A container control's page is ``{parent: id, panel: n}``.

Semantics (same as the Swift applier):

- Ops address nodes BY ID — controls, groups, container pages, ``longPressGroup`` and
  canvas-hosted controls; the first holder of an id (document order, depth-first) wins.
- Atomic: any failing op raises :class:`PatchError` (with ``op_index``); the input is
  never mutated. A ``base`` that isn't ``content_digest(layout)`` fails the batch.
- ``value: null`` always means "remove the key".
- A sectioned (``schemaVersion: 2``) document is folded to the inline form, the ops run,
  and it is lifted back so every facet stays in the section it lived in.
- ``add``/``duplicate``/``addTab`` mint opaque ids (``c_``/``g_``/``t_`` + 6 hex) when the
  given id is absent, taken or a ``$placeholder``; later ops in the batch may name the
  placeholder. ``PatchResult.minted`` maps placeholder (or ``"#<op index>"``) → id.
- ``PatchResult.inverse`` is the op list that turns ``document`` back into the input.

Not ported: the app's post-apply ``LayoutDecoder`` validation (``validate: true``).
"""
from __future__ import annotations

import copy
import random as _random
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from . import canonical as _canonical
from . import sections as _sections

__all__ = [
    "PatchError", "PatchResult", "decode_op", "decode_batch", "apply", "diff",
    "layout_hash", "OPS", "PRESENTATIONS", "ACTION_SLOTS",
]

#: ``"sha256:<hex>"`` over the canonical (RFC 8785) credential-stripped layout.
layout_hash = _canonical.content_digest

PRESENTATIONS = ("default", "landscape", "regular")
ACTION_SLOTS = ("action", "longPressAction")
_REFUSED_PROP_KEYS = ("id", "children", "panels")
_MAX_DEPTH = 64
_POOL_DEPTH = 96
_MAX_WRITABLE = 2


class PatchError(ValueError):
    """A batch that can't apply. ``op_index`` is the failing op, or None for a
    batch-level failure (decode, base, read-only)."""

    def __init__(self, message: str, op_index: Optional[int] = None):
        self.message = message
        self.op_index = op_index
        super().__init__(f"op {op_index}: {message}" if op_index is not None else message)


@dataclass
class PatchResult:
    document: Any
    minted: dict = field(default_factory=dict)
    inverse: list = field(default_factory=list)


class _Failure(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


# ── strict JSON equality (True != 1, 1 == 1.0) ───────────────────────────────

def _same(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


def _is_int(v) -> bool:
    return (isinstance(v, int) and not isinstance(v, bool)) or (isinstance(v, float) and v.is_integer())


def _str(v) -> Optional[str]:
    return v if isinstance(v, str) else None


# ── wire form ────────────────────────────────────────────────────────────────

#: Every canonical op name (aliases excluded).
OPS = ("setProp", "update", "setSync", "setAction", "add", "remove", "duplicate", "move",
       "resize", "place", "renameId", "layout", "setTheme", "addTab", "removeTab", "setTab",
       "moveTab", "upsertSource", "removeSource")


def _ref(v):
    """A tab/container ref: a non-negative integral number (tab index) or a non-empty
    string; None otherwise."""
    if _is_int(v) and not isinstance(v, bool) and v >= 0:
        return int(v)
    if isinstance(v, str) and v:
        return v
    return None


def decode_op(obj) -> dict:
    """One op (aliases accepted) → its canonical wire dict. Raises :class:`PatchError`."""
    if not isinstance(obj, dict):
        raise PatchError("an op must be an object")
    o = obj
    name = o.get("op")

    def s(k):
        v = o.get(k)
        if not isinstance(v, str) or not v:
            raise PatchError(f'{name if isinstance(name, str) else "op"} needs "{k}"')
        return v

    def opt_s(k):
        return _str(o.get(k))

    def pair(k):
        v = o.get(k)
        if v is None:
            return None
        ints = [int(x) for x in v if _is_int(x) and not isinstance(x, bool)] if isinstance(v, list) else []
        if len(ints) != 2:
            raise PatchError(f'"{k}" must be [int, int]')
        return ints

    def num(k):
        v = o.get(k)
        return int(v) if _is_int(v) and not isinstance(v, bool) else None

    def value(k):
        return copy.deepcopy(o.get(k))  # null / absent → None

    def obj_(k):
        v = o.get(k)
        return copy.deepcopy(v) if isinstance(v, dict) else {}

    def keys(k):
        v = o.get(k)
        return [x for x in v if isinstance(x, str)] if isinstance(v, list) else []

    def parent(k, alt):
        ref = _ref(o.get(k))
        if ref is None:
            ref = _ref(o.get(alt))
        if ref is None:
            return None
        out = {"parent": ref}
        if num("panel") is not None:
            out["panel"] = num("panel")
        return out

    def tab(k):
        ref = _ref(o.get(k))
        if ref is None:
            raise PatchError(f'needs a "{k}" (id, title or index)')
        return ref

    def put(d, **kv):
        for k, v in kv.items():
            if v is not None:
                d[k] = v
        return d

    if not isinstance(name, str) or not name:
        raise PatchError('op needs "op"')
    if name in ("setProp", "set", "unset"):
        d = {"op": "setProp", "id": s("id"), "key": s("key"),
             "value": None if name == "unset" else value("value")}
        return put(d, config=opt_s("config"))
    if name == "update":
        return {"op": "update", "id": s("id"), "set": obj_("set"), "unset": keys("unset")}
    if name == "setSync":
        return {"op": "setSync", "id": s("id"), "sync": value("sync")}
    if name == "setAction":
        d = {"op": "setAction", "id": s("id"), "action": value("action")}
        slot = opt_s("slot") or "action"
        return put(d, slot=None if slot == "action" else slot)
    if name == "add":
        p = parent("parent", "tab")
        if p is None:
            raise PatchError('add needs a "parent"')
        control = value("control")
        if control is None:
            control = value("child")
        if control is None:
            raise PatchError('add needs a "control"')
        d = {"op": "add", **p, "control": control}
        return put(d, position=pair("position"), span=pair("span"), index=num("index"))
    if name == "remove":
        return {"op": "remove", "id": s("id")}
    if name == "duplicate":
        return put({"op": "duplicate", "id": s("id")}, position=pair("position"))
    if name == "move":
        d = put({"op": "move", "id": s("id")}, position=pair("position"))
        d.update(parent("parent", "tab") or {})
        return put(d, index=num("index"))
    if name == "resize":
        span = pair("span")
        if span is None:
            raise PatchError('resize needs "span"')
        return {"op": "resize", "id": s("id"), "span": span}
    if name == "place":
        d = {"op": "place", "id": s("id"), "presentation": opt_s("presentation") or "default"}
        put(d, position=pair("position"), span=pair("span"))
        return put(d, hidden=True if o.get("hidden") is True else None)
    if name == "renameId":
        return {"op": "renameId", "from": s("from"), "to": s("to")}
    if name == "layout":
        return {"op": "layout", "set": obj_("set"), "unset": keys("unset")}
    if name == "setLayout":
        key, v = s("key"), value("value")
        if v is None:
            return {"op": "layout", "set": {}, "unset": [key]}
        return {"op": "layout", "set": {key: v}, "unset": []}
    if name == "setTheme":
        return put({"op": "setTheme", "key": s("key"), "value": value("value")}, scheme=opt_s("scheme"))
    if name == "addTab":
        d = {"op": "addTab"}
        if isinstance(o.get("tab"), dict):
            d["tab"] = obj_("tab")
        else:
            for k in ("title", "icon", "id", "grid"):
                if k in o:
                    d[k] = copy.deepcopy(o[k])
        return put(d, index=num("index"))
    if name == "removeTab":
        return {"op": "removeTab", "tab": tab("tab")}
    if name == "setTab":
        return {"op": "setTab", "tab": tab("tab"), "key": s("key"), "value": value("value")}
    if name == "renameTab":
        return {"op": "setTab", "tab": tab("from"), "key": "title", "value": s("to")}
    if name == "moveTab":
        i = num("index")
        if i is None:
            raise PatchError('moveTab needs "index"')
        return {"op": "moveTab", "tab": tab("tab"), "index": i}
    if name == "upsertSource":
        d = value("def")
        if d is None:
            raise PatchError('upsertSource needs "def"')
        return {"op": "upsertSource", "sourceId": s("sourceId"), "def": d}
    if name == "removeSource":
        return {"op": "removeSource", "sourceId": s("sourceId")}
    raise PatchError(f'unknown op "{name}"')


def decode_batch(obj) -> dict:
    """``{"ops": [...], "base"?, "author"?, "label"?}`` (or a bare op list) → a batch of
    canonical ops. Raises :class:`PatchError` naming the bad op."""
    if isinstance(obj, list):
        obj = {"ops": obj}
    if not isinstance(obj, dict) or not isinstance(obj.get("ops"), list):
        raise PatchError('a batch is {"ops": [...]}')
    ops = []
    for i, item in enumerate(obj["ops"]):
        try:
            ops.append(decode_op(item))
        except PatchError as e:
            raise PatchError(f"op {i}: {e.message}") from None
    out = {"ops": ops}
    for k in ("base", "author", "label"):
        if isinstance(obj.get(k), str):
            out[k] = obj[k]
    return out


# ── shared helpers ───────────────────────────────────────────────────────────

_MISSING = object()


def _get(root, path):
    cur = root
    for step in path:
        if isinstance(step, str) and isinstance(cur, dict) and step in cur:
            cur = cur[step]
        elif isinstance(step, int) and isinstance(cur, list) and 0 <= step < len(cur):
            cur = cur[step]
        else:
            return _MISSING
    return cur


def _set(root, path, new):
    """``root`` with the value at ``path`` replaced (in place where possible); ``new``
    None removes an object key or an array element. Returns the (new) root."""
    if not path:
        return new
    step, rest = path[0], path[1:]
    if isinstance(step, str) and isinstance(root, dict):
        if not rest:
            if new is None:
                root.pop(step, None)
            else:
                root[step] = new
        else:
            root[step] = _set(root.get(step, {}), rest, new)
    elif isinstance(step, int) and isinstance(root, list) and 0 <= step < len(root):
        if not rest:
            if new is None:
                del root[step]
            else:
                root[step] = new
        else:
            root[step] = _set(root[step], rest, new)
    return root


def _strings_under(key, value) -> set:
    out = set()

    def walk(v, depth):
        if depth >= _POOL_DEPTH:
            return
        if isinstance(v, dict):
            if isinstance(v.get(key), str):
                out.add(v[key])
            for x in v.values():
                walk(x, depth + 1)
        elif isinstance(v, list):
            for x in v:
                walk(x, depth + 1)

    walk(value, 0)
    return out


def _id_pool(value) -> set:
    """Every string under an ``id`` key anywhere — the pool a mint must avoid."""
    return _strings_under("id", value)


def _fresh_name(type_: str, taken: set) -> str:
    """"Gauge 1", "Live group 2": the type split at capitals, sentence-cased, numbered."""
    words = "".join((" " + ch) if ch.isupper() else ch for ch in type_)
    base = words[:1].upper() + words[1:].lower()
    n = 1
    while f"{base} {n}" in taken:
        n += 1
    return f"{base} {n}"


def _random_id(prefix: str, taken: set) -> str:
    while True:
        cand = f"{prefix}_{_random.randrange(0x1000000):06x}"
        if cand not in taken:
            return cand


def _placement(d: dict):
    """(row, col, rowSpan, colSpan) of a child, defaulting like the renderer."""
    def pair(key, fallback):
        v = d.get(key)
        if (isinstance(v, list) and len(v) >= 2 and all(
                isinstance(x, (int, float)) and not isinstance(x, bool) for x in v[:2])):
            return int(v[0]), int(v[1])
        return fallback
    r, c = pair("position", (0, 0))
    rs, cs = pair("span", (1, 1))
    return r, c, max(1, rs), max(1, cs)


def _content_rows(kids) -> int:
    rows = [r + rs for r, _, rs, _ in (_placement(k) for k in kids if isinstance(k, dict))]
    return max(rows) if rows else 0


def _map_structural(d: dict, fn) -> dict:
    for key in ("children", "panels"):
        if isinstance(d.get(key), list):
            d[key] = [fn(k) for k in d[key]]
    if "longPressGroup" in d:
        d["longPressGroup"] = fn(d["longPressGroup"])
    canvas = d.get("canvasConfig")
    if isinstance(canvas, dict) and isinstance(canvas.get("items"), list):
        items = []
        for it in canvas["items"]:
            if isinstance(it, dict) and "control" in it:
                it = dict(it)
                it["control"] = fn(it["control"])
            items.append(it)
        canvas["items"] = items
    return d


def _remint(value, taken: set, mint) -> Any:
    """A copy of a subtree with every structural id re-minted (``LayoutIDs.remint``);
    ``visible.when`` references inside the subtree follow their node."""
    renamed: dict = {}

    def fresh(v):
        if not isinstance(v, dict):
            return v
        d = dict(v)
        if isinstance(d.get("id"), str):
            new = mint("g" if d.get("type") == "group" else "c", taken)
            taken.add(new)
            renamed.setdefault(d["id"], new)
            d["id"] = new
        return _map_structural(d, fresh)

    def remap(v):
        if not isinstance(v, dict):
            return v
        vis = v.get("visible")
        if isinstance(vis, dict) and isinstance(vis.get("when"), str) and vis["when"] in renamed:
            v["visible"] = {**vis, "when": renamed[vis["when"]]}
        return _map_structural(v, remap)

    return remap(fresh(copy.deepcopy(value)))


def _renaming_references(doc, old: str, new: str):
    """Every reference to ``old`` rewritten to ``new``: ``visible.when`` on any node and
    ``hero``/``control``/``controlId``/``slots``/``controlIds`` inside ``glance``."""
    def walk(v, in_glance, depth):
        if depth >= _POOL_DEPTH:
            return v
        if isinstance(v, dict):
            vis = v.get("visible")
            if isinstance(vis, dict) and vis.get("when") == old:
                v["visible"] = {**vis, "when": new}
            for k in list(v):
                if k == "visible" or isinstance(v[k], str):
                    continue
                v[k] = walk(v[k], in_glance or (depth == 0 and k == "glance"), depth + 1)
            if in_glance:
                for k in ("hero", "control", "controlId"):
                    if v.get(k) == old:
                        v[k] = new
                for k in ("slots", "controlIds"):
                    if isinstance(v.get(k), list):
                        v[k] = [new if x == old else x for x in v[k]]
            return v
        if isinstance(v, list):
            return [walk(x, in_glance, depth + 1) for x in v]
        return v

    return walk(doc, False, 0)


# ── engine: document index ───────────────────────────────────────────────────

def _restore(nid, before: dict, after: dict) -> list:
    """The ``update`` that restores ``before`` over ``after`` on node ``nid``."""
    set_ = {k: copy.deepcopy(v) for k, v in before.items() if k not in after or not _same(after[k], v)}
    unset = sorted(k for k in after if k not in before)
    return [{"op": "update", "id": nid, "set": set_, "unset": unset}] if set_ or unset else []


class _Engine:
    def __init__(self, doc, mint):
        self.doc = doc
        self.mint = mint
        self.undo: list = []           # one list per op, execution order
        self.minted: dict = {}
        self.original_ids: dict = {}   # current id -> id in the input (renameId)

    @property
    def inverse(self) -> list:
        return [op for group in reversed(self.undo) for op in group]

    def resolve(self, nid: str) -> str:
        return self.minted.get(nid, nid) if nid.startswith("$") else nid

    @property
    def tabs(self) -> list:
        t = self.doc.get("tabs") if isinstance(self.doc, dict) else None
        return t if isinstance(t, list) else []

    def tab_index(self, ref):
        tabs = self.tabs
        if isinstance(ref, int):
            return ref if 0 <= ref < len(tabs) else None
        for key in ("id", "title"):
            for i, t in enumerate(tabs):
                if isinstance(t, dict) and t.get(key) == ref:
                    return i
        return None

    def node_path(self, raw: str):
        nid = self.resolve(raw)
        for t, tab in enumerate(self.tabs):
            hit = self._search(tab, ("tabs", t), nid, False, 0)
            if hit is not None:
                return hit
        return None

    def _search(self, v, path, nid, is_node, depth):
        if depth >= _MAX_DEPTH or not isinstance(v, dict):
            return None
        if is_node and v.get("id") == nid:
            return path
        for key in ("children", "panels"):
            kids = v.get(key)
            if isinstance(kids, list):
                for i, kid in enumerate(kids):
                    hit = self._search(kid, path + (key, i), nid, True, depth + 1)
                    if hit is not None:
                        return hit
        if "longPressGroup" in v:
            hit = self._search(v["longPressGroup"], path + ("longPressGroup",), nid, True, depth + 1)
            if hit is not None:
                return hit
        canvas = v.get("canvasConfig")
        items = canvas.get("items") if isinstance(canvas, dict) else None
        if isinstance(items, list):
            for i, item in enumerate(items):
                if not isinstance(item, dict) or "control" not in item:
                    continue
                p = path + ("canvasConfig", "items", i, "control")
                hit = self._search(item["control"], p, nid, True, depth + 1)
                if hit is not None:
                    return hit
        return None

    def node(self, nid):
        path = self.node_path(nid)
        d = _get(self.doc, path) if path is not None else _MISSING
        if not isinstance(d, dict):
            raise _Failure(f'no control or group "{nid}"')
        return path, d

    def container_path(self, ref, panel=None):
        tabs = self.tabs
        if isinstance(ref, int):
            if panel is not None:
                raise _Failure("a tab has no pages")
            if not 0 <= ref < len(tabs):
                raise _Failure(f"no tab {ref}")
            return ("tabs", ref)
        key = self.resolve(ref)
        if panel is None:
            for i, t in enumerate(tabs):
                if isinstance(t, dict) and t.get("id") == key:
                    return ("tabs", i)
        path = self.node_path(key)
        d = _get(self.doc, path) if path is not None else _MISSING
        if isinstance(d, dict):
            if panel is not None:
                panels = d.get("panels")
                if not (isinstance(panels, list) and 0 <= panel < len(panels) and isinstance(panels[panel], dict)):
                    raise _Failure(f"{key} has no page {panel}")
                return path + ("panels", panel)
            if isinstance(d.get("children"), list) or d.get("type") == "group":
                return path
            raise _Failure(f"{key} can't hold children")
        if panel is None:
            for i, t in enumerate(tabs):
                if isinstance(t, dict) and t.get("title") == key:
                    return ("tabs", i)
        raise _Failure(f'no tab, group or page "{key}"')

    def parent_ref(self, path) -> dict:
        """A ref naming the container at ``path`` (for inverses)."""
        if len(path) == 2 and isinstance(path[1], int):
            return {"parent": path[1]}
        d = _get(self.doc, path)
        if isinstance(d, dict) and isinstance(d.get("id"), str) and d["id"]:
            return {"parent": d["id"]}
        if len(path) >= 2 and isinstance(path[-1], int) and path[-2] == "panels":
            owner = _get(self.doc, path[:-2])
            if isinstance(owner, dict) and isinstance(owner.get("id"), str) and owner["id"]:
                return {"parent": owner["id"], "panel": path[-1]}
        raise _Failure("the container has no id to address")

    @staticmethod
    def slot(path):
        if len(path) < 2 or not isinstance(path[-1], int) or path[-2] != "children":
            raise _Failure("only a tab, group or page child can be removed or moved")
        return path[:-2], path[-1]

    def children(self, container) -> list:
        kids = _get(self.doc, container + ("children",))
        return list(kids) if isinstance(kids, list) else []

    def set_children(self, kids, container):
        self.doc = _set(self.doc, container + ("children",), kids)

    def edit_node(self, nid, transform):
        path, before = self.node(nid)
        after = copy.deepcopy(before)
        transform(after)
        self.doc = _set(self.doc, path, after)
        self.undo.append(_restore(after.get("id") if isinstance(after.get("id"), str) else self.resolve(nid),
                                  before, after))


# ── engine: node ops ─────────────────────────────────────────────────────────

def _span_ok(p) -> bool:
    return all(x >= 1 for x in p)


class _NodeOps(_Engine):
    def run(self, op: dict, index: int):
        name = op["op"]
        if name == "setProp":
            key, value, config = op["key"], op.get("value"), op.get("config")
            if key in _REFUSED_PROP_KEYS:
                raise _Failure(f"{key} can't be set with setProp")

            def t(d):
                if config is None:
                    _put(d, key, value)
                    return
                nested = dict(d[config]) if isinstance(d.get(config), dict) else {}
                _put(nested, key, value)
                _put(d, config, None if not nested and value is None else nested)
            self.edit_node(op["id"], t)
        elif name == "update":
            if "id" in op["set"] or "id" in op["unset"]:
                raise _Failure("id changes through renameId")

            def t(d):
                for k, v in op["set"].items():
                    _put(d, k, copy.deepcopy(v))
                for k in op["unset"]:
                    d.pop(k, None)
            self.edit_node(op["id"], t)
        elif name == "setSync":
            self.edit_node(op["id"], lambda d: _put(d, "sync", copy.deepcopy(op.get("sync"))))
        elif name == "setAction":
            slot = op.get("slot", "action")
            if slot not in ACTION_SLOTS:
                raise _Failure("slot must be action or longPressAction")
            self.edit_node(op["id"], lambda d: _put(d, slot, copy.deepcopy(op.get("action"))))
        elif name == "resize":
            if not _span_ok(op["span"]):
                raise _Failure("span must be at least [1, 1]")
            self.edit_node(op["id"], lambda d: d.__setitem__("span", list(op["span"])))
        elif name == "place":
            self._place(op)
        elif name == "add":
            self._add(op, index)
        elif name == "remove":
            path, d = self.node(op["id"])
            container, i = self.slot(path)
            ref = self.parent_ref(container)
            kids = self.children(container)
            del kids[i]
            self.set_children(kids, container)
            self.undo.append([{"op": "add", **ref, "control": copy.deepcopy(d), "index": i}])
        elif name == "duplicate":
            path, d = self.node(op["id"])
            container, _ = self.slot(path)
            taken = _id_pool(self.doc)
            dup = _remint(d, taken, self.mint)
            if not isinstance(dup, dict) or not isinstance(dup.get("id"), str):
                raise _Failure(f"{op['id']} has no id to copy")
            r, c, rs, cs = _placement(d)
            dup["position"] = list(op["position"]) if op.get("position") is not None else [r + rs, c]
            dup["span"] = [rs, cs]
            self.set_children(self.children(container) + [dup], container)
            self.minted[f"#{index}"] = dup["id"]
            self.undo.append([{"op": "remove", "id": dup["id"]}])
        elif name == "move":
            self._move(op)
        elif name == "renameId":
            self._rename_id(self.resolve(op["from"]), op["to"])
        else:
            self.run_document_op(op, index)

    def _place(self, op):
        pres, pos, span, hidden = op.get("presentation", "default"), op.get("position"), op.get("span"), op.get("hidden", False)
        if pres not in PRESENTATIONS:
            raise _Failure("presentation must be default, landscape or regular")
        if span is not None and not _span_ok(span):
            raise _Failure("span must be at least [1, 1]")
        if pos is not None and not all(x >= 0 for x in pos):
            raise _Failure("position must be ≥ [0, 0]")

        def t(d):
            if pres == "default":
                if hidden:
                    raise _Failure("the default presentation can't be hidden")
                if pos is None and span is None:
                    raise _Failure("place needs a position or span")
                if pos is not None:
                    d["position"] = list(pos)
                if span is not None:
                    d["span"] = list(span)
            elif hidden:
                d[pres] = {"hidden": True}
            elif pos is not None or span is not None:
                v = {}
                if pos is not None:
                    v["position"] = list(pos)
                if span is not None:
                    v["span"] = list(span)
                d[pres] = v
            else:
                d.pop(pres, None)
        self.edit_node(op["id"], t)

    def _add(self, op, op_index):
        d = op["control"]
        type_ = d.get("type") if isinstance(d, dict) else None
        if not isinstance(type_, str) or not type_:
            raise _Failure("add needs a control object with a type")
        d = copy.deepcopy(d)
        container = self.container_path(op["parent"], op.get("panel"))
        taken = _id_pool(self.doc)
        given = d["id"] if isinstance(d.get("id"), str) else ""
        placeholder = given if given.startswith("$") else None
        subtree = _id_pool(d)
        needs_mint = not given or placeholder is not None or bool(subtree & taken)
        if needs_mint:
            pool = taken | subtree
            if not given:
                # Documented rule ("mints when control.id is absent"): give the node an id
                # slot so remint fills it. (The Swift applier currently fails here.)
                d["id"] = ""
            d = _remint(d, pool, self.mint)
            if given and placeholder is None and given not in taken:
                d["id"] = given
            if "name" not in d and (not given or placeholder is not None):
                live = type_ == "group" and "dynamic" in d
                d["name"] = _fresh_name("liveGroup" if live else type_, _strings_under("name", self.doc))
        new_id = d.get("id")
        if not isinstance(new_id, str):
            raise _Failure("could not mint an id")
        if op.get("position") is not None:
            d["position"] = [max(0, x) for x in op["position"]]
        if op.get("span") is not None:
            d["span"] = [max(1, x) for x in op["span"]]
        kids = self.children(container)
        if "position" not in d:
            d["position"] = [_content_rows(kids), 0]
        at = op.get("index")
        i = min(max(0, len(kids) if at is None else at), len(kids))
        kids.insert(i, d)
        self.set_children(kids, container)
        if needs_mint:
            self.minted[placeholder or f"#{op_index}"] = new_id
        self.undo.append([{"op": "remove", "id": new_id}])

    def _move(self, op):
        pos, has_parent, at = op.get("position"), "parent" in op, op.get("index")
        if pos is None and not has_parent:
            raise _Failure("move needs a position or a parent")
        if pos is not None and not all(x >= 0 for x in pos):
            raise _Failure("position must be ≥ [0, 0]")
        path, before = self.node(op["id"])
        d = copy.deepcopy(before)
        if pos is not None:
            d["position"] = list(pos)
        nid = before["id"] if isinstance(before.get("id"), str) else self.resolve(op["id"])
        if not has_parent:
            self.doc = _set(self.doc, path, d)
            self.undo.append(_restore(nid, before, d))
            return
        target = self.container_path(op["parent"], op.get("panel"))
        if target[:len(path)] == path:
            raise _Failure(f"can't move {op['id']} into itself")
        src, i = self.slot(path)
        back = self.parent_ref(src)
        kids = self.children(src)
        del kids[i]
        self.set_children(kids, src)
        dest = self.container_path(op["parent"], op.get("panel"))
        dkids = self.children(dest)
        j = min(max(0, len(dkids) if at is None else at), len(dkids))
        dkids.insert(j, d)
        self.set_children(dkids, dest)
        self.undo.append([{"op": "move", "id": nid, **back, "index": i}] + _restore(nid, before, d))

    def _rename_id(self, old, new):
        if not new or new.startswith("$"):
            raise _Failure("renameId needs a real new id")
        if new in _id_pool(self.doc):
            raise _Failure(f"{new} is already used")
        path, _ = self.node(old)
        self.doc = _set(self.doc, path + ("id",), new)
        self.doc = _renaming_references(self.doc, old, new)
        for section in _sections.SECTIONS:
            m = self.doc.get(section)
            if isinstance(m, dict) and old in m:
                m[new] = m.pop(old)
        for k, v in list(self.minted.items()):
            if v == old:
                self.minted[k] = new
        self.original_ids[new] = self.original_ids.pop(old, old)
        self.undo.append([{"op": "renameId", "from": new, "to": old}])


def _put(d: dict, key, value):
    """``d[key] = value``; None removes the key (JSON null means "remove")."""
    if value is None:
        d.pop(key, None)
    else:
        d[key] = value


# ── engine: document, theme, tab and source ops ─────────────────────────────

class _Ops(_NodeOps):
    def _set_root(self, key, value):
        _put(self.doc, key, value)

    def _tab_or_fail(self, ref):
        i = self.tab_index(ref)
        if i is None:
            raise _Failure(f"no tab {ref}")
        return i

    def run_document_op(self, op, index):
        name = op["op"]
        root = self.doc
        if name == "layout":
            keys = set(op["set"]) | set(op["unset"])
            if "tabs" in keys:
                raise _Failure("tabs change through tab ops")
            before = {k: copy.deepcopy(root[k]) for k in keys if k in root}
            for k, v in op["set"].items():
                _put(root, k, copy.deepcopy(v))
            for k in op["unset"]:
                root.pop(k, None)
            back, drop = {}, []
            for k in keys:
                if k in before and (k not in root or not _same(before[k], root[k])):
                    back[k] = before[k]
                elif k not in before and k in root:
                    drop.append(k)
            self.undo.append([{"op": "layout", "set": back, "unset": sorted(drop)}] if back or drop else [])
        elif name == "setTheme":
            key, value, scheme = op["key"], copy.deepcopy(op.get("value")), op.get("scheme")
            theme = dict(root["theme"]) if isinstance(root.get("theme"), dict) else {}
            if scheme is not None:
                target = dict(theme[scheme]) if isinstance(theme.get(scheme), dict) else {}
            else:
                target = theme
            old = copy.deepcopy(target.get(key))
            _put(target, key, value)
            if scheme is not None:
                theme[scheme] = target
            else:
                theme = target
            self._set_root("theme", theme)
            inv = {"op": "setTheme", "key": key, "value": old}
            if scheme is not None:
                inv["scheme"] = scheme
            self.undo.append([inv])
        elif name == "addTab":
            verbatim = "tab" in op
            t = copy.deepcopy(op["tab"]) if verbatim else {
                k: copy.deepcopy(op[k]) for k in ("title", "icon", "id", "grid") if k in op}
            if not isinstance(t, dict):
                raise _Failure("addTab needs a tab object")
            tabs = list(self.tabs)
            tab_ids = {x["id"] for x in tabs if isinstance(x, dict) and isinstance(x.get("id"), str)}
            if not verbatim:
                given = _str(t.get("id")) or ""
                if not given or given in tab_ids:
                    t["id"] = self.mint("t", _id_pool(self.doc) | tab_ids)
                if not _str(t.get("title")):
                    t["title"] = f"Tab {len(tabs) + 1}"
                if not _str(t.get("icon")):
                    t["icon"] = "square.grid.2x2"
                if t.get("grid") is None:
                    t["grid"] = {"columns": 4, "rows": 8}
                if t.get("children") is None:
                    t["children"] = []
            at = op.get("index")
            i = min(max(0, len(tabs) if at is None else at), len(tabs))
            tabs.insert(i, t)
            self._set_root("tabs", tabs)
            if not verbatim and isinstance(t.get("id"), str):
                self.minted[f"#{index}"] = t["id"]
            self.undo.append([{"op": "removeTab", "tab": i}])
        elif name == "removeTab":
            i = self._tab_or_fail(op["tab"])
            tabs = list(self.tabs)
            if len(tabs) <= 1:
                raise _Failure("a layout needs at least one tab")
            removed = tabs.pop(i)
            self._set_root("tabs", tabs)
            self.undo.append([{"op": "addTab", "tab": copy.deepcopy(removed), "index": i}])
        elif name == "setTab":
            i = self._tab_or_fail(op["tab"])
            before = self.tabs[i]
            if not isinstance(before, dict):
                raise _Failure(f"no tab {op['tab']}")
            key, value = op["key"], copy.deepcopy(op.get("value"))
            if key == "children":
                raise _Failure("children change through add/remove/move")
            t = dict(before)
            # Retitling a legacy (id-less) tab pins its id to the OLD title (carter-m7s.7).
            if (key == "title" and isinstance(before.get("title"), str)
                    and not _same(value, before.get("title")) and not _str(before.get("id"))):
                t["id"] = before["title"]
            _put(t, key, value)
            tabs = list(self.tabs)
            tabs[i] = t
            self._set_root("tabs", tabs)
            changed = {k for k in set(before) | set(t)
                       if (k in before) != (k in t) or (k in t and not _same(before[k], t[k]))}
            order = sorted(changed - {"id"}) + (["id"] if "id" in changed else [])
            self.undo.append([{"op": "setTab", "tab": i, "key": k, "value": copy.deepcopy(before.get(k))}
                              for k in order])
        elif name == "moveTab":
            i = self._tab_or_fail(op["tab"])
            tabs = list(self.tabs)
            t = tabs.pop(i)
            j = min(max(0, op["index"]), len(tabs))
            tabs.insert(j, t)
            self._set_root("tabs", tabs)
            self.undo.append([{"op": "moveTab", "tab": j, "index": i}])
        elif name == "upsertSource":
            if not isinstance(op["def"], dict):
                raise _Failure("a source def must be an object")
            sid = op["sourceId"]
            sources = dict(root["sources"]) if isinstance(root.get("sources"), dict) else {}
            old = sources.get(sid)
            sources[sid] = copy.deepcopy(op["def"])
            self._set_root("sources", sources)
            self.undo.append([{"op": "upsertSource", "sourceId": sid, "def": old} if old is not None
                              else {"op": "removeSource", "sourceId": sid}])
        elif name == "removeSource":
            sid = op["sourceId"]
            sources = dict(root["sources"]) if isinstance(root.get("sources"), dict) else {}
            if sid not in sources:
                raise _Failure(f'no source "{sid}"')
            old = sources.pop(sid)
            self._set_root("sources", sources or None)
            self.undo.append([{"op": "upsertSource", "sourceId": sid, "def": old}])
        else:
            raise _Failure("unhandled op")


# ── sectioned documents: facets stay where they live ─────────────────────────

def _facet_homes(document: dict) -> dict:
    """section -> {id -> facets that id keeps in that section of the input}."""
    homes: dict = {}
    for name, facets in _sections.SECTIONS.items():
        m = document.get(name)
        if not isinstance(m, dict):
            continue
        for cid, entry in m.items():
            if not isinstance(entry, dict):
                continue
            keys = set(entry) & set(facets)
            if name == "placements" and isinstance(entry.get("default"), dict):
                keys |= set(entry["default"]) & {"position", "span"}
            if keys:
                homes.setdefault(name, {})[cid] = keys
    return homes


def _relift(doc: dict, homes: dict, original_ids: dict) -> dict:
    """Model form → the input's sectioned form: a facet an id kept in a section goes
    back there; everything else (and every new control) stays inline. Entries whose id
    is gone are dropped."""
    secs = {name: {cid: dict(e) for cid, e in doc[name].items() if isinstance(e, dict)}
            for name in _sections.SECTIONS if isinstance(doc.get(name), dict)}
    claimed: set = set()

    def lift(kids, depth):
        for child in kids:
            if not isinstance(child, dict):
                continue
            cid = child.get("id")
            if isinstance(cid, str) and cid and cid not in claimed:
                claimed.add(cid)
                original = original_ids.get(cid, cid)
                for name in _sections.SECTIONS:
                    for facet in sorted(homes.get(name, {}).get(original, ())):
                        if facet in child:
                            secs.setdefault(name, {}).setdefault(cid, {})[facet] = child.pop(facet)
            if depth < _MAX_DEPTH and child.get("type") == "group" and isinstance(child.get("children"), list):
                lift(child["children"], depth + 1)

    for tab in doc.get("tabs") or []:
        if isinstance(tab, dict) and isinstance(tab.get("children"), list):
            lift(tab["children"], 0)
    for name in _sections.SECTIONS:
        kept = {cid: e for cid, e in secs.get(name, {}).items() if cid in claimed and e}
        _put(doc, name, kept or None)
    if _sections.is_sectioned(doc):
        v = doc.get("schemaVersion")
        doc["schemaVersion"] = max(_sections.SCHEMA_VERSION, int(v) if _is_int(v) else 1)
    return doc


# ── apply ────────────────────────────────────────────────────────────────────

def apply(layout: dict, ops_or_batch, *, base: Optional[str] = None,
          mint: Optional[Callable[[str, set], str]] = None) -> PatchResult:
    """Run a batch (``{"ops": [...], "base"?}`` or a bare op list) against ``layout``
    (inline or sectioned). Returns :class:`PatchResult` ``(document, minted, inverse)``;
    raises :class:`PatchError` (the input is never mutated). ``base`` (or the batch's
    ``base``) must equal ``layout_hash(layout)``. ``mint(prefix, taken) -> id`` overrides
    the random ``c_``/``g_``/``t_`` minting (tests pass a deterministic one)."""
    batch = decode_batch(ops_or_batch)
    base = base if base is not None else batch.get("base")
    if not isinstance(layout, dict):
        raise PatchError("a layout must be a JSON object")
    if base is not None and _canonical.content_digest(layout) != base:
        raise PatchError(f"the layout changed since base {base[:15]}…; reread it and rebuild the ops")
    version = layout.get("schemaVersion")
    if _is_int(version) and not isinstance(version, bool) and version > _MAX_WRITABLE:
        raise PatchError("this layout was written by a newer CAR-TER and is read-only here")
    sectioned = _sections.is_sectioned(layout)
    engine = _Ops(_sections.to_inline(layout) if sectioned else copy.deepcopy(layout),
                  mint or _random_id)
    homes = _facet_homes(layout) if sectioned else {}
    for i, op in enumerate(batch["ops"]):
        try:
            engine.run(op, i)
        except _Failure as e:
            raise PatchError(e.message, i) from None
    doc = _relift(engine.doc, homes, engine.original_ids) if sectioned else engine.doc
    return PatchResult(document=doc, minted=dict(engine.minted), inverse=engine.inverse)


# ── diff ─────────────────────────────────────────────────────────────────────

class _Inexpressible(Exception):
    pass


def _no_mint(prefix, taken):
    raise _Failure("a diff never mints ids")


def _structural_ids(doc: dict) -> list:
    """Every structural node id (the applier's namespace), document order, with repeats."""
    out: list = []

    def walk(v, is_node, depth):
        if depth >= _MAX_DEPTH or not isinstance(v, dict):
            return
        if is_node and isinstance(v.get("id"), str):
            out.append(v["id"])
        for key in ("children", "panels"):
            if isinstance(v.get(key), list):
                for kid in v[key]:
                    walk(kid, True, depth + 1)
        if "longPressGroup" in v:
            walk(v["longPressGroup"], True, depth + 1)
        canvas = v.get("canvasConfig")
        if isinstance(canvas, dict) and isinstance(canvas.get("items"), list):
            for it in canvas["items"]:
                if isinstance(it, dict) and "control" in it:
                    walk(it["control"], True, depth + 1)

    for tab in doc.get("tabs") or []:
        walk(tab, False, 0)
    return out


def _tree(kids, depth=0):
    """The children tree (tab/group ``children``), pre-order. Every node must be an
    object with a real id, or the change can't be addressed."""
    for kid in kids:
        if not isinstance(kid, dict) or not isinstance(kid.get("id"), str) or not kid["id"] \
                or kid["id"].startswith("$") or depth >= _MAX_DEPTH:
            raise _Inexpressible
        yield kid
        if isinstance(kid.get("children"), list):
            yield from _tree(kid["children"], depth + 1)


def _check(doc: dict) -> set:
    """Tree ids of ``doc``; raises when ids are duplicated or collide with tab ids."""
    tabs = doc["tabs"]
    if not all(isinstance(t, dict) for t in tabs):
        raise _Inexpressible
    ids = _structural_ids(doc)
    if len(ids) != len(set(ids)):
        raise _Inexpressible
    tree = set()
    for t in tabs:
        kids = t.get("children", [])
        if not isinstance(kids, list):
            raise _Inexpressible
        tree |= {k["id"] for k in _tree(kids)}
    if tree & {t.get("id") for t in tabs}:
        raise _Inexpressible
    return tree


def _model(layout: dict) -> dict:
    return _sections.to_inline(layout) if _sections.is_sectioned(layout) else copy.deepcopy(layout)


def _diff_ops(old: dict, new: dict) -> list:
    a, b = _model(old), _model(new)
    if not isinstance(a.get("tabs"), list) or not isinstance(b.get("tabs"), list) or not b["tabs"]:
        raise _Inexpressible
    _check(a)
    new_tree = _check(b)
    eng = _Ops(a, _no_mint)
    ops: list = []

    def emit(op):
        eng.run(op, len(ops))
        ops.append(op)

    # 1. top-level keys
    keys = (set(eng.doc) | set(b)) - {"tabs"}
    set_ = {k: copy.deepcopy(b[k]) for k in sorted(keys) if k in b and (k not in eng.doc or not _same(eng.doc[k], b[k]))}
    unset = sorted(k for k in keys if k in eng.doc and k not in b)
    if set_ or unset:
        emit({"op": "layout", "set": set_, "unset": unset})

    # 2. tabs: matched by id when every tab has a unique one, else by index
    a_tabs, b_tabs = eng.tabs, b["tabs"]

    def tab_ids(tabs):
        ids = [t.get("id") for t in tabs]
        return ids if all(isinstance(i, str) and i for i in ids) and len(set(ids)) == len(ids) else None

    aids, bids = tab_ids(a_tabs), tab_ids(b_tabs)
    keyed = aids is not None and bids is not None
    if not keyed and len(a_tabs) != len(b_tabs):
        raise _Inexpressible
    if keyed:
        for t in b_tabs:
            if t["id"] not in aids:
                shell = {k: copy.deepcopy(v) for k, v in t.items() if k != "children"}
                if isinstance(t.get("children"), list):
                    shell["children"] = []
                emit({"op": "addTab", "tab": shell})

    def tab_ref(i):
        return bids[i] if keyed else i

    # 3. structure: every container's children in the new order (adds + moves)
    def place(ref, desired):
        for i, kid in enumerate(desired):
            cur = eng.children(eng.container_path(ref))
            if not (i < len(cur) and isinstance(cur[i], dict) and cur[i].get("id") == kid["id"]):
                if eng.node_path(kid["id"]) is not None:
                    emit({"op": "move", "id": kid["id"], "parent": ref, "index": i})
                else:
                    shell = {k: copy.deepcopy(v) for k, v in kid.items() if k != "children"}
                    if isinstance(kid.get("children"), list):
                        shell["children"] = []
                    emit({"op": "add", "parent": ref, "control": shell, "index": i})
            if isinstance(kid.get("children"), list):
                place(kid["id"], kid["children"])

    for i, t in enumerate(b_tabs):
        place(tab_ref(i), t.get("children") or [])

    # 4. removals: whatever is left of the old tree (outside tabs that go away)
    doomed_tabs = set(aids) - set(bids) if keyed else set()
    while True:
        gone = None
        for t in eng.tabs:
            if keyed and t.get("id") in doomed_tabs:
                continue
            for node in _tree(t.get("children") or []):
                if node["id"] not in new_tree:
                    gone = node["id"]
                    break
            if gone:
                break
        if gone is None:
            break
        emit({"op": "remove", "id": gone})

    # 5. node properties (position/span/tint/config/... incl. whole panels)
    for t in b_tabs:
        for node in _tree(t.get("children") or []):
            _, cur = eng.node(node["id"])
            ks = (set(cur) | set(node)) - {"id"}
            if isinstance(cur.get("children"), list) and isinstance(node.get("children"), list):
                ks.discard("children")
            s = {k: copy.deepcopy(node[k]) for k in sorted(ks) if k in node and (k not in cur or not _same(cur[k], node[k]))}
            u = sorted(k for k in ks if k in cur and k not in node)
            if s or u:
                emit({"op": "update", "id": node["id"], "set": s, "unset": u})

    # 6. tab removals + order
    if keyed:
        for tid in aids:
            if tid in doomed_tabs:
                emit({"op": "removeTab", "tab": tid})
        for i, tid in enumerate(bids):
            if eng.tabs[i].get("id") != tid:
                emit({"op": "moveTab", "tab": tid, "index": i})

    # 7. tab properties (title first: retitling a legacy tab pins its id, fixed last)
    for i, bt in enumerate(b_tabs):
        others = sorted((set(eng.tabs[i]) | set(bt)) - {"children", "title", "id"})
        for key in ["title"] + others + ["id"]:
            ct = eng.tabs[i]
            if (key in ct) != (key in bt) or (key in bt and not _same(ct[key], bt[key])):
                ref = i if key == "id" or not keyed else tab_ref(i)
                emit({"op": "setTab", "tab": ref, "key": key, "value": copy.deepcopy(bt.get(key))})
    return ops


def diff(old: dict, new: dict) -> Optional[list]:
    """Canonical-wire ops that turn ``old`` into ``new``, or None when the change can't
    be expressed safely (the caller then pushes the whole layout).

    Addresses nodes by id, so every tab/group child in both documents needs a unique id
    (and no node id may equal a tab id). Tabs are matched by id when every tab has a
    unique one (add/remove/reorder expressible), else by index (count must match).
    Container internals (``panels``, ``longPressGroup``, canvas items) change wholesale
    through ``update``. Keys holding JSON ``null`` can't be written (null removes).
    Every result is verified: ``apply(old, ops)`` must equal ``new`` canonically, else
    None. Order: ``layout``, ``addTab``, ``add``/``move``, ``remove``, ``update``,
    ``removeTab``/``moveTab``, ``setTab``."""
    if not isinstance(old, dict) or not isinstance(new, dict):
        return None
    try:
        ops = _diff_ops(old, new)
        out = apply(old, ops, mint=_no_mint).document
        if _canonical.canonical_bytes(out) != _canonical.canonical_bytes(new):
            return None
    except (_Inexpressible, _Failure, PatchError, TypeError, ValueError):
        return None
    return ops


