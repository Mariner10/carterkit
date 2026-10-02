"""Reference evaluator for a layout's ``derive`` block (see controldocs/derive.md).

This mirrors the app's ``Services/LayoutDerive.swift`` rule for rule, so Python and
Swift compute the same numbers. The shared fixtures in ``tests/fixtures/derive/``
(byte-identical to the app's ``CAR-TERTests/Fixtures/derive/``) prove it.

A derive node is a single-key JSON object (the op) or a number literal::

    {"mul": [{"control": "volts"}, {"control": "amps"}]}

Value rules: inputs coerce to numbers (bools are 1/0, numeric strings parse);
anything unreadable is ``None`` and ``None`` propagates; division by zero or a
non-finite result is ``None``; an unknown op parses to an invalid node that
evaluates to ``None`` (fail closed).
"""
from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Any, Callable, Optional

__all__ = [
    "NARY_OPS", "OPS", "TIME_UNITS", "MAX_NODES", "MAX_DEPTH", "MAX_ARGS",
    "Node", "parse", "evaluate_node", "to_number", "to_date",
    "graph_order", "evaluate", "problems", "consumers", "invalid_paths", "layout_controls",
    "DeriveRef", "arg", "ops",
]

#: n-ary ops: a non-empty argument list in, one value out.
NARY_OPS = ("add", "sub", "mul", "div", "min", "max", "avg", "sum", "coalesce")
#: Every op key the app understands (plus the ref/literal forms).
OPS = NARY_OPS + ("abs", "round", "clamp", "scale", "band", "since", "until")
#: since/until units, in seconds.
TIME_UNITS = {"seconds": 1, "minutes": 60, "hours": 3600, "days": 86_400, "weeks": 604_800}
#: Caps (LayoutSanitizer.maxDeriveNodes / maxDeriveDepth / maxDeriveArgs).
MAX_NODES = 256
MAX_DEPTH = 16
MAX_ARGS = 32


class Node:
    """One parsed derive node. ``kind`` is ``number``, ``control``, ``derive``,
    ``clock``, ``invalid`` or an op name; ``args`` holds the sub-nodes."""

    __slots__ = ("kind", "value", "args", "opts", "raw")

    def __init__(self, kind, value=None, args=(), opts=None, raw=None):
        self.kind = kind
        self.value = value          # number literal, or ref id
        self.args = list(args)      # sub-nodes (clamp: of, min?, max?)
        self.opts = opts or {}      # places / from / to / stops / labels / unit / has_min / has_max
        self.raw = raw              # the JSON it was parsed from

    def __repr__(self):
        return f"Node({self.kind!r}, {self.value!r}, {self.args!r})"

    # ── structure (DeriveNode.nodeCount / depth / maxArgs / refs) ──

    @property
    def is_leaf_arg(self) -> bool:
        return self.kind in ("number", "control", "derive")

    @property
    def node_count(self) -> int:
        if self.is_leaf_arg:
            return 0
        return 1 + sum(a.node_count for a in self.args)

    @property
    def depth(self) -> int:
        if self.is_leaf_arg:
            return 0
        return 1 + max((a.depth for a in self.args), default=0)

    @property
    def max_args(self) -> int:
        own = len(self.args)
        return max([own] + [a.max_args for a in self.args])

    @property
    def control_refs(self) -> set:
        if self.kind == "control":
            return {self.value}
        out: set = set()
        for a in self.args:
            out |= a.control_refs
        return out

    @property
    def derive_refs(self) -> set:
        if self.kind == "derive":
            return {self.value}
        out: set = set()
        for a in self.args:
            out |= a.derive_refs
        return out

    def invalid_nodes(self, path: str = "") -> list:
        """(path, raw) for every node in the tree this build cannot read."""
        if self.kind == "invalid":
            return [(path, self.raw)]
        out = []
        for i, a in enumerate(self.args):
            out += a.invalid_nodes(f"{path}/{i}")
        return out


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _finite_num(v) -> bool:
    return _is_num(v) and math.isfinite(v)


def _invalid(raw) -> Node:
    return Node("invalid", raw=raw)


