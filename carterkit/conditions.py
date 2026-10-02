"""Conditions v2 (carter-c1n.18): the `visible` / `enabled` condition grammar.

Mirrors CAR-TER/CAR-TER/Models/VisibilityCondition.swift (the device decoder) and
ControlDocs/visibility.md (the source of truth):

    {"all": [c, ...]} | {"any": [c, ...]} | {"not": c} | leaf
    leaf = {"ref": {"control"|"selected"|"field"|"derive": "<key>"}, "operator": op, "value": v}
         | {"when": "<control id>", "operator": op, "value": scalar}      # legacy, unchanged

Operators are the one Match grammar (eq ne gt gte lt lte in exists; aliases neq/is/isNot).
Depth cap 16. A node names exactly one of all/any/not/ref/when; all/any need >= 1 child.
`field` refs read a form cell (`<formId>.valid|dirty|<field>|<field>.error`, carter-c1n.20);
a `derive` ref resolves only as `form.<formId>.<cell>`. Any other `derive` is reserved: it
decodes but makes the whole condition false, so the lint warns.
"""

from __future__ import annotations

MATCH_OPS = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "exists"}
MATCH_ALIASES = {"neq": "ne", "is": "eq", "isNot": "ne"}
REF_KINDS = ("control", "selected", "field", "derive")
RESERVED_REFS = {"derive"}   # except keys starting "form." (a form cell)
SHAPE_KEYS = ("all", "any", "not", "ref", "when")
MAX_CONDITION_DEPTH = 16


def _f(severity: str, kind: str, where: str, detail: str) -> dict:
    return {"severity": severity, "kind": kind, "where": where, "detail": detail}


def canonical_op(op):
    """The canonical operator name, or None when unknown."""
    if op is None:
        return "eq"
    if not isinstance(op, str):
        return None
    return op if op in MATCH_OPS else MATCH_ALIASES.get(op)


def check_condition(cond, where: str, findings: list, depth: int = 1) -> None:
    """Append findings for one `visible`/`enabled` condition tree."""
    if depth > MAX_CONDITION_DEPTH:
        findings.append(_f("error", "condition_too_deep", where,
                           f"condition nests deeper than {MAX_CONDITION_DEPTH} — the app rejects the layout"))
        return
    if not isinstance(cond, dict):
        findings.append(_f("error", "bad_condition", where, "a condition must be an object"))
        return
    shapes = [k for k in SHAPE_KEYS if k in cond]
    if len(shapes) != 1:
        detail = ("needs one of all/any/not/ref/when" if not shapes
                  else f"mixes {'/'.join(shapes)} — a node carries exactly one")
        findings.append(_f("error", "bad_condition", where, f"condition {detail}"))
        return
    shape = shapes[0]
    if shape in ("all", "any"):
        kids = cond[shape]
        if not isinstance(kids, list) or not kids:
            findings.append(_f("error", "bad_condition", f"{where}.{shape}",
                               f"'{shape}' needs a non-empty array of conditions"))
            return
        for i, kid in enumerate(kids):
            check_condition(kid, f"{where}.{shape}[{i}]", findings, depth + 1)
        return
    if shape == "not":
        check_condition(cond["not"], f"{where}.not", findings, depth + 1)
        return
    _check_leaf(cond, shape, where, findings)


def _check_leaf(cond: dict, shape: str, where: str, findings: list) -> None:
    if "value" not in cond:
        findings.append(_f("error", "bad_condition", where, "condition leaf needs a 'value'"))
        return
    value = cond["value"]
    if shape == "when":
        if not isinstance(cond["when"], str):
            findings.append(_f("error", "bad_condition", where, "'when' must be a control id string"))
        if value is None or isinstance(value, (list, dict)):
            findings.append(_f("error", "bad_condition", where,
                               "the legacy {when, value} leaf takes a bool/number/string value; "
                               "use {\"ref\": {\"control\": ...}} for null or an 'in' list"))
    else:
        ref = cond["ref"]
        if (not isinstance(ref, dict) or len(ref) != 1
                or next(iter(ref)) not in REF_KINDS or not isinstance(next(iter(ref.values())), str)):
            findings.append(_f("error", "bad_condition", f"{where}.ref",
                               f"'ref' needs exactly one of {'/'.join(REF_KINDS)} naming a string key"))
            return
        kind = next(iter(ref))
        if kind in RESERVED_REFS and not ref[kind].startswith("form."):
            findings.append(_f("warn", "reserved_ref", f"{where}.ref",
                               f"'{kind}' refs are reserved for a later app version; on this build "
                               f"the whole condition evaluates false"))
    op = cond.get("operator")
    if op is not None and not isinstance(op, str):
        findings.append(_f("error", "bad_condition", where, "'operator' must be a string"))
        return
    canon = canonical_op(op)
    if canon is None:
        findings.append(_f("error", "bad_operator", where,
                           f"operator '{op}' is not one of {sorted(MATCH_OPS | set(MATCH_ALIASES))} — "
                           f"a push is refused and the condition fails closed"))
    elif canon == "in" and not isinstance(value, list):
        findings.append(_f("warn", "bad_condition", where, "'in' needs an array value; it never matches"))
    elif canon == "exists" and not isinstance(value, bool):
        findings.append(_f("warn", "bad_condition", where, "'exists' needs true/false; it never matches"))


def condition_refs(cond) -> list[tuple[str, str]]:
    """Every (kind, key) a well-formed condition reads, depth first."""
    out: list[tuple[str, str]] = []
    if not isinstance(cond, dict):
        return out
    for k in ("all", "any"):
        if isinstance(cond.get(k), list):
            for kid in cond[k]:
                out += condition_refs(kid)
            return out
    if "not" in cond:
        return condition_refs(cond["not"])
    if isinstance(cond.get("when"), str):
        return [("control", cond["when"])]
    ref = cond.get("ref")
    if isinstance(ref, dict) and len(ref) == 1:
        (kind, key), = ref.items()
        if isinstance(key, str):
            return [(kind, key)]
    return out
