"""Pure lint for the on-device local store (see controldocs/local-store.md).

A `sources.<name>.type == "local"` block declares typed collections and views; controls
read them with `sync[].method == "local"` (a query *stage*: where / groupBy / aggregate /
orderBy / limit) and write them with `action.method == "local"` (an *op*: insert / update /
upsert / delete / select, plus set / increment / decrement / toggle on a `singleton: true`
collection's one row). Everything here mirrors what the app's `LocalSchema` and
`LocalQueryCompiler` accept — the phone rejects the same shapes, this just says so before
the push. No SQL, no code: every rule is over JSON.

Every function returns a list of ``(severity, message)`` tuples; callers wrap them into
findings. Nothing here touches the catalog or the network.
"""
from __future__ import annotations

import re
from .local_compute import lint_computed

# ── caps (spec §1 settled decisions; LocalQueryLimits / LocalSourceSchema in Swift) ──
MAX_COLLECTIONS = 32
MAX_FIELDS = 64
MAX_LIMIT = 1000
MAX_GROUPS = 500
MAX_WHERE_DEPTH = 8
MAX_WHERE_LEAVES = 32
MAX_IN_MEMBERS = 64
MAX_VIEW_DEPTH = 8

FIELD_TYPES = ("string", "number", "integer", "bool", "date", "json")
RESERVED_FIELDS = {"id": "string", "createdAt": "date", "updatedAt": "date"}
RESERVED_NAMES = set(RESERVED_FIELDS) | {"_hlc"}
SHARED_NAMESPACE = "shared"
WEEK_STARTS = ("monday", "sunday")

WHERE_OPS = ("eq", "ne", "gt", "gte", "lt", "lte", "in", "contains", "exists")
AGGREGATE_OPS = ("count", "sum", "avg", "min", "max", "distinct", "first", "last")
BUCKET_UNITS = ("day", "week", "month", "year")
ACTION_OPS = ("insert", "update", "upsert", "delete", "select", "set", "increment", "decrement", "toggle")
SINGLETON_OPS = ("set", "increment", "decrement", "toggle")
SINGLETON_ROW_ID = "singleton"
TOKENS = ("now", "today", "startOfWeek", "startOfMonth", "startOfYear", "selected")
#: Tokens the app substitutes into a local action's `set` / `id` beside the store tokens.
ACTION_TOKENS = ("value", "item", "from", "to", "index", "x", "y", "bearing", "label", "id")

NAMESPACE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")
COLLECTION_RE = re.compile(r"^[a-z][A-Za-z0-9_]{0,47}$")
FIELD_RE = re.compile(r"^[a-z][A-Za-z0-9_]{0,63}$")
ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
_TOKEN_RE = re.compile(r"^\{\{(.+)\}\}$")

__all__ = ["lint_source", "lint_stage", "lint_op", "fields_for", "token_name",
           "FIELD_TYPES", "WHERE_OPS", "AGGREGATE_OPS", "BUCKET_UNITS", "ACTION_OPS",
           "TOKENS", "RESERVED_FIELDS", "MAX_LIMIT", "MAX_GROUPS"]


def token_name(value) -> str | None:
    """`"{{today}}"` → `"today"`; anything that is not exactly one token → None."""
    if not isinstance(value, str):
        return None
    m = _TOKEN_RE.match(value)
    return m.group(1) if m else None


def fields_for(schema: dict, name: str) -> dict | None:
    """{field: type} for a collection or a view (resolved to its base collection),
    reserved fields included; None when `name` is neither."""
    if not isinstance(schema, dict):
        return None
    seen = set()
    while name in (schema.get("views") or {}) and name not in seen:
        seen.add(name)
        name = (schema["views"][name] or {}).get("from")
    coll = (schema.get("collections") or {}).get(name)
    if coll is None:
        return None
    return {**RESERVED_FIELDS, **coll}


# ── source block ─────────────────────────────────────────────────────────────────

def lint_source(sdef: dict) -> tuple[list[tuple[str, str]], dict]:
    """Check one `sources.<name>` block of type local. Returns (problems, schema) where
    schema is ``{"namespace", "collections": {name: {field: type}}, "views": {...},
    "singletons": [name, ...]}`` — the normalized shape the binding lint consumes
    (collections keep only their fields)."""
    out: list[tuple[str, str]] = []
    schema: dict = {"namespace": None, "collections": {}, "views": {}, "singletons": []}
    _lint_source_header(sdef, out, schema)
    _lint_collections(sdef.get("collections"), out, schema)
    _lint_views(sdef.get("views"), out, schema)
    return out, schema