# ── parsing (DeriveNode.init(json:)) ──

def parse(raw: Any) -> Node:
    """The lenient single-key parse: never raises; anything unreadable is invalid."""
    if _finite_num(raw):
        return Node("number", float(raw), raw=raw)
    if isinstance(raw, dict) and len(raw) == 1:
        (op, body), = raw.items()
        node = _parse_op(op, body)
        if node is not None:
            node.raw = raw
            return node
    return _invalid(raw)


def _pair(v) -> Optional[list]:
    if not isinstance(v, list) or len(v) != 2:
        return None
    if not all(_finite_num(x) for x in v):
        return None
    return [float(x) for x in v]


def _parse_op(op: str, body: Any) -> Optional[Node]:
    if op in NARY_OPS:
        if not isinstance(body, list) or not body:
            return None
        return Node(op, args=[parse(x) for x in body])
    if op in ("control", "derive"):
        if not isinstance(body, str) or not body:
            return None
        return Node(op, body)
    if op == "clock":
        return Node("clock") if body is True or isinstance(body, dict) else None
    if op == "abs":
        if isinstance(body, list):
            return Node("abs", args=[parse(body[0])]) if len(body) == 1 else None
        return Node("abs", args=[parse(body)])
    if op == "round":
        if not isinstance(body, dict) or "of" not in body:
            return Node("round", args=[parse(body)], opts={"places": 0})
        places = 0
        if "places" in body:
            p = body["places"]
            if not (_is_num(p) and math.isfinite(p) and p == round(p) and 0 <= p <= 12):
                return None
            places = int(p)
        return Node("round", args=[parse(body["of"])], opts={"places": places})
    if op == "clamp":
        if not isinstance(body, dict) or "of" not in body or ("min" not in body and "max" not in body):
            return None
        args = [parse(body["of"])]
        if "min" in body:
            args.append(parse(body["min"]))
        if "max" in body:
            args.append(parse(body["max"]))
        return Node("clamp", args=args, opts={"has_min": "min" in body, "has_max": "max" in body})
    if op == "scale":
        if not isinstance(body, dict) or "of" not in body:
            return None
        frm, to = _pair(body.get("from")), _pair(body.get("to"))
        if frm is None or to is None:
            return None
        return Node("scale", args=[parse(body["of"])], opts={"from": frm, "to": to})
    if op == "band":
        if not isinstance(body, dict) or "of" not in body:
            return None
        stops, labels = body.get("stops"), body.get("labels")
        if not isinstance(stops, list) or not isinstance(labels, list):
            return None
        if not stops or not all(_finite_num(s) for s in stops):
            return None
        if not all(isinstance(s, str) for s in labels) or len(labels) != len(stops) + 1:
            return None
        if any(a >= b for a, b in zip(stops, stops[1:])):
            return None
        return Node("band", args=[parse(body["of"])],
                    opts={"stops": [float(s) for s in stops], "labels": list(labels)})
    if op in ("since", "until"):
        of, unit = body, "seconds"
        if isinstance(body, dict) and "of" in body:
            of = body["of"]
            if "unit" in body:
                if body["unit"] not in TIME_UNITS:
                    return None
                unit = body["unit"]
        return Node(op, args=[parse(of)], opts={"unit": unit})
    return None


# ── value semantics (DeriveNode.number / DeriveNode.date) ──

# Swift's Double(String): the whole string, decimal or hexadecimal, no underscores,
# no surrounding whitespace. inf/nan parse but are dropped as non-finite anyway.
_DECIMAL = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?\Z")
_HEX = re.compile(r"[+-]?0[xX](?:[0-9a-fA-F]+\.?[0-9a-fA-F]*|\.[0-9a-fA-F]+)(?:[pP][+-]?\d+)?\Z")


def _swift_double(s: str) -> Optional[float]:
    if _DECIMAL.match(s):
        n = float(s)
    elif _HEX.match(s):
        body = s.lstrip("+-")
        sign = -1.0 if s.startswith("-") else 1.0
        if "p" not in body.lower():
            body += "p0"
        try:
            n = sign * float.fromhex(body)
        except (ValueError, OverflowError):
            return None
    else:
        return None
    return n


