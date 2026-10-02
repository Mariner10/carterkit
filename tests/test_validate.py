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


def _one_label(**fields):
    ctrl = {"type": "label", "id": "fern", "position": [0, 0], **fields}
    return {"name": "t", "tabs": [{"name": "T", "grid": {"columns": 2, "rows": 2},
                                   "children": [ctrl]}]}


def test_relative_format_lint():
    from carterkit.validate import validate_layout
    kinds = lambda lay: {f["kind"] for f in validate_layout(lay, CAT)}
    ok = kinds(_one_label(formatValue="relative:day", placeholder="Not watered yet"))
    assert "bad_relative_format" not in ok and "unknown_field" not in ok
    assert "bad_relative_format" in kinds(_one_label(formatValue="relative:days"))
    gauge = _one_label(formatValue="relative")
    gauge["tabs"][0]["children"][0].update({"type": "gauge", "min": 0, "max": 1})
    assert "relative_format_type" in kinds(gauge)


# carter-eqd — the control `unit` field (values.md "Units").
def _unit_layout(ctype, unit):
    return {"name": "U", "version": 1, "tabs": [{"title": "A", "grid": {"columns": 4, "rows": 4},
            "children": [{"type": ctype, "id": "c", "position": [0, 0], "unit": unit}]}]}


def _unit_kinds(ctype, unit):
    from carterkit import validate_layout
    return [f["kind"] for f in validate_layout(_unit_layout(ctype, unit))]


def test_known_units_and_symbols_are_clean():
    for ctype in ("gauge", "label", "progressRing"):
        for unit in ("celsius", "Celsius", "°F", "km/h", "percent"):
            kinds = _unit_kinds(ctype, unit)
            assert "unknown_field" not in kinds and "unit_typo" not in kinds, (ctype, unit, kinds)


def test_literal_unit_is_allowed():
    assert "unit_typo" not in _unit_kinds("gauge", "dBFS")
    assert "unit_typo" not in _unit_kinds("label", "°/s")


def test_probable_unit_typo_warns():
    from carterkit import validate_layout
    found = [f for f in validate_layout(_unit_layout("gauge", "celcius")) if f["kind"] == "unit_typo"]
    assert found and found[0]["severity"] == "warn" and "'celsius'" in found[0]["detail"]
    assert "unit_typo" in _unit_kinds("progressRing", "kilometersperhr")
    assert "bad_unit" in _unit_kinds("label", 5)


# carter-pby — a "<your-token>" template slot is not an embedded credential.
def test_embedded_secret_skips_template_placeholders():
    from carterkit import validate_layout

    def lay(tok):
        return {"name": "S", "version": 1,
                "connection": {"url": "wss://relay.example.net", "token": tok},
                "tabs": [{"title": "A", "icon": "house", "grid": {"columns": 2, "rows": 2},
                          "children": []}]}
    kinds = lambda tok: {f["kind"] for f in validate_layout(lay(tok))}
    assert "embedded_secret" not in kinds("<your-token>")
    assert "embedded_secret" in kinds("abc123realtoken")


# carter-avv — sync `staleAfter` and layout `liveness` (sync.md / layout-config.md).
def _stale_layout(stale=None, liveness=None):
    sync = {"method": "meshsocket", "event": "broadcast", "valuePath": "v"}
    if stale is not None:
        sync["staleAfter"] = stale
    lay = {"name": "S", "version": 1, "tabs": [{"title": "A", "icon": "house",
           "grid": {"columns": 2, "rows": 2},
           "children": [{"type": "label", "id": "a", "position": [0, 0], "sync": [sync]}]}]}
    if liveness is not None:
        lay["liveness"] = liveness
    return lay


def _stale_kinds(**kw):
    from carterkit import validate_layout
    return [f["kind"] for f in validate_layout(_stale_layout(**kw))]


def test_stale_after_and_liveness_are_known_fields():
    kinds = _stale_kinds(stale=120, liveness={"staleAfter": 60})
    assert "unknown_field" not in kinds and "bad_stale_after" not in kinds
    assert "bad_stale_after" not in _stale_kinds(stale=0, liveness={"staleAfter": 86400})


def test_stale_after_out_of_range_warns():
    from carterkit import validate_layout
    for bad in (-1, "120", True, 90000):
        found = [f for f in validate_layout(_stale_layout(stale=bad)) if f["kind"] == "bad_stale_after"]
        assert found and found[0]["severity"] == "warn", bad
    assert "bad_stale_after" in _stale_kinds(liveness={"staleAfter": 100000})
    assert "bad_liveness" in _stale_kinds(liveness=5)
    assert "unknown_field" in _stale_kinds(liveness={"stale": 5})


