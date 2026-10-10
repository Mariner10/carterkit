"""Form builder sugar: the `form` block a group carries (see ControlDocs/form.md).

Builder only. Validation lives in validate.py (`bad_form`): build with
`ui.group("New", form=carterkit.form(...))` and run `validate_layout`.
"""
from __future__ import annotations


def rules(*, required: bool = None, min: float = None, max: float = None,
          min_length: int = None, max_length: int = None, one_of: list = None,
          kind: str = None) -> dict:
    """One field's validators (required, min, max, minLength, maxLength, oneOf, kind)."""
    out: dict = {}
    for key, v in (("required", required), ("min", min), ("max", max), ("minLength", min_length),
                   ("maxLength", max_length), ("oneOf", one_of), ("kind", kind)):
        if v is not None:
            out[key] = v
    return out


def form(*, fields: dict = None, submit: dict = None, mode: str = None,
         collection: str = None, after_submit: str = None) -> dict:
    """A group's `form` block. `fields` maps field name -> `rules(...)` or a plain dict;
    `submit` is one action, e.g. {"method": "local", "op": "insert", "set": "{{form}}"}."""
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
        out["fields"] = {name: dict(r) for name, r in fields.items()}
    if submit is not None:
        out["submit"] = submit
    if after_submit is not None:
        out["afterSubmit"] = after_submit
    return out
