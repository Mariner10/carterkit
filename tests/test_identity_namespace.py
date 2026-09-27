"""carter-1o0: container panel children, long-press popup children and dynamic decks are
inside the id namespace, as on the device (LayoutSanitizer IdentityPass) and in the MCP.
Mirrors CAR-TERTests/IdentityNamespaceWideningTests.swift and the layout-conformance
fixtures panel-child-duplicate-id / long-press-child-duplicate-id."""

import carterkit
from carterkit import validate


def _label(cid):
    return {"id": cid, "type": "label", "text": "x", "position": [0, 0]}


def _host(gid, *kids):
    return {"id": gid, "position": [0, 0], "grid": {"columns": 1, "rows": 1},
            "children": list(kids)}


def _carousel(cid, *panels):
    return {"type": "carousel", "id": cid, "position": [0, 1], "panels": list(panels)}


def _press(cid, popup):
    return {"type": "button", "id": cid, "position": [0, 2], "longPressGroup": popup}


def _doc(*children):
    return {"name": "t", "version": 1, "tabs": [
        {"title": "A", "icon": "star", "grid": {"columns": 4, "rows": 8},
         "children": list(children)}]}


def _errors(doc):
    cat = carterkit.controls(include_theme=True)
    return [f for f in validate.validate_layout(doc, cat) if f["severity"] == "error"]


def test_panel_child_duplicating_a_grid_id_is_an_error():
    errs = _errors(_doc(_label("x"), _carousel("c", _host("p", _label("x")))))
    dups = [f for f in errs if f["kind"] == "duplicate_id"]
    assert len(dups) == 1 and "panels[0]" in dups[0]["where"]


def test_long_press_child_duplicating_a_grid_id_is_an_error():
    errs = _errors(_doc(_label("x"), _press("b", _host("l", _label("x")))))
    dups = [f for f in errs if f["kind"] == "duplicate_id"]
    assert len(dups) == 1 and "longPressGroup" in dups[0]["where"]


def test_nested_hosts_and_groups_inside_panels_are_walked():
    inner = {"type": "group", "id": "g", "position": [0, 0],
             "grid": {"columns": 1, "rows": 1}, "children": [_label("x")]}
    errs = _errors(_doc(_label("x"), _carousel("c", _host("p", _press("b", _host("l", inner))))))
    assert [f["kind"] for f in errs if f["kind"] == "duplicate_id"] == ["duplicate_id"]


def test_empty_panel_child_id_is_an_error():
    errs = _errors(_doc(_carousel("c", _host("p", _label("")))))
    assert any(f["kind"] == "missing_field" and "panels[0]" in f["where"] for f in errs)


def test_panel_and_popup_group_ids_stay_local():
    doc = _doc(_label("p"), _carousel("c", _host("p", _label("a"))),
               _press("b", _host("p", _label("z"))))
    assert [f for f in _errors(doc) if f["kind"] == "duplicate_id"] == []


def test_identity_ids_skip_dynamic_slot_content():
    slot = {"type": "group", "id": "deck", "dynamic": "deck", "position": [1, 0],
            "grid": {"columns": 1, "rows": 1}, "children": [_label("placeholder")]}
    doc = _doc(_label("x"), _carousel("c", _host("p", _label("pc"))),
               _press("b", _host("l", _label("lc"))), slot)
    assert set(validate.identity_ids(doc)) == {"x", "c", "pc", "b", "lc", "deck"}


def _deck_layout():
    slot = {"type": "group", "id": "deck", "dynamic": "deck", "position": [1, 0],
            "grid": {"columns": 4, "rows": 4}, "children": []}
    return _doc(_label("x"), _carousel("c", _host("p", _label("pc"))), slot)


def _deck_errors(children):
    findings = carterkit.lint_dynamic_traffic(
        _deck_layout(), observed=[{"msg_type": "deck", "children": children}])
    return [f for f in findings if f["severity"] == "error"]


def test_deck_reusing_a_layout_id_is_an_error():
    for taken in ("x", "pc", "deck"):
        errs = _deck_errors([_label(taken)])
        assert [f["kind"] for f in errs] == ["duplicate_id"], (taken, errs)
        assert "layout" in errs[0]["detail"]


def test_deck_with_fresh_ids_is_clean():
    assert _deck_errors([_label("y")]) == []


def test_deck_duplicate_inside_its_own_panels_is_an_error():
    errs = _deck_errors([_label("y"), _carousel("c2", _host("p", _label("y")))])
    assert [f["kind"] for f in errs] == ["duplicate_id"]