def _lint_source_header(sdef, out, schema):
    ns = sdef.get("namespace")
    if ns is not None:
        if not isinstance(ns, str) or not NAMESPACE_RE.match(ns):
            out.append(("error", "namespace must match ^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$"))
        elif ns == SHARED_NAMESPACE:
            out.append(("error", "namespace 'shared' is reserved"))
        else:
            schema["namespace"] = ns
    wk = sdef.get("weekStartsOn")
    if wk is not None and wk not in WEEK_STARTS:
        out.append(("error", f"weekStartsOn must be one of {list(WEEK_STARTS)}, got {wk!r}"))
    for key in ("url", "baseURL", "topic", "username", "password", "headers"):
        if key in sdef:
            out.append(("warn", f"'{key}' means nothing on a local source (no network, no credentials)"))


def _lint_collections(colls, out, schema):
    if not isinstance(colls, dict) or not colls:
        out.append(("error", "local source needs a non-empty 'collections' object"))
        return
    if len(colls) > MAX_COLLECTIONS:
        out.append(("error", f"at most {MAX_COLLECTIONS} collections per source ({len(colls)} declared)"))
    for cname, cdef in colls.items():
        if not COLLECTION_RE.match(str(cname)):
            out.append(("error", f"collection name {cname!r} must match ^[a-z][A-Za-z0-9_]{{0,47}}$"))
            continue
        if not isinstance(cdef, dict):
            out.append(("error", f"collection {cname}: must be an object with 'fields'"))
            continue
        fields = cdef.get("fields")
        if not isinstance(fields, dict) or not fields:
            out.append(("error", f"collection {cname}: 'fields' (name → type) is required"))
            continue
        if len(fields) > MAX_FIELDS:
            out.append(("error", f"collection {cname}: at most {MAX_FIELDS} fields ({len(fields)} declared)"))
        for flag in ("shared", "mirror", "singleton"):
            if flag in cdef and not isinstance(cdef[flag], bool):
                out.append(("error", f"collection {cname}: '{flag}' must be true or false"))
        for key in cdef:
            if key not in ("fields", "shared", "mirror", "singleton", "defaults", "order"):
                out.append(("warn", f"collection {cname}: unknown key '{key}' is ignored"))
        clean: dict = {}
        for fname, ftype in fields.items():
            if fname in RESERVED_NAMES:
                out.append(("error", f"collection {cname}: field '{fname}' is reserved (store-managed)"))
                continue
            if not FIELD_RE.match(str(fname)):
                out.append(("error", f"collection {cname}: field name {fname!r} must match ^[a-z][A-Za-z0-9_]{{0,63}}$"))
                continue
            if isinstance(ftype, dict):
                # Object form: {"type": ..., options} (carter-73q2.28, local-store.md Field options).
                opts = dict(ftype)
                ftype = opts.pop("type", None)
                if ftype not in FIELD_TYPES:
                    out.append(("error", f"collection {cname}.{fname}: unknown type {ftype!r}; use one of {list(FIELD_TYPES)}"))
                    continue
                _lint_field_options(cname, fname, ftype, opts, out)
            elif ftype not in FIELD_TYPES:
                out.append(("error", f"collection {cname}.{fname}: unknown type {ftype!r}; use one of {list(FIELD_TYPES)}"))
                continue
            clean[fname] = ftype
        problems, computed = lint_computed(cname, fields, clean)
        out.extend(problems)
        if computed:
            schema.setdefault("computed", {})[cname] = sorted(computed)
        defaults = cdef.get("defaults")
        if isinstance(defaults, dict):
            for field in computed & defaults.keys():
                out.append(("error", f"collection {cname}: field {field} is computed, so it can't have a default"))
        schema["collections"][cname] = clean
        if cdef.get("singleton") is True:
            schema["singletons"].append(cname)
        _lint_defaults(cname, cdef, clean, out)
        _lint_order(cname, cdef, fields, out)


