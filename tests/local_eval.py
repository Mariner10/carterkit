"""A tiny pure-Python evaluator for local-store query stages — the "third engine".

The app compiles a stage to SQLite (`LocalQueryCompiler`) and the hub will have a Go
copy; this one runs the same §4 semantics over in-memory records so the shared
conformance fixtures (`CAR-TERTests/Fixtures/local-query/*.json`) can be checked here
too. It is a TEST HELPER, not part of the package: carterkit lints stages, it never
runs them. Deliberately small; anything it cannot express raises.
"""
from __future__ import annotations

import datetime as dt
import math
from zoneinfo import ZoneInfo

from carterkit import local as L


class InvalidStage(Exception):
    pass


class UnknownCollection(Exception):
    pass


# ── dates (§2.3) ────────────────────────────────────────────────────────────────

def parse_instant(s: str) -> dt.datetime | None:
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is None:
        return None
    return d.astimezone(dt.timezone.utc)


def instant_string(d: dt.datetime) -> str:
    d = d.astimezone(dt.timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%S.") + f"{d.microsecond // 1000:03d}Z"


def normalize_date(s):
    """Calendar date stays; any instant becomes UTC with milliseconds; else None."""
    if not isinstance(s, str):
        return None
    if len(s) == 10:
        try:
            dt.date.fromisoformat(s)
            return s
        except ValueError:
            return None
    d = parse_instant(s)
    return instant_string(d) if d else None


def calendar_date(d: dt.datetime, tz) -> str:
    return d.astimezone(tz).strftime("%Y-%m-%d")


# ── store ───────────────────────────────────────────────────────────────────────

class Store:
    """Records of one fixture: `schema` is the normalized `lint_source` output."""

    def __init__(self, fixture: dict):
        problems, self.schema = L.lint_source(fixture["schema"])
        errors = [m for sev, m in problems if sev == "error"]
        if errors:
            raise InvalidStage("; ".join(errors))
        self.tz = ZoneInfo(fixture["timeZone"])
        self.now = parse_instant(fixture["now"])
        self.week_starts_on = fixture.get("weekStartsOn", "monday")
        self.selected = fixture.get("selected") or {}
        self.rows: dict[str, list[dict]] = {}
        for cname, recs in (fixture.get("records") or {}).items():
            fields = L.fields_for(self.schema, cname)
            out = []
            for i, rec in enumerate(recs):
                stamp = instant_string(dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc)
                                       + dt.timedelta(seconds=i))
                row = {"id": rec["id"], "createdAt": stamp, "updatedAt": stamp}
                for f, t in fields.items():
                    if f in L.RESERVED_FIELDS:
                        continue
                    v = rec["fields"].get(f)
                    row[f] = normalize_date(v) if (t == "date" and v is not None) else v
                out.append(row)
            self.rows[cname] = out

    # tokens (§4.5)
    def token(self, name, base):
        cal = self.now.astimezone(self.tz)
        if name == "now":
            return instant_string(self.now)
        if name == "today":
            return cal.strftime("%Y-%m-%d")
        if name == "startOfWeek":
            first = 0 if self.week_starts_on == "monday" else 6          # Monday=0 … Sunday=6
            back = (cal.weekday() - first) % 7
            return (cal.date() - dt.timedelta(days=back)).isoformat()
        if name == "startOfMonth":
            return cal.strftime("%Y-%m-01")
        if name == "startOfYear":
            return cal.strftime("%Y-01-01")
        if name == "selected":
            return self.selected.get(base)
        return None

    def resolve(self, name):
        """(base collection, [views outermost→innermost]) or UnknownCollection."""
        views = []
        cur = name
        while cur in self.schema["views"]:
            views.append(self.schema["views"][cur])
            cur = views[-1]["from"]
        if cur not in self.schema["collections"]:
            raise UnknownCollection(name)
        return cur, views

    def query(self, name: str, stage: dict) -> dict:
        base, views = self.resolve(name)
        fields = L.fields_for(self.schema, base)
        problems = L.lint_stage(stage, fields)
        errors = [m for sev, m in problems if sev == "error"]
        if errors:
            raise InvalidStage("; ".join(errors))
        rows = list(self.rows.get(base, []))
        for view in reversed(views):                       # innermost first (§4.6)
            rows = self._rows(rows, view, fields, base)
        if "groupBy" in stage:
            return {"shape": "groups", "groups": self._groups(rows, stage, fields, base)}
        if "aggregate" in stage:
            return {"shape": "scalar", "value": self._scalar(rows, stage, fields, base)}
        out = self._rows(rows, stage, fields, base, default_limit=L.MAX_LIMIT)
        return {"shape": "rows", "ids": [r["id"] for r in out], "rows": out,
                "total": len(self.rows.get(base, []))}

    # ── where (§4.1) ────────────────────────────────────────────────────────────
    def _bind(self, value, ftype, base):
        """(ok, bound): a token is substituted; a literal is type-checked (mismatch →
        not ok, the leaf is FALSE — `LocalQueryCompiler.bind`)."""
        tok = L.token_name(value)
        if tok is not None:
            value = self.token(tok, base)
            if value is None:
                return False, None
        if value is None:
            return True, None
        if ftype in ("string", "date"):
            if not isinstance(value, str):
                return False, None
            return True, (normalize_date(value) or value) if ftype == "date" else value
        if ftype in ("number", "integer"):
            return (isinstance(value, (int, float)) and not isinstance(value, bool)), value
        if ftype == "bool":
            return isinstance(value, bool), value
        return False, None

    def _match(self, node, row, fields, base) -> bool:
        for key, value in node.items():
            if key == "and":
                if not all(self._match(sub, row, fields, base) for sub in value):
                    return False
                continue
            if key == "or":
                if not any(self._match(sub, row, fields, base) for sub in value):
                    return False
                continue
            ops = value if isinstance(value, dict) else {"eq": value}
            for op, v in ops.items():
                if not self._leaf(row.get(key), fields[key], op, v, base):
                    return False
        return True

    def _leaf(self, have, ftype, op, v, base) -> bool:
        if op == "exists":
            return (have is not None) == v
        if op == "contains":
            ok, bound = self._bind(v, "string", base)
            return ok and have is not None and bound in have
        if op == "in":
            members = []
            for m in v:
                ok, bound = self._bind(m, ftype, base)
                if not ok or bound is None:
                    return False
                members.append(bound)
            return have is not None and have in members
        ok, bound = self._bind(v, ftype, base)
        if not ok:
            return False
        if op == "ne":
            return have is None or have != bound        # `IS NOT`: a null row counts
        if bound is None or have is None:
            return False                                 # null never matches
        if ftype == "bool" and op != "eq":
            raise InvalidStage("bool supports eq/ne only")
        return {"eq": have == bound, "gt": have > bound, "gte": have >= bound,
                "lt": have < bound, "lte": have <= bound}[op]

    # ── rows: where → order → limit (§4.4) ──────────────────────────────────────
    def _rows(self, rows, stage, fields, base, default_limit=None):
        if "where" in stage:
            rows = [r for r in rows if self._match(stage["where"], r, fields, base)]
        keys = _order_keys(stage.get("orderBy"))
        rows = _sort(rows, keys)
        limit = stage.get("limit", default_limit)
        return rows[:limit] if limit is not None else rows

    # ── scalar (§4.2) ───────────────────────────────────────────────────────────
    def _scalar(self, rows, stage, fields, base):
        rows = self._rows(rows, {"where": stage["where"]} if "where" in stage else {}, fields, base)
        op, field = _agg(stage["aggregate"])
        if op in ("first", "last"):
            keys = _order_keys(stage.get("orderBy")) or [("createdAt", False)]
            if op == "last":
                keys = [(f, not d) for f, d in keys]
            ordered = _sort(rows, keys, id_desc=(op == "last" and "id" not in [f for f, _ in keys]))
            return ordered[0][field] if ordered else None
        return _aggregate(rows, op, field)

    # ── groups (§4.3) ───────────────────────────────────────────────────────────
    def _groups(self, rows, stage, fields, base):
        rows = self._rows(rows, {"where": stage["where"]} if "where" in stage else {}, fields, base)
        g = stage["groupBy"]
        field = g if isinstance(g, str) else g["field"]
        buckets: dict = {}
        for r in rows:
            k = self._group_key(r.get(field), g, fields[field])
            buckets.setdefault(k, []).append(r)
        op, afield = _agg(stage.get("aggregate", "count"))
        groups = [{"key": k, "value": _aggregate(rs, op, afield)} for k, rs in buckets.items()]
        keys = _order_keys(stage.get("orderBy")) or [("key", False)]
        groups = _sort(groups, keys, tiebreak=None)
        return groups[:min(stage.get("limit", L.MAX_GROUPS), L.MAX_GROUPS)]

    def _group_key(self, v, g, ftype):
        if v is None or isinstance(g, str):
            return v
        if "width" in g:
            w = float(g["width"])
            return math.trunc(v / w) * w
        unit = g["bucket"]
        if len(v) == 10:
            d = dt.date.fromisoformat(v)
        else:
            d = parse_instant(v).astimezone(self.tz).date()
        if unit == "day":
            return d.isoformat()
        if unit == "month":
            return d.strftime("%Y-%m")
        if unit == "year":
            return d.strftime("%Y")
        first = 0 if self.week_starts_on == "monday" else 6
        return (d - dt.timedelta(days=(d.weekday() - first) % 7)).isoformat()


# ── helpers ─────────────────────────────────────────────────────────────────────

def _order_keys(o):
    if o is None:
        return []
    names = [o] if isinstance(o, str) else list(o)
    return [(n[1:], True) if n.startswith("-") else (n, False) for n in names]


def _sort(items, keys, tiebreak="id", id_desc=False):
    """Stable multi-key sort, NULL last on every key, `id` as the final tiebreak."""
    out = list(items)
    if tiebreak and tiebreak not in [f for f, _ in keys]:
        out.sort(key=lambda r: r[tiebreak], reverse=id_desc)
    for field, desc in reversed(keys):
        present = [r for r in out if r.get(field) is not None]
        present.sort(key=lambda r: r[field], reverse=desc)
        out = present + [r for r in out if r.get(field) is None]
    return out


def _agg(a):
    if isinstance(a, str):
        return a, None
    return a["op"], a.get("field")


def _aggregate(rows, op, field):
    if op == "count":
        return len(rows)
    vals = [r[field] for r in rows if r.get(field) is not None]
    if op == "sum":
        return float(sum(vals))
    if op == "avg":
        return (sum(vals) / len(vals)) if vals else None
    if op == "min":
        return min(vals) if vals else None
    if op == "max":
        return max(vals) if vals else None
    if op == "distinct":
        return len({repr(v) for v in vals})
    raise InvalidStage(f"{op} is not a group aggregate")


# ── comparison (§10.3) ──────────────────────────────────────────────────────────

def same_value(have, want) -> bool:
    if have is None or want is None:
        return have is None and want is None
    if isinstance(have, (int, float)) and isinstance(want, (int, float)) \
            and not isinstance(have, bool) and not isinstance(want, bool):
        return math.isclose(have, want, rel_tol=0, abs_tol=1e-9)
    return have == want


def compare(result: dict, expected: dict) -> list[str]:
    """Differences between an evaluator result and a fixture `expected`; [] = match."""
    diffs = []
    shape = expected.get("shape")
    if result["shape"] != shape:
        return [f"shape {result['shape']} != {shape}"]
    if shape == "scalar":
        if not same_value(result["value"], expected["value"]):
            diffs.append(f"value {result['value']!r} != {expected['value']!r}")
    elif shape == "groups":
        want = expected["groups"]
        if len(result["groups"]) != len(want):
            return [f"{len(result['groups'])} groups != {len(want)}: {result['groups']}"]
        for h, w in zip(result["groups"], want):
            if not same_value(h["key"], w["key"]) or not same_value(h["value"], w["value"]):
                diffs.append(f"group {h} != {w}")
    else:
        if result["ids"] != expected["ids"]:
            diffs.append(f"ids {result['ids']} != {expected['ids']}")
        if "total" in expected and result["total"] != expected["total"]:
            diffs.append(f"total {result['total']} != {expected['total']}")
        for h, w in zip(result["rows"], expected.get("rows") or []):
            for k, v in w.items():
                if not same_value(h.get(k), v):
                    diffs.append(f"row {h['id']}.{k} {h.get(k)!r} != {v!r}")
    return diffs