# carter-akc — every per-element action carrier gets the dead_action lint, and the
# remedy for a payload that already carries msg_type is event 'broadcast_request'.
def _action_layout(ctype, akey, action):
    return {"name": "A", "version": 1, "tabs": [{"title": "A", "icon": "house",
            "grid": {"columns": 4, "rows": 4},
            "children": [{"type": ctype, "id": "c", "position": [0, 0], akey: action}]}]}


def test_dead_action_covers_every_secondary_carrier():
    from carterkit import validate_layout
    from carterkit.validate import SECONDARY_ACTION_KEYS
    for ctype, akey in (("boxPlot", "boxAction"), ("chord", "arcAction"),
                        ("heatmap", "cellAction"), ("treemap", "itemAction"),
                        ("gantt", "taskAction"), ("pieChart", "sliceAction")):
        assert akey in SECONDARY_ACTION_KEYS
        lay = _action_layout(ctype, akey, {"event": "set_power"})
        assert "dead_action" in {f["kind"] for f in validate_layout(lay)}, akey
        ok = _action_layout(ctype, akey, {"event": "broadcast_request",
                                          "payload": {"msg_type": "tap"}})
        assert "dead_action" not in {f["kind"] for f in validate_layout(ok)}, akey


# carter-y85y — ControlDocs nest the secondary carriers inside the per-type config
# (gantt.md: ganttConfig.taskAction), so the lint must look there too.
def test_dead_action_covers_secondary_carrier_nested_in_config():
    from carterkit import validate_layout
    for ctype, ckey, akey in (("gantt", "ganttConfig", "taskAction"),
                              ("heatmap", "heatmapConfig", "cellAction"),
                              ("graph", "graphConfig", "nodeAction"),
                              ("chord", "chordConfig", "arcAction")):
        lay = _action_layout(ctype, ckey, {akey: {"event": "broadcast",
                                                  "payload": {"msg_type": "tap"}}})
        dead = [f for f in validate_layout(lay) if f["kind"] == "dead_action"]
        assert len(dead) == 1, (ckey, akey)
        assert f"{ckey}.{akey}" in dead[0]["detail"], dead[0]["detail"]
        ok = _action_layout(ctype, ckey, {akey: {"event": "broadcast_request",
                                                 "payload": {"msg_type": "tap"}}})
        assert "dead_action" not in {f["kind"] for f in validate_layout(ok)}, akey


# carter-du4t — compass pucks each carry an action in compassConfig.pucks[].action.
def test_dead_action_covers_compass_puck_actions():
    from carterkit import validate_layout
    pucks = [{"id": "a", "bearing": 0, "action": {"event": "broadcast_request",
                                                  "payload": {"msg_type": "go"}}},
             {"id": "b", "bearing": 90, "action": {"event": "broadcast",
                                                   "payload": {"msg_type": "go"}}}]
    lay = _action_layout("compass", "compassConfig", {"pucks": pucks})
    dead = [f for f in validate_layout(lay) if f["kind"] == "dead_action"]
    assert len(dead) == 1, dead
    assert "compassConfig.pucks[1].action" in dead[0]["detail"], dead[0]["detail"]
    pucks[1]["action"]["event"] = "broadcast_request"
    assert "dead_action" not in {f["kind"] for f in validate_layout(lay)}


def test_dead_action_remedy_keeps_existing_msg_type():
    from carterkit import validate_layout
    lay = _action_layout("button", "action", {"event": "broadcast",
                                              "payload": {"msg_type": "lights"}})
    dead = [f for f in validate_layout(lay) if f["kind"] == "dead_action"]
    assert dead and "'broadcast_request'" in dead[0]["detail"]
    assert "send='broadcast'" not in dead[0]["detail"]
    bare = _action_layout("button", "action", {"event": "set_power"})
    dead = [f for f in validate_layout(bare) if f["kind"] == "dead_action"]
    assert dead and "send='set_power'" in dead[0]["detail"]


# carter-qii — list.action (row tap fires with {{value}} = row id; list.md "Row taps").
def test_list_row_tap_action_lints_clean():
    from carterkit import build, bind, validate_layout
    row = build.list(id="todo", action=bind.local_op("update", "items", id="{{value}}",
                                                     set={"done": True}))
    assert row["action"] == {"method": "local", "op": "update", "collection": "items",
                             "id": "{{value}}", "set": {"done": True}}
    row.update({"position": [0, 0], "span": [2, 2],
                "sync": [{"method": "local", "collection": "items"}]})
    lay = {"name": "C", "version": 1,
           "sources": {"db": {"type": "local", "namespace": "checklist", "collections": {
               "items": {"fields": {"title": "string", "done": "bool"}}}}},
           "tabs": [{"title": "A", "icon": "checklist", "grid": {"columns": 2, "rows": 4},
                     "children": [row]}]}
    findings = validate_layout(lay)
    assert not [f for f in findings if f["severity"] == "error"], findings
    assert "unknown_field" not in {f["kind"] for f in findings}