#: Field options beside the type (object-form field declarations, local-store.md).
FIELD_OPTION_KEYS = ("label", "unit", "required", "default", "choices", "multiple", "range",
                     "decimals", "labels", "symbol", "display", "compute")
#: display value -> the stored types it fits (mirrors the app's LocalFieldDisplay).
FIELD_DISPLAYS = {
    "number": ("number", "integer"), "duration": ("number", "integer"),
    "text": ("string",), "longText": ("string",), "photo": ("string",),
    "toggle": ("bool",), "date": ("date",), "time": ("date",), "dateTime": ("date",),
    "choice": ("string", "json"), "rating": ("integer",), "location": ("json",),
}
MAX_CHOICES = 100


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _lint_field_options(cname, fname, ftype, opts, out):
    """Validate one object-form field's options the way the app's LocalSourceSchema does;
    every problem is an error naming the collection, the field and the option."""
    where = f"collection {cname}.{fname}"

    def err(msg):
        out.append(("error", f"{where}: {msg}"))

    for key in opts:
        if key not in FIELD_OPTION_KEYS:
            err(f"unknown option {key!r}")
    for key, limit in (("label", 64), ("unit", 16), ("symbol", 64), ("display", 32)):
        v = opts.get(key)
        if v is not None and (not isinstance(v, str) or not v.strip() or len(v) > limit):
            err(f"{key} must be text of 1-{limit} characters")
    for key in ("required", "multiple"):
        if opts.get(key) is not None and not isinstance(opts[key], bool):
            err(f"{key} must be true or false")
    display = opts.get("display")
    if isinstance(display, str):
        if display not in FIELD_DISPLAYS:
            err(f"unknown display {display!r}; use one of {sorted(FIELD_DISPLAYS)}")
        elif ftype not in FIELD_DISPLAYS[display]:
            err(f"display {display!r} does not fit type {ftype}")
    numeric = ftype in _NUMERIC
    if opts.get("unit") is not None and not numeric:
        err("unit needs a number field")
    dec = opts.get("decimals")
    if dec is not None:
        if not _is_num(dec) or float(dec) != int(dec) or not 0 <= dec <= 6:
            err("decimals must be 0-6")
        elif not numeric:
            err("decimals needs a number field")
    rng = opts.get("range")
    if rng is not None:
        if not (isinstance(rng, list) and len(rng) == 2 and all(_is_num(x) for x in rng) and rng[0] <= rng[1]):
            err("range must be [min, max] with min <= max")
            rng = None
        elif not numeric:
            err("range needs a number field")
    if rng is None and display == "rating":
        rng = [1, 5]
    labels = opts.get("labels")
    if labels is not None:
        if not (isinstance(labels, list) and len(labels) == 2 and all(isinstance(x, str) and x for x in labels)):
            err("labels must be two words")
        elif ftype != "bool":
            err("labels needs a yes/no (bool) field")
    if opts.get("symbol") is not None and display != "rating":
        err("symbol needs display 'rating'")
    choices = opts.get("choices")
    multiple = opts.get("multiple") is True
    if choices is not None:
        if not (isinstance(choices, list) and all(isinstance(c, str) and 0 < len(c) <= 64 for c in choices)):
            err("choices must be a list of text")
            choices = None
        elif not 1 <= len(choices) <= MAX_CHOICES:
            err(f"choices must list 1-{MAX_CHOICES} values")
        elif len(set(choices)) != len(choices):
            err("choices lists a value twice")
        elif ftype != ("json" if multiple else "string"):
            err("multiple choices need a json field" if multiple else "choices need a string field")
    elif multiple:
        err("multiple needs choices")
    elif display == "choice":
        err("display 'choice' needs choices")
    if "default" in opts and opts["default"] is not None:
        _lint_option_default(opts["default"], ftype, choices if isinstance(choices, list) else None,
                             multiple, rng, display, err)


