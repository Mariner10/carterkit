"""Form groups (carter-c1n.20): the `form` lint and builder sugar.

The device mirror is CAR-TER/CAR-TER/Models/FormConfig.swift; the shared accept/reject
cases live in the app's layout-conformance fixtures (form-group, form-regex-validator,
form-unknown-kind), which test_conformance.py runs.
"""

from __future__ import annotations

import pytest

import carterkit
from carterkit.forms import VALIDATORS


def _layout(form: dict, children: list | None = None) -> dict:
    kids = children if children is not None else [
        {"type": "textInput", "id": "name", "position": [0, 0]},
        {"type": "stepper", "id": "everyDays", "position": [0, 1], "min": 1, "max": 60},
        {"type": "button", "id": "save", "position": [1, 0], "label": "Save", "role": "submit"},
    ]
    return {"name": "F", "version": 1, "tabs": [{"title": "A", "icon": "leaf", "grid": {"columns": 2, "rows": 4},
            "children": [{"type": "group", "id": "f", "position": [0, 0], "span": [3, 2],
                          "grid": {"columns": 2, "rows": 2}, "form": form, "children": kids}]}]}


GOOD = {"collection": "plants",
        "fields": {"name": {"required": True, "maxLength": 40},
                   "everyDays": {"required": True, "min": 1, "max": 60, "kind": "integer"}},
        "submit": {"method": "local", "op": "insert", "set": "{{form}}"}}


def _kinds(layout, severity=None):
    return [f["kind"] for f in carterkit.validate_layout(layout)
            if severity is None or f["severity"] == severity]


def test_the_validator_set_is_closed_and_matches_the_app():
    assert VALIDATORS == ("required", "min", "max", "minLength", "maxLength", "oneOf", "kind")


def test_a_good_form_lints_clean():
    assert _kinds(_layout(GOOD)) == []


@pytest.mark.parametrize("rules", [{"pattern": "^a"}, {"regex": "x"}, {"kind": "phone"},
                                   {"minLength": -1}, {"required": "yes"}, {"oneOf": "a"}])
def test_bad_validators_are_errors(rules):
    form = dict(GOOD, fields={"name": rules})
    assert "bad_form" in _kinds(_layout(form), "error")


def test_warnings_for_miswired_forms():
    form = dict(GOOD, fields={"nope": {"required": True}})
    kinds = _kinds(_layout(form), "warn")
    assert "form_field_unbound" in kinds
    no_submit = [{"type": "textInput", "id": "name", "position": [0, 0],
                  "action": {"method": "meshsocket", "event": "broadcast_request", "payload": {"msg_type": "x"}}}]
    kinds = _kinds(_layout({k: v for k, v in GOOD.items() if k != "submit"}, no_submit), "warn")
    assert {"bad_form", "form_input_binding"} <= set(kinds)


def test_local_submit_needs_a_collection():
    form = {"fields": {}, "submit": {"method": "local", "op": "insert", "set": "{{form}}"}}
    assert "bad_form" in _kinds(_layout(form), "error")


def test_field_key_names_the_draft_field():
    kids = [{"type": "textInput", "id": "editName", "field": "name", "position": [0, 0]},
            {"type": "button", "id": "save", "position": [1, 0], "label": "Save", "role": "submit"}]
    form = dict(GOOD, fields={"name": {"required": True}})
    assert _kinds(_layout(form, kids)) == []


def test_role_and_field_outside_a_form_warn():
    lay = {"name": "F", "version": 1, "tabs": [{"title": "A", "icon": "leaf", "grid": {"columns": 2, "rows": 2},
           "children": [{"type": "button", "id": "b", "position": [0, 0], "label": "B", "role": "submit"},
                        {"type": "textInput", "id": "t", "position": [1, 0], "field": "name"}]}]}
    assert _kinds(lay, "warn").count("form_outside") == 2


def test_builder_sugar():
    ui = carterkit.Layout("Plants", cols=2, rows=6)
    with ui.tab("Add", icon="leaf"):
        with ui.group("New plant", id="plantForm", span=(4, 2), cols=2, rows=3,
                      form=carterkit.form(collection="plants",
                                          fields={"name": carterkit.form_rules(required=True, max_length=40)},
                                          submit={"method": "local", "op": "insert", "set": "{{form}}"})):
            ui.text_input("name", placeholder="Name")
            ui.button("save", label="Save", role="submit")
    doc = ui.layout
    group = doc["tabs"][0]["children"][0]
    assert group["form"]["fields"] == {"name": {"required": True, "maxLength": 40}}
    assert [f for f in carterkit.validate_layout(doc) if f["severity"] == "error"] == []
    with pytest.raises(ValueError):
        carterkit.form_rules(kind="phone")
    with pytest.raises(ValueError):
        carterkit.form(fields={"x": {"pattern": "a"}})