# ─── requires / fallback / since (carter-0gj.27) ─────────────────────────────

import copy as _copy

#: The real catalog with two controls pretending to be newer than the 1.2.4 default.
NEWER = _copy.deepcopy(CAT)
NEWER["symbol"]["since"] = "1.3"
NEWER["compass"]["since"] = "1.4"


def _sym(**kw):
    return {"type": "symbol", "id": "s", "position": [0, 0], "label": "Fan", **kw}


def _needs(findings):
    return [f for f in findings if f["kind"] == "needs_newer_app"]


def _bad(findings, kind):
    return [f for f in findings if f["kind"] == kind]


def test_catalog_exposes_since():
    doc = catalog.parse_doc('---\ntype: knob\nlabel: Knob\ncategory: controls\n'
                            'since: "1.3"\n---\nbody', "knob")
    assert doc["since"] == "1.3"
    assert catalog._compact(doc)["since"] == "1.3"
    assert "since" not in CAT["gauge"]          # absent = baseline


def test_newer_control_without_fallback_warns():
    f = validate.validate_layout(_layout([_sym()]), NEWER)
    [w] = _needs(f)
    assert w["severity"] == "warn" and "1.3" in w["detail"] and "1.2.4" in w["detail"]
    assert not [x for x in f if x["severity"] == "error"]


def test_newer_control_silent_with_fallback():
    f = validate.validate_layout(_layout([_sym(fallback={"type": "label", "label": "Fan"})]), NEWER)
    assert not _needs(f) and not _bad(f, "bad_fallback") and "unknown_field" not in _kinds(f)


def test_requires_app_covers_newer_control():
    lay = _layout([_sym()])
    lay["requires"] = {"app": "1.3"}
    assert not _needs(validate.validate_layout(lay, NEWER))
    lay["requires"] = {"app": "1.2.9"}
    assert _needs(validate.validate_layout(lay, NEWER))


def test_target_app_argument_and_precedence():
    lay = _layout([_sym()])
    assert not _needs(validate.validate_layout(lay, NEWER, target_app="1.3.0"))
    lay["requires"] = {"app": "1.2"}                       # requires.app wins
    assert _needs(validate.validate_layout(lay, NEWER, target_app="2.0"))
    assert validate.effective_target_app({}, None) == ("1.2.4", "the kit's default target")
    assert validate.effective_target_app({"requires": {"app": "x"}}, "1.3")[0] == "1.3"


def test_fallback_that_is_also_too_new_warns():
    assert not _needs(validate.validate_layout(_layout([_sym(fallback={"type": "compass"})]),
                                               NEWER, target_app="1.4"))
    [w] = _needs(validate.validate_layout(_layout([{"type": "compass", "id": "c", "position": [0, 0],
                                                    "fallback": {"type": "symbol"}}]), NEWER))
    assert "fallback chain" in w["detail"]
    # a chain reaches a known control on the second hop: silent
    chained = _sym(fallback={"type": "compass", "fallback": {"type": "label"}})
    assert not _needs(validate.validate_layout(_layout([chained]), NEWER))


def test_newer_control_nested_in_group_and_canvas():
    grp = {"type": "group", "id": "g", "position": [0, 0], "span": [2, 4],
           "grid": {"columns": 4, "rows": 2}, "children": [_sym()]}
    assert len(_needs(validate.validate_layout(_layout([grp]), NEWER))) == 1
    canvas = {"type": "canvas", "id": "cv", "position": [0, 0], "span": [2, 2],
              "canvasConfig": {"items": [{"id": "i1", "control": _sym(
                  fallback={"type": "group", "children": []})}]}}
    f = validate.validate_layout(_layout([canvas]), NEWER)
    assert _needs(f), "a group fallback can't stand in for a canvas item"
    assert any("canvas item" in x["detail"] for x in _bad(f, "bad_fallback"))


def test_bad_fallback_shapes_are_reported_not_raised():
    cases = [
        ("slider", "control object"),
        ({"label": "no type"}, "needs a 'type'"),
        ({"type": "warpDrive"}, "unknown control type"),
        ({"type": "label", "id": "x", "span": [1, 1]}, "ignored"),
    ]
    for fb, needle in cases:
        f = validate.validate_layout(_layout([_sym(fallback=fb)]), NEWER)
        assert any(needle in x["detail"] for x in _bad(f, "bad_fallback")), (fb, f)
        assert all(x["severity"] == "warn" for x in _bad(f, "bad_fallback"))