def _lint_option_default(v, ftype, choices, multiple, rng, display, err):
    if ftype == "date" and v == "now":
        return
    bad = False
    if ftype == "json":
        bad = False
    elif not _literal_matches(v, ftype) or token_name(v) is not None:
        bad = True
    elif ftype == "integer" and isinstance(v, float) and not v.is_integer():
        bad = True
    elif ftype == "date" and not _valid_date(v):
        bad = True
    if not bad and choices is not None:
        items = v if multiple else [v]
        bad = not isinstance(items, list) or any(i not in choices for i in items)
    if not bad and rng is not None and _is_num(v):
        bad = not rng[0] <= v <= rng[1]
    if not bad and display == "location":
        bad = not (isinstance(v, dict) and _is_num(v.get("lat")) and _is_num(v.get("lon"))
                   and -90 <= v["lat"] <= 90 and -180 <= v["lon"] <= 180)
    if bad:
        err(f"default {v!r} does not fit the field")


def _lint_order(cname, cdef, fields, out):
    """`order`: the fields in display order, each declared once."""
    order = cdef.get("order")
    if order is None:
        return
    if not isinstance(order, list) or not all(isinstance(x, str) for x in order):
        out.append(("error", f"collection {cname}: 'order' must be a list of field names"))
        return
    if len(set(order)) != len(order):
        out.append(("error", f"collection {cname}: order names a field twice"))
    for name in order:
        if name not in fields:
            out.append(("error", f"collection {cname}: order names undeclared field '{name}'"))


def _lint_defaults(cname, cdef, fields, out):
    """`defaults` (field → starting value) belongs to a singleton collection only."""
    if "defaults" not in cdef:
        return
    d = cdef["defaults"]
    if cdef.get("singleton") is not True:
        out.append(("error", f"collection {cname}: 'defaults' needs 'singleton': true"))
        return
    if not isinstance(d, dict):
        out.append(("error", f"collection {cname}: 'defaults' must be an object of field → value"))
        return
    for fname, v in d.items():
        ftype = fields.get(fname)
        if ftype is None:
            out.append(("error", f"collection {cname}: default for undeclared field '{fname}'"))
        elif token_name(v) is not None:
            out.append(("error", f"collection {cname}.defaults.{fname}: a default is a literal, not a token"))
        elif v is not None and ftype != "json" and not _literal_matches(v, ftype):
            out.append(("error", f"collection {cname}.defaults.{fname}: {v!r} is not a {ftype}"))
        elif ftype == "integer" and isinstance(v, float) and not v.is_integer():
            out.append(("error", f"collection {cname}.defaults.{fname}: {v!r} has a fraction; the field is integer"))
        elif ftype == "date" and isinstance(v, str) and not _valid_date(v):
            out.append(("error", f"collection {cname}.defaults.{fname}: {v!r} is not a valid date"))


def _lint_views(views, out, schema):
    if views is None:
        return
    if not isinstance(views, dict):
        out.append(("error", "'views' must be an object of {name: {from, where?, orderBy?, limit?}}"))
        return
    colls = schema["collections"]
    for vname, vdef in views.items():
        if not COLLECTION_RE.match(str(vname)):
            out.append(("error", f"view name {vname!r} must match ^[a-z][A-Za-z0-9_]{{0,47}}$"))
            continue
        if vname in colls:
            out.append(("error", f"view {vname} collides with a collection of the same name"))
            continue
        if not isinstance(vdef, dict) or not isinstance(vdef.get("from"), str):
            out.append(("error", f"view {vname}: needs 'from' naming a collection or another view"))
            continue
        for key in ("groupBy", "aggregate"):
            if key in vdef:
                out.append(("error", f"view {vname}: '{key}' is not allowed on a view (a view is a row set; "
                                     f"aggregate in the binding)"))
        for key in vdef:
            if key not in ("from", "where", "orderBy", "limit"):
                out.append(("warn", f"view {vname}: unknown key '{key}' is ignored"))
        schema["views"][vname] = vdef
    # Resolve every chain: unknown from, cycles, depth, then lint each view's own stage
    # against the base collection's fields.
    for vname, vdef in list(schema["views"].items()):
        cur, hops, seen = vdef.get("from"), 0, {vname}
        while cur not in colls:
            if cur in seen:
                out.append(("error", f"view {vname}: cyclic 'from' chain"))
                break
            if cur not in schema["views"]:
                out.append(("error", f"view {vname}: unknown from {cur!r}"))
                break
            seen.add(cur)
            hops += 1
            if hops >= MAX_VIEW_DEPTH:
                out.append(("error", f"view {vname}: nesting deeper than {MAX_VIEW_DEPTH}"))
                break
            cur = schema["views"][cur].get("from")
        else:
            fields = {**RESERVED_FIELDS, **colls[cur]}
            stage = {k: vdef[k] for k in ("where", "orderBy", "limit") if k in vdef}
            out.extend((sev, f"view {vname}: {msg}") for sev, msg in lint_stage(stage, fields))


