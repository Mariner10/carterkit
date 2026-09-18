"""Tests for validate.py — schema-driven layout linting against the real catalog."""

from pathlib import Path

from carterkit import catalog
from carterkit import validate

DOCS = Path(__file__).parent.parent / "carterkit" / "controldocs"
CAT = catalog.build_catalog(DOCS, include_theme=True)


def _layout(children, columns=4, rows=4):
    return {"name": "T", "version": 1,
            "tabs": [{"title": "Main", "icon": "house.fill",
                      "grid": {"columns": columns, "rows": rows},
                      "children": children}]}


def _kinds(findings):
    return {f["kind"] for f in findings}


def test_clean_layout_no_errors():
    layout = _layout([
        {"type": "gauge", "id": "bat", "position": [0, 0], "span": [2, 2],
         "min": 0, "max": 100, "label": "Battery", "tint": "#34C759",
         "sync": [{"method": "meshsocket", "type": "listen", "event": "broadcast",
                   "valuePath": "battery"}]},
        {"type": "button", "id": "go", "position": [0, 2], "label": "Go", "style": "ghost"},
    ])
    findings = validate.validate_layout(layout, CAT)
    errors = [f for f in findings if f["severity"] == "error"]
    assert errors == [], errors


def test_missing_top_level_fields():
    findings = validate.validate_layout({"tabs": []}, CAT)
    details = " ".join(f["detail"] for f in findings)
    assert "name" in details and "version" in details


def test_duplicate_id():
    layout = _layout([
        {"type": "button", "id": "x", "position": [0, 0]},
        {"type": "button", "id": "x", "position": [0, 1]},
    ])
    assert "duplicate_id" in _kinds(validate.validate_layout(layout, CAT))


def test_unknown_type():
    layout = _layout([{"type": "frobnicator", "id": "f", "position": [0, 0]}])
    assert "unknown_type" in _kinds(validate.validate_layout(layout, CAT))


def test_bad_enum_value():
    # An unrecognized enum is a WARNING, not an error: the app never rejects a layout
    # for one — it renders the control with the field's default. The message still names
    # the accepted values so lint readers catch the typo.
    layout = _layout([{"type": "button", "id": "b", "position": [0, 0],
                       "style": "sparkly"}])
    findings = validate.validate_layout(layout, CAT)
    assert "bad_enum" in _kinds(findings)
    enum = [f for f in findings if f["kind"] == "bad_enum"]
    assert all(f["severity"] == "warn" for f in enum)
    assert any("filled" in f["detail"] for f in enum)  # accepted values named


def test_parameterized_enum_ok():
    # `formatValue: "decimal:2"` is a real parameterized format — the base token matches.
    layout = _layout([{"type": "slider", "id": "s", "position": [0, 0],
                       "formatValue": "decimal:2"}])
    findings = validate.validate_layout(layout, CAT)
    assert not any(f["kind"] == "bad_enum" for f in findings)


def test_unknown_field_is_warning():
    layout = _layout([{"type": "button", "id": "b", "position": [0, 0],
                       "flooberity": 7}])
    findings = validate.validate_layout(layout, CAT)
    uf = [f for f in findings if f["kind"] == "unknown_field"]
    assert uf and uf[0]["severity"] == "warn"


def test_grid_overlap_detected():
    layout = _layout([
        {"type": "button", "id": "a", "position": [0, 0], "span": [1, 2]},
        {"type": "button", "id": "b", "position": [0, 1]},
    ])
    assert "overlap" in _kinds(validate.validate_layout(layout, CAT))


def test_group_recursion_and_nested_ids():
    layout = _layout([
        {"type": "group", "id": "g", "position": [0, 0], "span": [2, 2],
         "grid": {"columns": 2, "rows": 2}, "children": [
             {"type": "toggle", "id": "dup", "position": [0, 0]},
         ]},
        {"type": "toggle", "id": "dup", "position": [0, 2]},
    ])
    # nested + top-level share id 'dup' -> duplicate
    assert "duplicate_id" in _kinds(validate.validate_layout(layout, CAT))