def to_number(value: Any) -> Optional[float]:
    """Numbers pass through, bools are 1/0, numeric strings parse (spaces and tabs
    trimmed); anything else, or a non-finite result, is None."""
    if isinstance(value, bool):
        n = 1.0 if value else 0.0
    elif _is_num(value):
        n = float(value)
    elif isinstance(value, str):
        n = _swift_double(value.strip(" \t"))
    else:
        n = None
    if n is None or not math.isfinite(n):
        return None
    return n


_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d+)?(Z|[+-]\d{2}:?\d{2})\Z")
_PLAIN = re.compile(r"(\d{4})-(\d{2})-(\d{2})\Z")


def _parse_date_string(s: str) -> Optional[float]:
    """GanttTime.parseDate: ISO-8601 with a zone (optional fraction), or a plain
    yyyy-MM-dd read as UTC midnight. Epoch seconds, or None."""
    m = _ISO.match(s)
    try:
        if m:
            y, mo, d, h, mi, sec, frac, zone = m.groups()
            dt = datetime(int(y), int(mo), int(d), int(h), int(mi), int(sec), tzinfo=timezone.utc)
            t = dt.timestamp() + (float(frac) if frac else 0.0)
            if zone != "Z":
                z = zone.replace(":", "")
                offset = (int(z[1:3]) * 60 + int(z[3:5])) * 60
                t -= offset if z[0] == "+" else -offset
            return t
        m = _PLAIN.match(s)
        if m:
            y, mo, d = (int(x) for x in m.groups())
            return datetime(y, mo, d, tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None
    return None


def _epoch(n: float) -> Optional[float]:
    if not math.isfinite(n):
        return None
    return n / 1000 if abs(n) > 1e11 else n


def to_date(value: Any) -> Optional[float]:
    """A date argument as epoch seconds: an ISO-8601 / yyyy-MM-dd string, or an epoch
    number (seconds; milliseconds when larger than 10^11). Bools are not dates."""
    if isinstance(value, str):
        t = _parse_date_string(value)
        if t is not None:
            return t
        n = _swift_double(value)
        return None if n is None else _epoch(n)
    if _is_num(value):
        return _epoch(float(value))
    return None


# ── evaluation (DeriveNode.evaluate) ──

def _finite(x: float) -> Optional[float]:
    return x if math.isfinite(x) else None


def _round_half_away(x: float) -> float:
    a = abs(x)
    f = math.floor(a)
    r = f + 1.0 if a - f >= 0.5 else f
    return math.copysign(r, x)


def evaluate_node(node: Node, control: Callable[[str], Any], derive: Callable[[str], Any],
                  now: float) -> Any:
    """The node's value (a float, a label string, or a raw input value through
    ``coalesce`` / a ref), or None. ``now`` is epoch seconds."""
    def ev(n):
        return evaluate_node(n, control, derive, now)

    def num(n):
        return to_number(ev(n))

    k = node.kind
    if k == "number":
        return node.value
    if k == "control":
        return control(node.value)
    if k == "derive":
        return derive(node.value)
    if k == "clock":
        return float(now)
    if k == "invalid":
        return None
    if k == "coalesce":
        for a in node.args:
            v = ev(a)
            if v is not None:
                return v
        return None
    if k in NARY_OPS:
        xs = []
        for a in node.args:
            x = num(a)
            if x is None:
                return None
            xs.append(x)
        first, rest = xs[0], xs[1:]
        try:
            if k in ("add", "sum"):
                acc = 0.0
                for x in xs:
                    acc += x
                return _finite(acc)
            if k == "sub":
                acc = first
                for x in rest:
                    acc -= x
                return _finite(acc)
            if k == "mul":
                acc = 1.0
                for x in xs:
                    acc *= x
                return _finite(acc)
            if k == "div":
                acc = first
                for d in rest:
                    if d == 0:
                        return None
                    acc /= d
                return _finite(acc)
            if k == "min":
                return min(xs)
            if k == "max":
                return max(xs)
            if k == "avg":
                acc = 0.0
                for x in xs:
                    acc += x
                return _finite(acc / len(xs))
        except OverflowError:
            return None
    if k == "abs":
        v = num(node.args[0])
        return None if v is None else abs(v)
    if k == "round":
        v = num(node.args[0])
        if v is None:
            return None
        scale = 10.0 ** node.opts["places"]
        return _finite(_round_half_away(v * scale) / scale)
    if k == "clamp":
        v = num(node.args[0])
        if v is None:
            return None
        i = 1
        if node.opts.get("has_min"):
            lo = num(node.args[i])
            i += 1
            if lo is None:
                return None
            v = max(v, lo)
        if node.opts.get("has_max"):
            hi = num(node.args[i])
            if hi is None:
                return None
            v = min(v, hi)
        return v
    if k == "scale":
        v = num(node.args[0])
        frm, to = node.opts["from"], node.opts["to"]
        if v is None or frm[1] == frm[0]:
            return None
        return _finite(to[0] + (v - frm[0]) / (frm[1] - frm[0]) * (to[1] - to[0]))
    if k == "band":
        v = num(node.args[0])
        if v is None:
            return None
        stops, labels = node.opts["stops"], node.opts["labels"]
        i = next((j for j, s in enumerate(stops) if v < s), len(stops))
        return labels[i]
    if k in ("since", "until"):
        d = to_date(ev(node.args[0]))
        if d is None:
            return None
        unit = TIME_UNITS[node.opts["unit"]]
        delta = (now - d) if k == "since" else (d - now)
        return _finite(delta / unit)
    return None


# ── the graph (DeriveGraph) ──

def _parsed(block) -> dict:
    """{id: Node} from a raw ``derive`` block (or an already-parsed one)."""
    if not isinstance(block, dict):
        return {}
    return {k: v if isinstance(v, Node) else parse(v) for k, v in block.items()}


def graph_order(block) -> list:
    """Evaluation order (Kahn's algorithm over derive → derive edges, ties broken by
    id). Nodes on a cycle, or reading a missing derive, are left out."""
    nodes = _parsed(block)
    pending = {k: set(n.derive_refs) for k, n in nodes.items()}
    order: list = []
    ready = sorted(k for k, refs in pending.items() if not refs)
    while ready:
        nid = ready.pop(0)
        order.append(nid)
        pending.pop(nid, None)
        nxt = []
        for other, refs in pending.items():
            if nid in refs:
                refs.discard(nid)
                if not refs:
                    nxt.append(other)
        ready = sorted(ready + nxt)
    return order


def evaluate(block, inputs: Optional[dict] = None, now: float = 0.0) -> dict:
    """Evaluate every derive entry from ``inputs`` (control id → displayed value).

    Returns {derive id: value or None} for each entry in evaluation order; entries
    the graph cannot order (cycles, missing derive refs) are absent."""
    nodes = _parsed(block)
    values = dict(inputs or {})
    out: dict = {}
    for nid in graph_order(nodes):
        out[nid] = evaluate_node(nodes[nid], values.get, out.get, now)
    return out


def _walk(children, out):
    """Every placed control (XRayModel.allControls): tab/group children, container
    panels, long-press groups and canvas items. Iterative, so hostile nesting cannot
    blow the stack."""
    stack = [children]
    while stack:
        level = stack.pop()
        if not isinstance(level, list):
            continue
        nested = []
        for ch in level:
            if not isinstance(ch, dict):
                continue
            if ch.get("type") == "group":
                nested.append(ch.get("children"))
                continue
            out.append(ch)
            panels = ch.get("panels")
            for p in panels if isinstance(panels, list) else []:
                if isinstance(p, dict):
                    nested.append(p.get("children"))
            lpg = ch.get("longPressGroup")
            if isinstance(lpg, dict):
                nested.append(lpg.get("children"))
            canvas = ch.get("canvasConfig")
            items = canvas.get("items") if isinstance(canvas, dict) else None
            for item in items if isinstance(items, list) else []:
                if isinstance(item, dict) and isinstance(item.get("control"), dict):
                    nested.append([item["control"]])
        stack.extend(reversed(nested))


def json_depth(value, limit: int = 1000) -> int:
    """Nesting depth of a JSON value (iterative), capped at ``limit``."""
    deepest, stack = 0, [(value, 1)]
    while stack:
        v, d = stack.pop()
        if isinstance(v, (dict, list)):
            deepest = max(deepest, d)
            if deepest >= limit:
                return limit
            stack.extend((x, d + 1) for x in (v.values() if isinstance(v, dict) else v))
    return deepest


def layout_controls(layout: dict) -> list:
    out: list = []
    for tab in (layout or {}).get("tabs") or []:
        if isinstance(tab, dict):
            _walk(tab.get("children"), out)
    return out


def consumers(layout: dict) -> dict:
    """{derive id: [control ids bound with {"method": "derive", "from": id}]}."""
    out: dict = {}
    for ch in layout_controls(layout):
        cid = ch.get("id")
        sync = ch.get("sync")
        if not isinstance(cid, str) or not isinstance(sync, list):
            continue
        for s in sync:
            if isinstance(s, dict) and s.get("method") == "derive":
                frm = s.get("from")
                if isinstance(frm, str) and frm and cid not in out.setdefault(frm, []):
                    out[frm].append(cid)
    return out


def problems(block, control_ids, consumers_map: Optional[dict] = None) -> list:
    """(id, reason) for everything the app's decoder refuses (DeriveGraph.problems):
    empty ids, id collisions with controls, caps, unknown refs and cycles (including
    through a binding). Unknown ops are NOT here: see :func:`invalid_paths`."""
    nodes = _parsed(block)
    control_ids = set(control_ids)
    consumers_map = consumers_map or {}
    out: list = []
    total = sum(max(1, n.node_count) for n in nodes.values())
    for nid in sorted(nodes):
        node = nodes[nid]
        if not nid:
            out.append((nid, "empty derive id"))
            continue
        if nid in control_ids:
            out.append((nid, f'derive id "{nid}" collides with a control id'))
        if node.depth > MAX_DEPTH:
            out.append((nid, f"nests {node.depth} deep (max {MAX_DEPTH})"))
        if node.max_args > MAX_ARGS:
            out.append((nid, f"an op has {node.max_args} arguments (max {MAX_ARGS})"))
        for ref in sorted(node.derive_refs):
            if ref not in nodes:
                out.append((nid, f'unknown ref {{"derive": "{ref}"}}'))
        for ref in sorted(node.control_refs):
            if ref not in control_ids:
                out.append((nid, f'unknown ref {{"control": "{ref}"}}'))
    if total > MAX_NODES:
        out.append(("", f"{total} derive nodes (max {MAX_NODES})"))
    bound: dict = {}
    for d, controls in consumers_map.items():
        for c in controls:
            bound.setdefault(c, set()).add(d)

    def edges(nid):
        node = nodes.get(nid)
        if node is None:
            return set()
        e = set(node.derive_refs)
        for c in node.control_refs:
            e |= bound.get(c, set())
        return {x for x in e if x in nodes}

    for nid in sorted(nodes):
        stack, seen = list(edges(nid)), set()
        while stack:
            nxt = stack.pop()
            if nxt == nid:
                out.append((nid, f'derive cycle through "{nid}"'))
                break
            if nxt in seen:
                continue
            seen.add(nxt)
            stack.extend(edges(nxt))
    return out


def invalid_paths(block) -> list:
    """(derive id, path inside the tree, raw JSON) for every node this build cannot
    read: an unknown op or a malformed shape. The app loads these and evaluates them
    to nil (fail closed); an author almost always meant something else."""
    out = []
    for nid, node in sorted(_parsed(block).items()):
        for path, raw in node.invalid_nodes():
            out.append((nid, path, raw))
    return out


# ── authoring: node builders (``Layout.derive`` / ``ops``) ──

class DeriveRef:
    """What ``Layout.derive(...)`` returns: use it as an argument of another node
    (``{"derive": id}``) or bind a control to it with ``sync=ref.sync``."""

    def __init__(self, derive_id: str):
        self.id = derive_id

    @property
    def node(self) -> dict:
        return {"derive": self.id}

    @property
    def sync(self) -> list:
        """A ready ``sync`` list: ``ui.gauge("w", sync=watts.sync)``."""
        return [{"method": "derive", "from": self.id}]

    def __repr__(self):
        return f"DeriveRef({self.id!r})"


def arg(value: Any) -> Any:
    """Normalize one argument to derive JSON: numbers stay, a control handle (or a
    bare string id) becomes ``{"control": id}``, a :class:`DeriveRef` becomes
    ``{"derive": id}``, and dicts (nested nodes) are normalized recursively."""
    if isinstance(value, bool):
        raise TypeError("derive arguments are numbers, refs or nodes, not bools")
    if _is_num(value):
        return value
    if isinstance(value, DeriveRef):
        return value.node
    if isinstance(value, str):
        return {"control": value}
    if isinstance(value, dict):
        return {k: _normalize_body(v) for k, v in value.items()}
    cid = getattr(value, "id", None)
    if isinstance(cid, str):
        return {"control": cid}
    raise TypeError(f"not a derive argument: {value!r}")


def _normalize_body(body: Any) -> Any:
    if isinstance(body, list):
        return [arg(x) for x in body]
    if isinstance(body, dict):
        return {k: (arg(v) if k in ("of", "min", "max") else v) for k, v in body.items()}
    if isinstance(body, (str, bool)) or body is None:
        return body          # a ref id ({"control": "v"}), {"clock": true}
    return arg(body)


class ops:
    """Node builders: ``ops.mul(volts, amps)``, ``ops.round(x, places=1)``,
    ``ops.band(t, stops=[20, 30], labels=["low", "ok", "high"])``. Arguments are
    numbers, control handles (or ids), :class:`DeriveRef` s, or nested nodes."""

    @staticmethod
    def _nary(op, args):
        if not args:
            raise ValueError(f"{op} needs at least one argument")
        return {op: [arg(a) for a in args]}

    add = staticmethod(lambda *a: ops._nary("add", a))
    sum = staticmethod(lambda *a: ops._nary("sum", a))
    sub = staticmethod(lambda *a: ops._nary("sub", a))
    mul = staticmethod(lambda *a: ops._nary("mul", a))
    div = staticmethod(lambda *a: ops._nary("div", a))
    min = staticmethod(lambda *a: ops._nary("min", a))
    max = staticmethod(lambda *a: ops._nary("max", a))
    avg = staticmethod(lambda *a: ops._nary("avg", a))
    coalesce = staticmethod(lambda *a: ops._nary("coalesce", a))

    @staticmethod
    def control(control_id: str) -> dict:
        return {"control": control_id}

    @staticmethod
    def clock() -> dict:
        return {"clock": True}

    @staticmethod
    def abs(x) -> dict:
        return {"abs": arg(x)}

    @staticmethod
    def round(x, places: int = 0) -> dict:
        return {"round": {"of": arg(x), "places": int(places)}}

    @staticmethod
    def clamp(x, min=None, max=None) -> dict:
        if min is None and max is None:
            raise ValueError("clamp needs min, max or both")
        body = {"of": arg(x)}
        if min is not None:
            body["min"] = arg(min)
        if max is not None:
            body["max"] = arg(max)
        return {"clamp": body}

    @staticmethod
    def scale(x, from_, to) -> dict:
        return {"scale": {"of": arg(x), "from": list(from_), "to": list(to)}}

    @staticmethod
    def band(x, stops, labels) -> dict:
        if len(labels) != len(stops) + 1:
            raise ValueError("band needs one more label than stops")
        return {"band": {"of": arg(x), "stops": list(stops), "labels": list(labels)}}

    @staticmethod
    def since(x, unit: str = "seconds") -> dict:
        if unit not in TIME_UNITS:
            raise ValueError(f"unit must be one of {', '.join(TIME_UNITS)}")
        return {"since": {"of": arg(x), "unit": unit}}

    @staticmethod
    def until(x, unit: str = "seconds") -> dict:
        if unit not in TIME_UNITS:
            raise ValueError(f"unit must be one of {', '.join(TIME_UNITS)}")
        return {"until": {"of": arg(x), "unit": unit}}