# ── query stage (sync) ───────────────────────────────────────────────────────────

_NUMERIC = ("number", "integer")
_LITERAL_TYPES = {"string": str, "date": str, "number": (int, float), "integer": (int, float),
                  "bool": bool}


def _literal_matches(value, ftype) -> bool:
    """Does a literal (non-token, non-null) JSON value have the field's JSON type? The
    app treats a mismatch as "matches nothing", so the lint only warns."""
    if value is None or token_name(value) is not None or ftype == "json":
        return True
    py = _LITERAL_TYPES[ftype]
    if isinstance(value, bool):
        return ftype == "bool"
    return isinstance(value, py)


def lint_stage(stage: dict, fields: dict) -> list[tuple[str, str]]:
    """Check a binding's query stage `{where?, groupBy?, aggregate?, orderBy?, limit?}`
    against `fields` ({name: type}, reserved fields included — see `fields_for`)."""
    out: list[tuple[str, str]] = []
    if not isinstance(stage, dict):
        return [("error", "stage must be an object")]
    for key in stage:
        if key not in ("where", "groupBy", "aggregate", "orderBy", "limit"):
            out.append(("warn", f"unknown stage key '{key}' is ignored (no projections, joins or having)"))
    grouped = "groupBy" in stage
    if "where" in stage:
        leaves = _lint_where(stage["where"], fields, out, "where", depth=1)
        if leaves > MAX_WHERE_LEAVES:
            out.append(("error", f"where has {leaves} leaves; at most {MAX_WHERE_LEAVES}"))
    if grouped:
        _lint_group_by(stage["groupBy"], fields, out)
    if "aggregate" in stage:
        _lint_aggregate(stage["aggregate"], fields, out, grouped)
    if "orderBy" in stage:
        _lint_order_by(stage["orderBy"], fields, out, grouped)
    if "limit" in stage:
        lim = stage["limit"]
        if isinstance(lim, bool) or not isinstance(lim, int) or not 1 <= lim <= MAX_LIMIT:
            out.append(("error", f"limit must be an integer from 1 to {MAX_LIMIT}, got {lim!r}"))
    return out


def _lint_where(node, fields, out, path, depth) -> int:
    """Returns the leaf count; appends problems. Mirrors `LocalWhere.parse`."""
    if not isinstance(node, dict):
        out.append(("error", f"{path} must be an object"))
        return 0
    if depth > MAX_WHERE_DEPTH:
        out.append(("error", f"{path} nests deeper than {MAX_WHERE_DEPTH}"))
        return 0
    leaves = 0
    for key, value in node.items():
        if key in ("and", "or"):
            if not isinstance(value, list):
                out.append(("error", f"{path}.{key} must be an array of where objects"))
                continue
            for i, sub in enumerate(value):
                leaves += _lint_where(sub, fields, out, f"{path}.{key}[{i}]", depth + 1)
            continue
        ftype = fields.get(key)
        if ftype is None:
            out.append(("error", f"{path}.{key}: unknown field '{key}' (declare it on the collection)"))
            continue
        if isinstance(value, list):
            out.append(("error", f"{path}.{key}: an array is not a value (use {{\"in\": [...]}})"))
            continue
        if isinstance(value, dict):
            if not value:
                out.append(("error", f"{path}.{key}: empty operator object"))
                continue
            for op, v in value.items():
                leaves += 1
                _lint_leaf(key, ftype, op, v, out, f"{path}.{key}.{op}")
        else:
            leaves += 1
            _lint_leaf(key, ftype, "eq", value, out, f"{path}.{key}")
    return leaves