def test_format_findings_clean():
    assert "No issues" in validate.format_findings([])


def test_keep_awake_must_be_bool():
    from carterkit.validate import validate_layout
    base = {"name": "K", "version": 1, "tabs": []}
    assert not [f for f in validate_layout({**base, "keepAwake": True}, {})
                if f["kind"] == "bad_top_level"]
    bad = [f for f in validate_layout({**base, "keepAwake": "true"}, {})
           if f["kind"] == "bad_top_level"]
    assert bad and "keepAwake" in bad[0]["detail"]


def test_batch_publishers_must_be_bool_and_needs_publishers():
    from carterkit.validate import validate_layout
    base = {"name": "B", "version": 1, "tabs": []}
    bad = [f for f in validate_layout({**base, "batchPublishers": "yes"}, {})
           if f["kind"] == "bad_top_level"]
    assert bad and "batchPublishers" in bad[0]["detail"]
    lonely = [f for f in validate_layout({**base, "batchPublishers": True}, {})
              if f["kind"] == "bad_top_level"]
    assert lonely and lonely[0]["severity"] == "info"
    ok = [f for f in validate_layout({**base, "batchPublishers": True,
                                      "publishers": [{"sensor": "motion"}]}, {})
          if f["kind"] == "bad_top_level"]
    assert not ok


# ── glance v2 — the layout projected onto iOS surfaces ───────────────────────
#
# Severity follows what iOS does with the mistake: a missing control id means the
# tile is quietly omitted (warn), while a `step` with nothing to step is a button
# the user can press forever with no effect (error).

def _glance_layout(glance):
    layout = _layout([
        {"type": "gauge", "id": "cpu", "position": [0, 0], "min": 0, "max": 100,
         "sync": [{"method": "meshsocket", "type": "listen", "event": "broadcast",
                   "valuePath": "cpu"}]},
        {"type": "toggle", "id": "lights", "position": [0, 1]},
    ])
    layout["glance"] = glance
    return layout


def _glance_findings(glance):
    return [f for f in validate.validate_layout(_glance_layout(glance), CAT)
            if f["kind"].startswith("bad_glance")]


def _codes(glance):
    return {f["kind"] for f in _glance_findings(glance)}


def test_glance_tiles_and_controls_flag_missing_control_ids():
    codes = _codes({
        "hero": "ghost",
        "controls": [{"id": "c", "kind": "toggle", "control": "nope", "valueControl": "gone"}],
        "widgets": [{"id": "w", "scene": {"rows": [[{"tile": "gauge", "control": "absent"}]]}}],
    })
    assert codes == {"bad_glance"}
    details = " ".join(f["detail"] for f in _glance_findings({
        "widgets": [{"id": "w", "scene": {"rows": [[{"tile": "gauge", "control": "absent"}]]}}]}))
    assert "absent" in details


def test_glance_known_control_ids_are_clean():
    assert _codes({
        "hero": "cpu", "slots": ["lights"],
        "controls": [{"id": "c", "kind": "toggle", "control": "lights", "valueControl": "cpu"}],
        "widgets": [{"id": "w", "families": ["systemSmall"],
                     "scene": {"rows": [[{"tile": "gauge", "control": "cpu"}]]}}],
        "island": {"compactTrailing": {"tile": "ring", "control": "cpu"}},
        "lockScreen": {"rows": [[{"tile": "value", "control": "cpu"}]]},
        "live": {"tier": "periodic"},
    }) == set()


def test_glance_unknown_tile_kind_warns():
    findings = _glance_findings({"widgets": [{"id": "w", "scene": {
        "rows": [[{"tile": "chart", "control": "cpu"}]]}}]})
    assert [f["kind"] for f in findings] == ["bad_glance_tile"]
    assert findings[0]["severity"] == "warn" and "chart" in findings[0]["detail"]


