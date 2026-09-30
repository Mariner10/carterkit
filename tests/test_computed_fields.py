import pytest
from carterkit import local
from carterkit.local_compute import parse_compute


def source(compute, **options):
    return {"type": "local", "collections": {"log": {"singleton": True, "fields": {
        "a": "number", "b": "bool", "when": "date", "text": "string",
        "sum": {"type": "number", "compute": compute, **options},
    }}}}


def errors(src):
    return [message for severity, message in local.lint_source(src)[0] if severity == "error"]


@pytest.mark.parametrize("op", ["add", "sub", "mul", "div"])
def test_arithmetic_and_boolean_inputs(op):
    src = source({op: [{"field": "a"}, {"field": "b"}, 2]})
    assert errors(src) == []
    problems, schema = local.lint_source(src)
    assert local.fields_for(schema, "log")["sum"] == "number"
    for write in [{"op": "set", "set": {"sum": 9}}, {"op": "increment", "field": "sum"},
                  {"op": "upsert", "id": "singleton", "set": {"sum": 9}}]:
        assert any("is computed" in message for _, message in local.lint_op({"collection": "log", **write}, schema))
    assert local.lint_op({"collection": "log", "op": "set", "set": {"a": 9}}, schema) == []


@pytest.mark.parametrize("op", ["since", "until"])
@pytest.mark.parametrize("unit", ["seconds", "minutes", "hours", "days", "weeks"])
def test_dates(op, unit):
    assert errors(source({op: {"of": {"field": "when"}, "unit": unit}})) == []


@pytest.mark.parametrize("formula, message", [
    ({"pow": [1, 2]}, "unknown op"),
    ({"field": "sum"}, "reads itself"),
    ({"field": "missing"}, "undeclared field"),
    ({"field": "text"}, "not a number"),
    ({"since": {"of": {"field": "a"}}}, "not a date"),
    ({"since": {"of": 1}}, "reads one date field"),
    ({"since": {"of": {"field": "when"}, "unit": "years"}}, "unit must"),
    ({"add": [1]}, "takes 2-8"),
    ({"add": [1, 2]}, "reads no field"),
    (True, "must be a number"),
    ({"add": [{"field": "a"}, float("inf")]}, "not finite"),
])
def test_invalid_formulas(formula, message):
    assert any(message in error for error in errors(source(formula)))


@pytest.mark.parametrize("option, value, message", [
    ("type", "string", "needs a number"), ("required", True, "can't be required"),
    ("default", 3, "can't have a default"), ("choices", ["A"], "can't have a choices"),
])
def test_incompatible_options(option, value, message):
    assert any(message in error for error in errors(source({"field": "a"}, **{option: value})))


def test_cross_computed_and_singleton_defaults():
    src = source({"field": "a"})
    collection = src["collections"]["log"]
    collection["fields"]["a"] = {"type": "number", "compute": {"field": "b"}}
    assert any("reads computed field a" in error for error in errors(src))
    collection["defaults"] = {"sum": 3}
    assert any("can't have a default" in error for error in errors(src))


def test_complexity_limits():
    nested = {"field": "a"}
    for _ in range(4):
        nested = {"add": [nested, 1]}
    with pytest.raises(ValueError, match="deeper than 4"):
        parse_compute(nested)
    with pytest.raises(ValueError, match="more than 24"):
        parse_compute({"add": [{"add": [1] * 8}] * 3})