def _lint_leaf(field, ftype, op, v, out, path):
    if op not in WHERE_OPS:
        out.append(("error", f"{path}: unknown operator '{op}'; use one of {list(WHERE_OPS)}"))
        return
    if ftype == "json" and op != "exists":
        out.append(("error", f"{path}: field '{field}' is json; only 'exists' applies"))
        return
    if op == "exists":
        if not isinstance(v, bool):
            out.append(("error", f"{path}: exists takes true or false"))
        return
    if op == "contains":
        if ftype != "string":
            out.append(("error", f"{path}: contains needs a string field ('{field}' is {ftype})"))
        elif not isinstance(v, str):
            out.append(("warn", f"{path}: contains wants a string; this never matches"))
        return
    if op == "in":
        if not isinstance(v, list):
            out.append(("error", f"{path}: in must be an array"))
            return
        if len(v) > MAX_IN_MEMBERS:
            out.append(("error", f"{path}: at most {MAX_IN_MEMBERS} members in 'in' ({len(v)} given)"))
        for m in v:
            _lint_value(field, ftype, m, out, path)
        return
    if ftype == "bool" and op in ("gt", "gte", "lt", "lte"):
        out.append(("error", f"{path}: bool field '{field}' supports eq/ne only"))
        return
    _lint_value(field, ftype, v, out, path)


def _lint_value(field, ftype, v, out, path):
    tok = token_name(v)
    if tok is not None:
        if tok not in TOKENS:
            out.append(("error", f"{path}: unknown token '{{{{{tok}}}}}'; store tokens are "
                                 f"{', '.join('{{' + t + '}}' for t in TOKENS)}"))
        elif tok == "selected" and ftype != "string":
            out.append(("warn", f"{path}: {{{{selected}}}} is an id (string); '{field}' is {ftype}"))
        elif tok != "selected" and ftype != "date":
            out.append(("warn", f"{path}: {{{{{tok}}}}} is a date; '{field}' is {ftype}, so this never matches"))
        return
    if isinstance(v, (dict, list)):
        out.append(("error", f"{path}: a {type(v).__name__} is not a comparable value"))
    elif not _literal_matches(v, ftype):
        out.append(("warn", f"{path}: {v!r} is not a {ftype}; the app treats a type mismatch as "
                            f"'matches nothing'"))


def _lint_group_by(g, fields, out):
    if isinstance(g, str):
        field, unit, width = g, None, None
        if fields.get(g) == "json":
            out.append(("error", f"groupBy: cannot group by json field '{g}'"))
    elif isinstance(g, dict):
        field, unit, width = g.get("field"), g.get("bucket"), g.get("width")
        if not isinstance(field, str):
            out.append(("error", "groupBy.field must be a string"))
            return
        if unit is not None and width is not None:
            out.append(("error", "groupBy: bucket and width are exclusive"))
            return
        for key in g:
            if key not in ("field", "bucket", "width"):
                out.append(("warn", f"groupBy: unknown key '{key}' is ignored"))
    else:
        out.append(("error", "groupBy must be a field name or {field, bucket|width}"))
        return
    ftype = fields.get(field)
    if ftype is None:
        out.append(("error", f"groupBy: unknown field '{field}'"))
        return
    if unit is not None:
        if unit not in BUCKET_UNITS:
            out.append(("error", f"groupBy.bucket: unknown unit {unit!r}; use one of {list(BUCKET_UNITS)}"))
        elif ftype != "date":
            out.append(("error", f"groupBy.bucket needs a date field ('{field}' is {ftype})"))
    if width is not None:
        if isinstance(width, bool) or not isinstance(width, (int, float)) or not width > 0:
            out.append(("error", "groupBy.width must be a number > 0"))
        elif ftype not in _NUMERIC:
            out.append(("error", f"groupBy.width needs a numeric field ('{field}' is {ftype})"))


def _lint_aggregate(a, fields, out, grouped):
    if isinstance(a, str):
        op, field = a, None
    elif isinstance(a, dict):
        op, field = a.get("op"), a.get("field")
        for key in a:
            if key not in ("op", "field"):
                out.append(("warn", f"aggregate: unknown key '{key}' is ignored"))
    else:
        out.append(("error", "aggregate must be an op name or {op, field}"))
        return
    if op not in AGGREGATE_OPS:
        out.append(("error", f"aggregate: unknown op {op!r}; use one of {list(AGGREGATE_OPS)}"))
        return
    if op == "count":
        if field is not None:
            out.append(("error", "aggregate: count takes no field"))
        return
    if field is None or not isinstance(field, str):
        out.append(("error", f"aggregate: {op} needs a 'field' (use the object form)"))
        return
    ftype = fields.get(field)
    if ftype is None:
        out.append(("error", f"aggregate: unknown field '{field}'"))
        return
    if op in ("first", "last"):
        if grouped:
            out.append(("error", f"aggregate: {op} is not a group aggregate"))
        elif ftype == "json":
            out.append(("error", f"aggregate: {op} cannot read a json field ('{field}')"))
    elif op in ("sum", "avg") and ftype not in _NUMERIC:
        out.append(("error", f"aggregate: {op} needs a numeric field ('{field}' is {ftype})"))
    elif op in ("min", "max") and ftype in ("json", "bool"):
        out.append(("error", f"aggregate: {op} needs a number, string or date field ('{field}' is {ftype})"))
    elif op == "distinct" and ftype == "json":
        out.append(("error", f"aggregate: distinct cannot count a json field ('{field}')"))


