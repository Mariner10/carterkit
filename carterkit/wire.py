"""Reference evaluator for the app's sync matching — `filter` + `valuePath`.

The app decides whether a frame reaches a control in three steps, and each one
fails silently on the device:

1. **filter** (`jsonMatches`): frame and filter must both be JSON objects; every
   top-level filter key must be present in the frame with an *equal* value
   (whole-value equality, so a nested filter value must match exactly).
2. **valuePath** (`extractValue` / `extractJSON` / `extractArray`): split on `.`
   with empty segments dropped (`a..b` == `a.b`, `.a` == `a`). An object looks a
   segment up as a key (even `"0"`); an array needs a segment Swift's `Int(_:)`
   parses (ASCII digits, optional `+`/`-` sign, no whitespace or `_`) that is
   `>= 0` and in range. A scalar mid-walk fails. No path = the whole frame.
3. **type** (`controlValue`): a scalar control renders only bool / number / string.

This module mirrors those rules exactly and reports *where* a frame fails, so the
MCP lint and the app agree. JSON equality is typed like the app's `JSONValue`:
numbers are doubles (`1 == 1.0`) but a bool is never a number (`True != 1`, the
Python trap). Pure functions, no I/O. Golden fixtures shared with the app live in
`tests/fixtures/wire/` (see the README there).
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from typing import Any, Optional

__all__ = [
    "ABSENT", "PathMiss", "FilterMiss", "TypeMiss", "Walk", "Outcome",
    "json_equal", "walk", "match", "scalar", "log_source", "evaluate",
    "levenshtein", "near_miss_msg_type", "frame_for", "path_segments",
    "DELIVERED", "FILTER_MISS", "PATH_MISS", "TYPE_MISS",
]

DELIVERED = "delivered"
FILTER_MISS = "filter_miss"
PATH_MISS = "path_miss"
TYPE_MISS = "type_miss"

_INT_RE = re.compile(r"\A[+-]?[0-9]+\Z", re.ASCII)
_INT_MIN, _INT_MAX = -(2 ** 63), 2 ** 63 - 1


class _Absent:
    """Sentinel for a filter key the frame doesn't carry (distinct from JSON null)."""

    _inst = None

    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
        return cls._inst

    def __repr__(self) -> str:
        return "<absent>"

    def __bool__(self) -> bool:
        return False

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self


ABSENT = _Absent()


@dataclass(frozen=True)
class PathMiss:
    """The walk stopped at `segment` (0-based position `index` among the
    non-empty segments). `reason`: missing_key | bad_index | out_of_range |
    not_container."""
    segment: str
    index: int
    reason: str


@dataclass(frozen=True)
class FilterMiss:
    """Filter key `key` expected `expected`, frame had `actual` (`ABSENT` when the
    key is missing). `near` = the frame was probably meant for this control."""
    key: str
    expected: Any
    actual: Any
    near: bool


@dataclass(frozen=True)
class TypeMiss:
    """The resolved value can't render in a scalar control. `kind`: null | object
    | array | other."""
    kind: str


@dataclass(frozen=True)
class Walk:
    ok: bool
    value: Any = None
    miss: Optional[PathMiss] = None


@dataclass(frozen=True)
class Outcome:
    """`kind` is one of DELIVERED / FILTER_MISS / PATH_MISS / TYPE_MISS."""
    kind: str
    value: Any = None
    filter_misses: tuple = field(default_factory=tuple)
    path_miss: Optional[PathMiss] = None
    type_miss: Optional[TypeMiss] = None

    @property
    def delivered(self) -> bool:
        return self.kind == DELIVERED

    @property
    def near(self) -> bool:
        """A filter miss worth reporting: some key nearly matched, and the frame's
        msg_type (if the filter names one) isn't an unrelated message."""
        if self.kind != FILTER_MISS or not self.filter_misses:
            return False
        if any(m.key == "msg_type" and not m.near for m in self.filter_misses):
            return False
        return any(m.near for m in self.filter_misses)


# ---------------------------------------------------------------------------
# JSON equality (the app's `JSONValue ==`)


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def json_equal(a: Any, b: Any) -> bool:
    """Typed JSON equality as the app sees it: numbers compare as doubles
    (`1 == 1.0`), a bool only equals a bool (`True != 1`), objects compare by key
    set and values, arrays element-wise in order."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a is b
    if _is_number(a) or _is_number(b):
        if not (_is_number(a) and _is_number(b)):
            return False
        try:
            return float(a) == float(b)
        except OverflowError:  # an int past double range; Swift would not decode it
            return a == b
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, str) or isinstance(b, str):
        return isinstance(a, str) and isinstance(b, str) and a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(json_equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(json_equal(x, y) for x, y in zip(a, b))
    return False


# ---------------------------------------------------------------------------
# valuePath walking


def path_segments(path: Optional[str]) -> list:
    """`path.split(separator: ".")` in Swift: empty segments are dropped."""
    if not path:
        return []
    return [s for s in str(path).split(".") if s]


def _swift_int(seg: str) -> Optional[int]:
    """Swift's `Int(String)`: ASCII digits with an optional sign, in Int64 range."""
    if not _INT_RE.match(seg):
        return None
    n = int(seg)
    return n if _INT_MIN <= n <= _INT_MAX else None


