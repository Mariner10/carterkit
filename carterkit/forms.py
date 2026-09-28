"""Form groups (carter-c1n.20): the `form` block a group carries.

Mirrors CAR-TER/CAR-TER/Models/FormConfig.swift + Services/FormRuntime.swift (the device)
and ControlDocs/form.md (the source of truth):

    "form": {"mode": "create"|"edit", "collection": "plants",
             "fields": {"<field>": {validators}}, "submit": {action},
             "afterSubmit": "clear"|"keep"}

Validators are a CLOSED set: required, min, max, minLength, maxLength, oneOf, kind
(integer|number|date|email|url). No regex. An unknown validator or kind makes the device
refuse the whole layout, so the lint reports it as an error (`bad_form`).

Inputs inside the group (nested groups included, nested forms excluded) are draft
fields named by their `field` key, else their `id`; a button with `role: "submit"`
submits the form.
"""

from __future__ import annotations

FORM_KEYS = {"mode", "collection", "fields", "submit", "afterSubmit"}
VALIDATORS = ("required", "min", "max", "minLength", "maxLength", "oneOf", "kind")
KINDS = ("integer", "number", "date", "email", "url")
INPUT_TYPES = {"textInput", "stepper", "slider", "toggle", "picker",
               "segmentedControl", "datePicker", "colorPicker"}


def _f(severity: str, kind: str, where: str, detail: str) -> dict:
    return {"severity": severity, "kind": kind, "where": where, "detail": detail}


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def form_fields(children) -> tuple[list[str], list[str], list[dict]]:
    """(draft field names, role:submit button ids, input controls) of a form's children."""
    names: list[str] = []
    submits: list[str] = []
    inputs: list[dict] = []

    def walk(kids):
        for ch in kids or []:
            if not isinstance(ch, dict):
                continue
            if ch.get("type") == "group":
                if "form" not in ch:
                    walk(ch.get("children"))
                continue
            if ch.get("type") in INPUT_TYPES:
                inputs.append(ch)
                name = ch.get("field") or ch.get("id")
                if isinstance(name, str) and name not in names:
                    names.append(name)
            if ch.get("type") == "button" and ch.get("role") == "submit":
                submits.append(ch.get("id"))
    walk(children)
    return names, submits, inputs


def check_rules(rules, where: str, findings: list) -> None:
    if not isinstance(rules, dict):
        findings.append(_f("error", "bad_form", where, "a field's validators must be an object"))
        return
    for k in rules:
        if k not in VALIDATORS:
            findings.append(_f("error", "bad_form", where,
                               f"unknown validator '{k}': the set is closed ({', '.join(VALIDATORS)}); "
                               f"the app refuses the layout"))
    if "required" in rules and not isinstance(rules["required"], bool):
        findings.append(_f("error", "bad_form", where, "'required' must be true/false"))
    for k in ("min", "max"):
        if k in rules and not _num(rules[k]):
            findings.append(_f("error", "bad_form", where, f"'{k}' must be a number"))
    for k in ("minLength", "maxLength"):
        if k in rules and (not isinstance(rules[k], int) or isinstance(rules[k], bool) or rules[k] < 0):
            findings.append(_f("error", "bad_form", where, f"'{k}' must be an integer >= 0"))
    if "oneOf" in rules and not isinstance(rules["oneOf"], list):
        findings.append(_f("error", "bad_form", where, "'oneOf' must be an array"))
    if "kind" in rules and rules["kind"] not in KINDS:
        findings.append(_f("error", "bad_form", where,
                           f"kind '{rules['kind']}' is not one of {', '.join(KINDS)}; the app refuses the layout"))
    if _num(rules.get("min")) and _num(rules.get("max")) and rules["min"] > rules["max"]:
        findings.append(_f("warn", "bad_form", where, "min > max: no value can pass"))
    ml, xl = rules.get("minLength"), rules.get("maxLength")
    if isinstance(ml, int) and isinstance(xl, int) and ml > xl:
        findings.append(_f("warn", "bad_form", where, "minLength > maxLength: no value can pass"))