def _lint_order_by(o, fields, out, grouped):
    names = [o] if isinstance(o, str) else o
    if not isinstance(names, list) or not names or not all(isinstance(n, str) for n in names):
        out.append(("error", "orderBy must be a field name or a non-empty array of field names"))
        return
    for n in names:
        field = n[1:] if n.startswith("-") else n
        if not field:
            out.append(("error", "orderBy: empty field name"))
        elif grouped and field not in ("key", "value"):
            out.append(("error", f"orderBy: a grouped query orders by 'key' or 'value' only, not '{field}'"))
        elif not grouped and field not in fields:
            out.append(("error", f"orderBy: unknown field '{field}'"))


# ── ops (action) ─────────────────────────────────────────────────────────────────

def lint_op(a: dict, schema: dict | None) -> list[tuple[str, str]]:
    """Check a `method: local` action: op, collection, id, set (see local-store.md Ops).
    `schema` is the normalized source schema from `lint_source` (None = unknown source,
    so field checks are skipped)."""
    out: list[tuple[str, str]] = []
    op = a.get("op")
    if op not in ACTION_OPS:
        out.append(("error", f"op must be one of {list(ACTION_OPS)}, got {op!r}"))
        return out
    coll = a.get("collection")
    if not isinstance(coll, str) or not coll:
        out.append(("error", f"{op} needs a 'collection'"))
        return out
    if "where" in a:
        out.append(("error", f"{op} takes no 'where': a layout writes and deletes by id only"))
    for key in ("event", "topic", "url", "path", "mode"):
        if key in a:
            out.append(("warn", f"'{key}' means nothing on a local action"))
    fields = None
    if schema is not None:
        if coll in (schema.get("views") or {}):
            if op != "select":
                out.append(("error", f"{op} targets collections only; '{coll}' is a view"))
        elif coll not in (schema.get("collections") or {}):
            out.append(("error", f"unknown collection '{coll}'"))
        fields = fields_for(schema, coll)
    computed = set((schema or {}).get("computed", {}).get(coll, []))
    written = set(a["set"]) if op in ("set", "insert", "update", "upsert") and isinstance(a.get("set"), dict) else set()
    if op in ("increment", "decrement", "toggle") and isinstance(a.get("field"), str):
        written.add(a["field"])
    for field in sorted(computed & written):
        out.append(("error", f"field {field} is computed from other fields; leave it out"))
    singletons = (schema or {}).get("singletons") or []
    if op in SINGLETON_OPS:
        _lint_singleton_op(a, op, coll, schema, fields, singletons, out)
        return out
    if coll in singletons and op in ("insert", "update", "upsert"):
        out.append(("warn", f"'{coll}' is a singleton (one row, id '{SINGLETON_ROW_ID}'); write it with op set"))
    needs_id = op in ("update", "upsert", "delete")
    if needs_id and not a.get("id"):
        out.append(("error", f"{op} needs an 'id' (a literal, '{{{{selected}}}}' or another token)"))
    if op == "select" and "id" not in a:
        out.append(("error", "select needs an 'id' (a string, a token, or null to clear the selection)"))
    ident = a.get("id")
    if ident is not None:
        _lint_id(ident, out)
    if op in ("insert", "update", "upsert"):
        s = a.get("set")
        if not isinstance(s, dict) or not s:
            out.append(("error", f"{op} needs a non-empty 'set' object of field → value"))
        else:
            _lint_set(s, fields, out)
    elif "set" in a:
        out.append(("warn", f"'set' is ignored by {op}"))
    return out


