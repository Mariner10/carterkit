"""carter-upj2 / aif-eyfa — the app (CAR-TER LayoutSanitizer) refuses a control or group that
sits inside a `children` array (tab or group) with no `position`: the kit reports an
error finding (kind "missing_field") at the child's path, mentioning 'position'."""
import carterkit


def _layout(children, grid=None):
    return {"name": "L", "version": 1, "tabs": [{"title": "A", "icon": "star",
                                                 "grid": grid or {"columns": 4, "rows": 4},
                                                 "children": children}]}


def _group(gid, children, position=True):
    g = {"type": "group", "id": gid, "span": [2, 2],
         "grid": {"columns": 2, "rows": 2}, "children": children}
    if position:
        g["position"] = [0, 0]
    return g


def _label(cid, position=True):
    c = {"type": "label", "id": cid, "span": [1, 1], "text": "hi"}
    if position:
        c["position"] = [0, 0]
    return c


def _missing(findings):
    return [f for f in findings if f["kind"] == "missing_field" and "position" in f["detail"]]


def test_control_without_position_in_tab_children_is_an_error():
    layout = _layout([_label("g1", position=False)])
    found = _missing(carterkit.validate_layout(layout))
    assert len(found) == 1
    assert found[0]["severity"] == "error"
    assert "g1" in found[0]["where"]


def test_group_without_position_in_tab_children_is_an_error():
    layout = _layout([_group("grp", [_label("c")], position=False)])
    found = _missing(carterkit.validate_layout(layout))
    assert len(found) == 1
    assert "grp" in found[0]["where"]


def test_control_without_position_inside_a_group_is_an_error():
    layout = _layout([_group("grp", [_label("c1", position=False)])])
    found = _missing(carterkit.validate_layout(layout))
    assert len(found) == 1
    assert "c1" in found[0]["where"]
    assert "grp" in found[0]["where"]


def test_fully_positioned_layout_is_clean():
    layout = _layout([_group("grp", [_label("c1")]), _label("t1")])
    assert _missing(carterkit.validate_layout(layout)) == []


def test_each_missing_child_is_reported_once():
    layout = _layout([_label(i, position=False) for i in ("a", "b", "c")])
    found = _missing(carterkit.validate_layout(layout))
    assert len(found) == 3
    for i in ("a", "b", "c"):
        assert any(i in f["where"] for f in found)


def test_sectioned_placement_supplies_position():
    layout = _layout([_label("g1", position=False)])
    layout["schemaVersion"] = 2
    layout["placements"] = {"g1": {"position": [0, 0]}}
    assert _missing(carterkit.validate_layout(layout)) == []