def test_step_cycle_and_set_need_a_control_to_drive():
    for kind in ("step", "cycle", "set"):
        findings = _glance_findings({"controls": [{"id": "c", "kind": kind,
                                                   "states": [{"value": 1}, {"value": 2}]}]})
        errors = [f for f in findings if f["severity"] == "error"]
        assert errors and errors[0]["kind"] == "bad_glance_control"
        assert "control" in errors[0]["detail"]


def test_cycle_needs_at_least_two_states():
    findings = _glance_findings({"controls": [
        {"id": "fan", "kind": "cycle", "control": "lights", "states": [{"value": "off"}]}]})
    errors = [f for f in findings if f["severity"] == "error"]
    assert errors and "two states" in errors[0]["detail"]
    assert not [f for f in _glance_findings({"controls": [
        {"id": "fan", "kind": "cycle", "control": "lights",
         "states": [{"value": "off"}, {"value": "on"}]}]}) if f["severity"] == "error"]


def test_non_numeric_delta_is_an_error_on_controls_and_tiles():
    control = [f for f in _glance_findings({"controls": [
        {"id": "up", "kind": "step", "control": "cpu", "delta": "10"}]})
        if f["severity"] == "error"]
    assert control and control[0]["kind"] == "bad_glance_control"
    tile = [f for f in _glance_findings({"widgets": [{"id": "w", "scene": {
        "rows": [[{"tile": "step", "control": "cpu", "delta": "10"}]]}}]})
        if f["severity"] == "error"]
    assert tile and tile[0]["kind"] == "bad_glance_control"


def test_unknown_widget_family_warns():
    findings = _glance_findings({"widgets": [
        {"id": "w", "families": ["systemSmall", "systemHuge"],
         "scene": {"rows": [[{"tile": "value", "control": "cpu"}]]}}]})
    assert [f["kind"] for f in findings] == ["bad_glance_family"]
    assert "systemHuge" in findings[0]["detail"]


def test_unknown_live_tier_warns():
    findings = _glance_findings({"live": {"tier": "instant"}})
    assert [f["kind"] for f in findings] == ["bad_glance_live"]
    assert findings[0]["severity"] == "warn"


def test_single_tile_island_region_given_a_scene_warns():
    findings = _glance_findings({"island": {
        "minimal": {"rows": [[{"tile": "light", "control": "cpu"}]]}}})
    assert "bad_glance_island" in {f["kind"] for f in findings}
    # the expanded bottom legitimately takes a scene
    assert not _glance_findings({"island": {"expanded": {
        "bottom": {"rows": [[{"tile": "gauge", "control": "cpu"}]]}}}})


def test_span_wider_than_the_scene_warns():
    findings = _glance_findings({"widgets": [{"id": "w", "scene": {
        "rows": [[{"tile": "gauge", "control": "cpu"}, {"tile": "gauge", "control": "lights"}],
                 [{"tile": "sparkline", "control": "cpu", "span": 5}]]}}]})
    spans = [f for f in findings if f["kind"] == "bad_glance_span"]
    assert spans and "5" in spans[0]["detail"]
    # a spanning tile that exactly fills the row is fine
    assert not _glance_findings({"widgets": [{"id": "w", "scene": {
        "rows": [[{"tile": "gauge", "control": "cpu"}, {"tile": "gauge", "control": "lights"}],
                 [{"tile": "sparkline", "control": "cpu", "span": 2}]]}}]})


def test_declared_columns_are_respected_over_the_longest_row():
    assert not _glance_findings({"widgets": [{"id": "w", "scene": {
        "columns": 4, "rows": [[{"tile": "gauge", "control": "cpu", "span": 4}]]}}]})


def test_glance_validation_survives_malformed_json():
    """A linter that raises on bad input is useless — every branch must tolerate
    whatever a hand-written or LLM-written layout throws at it."""
    for glance in ({"controls": "nope"}, {"widgets": [None]}, {"island": 4},
                   {"widgets": [{"id": "w", "scene": {"rows": "no"}}]},
                   {"widgets": [{"id": "w", "scene": {"rows": [["tile"]]}}]},
                   {"lockScreen": []}, {"live": {"tier": None}}):
        validate.validate_layout(_glance_layout(glance), CAT)
