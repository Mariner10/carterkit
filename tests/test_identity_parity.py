"""carter-m7s.7 — identity + nesting parity with the app.

The app's CAR-TERTests/IdentityIntegrityTests.swift runs these same documents through
LayoutDecoder: what the kit reports as an error, a strict device decode (wire / import /
join / model) refuses and a disk load repairs with a diagnostic. Keep the fixtures in step.
"""
from pathlib import Path

from carterkit import catalog, validate
from carterkit.buffer import LayoutBuffer, tab_slug
from carterkit.layout import Layout

DOCS = Path(__file__).resolve().parent.parent / "carterkit" / "controldocs"
CAT = catalog.build_catalog(DOCS, include_theme=True)


def _label(cid):
    c = {"type": "label", "text": "x", "position": [0, 0]}
    if cid is not None:
        c["id"] = cid
    return c


def _group(gid, *children):
    return {"type": "group", "id": gid, "position": [0, 0],
            "grid": {"columns": 1, "rows": 1}, "children": list(children)}


def _nested(levels):
    node = _label("leaf")
    for i in range(levels):
        node = _group(f"g{i}", node)
    return node


def _doc(children, tab_extra=None, more_tabs=()):
    tab = {"title": "A", "icon": "star", "grid": {"columns": 4, "rows": 8},
           "children": list(children)}
    tab.update(tab_extra or {})
    return {"name": "t", "version": 1, "tabs": [tab, *more_tabs]}


def _errors(layout):
    return [(f["kind"], f["where"]) for f in validate.validate_layout(layout, CAT)
            if f["severity"] == "error"]


def _kinds(layout):
    return {k for k, _ in _errors(layout)}


def test_duplicate_id_in_a_group_is_an_error():
    assert "duplicate_id" in _kinds(_doc([_label("x"), _group("g", _label("x"))]))


def test_empty_and_missing_ids_are_errors():
    errs = _errors(_doc([_label(""), _label(None), _label("label-1")]))
    assert sum(1 for k, _ in errs if k == "missing_field") == 2


def test_unique_ids_are_clean():
    assert "duplicate_id" not in _kinds(_doc([_label("a"), _group("g", _label("b"))]))


def test_tab_ids_must_be_unique_and_non_empty():
    second = {"id": "home", "title": "B", "icon": "star",
              "grid": {"columns": 4, "rows": 8}, "children": []}
    assert "duplicate_id" in _kinds(_doc([], {"id": "home"}, [second]))
    assert "missing_field" in _kinds(_doc([], {"id": ""}))
    assert not _errors(_doc([], {"id": "home"}))


def test_nesting_limit_matches_the_app():
    assert validate.MAX_DEPTH == 8          # LayoutLimits.maxNestingDepth
    assert "too_deep" not in _kinds(_doc([_nested(validate.MAX_DEPTH)]))
    assert "too_deep" in _kinds(_doc([_nested(validate.MAX_DEPTH + 1)]))


def test_builders_emit_stable_unique_tab_ids():
    assert tab_slug("Living Room", ()) == "living-room"
    assert tab_slug("Living Room", {"living-room"}) == "living-room-2"
    assert tab_slug("!!!", ()) == "tab"
    buf = LayoutBuffer.blank()
    buf.add_tab("Main")
    buf.add_tab("Main")
    assert [t["id"] for t in buf.tabs] == ["tab-1", "main", "main-2"]

    ui = Layout("Plants")
    ui.tab("Garden")
    ui.tab("Garden")
    ids = [t["id"] for t in ui.layout["tabs"]]
    assert ids == ["garden", "garden-2"]
    assert not _kinds(ui.layout) & {"duplicate_id", "missing_field"}


def test_name_is_a_known_field_on_controls_and_groups():
    # App-minted opaque ids + a readable `name` (Carter 2026-09-26): the kit accepts the
    # editor's output without unknown-field warnings, and slug ids stay valid.
    named = dict(_label("c_7f3a9e"), name="Water level")
    group = dict(_group("g_0a1b2c", _label("pump-speed")), name="Pump")
    findings = validate.validate_layout(_doc([named, group]), CAT)
    assert not [f for f in findings if f["kind"] in ("unknown_field", "duplicate_id")]

    ui = Layout("Plants")
    ui.tab("Garden")
    with ui.group("Pump", name="Pump box"):
        ui.label("Level", name="Water level")
    g = ui.layout["tabs"][0]["children"][0]
    assert g["name"] == "Pump box" and g["children"][0]["name"] == "Water level"
    assert "name" not in ui.layout["tabs"][0]  # absent unless asked for