def check_form(group: dict, where: str, findings: list) -> None:
    """Lint one group's `form` block (call only when the group has one)."""
    form = group.get("form")
    spot = f"{where}.form"
    if not isinstance(form, dict):
        findings.append(_f("error", "bad_form", spot, "'form' must be an object"))
        return
    for k in form:
        if k not in FORM_KEYS:
            findings.append(_f("warn", "unknown_field", spot, f"form: unknown field '{k}' (ignored)"))
    mode = form.get("mode", "create")
    if mode not in ("create", "edit"):
        findings.append(_f("error", "bad_form", spot, f"mode '{mode}' is not create or edit"))
    if form.get("afterSubmit", "clear") not in ("clear", "keep"):
        findings.append(_f("error", "bad_form", spot, "afterSubmit must be clear or keep"))
    if "collection" in form and not isinstance(form["collection"], str):
        findings.append(_f("error", "bad_form", spot, "'collection' must be a string"))
    if mode == "edit" and not form.get("collection"):
        findings.append(_f("warn", "bad_form", spot, "an edit form needs 'collection' to prefill from {{selected}}"))

    names, submits, inputs = form_fields(group.get("children"))
    fields = form.get("fields", {})
    if not isinstance(fields, dict):
        findings.append(_f("error", "bad_form", f"{spot}.fields", "'fields' must be an object"))
        fields = {}
    for name, rules in fields.items():
        check_rules(rules, f"{spot}.fields.{name}", findings)
        if name not in names:
            findings.append(_f("warn", "form_field_unbound", f"{spot}.fields.{name}",
                               f"no input in the form writes '{name}' (field names are an input's "
                               f"`field`, else its id); the validators never run"))

    submit = form.get("submit")
    if submit is None:
        findings.append(_f("warn", "bad_form", spot, "no 'submit' action: pressing submit writes nothing"))
    elif not isinstance(submit, dict) or not isinstance(submit.get("method"), str):
        findings.append(_f("error", "bad_form", f"{spot}.submit", "'submit' must be an action with a 'method'"))
    elif submit.get("method") == "local" and not (submit.get("collection") or form.get("collection")):
        findings.append(_f("error", "bad_form", f"{spot}.submit",
                           "a local submit needs 'collection' (on the submit or the form)"))
    if not submits:
        findings.append(_f("warn", "bad_form", spot, "no button with role: \"submit\" inside the form"))
    for ch in inputs:
        for k in ("action", "sync"):
            if k in ch:
                findings.append(_f("warn", "form_input_binding", f"{where}/{ch.get('id')}",
                                   f"'{k}' on a form input is ignored: its value waits in the draft "
                                   f"until the form's submit"))


def stray_form_keys(ch: dict, in_form: bool, where: str, findings: list) -> None:
    """`role` / `field` outside a form do nothing: warn."""
    if ch.get("role") is not None and ch.get("role") != "submit":
        findings.append(_f("warn", "bad_enum", where, f"role '{ch.get('role')}' is not 'submit'"))
    if not in_form:
        if ch.get("role") == "submit":
            findings.append(_f("warn", "form_outside", where, "role: \"submit\" outside a form group does nothing"))
        if "field" in ch and ch.get("type") in INPUT_TYPES:
            findings.append(_f("warn", "form_outside", where, "'field' outside a form group does nothing"))


# --- builder sugar ---------------------------------------------------------------------

def rules(*, required: bool = None, min: float = None, max: float = None,
          min_length: int = None, max_length: int = None, one_of: list = None,
          kind: str = None) -> dict:
    """One field's validators (the closed set). `kind` is integer|number|date|email|url."""
    if kind is not None and kind not in KINDS:
        raise ValueError(f"kind {kind!r} is not one of {KINDS}")
    out: dict = {}
    for key, v in (("required", required), ("min", min), ("max", max), ("minLength", min_length),
                   ("maxLength", max_length), ("oneOf", one_of), ("kind", kind)):
        if v is not None:
            out[key] = v
    return out


def form(*, fields: dict = None, submit: dict = None, mode: str = None,
         collection: str = None, after_submit: str = None) -> dict:
    """A group's `form` block: `ui.group("New plant", form=carterkit.form(...))`.

    `fields` maps a field name to `rules(...)` (or a plain dict, checked against the closed
    set); `submit` is one action, e.g. `{"method": "local", "op": "insert", "set": "{{form}}"}`.
    """
    if mode is not None and mode not in ("create", "edit"):
        raise ValueError("mode must be 'create' or 'edit'")
    if after_submit is not None and after_submit not in ("clear", "keep"):
        raise ValueError("after_submit must be 'clear' or 'keep'")
    out: dict = {}
    if mode is not None:
        out["mode"] = mode
    if collection is not None:
        out["collection"] = collection
    if fields:
        for name, r in fields.items():
            bad = [k for k in r if k not in VALIDATORS]
            if bad:
                raise ValueError(f"field {name!r}: unknown validator(s) {bad}; allowed {VALIDATORS}")
        out["fields"] = {name: dict(r) for name, r in fields.items()}
    if submit is not None:
        out["submit"] = submit
    if after_submit is not None:
        out["afterSubmit"] = after_submit
    return out