def _lint_singleton_op(a, op, coll, schema, fields, singletons, out):
    """set / increment / decrement / toggle write a singleton's one row; the arithmetic
    and the flip run in one SQL UPDATE on the phone (toggle is in-app only)."""
    if schema is not None and coll in (schema.get("collections") or {}) and coll not in singletons:
        out.append(("error", f"{op} needs a singleton collection; declare '{coll}' with 'singleton': true"))
    if "id" in a:
        out.append(("warn", f"'id' is ignored by {op}: a singleton has one row"))
    if op == "set":
        s = a.get("set")
        if not isinstance(s, dict) or not s:
            out.append(("error", "set needs a non-empty 'set' object of field → value"))
        else:
            _lint_set(s, fields, out)
        return
    if "set" in a:
        out.append(("warn", f"'set' is ignored by {op}"))
    field = a.get("field")
    if not isinstance(field, str) or not field:
        out.append(("error", f"{op} needs a 'field'"))
        return
    if op == "toggle" and "by" in a:
        out.append(("warn", "'by' is ignored by toggle"))
    by = a.get("by")
    if op != "toggle" and by is not None and token_name(by) is None and (
            isinstance(by, bool) or not isinstance(by, (int, float))):
        out.append(("error", f"{op}: 'by' must be a number, got {by!r}"))
        by = None
    if fields is None:
        return
    ftype = fields.get(field)
    if ftype is None or field in RESERVED_FIELDS:
        out.append(("error", f"{op}: unknown field '{field}' (declare it on the collection)"))
    elif op == "toggle" and ftype != "bool":
        out.append(("error", f"toggle needs a bool field; '{field}' is {ftype}"))
    elif op != "toggle" and ftype not in _NUMERIC:
        out.append(("error", f"{op} needs a number or integer field; '{field}' is {ftype}"))
    elif op != "toggle" and ftype == "integer" and isinstance(by, float) and not by.is_integer():
        out.append(("error", f"{op}: by {by!r} has a fraction; '{field}' is integer"))


def _lint_id(ident, out):
    if not isinstance(ident, str):
        out.append(("error", "id must be a string"))
        return
    tok = token_name(ident)
    if tok is not None:
        if tok not in TOKENS and tok not in ACTION_TOKENS:
            out.append(("error", f"id: unknown token '{{{{{tok}}}}}'"))
    elif not ID_RE.match(ident):
        out.append(("error", "id must be 1–128 chars of [A-Za-z0-9_.:-]"))


def _lint_set(s, fields, out):
    for fname, v in s.items():
        if fname in RESERVED_NAMES:
            out.append(("error", f"set.{fname}: reserved field (the store manages id/createdAt/updatedAt)"))
            continue
        if fields is None:
            continue
        ftype = fields.get(fname)
        if ftype is None:
            out.append(("error", f"set.{fname}: unknown field (declare it on the collection)"))
            continue
        tok = token_name(v)
        if tok is not None:
            if tok not in TOKENS and tok not in ACTION_TOKENS:
                out.append(("error", f"set.{fname}: unknown token '{{{{{tok}}}}}'"))
            elif tok in ("now", "today", "startOfWeek", "startOfMonth", "startOfYear") and ftype != "date":
                out.append(("warn", f"set.{fname}: {{{{{tok}}}}} writes a date into a {ftype} field — the write is rejected"))
        elif v is not None and ftype != "json" and not _literal_matches(v, ftype):
            out.append(("error", f"set.{fname}: {v!r} is not a {ftype}; the store rejects, never coerces"))
        elif ftype == "integer" and isinstance(v, float) and not v.is_integer():
            out.append(("error", f"set.{fname}: {v!r} has a fraction; the field is integer"))
        elif ftype == "date" and isinstance(v, str) and not _valid_date(v):
            out.append(("error", f"set.{fname}: {v!r} is not a valid date (YYYY-MM-DD or an ISO-8601 instant)"))


def _valid_date(s: str) -> bool:
    """A calendar date or an ISO-8601 instant with a zone (what LocalDates.normalize accepts)."""
    import datetime as _dt
    try:
        if len(s) == 10:
            _dt.date.fromisoformat(s)
            return True
        d = _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d.tzinfo is not None
    except ValueError:
        return False
