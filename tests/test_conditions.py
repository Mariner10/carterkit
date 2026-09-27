"""Conditions v2 (carter-c1n.18): the `visible`/`enabled` lint and builder sugar.

The shared cases live in the app repo (CAR-TER/CAR-TERTests/Fixtures/conditions/v2.json,
which the device's ConditionTreeTests also runs). Point CARTER_CONDITIONS_FIXTURE at the
file, or keep the workspace layout (this repo beside CAR-TER/); otherwise those skip.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from carterkit import Layout, catalog, validate
from carterkit.conditions import check_condition, condition_refs

DOCS = Path(__file__).parent.parent / "carterkit" / "controldocs"
CAT = catalog.build_catalog(DOCS, include_theme=True)
_REL = Path("CAR-TER") / "CAR-TERTests" / "Fixtures" / "conditions" / "v2.json"


def _fixture() -> dict | None:
    env = os.environ.get("CARTER_CONDITIONS_FIXTURE")
    if env:
        return json.loads(Path(env).read_text())
    for parent in Path(__file__).resolve().parents:
        if (parent / _REL).is_file():
            return json.loads((parent / _REL).read_text())
    return None


FIXTURE = _fixture()
needs_fixture = pytest.mark.skipif(FIXTURE is None, reason="app repo conditions fixture not found")


def _errors(cond) -> list[dict]:
    findings: list[dict] = []
    check_condition(cond, "c", findings)
    return [f for f in findings if f["severity"] == "error"]


def _cases(bucket):
    return [(c["name"], c["condition"]) for c in (FIXTURE or {}).get(bucket, [])]


@needs_fixture
@pytest.mark.parametrize("name,cond", _cases("accept") + _cases("failClosed"))
def test_shared_accept_cases_lint_clean(name, cond):
    assert _errors(cond) == [] or name.startswith("unknown-operator"), name


@needs_fixture
@pytest.mark.parametrize("name,cond", _cases("reject"))
def test_shared_reject_cases_are_errors(name, cond):
    assert _errors(cond), name


def test_legacy_leaf_is_clean_and_unknown_operator_is_error():
    assert _errors({"when": "a", "operator": "gt", "value": 3}) == []
    assert _errors({"when": "a", "value": True}) == []
    assert _errors({"when": "a", "operator": "neq", "value": "x"}) == []
    assert {f["kind"] for f in _errors({"when": "a", "operator": "between", "value": 1})} == {"bad_operator"}


def test_reserved_refs_warn():
    findings: list[dict] = []
    check_condition({"ref": {"derive": "form.f.valid"}, "value": True}, "c", findings)
    assert [f["kind"] for f in findings] == ["reserved_ref"]
    assert findings[0]["severity"] == "warn"


def test_depth_cap_is_16():
    c = {"when": "a", "value": True}
    for _ in range(15):
        c = {"not": c}
    assert _errors(c) == []
    assert {f["kind"] for f in _errors({"not": c})} == {"condition_too_deep"}


def test_condition_refs():
    cond = {"all": [{"when": "a", "value": 1},
                    {"not": {"ref": {"selected": "plants"}, "operator": "ne", "value": None}}]}
    assert condition_refs(cond) == [("control", "a"), ("selected", "plants")]


def test_validate_layout_lints_visible_and_enabled():
    layout = {"name": "T", "version": 1, "tabs": [{"title": "M", "icon": "house",
              "grid": {"columns": 4, "rows": 4}, "children": [
        {"type": "toggle", "id": "a", "position": [0, 0]},
        {"type": "button", "id": "go", "position": [1, 0], "label": "Go",
         "enabled": {"all": [{"when": "a", "value": True}]},
         "visible": {"any": []}},
        {"type": "group", "id": "g", "position": [2, 0], "grid": {"columns": 1, "rows": 1},
         "enabled": {"not": {"when": "a", "operator": "between", "value": 1}}, "children": []},
    ]}]}
    findings = validate.validate_layout(layout, CAT)
    assert not [f for f in findings if f["kind"] == "unknown_field"]
    bad = sorted((f["kind"], f["where"]) for f in findings if f["severity"] == "error")
    assert ("bad_condition", "Main/go.visible.any") in bad or any(
        k == "bad_condition" and w.endswith("go.visible.any") for k, w in bad), bad
    assert any(k == "bad_operator" and "g.enabled.not" in w for k, w in bad), bad


def test_builder_combinators_and_enabled():
    with Layout("T", cols=4, rows=4) as ui:
        with ui.tab("Main", icon="house"):
            power = ui.slider("power", min=0, max=100)
            mode = ui.picker("mode", options=["auto", "manual"])
            ui.button("go", label="Go", enabled=(power > 50) & mode.eq("auto") & ~(power > 90),
                      visible=(power > 0) | mode.eq("manual"))
            with ui.group("G", enabled=~mode.eq("manual")):
                pass
    tab = ui.layout["tabs"][0]["children"]
    go = next(c for c in tab if c.get("id") == "go")
    assert go["enabled"] == {"all": [
        {"when": "power", "operator": "gt", "value": 50},
        {"when": "mode", "operator": "eq", "value": "auto"},
        {"not": {"when": "power", "operator": "gt", "value": 90}}]}
    assert go["visible"] == {"any": [
        {"when": "power", "operator": "gt", "value": 0},
        {"when": "mode", "operator": "eq", "value": "manual"}]}
    g = next(c for c in tab if c.get("type") == "group")
    assert g["enabled"] == {"not": {"when": "mode", "operator": "eq", "value": "manual"}}
    assert [f for f in validate.validate_layout(ui.layout, CAT) if f["severity"] == "error"] == []
