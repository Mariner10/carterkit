"""carter-m7s.37 — the sectioned document (schemaVersion 2): read both forms, validate
section ids, to_sectioned()/to_inline() round-trip, sections win over inline."""
import copy

import carterkit
from carterkit import Layout, to_inline, to_sectioned, is_sectioned
from carterkit.contract import extract_contract
from carterkit import sections as kit_sections
from carterkit.hub import _walk_children


def _inline():
    return {
        "name": "Greenhouse", "version": 4,
        "tabs": [{"title": "Plants", "icon": "leaf", "grid": {"columns": 2, "rows": 8}, "children": [
            {"type": "gauge", "id": "c_soil", "label": "Soil", "position": [0, 0], "span": [3, 2],
             "tint": "#34C759", "landscape": {"position": [0, 2], "span": [2, 1]},
             "sync": [{"method": "meshsocket", "event": "soil"}]},
            {"type": "group", "id": "g_bench", "label": "Bench", "position": [3, 0], "span": [3, 2],
             "hideBackground": True, "grid": {"columns": 2, "rows": 2}, "children": [
                {"type": "button", "id": "c_water", "label": "Water", "position": [0, 0],
                 "span": [1, 2], "icon": "drop",
                 "action": {"method": "meshsocket", "mode": "broadcast",
                            "event": "broadcast_request", "payload": {"msg_type": "water"}}}]},
        ]}],
    }


def _errors(layout):
    return [f for f in carterkit.validate_layout(layout) if f["severity"] == "error"]


def test_round_trip_is_lossless():
    inline = _inline()
    sectioned = to_sectioned(inline)
    assert sectioned["schemaVersion"] == 2
    assert sectioned["placements"]["c_water"] == {"position": [0, 0], "span": [1, 2]}
    assert sectioned["styles"]["g_bench"] == {"hideBackground": True}
    assert "sync" in sectioned["connectivity"]["c_soil"]
    assert "position" not in sectioned["tabs"][0]["children"][0]
    assert to_inline(sectioned) == inline
    assert inline == _inline()                    # pure: the input is untouched


def test_both_forms_validate_the_same():
    inline, sectioned = _inline(), to_sectioned(_inline())
    strip = lambda fs: sorted((f["kind"], f["where"]) for f in fs)
    assert strip(carterkit.validate_layout(sectioned)) == strip(carterkit.validate_layout(inline))


def test_section_entry_wins_and_default_alias():
    doc = _inline()
    doc["tabs"][0]["children"][0]["tint"] = "#000000"
    doc["schemaVersion"] = 2
    doc["styles"] = {"c_soil": {"tint": "#FFFFFF"}}
    doc["placements"] = {"g_bench": {"default": {"position": [4, 0]}}}
    folded = to_inline(doc)
    kids = folded["tabs"][0]["children"]
    assert kids[0]["tint"] == "#FFFFFF"
    assert kids[1]["position"] == [4, 0]
    assert not is_sectioned(folded) and "schemaVersion" not in folded


def test_unknown_ids_are_errors_and_dropped():
    doc = to_sectioned(_inline())
    doc["styles"]["ghost"] = {"tint": "#FF0000"}
    doc["connectivity"]["c_water"] = 5
    found = [f for f in _errors(doc) if f["kind"] == "bad_section"]
    assert sorted(f["where"] for f in found) == ["root.connectivity.c_water", "root.styles.ghost"]
    folded = to_inline(doc)
    assert "ghost" not in folded.get("styles", {})


def test_non_facet_keys_survive():
    doc = to_sectioned(_inline())
    doc["placements"]["c_soil"]["com.example.snap"] = {"grid": 4}
    folded = to_inline(doc)
    assert folded["placements"] == {"c_soil": {"com.example.snap": {"grid": 4}}}
    assert folded["schemaVersion"] == 2
    assert to_sectioned(folded)["placements"]["c_soil"]["com.example.snap"] == {"grid": 4}


def test_readers_see_sectioned_bindings():
    sectioned = to_sectioned(_inline())
    by_id = {c["id"]: c for c in _walk_children(sectioned)}
    assert by_id["c_soil"]["sync"][0]["event"] == "soil"
    assert extract_contract(sectioned) == extract_contract(_inline())


def test_sections_warn_without_schema_version():
    doc = to_sectioned(_inline())
    del doc["schemaVersion"]
    assert any(f["kind"] == "bad_schema_version" for f in carterkit.validate_layout(doc))


def test_builder_to_sectioned():
    with Layout("S", cols=2, rows=4) as ui:
        with ui.tab("Main", icon="gauge"):
            ui.gauge("cpu", label="CPU", span=(2, 2))
    out = ui.to_sectioned()
    assert out["placements"]["cpu"]["span"] == [2, 2]
    assert to_inline(out) == ui.layout
    assert copy.deepcopy(ui.layout) == ui.layout


def test_container_insides_are_outside_the_namespace_like_the_app():
    """carter-m7s.39 parity with the app's SectionedDocumentTests: carousel panels,
    canvas items and long-press groups keep their insides inline; a section entry
    naming one of them is dropped. A dynamic group is an ordinary group."""
    inner = {"type": "button", "id": "c_inpanel", "label": "Go", "position": [0, 0]}
    layout = {
        "schemaVersion": 2, "name": "C", "version": 1,
        "tabs": [{"title": "T", "icon": "house", "grid": {"columns": 4, "rows": 12}, "children": [
            {"type": "carousel", "id": "c_car", "panels": [
                {"type": "group", "id": "p_home", "position": [0, 0],
                 "grid": {"columns": 1, "rows": 1}, "children": [inner]}]},
            {"type": "canvas", "id": "c_canvas", "canvasConfig": {"items": [
                {"id": "i1", "control": {"type": "gauge", "id": "c_ingauge"}}]}},
            {"type": "button", "id": "c_lp", "longPressGroup": {
                "type": "group", "id": "g_lp", "position": [0, 0], "grid": {"columns": 2, "rows": 1},
                "children": [{"type": "button", "id": "c_inlp", "position": [0, 0]}]}},
            {"type": "group", "id": "g_dyn", "dynamic": "feed", "grid": {"columns": 4, "rows": 2},
             "children": []}]}],
        "placements": {"c_car": {"position": [0, 0]}, "c_canvas": {"position": [3, 0]},
                       "c_lp": {"position": [7, 0]}, "g_dyn": {"position": [8, 0]},
                       "c_inpanel": {"position": [1, 1]}, "c_inlp": {"position": [1, 1]}},
        "styles": {"c_ingauge": {"tint": "#000000"}, "g_lp": {"tint": "#000000"}},
    }
    dropped = {where for where, _ in kit_sections.section_issues(layout)}
    assert dropped == {"root.placements.c_inpanel", "root.placements.c_inlp",
                       "root.styles.c_ingauge", "root.styles.g_lp"}
    folded = to_inline(layout)
    assert folded["tabs"][0]["children"][3]["position"] == [8, 0]
    assert folded["tabs"][0]["children"][0]["panels"][0]["children"][0] == inner
