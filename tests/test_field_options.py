"""carter-73q2.28: object-form field declarations (type + options) in a local source."""
from __future__ import annotations

import json

import pytest

from carterkit import Layout, local

ALL_TYPES = {
    "when": {"type": "date", "required": True, "default": "now", "display": "dateTime"},
    "cups": {"type": "number", "unit": "cups", "range": [0, 20], "decimals": 1, "default": 1},
    "mood": {"type": "string", "choices": ["Good", "Okay", "Rough"], "display": "choice"},
    "tags": {"type": "json", "choices": ["Work", "Home"], "multiple": True},
    "stars": {"type": "integer", "display": "rating", "symbol": "star", "default": 4},
    "done": {"type": "bool", "labels": ["Done", "Not yet"], "default": False},
    "took": {"type": "number", "display": "duration", "unit": "min"},
    "place": {"type": "json", "display": "location"},
    "note": {"type": "string", "display": "longText", "label": "A note"},
    "plain": "string",
}


def lint(fields, **extra):
    src = {"type": "local", "collections": {"log": {"fields": fields, **extra}}}
    return local.lint_source(src)


def errors(fields, **extra):
    return [m for sev, m in lint(fields, **extra)[0] if sev == "error"]


def test_metadata_form_accepted_beside_plain_form():
    findings, schema = lint(ALL_TYPES, order=["when", "cups"])
    assert [f for f in findings if f[0] == "error"] == []
    assert schema["collections"]["log"]["cups"] == "number"
    assert schema["collections"]["log"]["plain"] == "string"


def test_plain_form_still_valid():
    assert errors({"title": "string", "pages": "integer"}) == []


def test_metadata_round_trips_through_layout_json(tmp_path):
    with Layout("Log") as ui:
        ui.source_local("db", collections={"log": {"fields": ALL_TYPES, "order": ["when"]}})
        with ui.tab("Main"):
            ui.label("x", text="x")
    out = tmp_path / "l.json"
    ui.save(str(out))
    again = json.loads(out.read_text())
    assert again["sources"]["db"]["collections"]["log"]["fields"] == ALL_TYPES
    assert errors(again["sources"]["db"]["collections"]["log"]["fields"]) == []


@pytest.mark.parametrize("fields,expected", [
    ({"x": {"type": "number", "colour": "red"}}, "unknown option 'colour'"),
    ({"x": {"type": "number", "range": [5, 1]}}, "range must be [min, max]"),
    ({"x": {"type": "string", "range": [1, 5]}}, "range needs a number field"),
    ({"x": {"type": "string", "unit": "kg"}}, "unit needs a number field"),
    ({"x": {"type": "number", "display": "rating"}}, "display 'rating' does not fit type number"),
    ({"x": {"type": "number", "display": "sparkles"}}, "unknown display 'sparkles'"),
    ({"x": {"type": "string", "choices": []}}, "choices must list"),
    ({"x": {"type": "string", "choices": ["a", "a"]}}, "choices lists a value twice"),
    ({"x": {"type": "string", "choices": ["a"], "multiple": True}}, "multiple choices need a json field"),
    ({"x": {"type": "json", "multiple": True}}, "multiple needs choices"),
    ({"x": {"type": "string", "choices": ["a"], "default": "b"}}, "default 'b' does not fit"),
    ({"x": {"type": "number", "range": [0, 5], "default": 9}}, "default 9 does not fit"),
    ({"x": {"type": "integer", "default": 1.5}}, "default 1.5 does not fit"),
    ({"x": {"type": "number", "required": "yes"}}, "required must be true or false"),
    ({"x": {"type": "bool", "labels": ["On"]}}, "labels must be two words"),
    ({"x": {"type": "integer", "symbol": "star"}}, "symbol needs display 'rating'"),
    ({"x": {"type": "number", "decimals": 9}}, "decimals must be 0-6"),
    ({"x": {"required": True}}, "unknown type None"),
])
def test_bad_metadata_rejected_with_named_error(fields, expected):
    errs = errors(fields)
    assert any(expected in e and "collection log.x" in e for e in errs), errs


def test_order_must_name_declared_fields_once():
    assert any("order names a field twice" in e for e in errors({"a": "string"}, order=["a", "a"]))
    assert any("undeclared field 'b'" in e for e in errors({"a": "string"}, order=["b"]))