def test_fallback_chain_longer_than_the_app_follows():
    fb = {"type": "label"}
    for _ in range(4):
        fb = {"type": "warpDrive", "fallback": fb}
    f = validate.validate_layout(_layout([_sym(fallback=fb)]), NEWER)
    assert any("at most 4" in x["detail"] for x in _bad(f, "bad_fallback"))
    assert _needs(f)


def test_bad_requires_shapes_are_reported_not_raised():
    for req, where in [("1.3", "root.requires"), ({"app": 1.3}, "root.requires.app"),
                       ({"app": "v1.3"}, "root.requires.app"),
                       ({"features": "control.symbol"}, "root.requires.features"),
                       ({"features": ["Bad Name"]}, "root.requires.features[0]"),
                       ({"app": "1.3", "min": "1.2"}, "root.requires.min")]:
        lay = _layout([_sym()])
        lay["requires"] = req
        f = validate.validate_layout(lay, NEWER)
        assert [x for x in _bad(f, "bad_requires") if x["where"] == where], (req, f)
        assert not [x for x in f if x["severity"] == "error"]
    ok = _layout([_sym()])
    ok["requires"] = {"app": "1.3", "features": ["control.symbol", "sync.mqtt@2"]}
    assert not _bad(validate.validate_layout(ok, NEWER), "bad_requires")


def test_bundled_catalog_has_no_newer_controls_yet():
    # Every control in the vendored docs shipped in 1.2.4 (carter-0gj.27): no `since`.
    assert not [t for t, spec in CAT.items() if spec.get("since")]


# carter-5q1y — contract reservations: asset://, data:image soft budget, name@N features.
def _res_layout(**top):
    lay = {"name": "R", "version": 1, "tabs": [{"title": "A", "icon": "house",
           "grid": {"columns": 2, "rows": 2}, "children": [
               {"type": "image", "id": "pic", "position": [0, 0], "url": top.pop("url", "https://x.example/a.png")}]}]}
    lay.update(top)
    return lay


def _res(**top):
    from carterkit import validate_layout
    return validate_layout(_res_layout(**top))


def test_asset_scheme_is_reserved_not_refused():
    found = [f for f in _res(url="asset://pack/logo.png") if f["kind"] in ("reserved_scheme", "bad_url")]
    assert [(f["kind"], f["severity"]) for f in found] == [("reserved_scheme", "warn")]


def test_data_image_soft_budget_warns_below_the_hard_cap():
    from carterkit.validate import SOFT_DATA_IMAGE, MAX_DATA_IMAGE
    assert SOFT_DATA_IMAGE < MAX_DATA_IMAGE
    head = "data:image/png;base64,"
    small = head + "A" * 1000
    assert "inline_blob" not in {f["kind"] for f in _res(url=small)}
    soft = [f for f in _res(url=head + "A" * (SOFT_DATA_IMAGE + 10)) if f["kind"] == "inline_blob"]
    assert soft and soft[0]["severity"] == "warn" and "soft budget" in soft[0]["detail"]
    hard = [f for f in _res(url=head + "A" * (MAX_DATA_IMAGE + 10)) if f["kind"] == "inline_blob"]
    assert hard and hard[0]["severity"] == "error"


def test_parse_feature_matches_the_app():
    from carterkit.validate import parse_feature
    assert parse_feature("control.gauge") == ("control.gauge", 1)
    assert parse_feature("layout.fallback@2") == ("layout.fallback", 2)
    for odd in ("x@0", "x@-1", "x@two", "x@"):
        assert parse_feature(odd) == (odd, 1)


def test_requires_features_name_at_n():
    kinds = lambda feats: {(f["kind"], f["severity"]) for f in _res(requires={"features": feats})}
    ok = kinds(["control.progressRing", "sync.mqtt", "layout.fallback@1"])
    assert not {k for k, _ in ok} & {"bad_requires", "unknown_feature"}
    assert ("unknown_feature", "warn") in kinds(["layout.fallback@2"])
    assert ("unknown_feature", "warn") in kinds(["local.store@2"])
    assert ("bad_requires", "warn") in kinds(["control gauge"])


def test_known_features_come_from_the_vendored_app_list():
    import carterkit
    from carterkit.validate import app_features, known_features
    data = app_features()
    assert data["features"] and data["app"], "carterkit/app_features.json missing or empty"
    have = known_features()
    # every catalog control is a feature the app reports, and nothing else is a control
    assert {n[len("control."):] for n in have if n.startswith("control.")} == \
        set(carterkit.controls())
    assert {"sync.meshsocket", "action.http", "layout.requires"} <= set(have)