def walk(frame: Any, path: Optional[str]) -> Walk:
    """Resolve `path` in `frame`. Nil/empty path (or one with only dots) is the
    whole frame. On failure, `miss` names the segment the walk stopped at."""
    current = frame
    for i, seg in enumerate(path_segments(path)):
        if isinstance(current, dict):
            if seg not in current:
                return Walk(False, miss=PathMiss(seg, i, "missing_key"))
            current = current[seg]
        elif isinstance(current, (list, tuple)):
            n = _swift_int(seg)
            if n is None or n < 0:
                return Walk(False, miss=PathMiss(seg, i, "bad_index"))
            if n >= len(current):
                return Walk(False, miss=PathMiss(seg, i, "out_of_range"))
            current = current[n]
        else:
            return Walk(False, miss=PathMiss(seg, i, "not_container"))
    return Walk(True, value=current)


# ---------------------------------------------------------------------------
# filter matching


def levenshtein(a: str, b: str) -> int:
    """Edit distance (insert / delete / substitute, each cost 1)."""
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def near_miss_msg_type(a: Any, b: Any) -> bool:
    """Two different msg_type strings within edit distance 2 (a likely typo,
    e.g. `telemetery` vs `telemetry`)."""
    if not (isinstance(a, str) and isinstance(b, str)) or a == b:
        return False
    return levenshtein(a, b) <= 2


def _miss(key: str, expected: Any, actual: Any) -> FilterMiss:
    if actual is ABSENT:
        near = False
    elif key == "msg_type":
        near = near_miss_msg_type(actual, expected)
    else:
        near = True  # the key is there, just with another value
    return FilterMiss(key, expected, actual, near)


def match(frame: Any, filter: Any) -> tuple:
    """The filter keys that fail, sorted by key; `()` means the frame matches.
    `filter=None` (no filter) always matches. A non-object frame misses every
    key; a non-object filter can never match (key `""`)."""
    if filter is None:
        return ()
    if not isinstance(filter, dict):
        return (FilterMiss("", filter, ABSENT, False),)
    if not isinstance(frame, dict):
        if not filter:
            return (FilterMiss("", filter, ABSENT, False),)
        return tuple(FilterMiss(k, filter[k], ABSENT, False) for k in sorted(filter))
    misses = []
    for key in sorted(filter):
        expected = filter[key]
        actual = frame.get(key, ABSENT)
        if actual is ABSENT or not json_equal(actual, expected):
            misses.append(_miss(key, expected, actual))
    return tuple(misses)


# ---------------------------------------------------------------------------
# value typing


def _kind(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, (list, tuple)):
        return "array"
    return "other"


def scalar(value: Any):
    """The app's `controlValue`: bool / number / string pass through unchanged;
    anything else is a `TypeMiss`."""
    if isinstance(value, (bool, str)) or _is_number(value):
        return value
    return TypeMiss(_kind(value))


def log_source(frame: Any, path: Optional[str]) -> Any:
    """The app's `logEntrySource`: the object/array at `path`, else the whole
    frame (a failed walk or a scalar both fall back)."""
    if not path:
        return frame
    w = walk(frame, path)
    if w.ok and isinstance(w.value, (dict, list, tuple)):
        return w.value
    return frame


# ---------------------------------------------------------------------------
# the whole pipeline


def evaluate(frame: Any, sync: dict, *, require_scalar: bool = True) -> Outcome:
    """What happens to `frame` at a control bound by `sync` (a layout sync dict
    with optional `filter` / `valuePath`). Order matches the app: filter, then
    path, then (for scalar controls) value type. Pass `require_scalar=False` for
    controls that take objects/arrays (charts, tables, logs)."""
    sync = sync or {}
    misses = match(frame, sync.get("filter"))
    if misses:
        return Outcome(FILTER_MISS, filter_misses=misses)
    w = walk(frame, sync.get("valuePath"))
    if not w.ok:
        return Outcome(PATH_MISS, path_miss=w.miss)
    if require_scalar:
        v = scalar(w.value)
        if isinstance(v, TypeMiss):
            return Outcome(TYPE_MISS, value=w.value, type_miss=v)
    return Outcome(DELIVERED, value=w.value)


def frame_for(sync: dict, value: Any) -> dict:
    """The smallest frame `sync` delivers `value` from: the filter's keys plus
    `value` nested at `valuePath` (like `Hub.frame_for`). With no valuePath the
    value must be a dict and is merged in. Raises ValueError otherwise."""
    sync = sync or {}
    filt = sync.get("filter")
    frame: dict = copy.deepcopy(filt) if isinstance(filt, dict) else {}
    segs = path_segments(sync.get("valuePath"))
    if not segs:
        if not isinstance(value, dict):
            raise ValueError("sync has no valuePath (it takes the whole frame); pass a dict")
        frame.update(copy.deepcopy(value))
        return frame
    cur = frame
    for seg in segs[:-1]:
        nxt = cur.get(seg)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[seg] = nxt
        cur = nxt
    cur[segs[-1]] = value
    return frame
