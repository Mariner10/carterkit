"""Tests for grid.py — occupancy, slot finding, placement validation, rendering."""

from carterkit import grid


def test_occupancy_counts_spanned_cells():
    children = [
        {"id": "a", "position": [0, 0], "span": [2, 2]},
        {"id": "b", "position": [0, 2]},  # default span [1,1]
    ]
    occ = grid.occupancy(children)
    assert len(occ) == 5  # 4 for a, 1 for b
    assert occ[(0, 0)] == "a" and occ[(1, 1)] == "a"
    assert occ[(0, 2)] == "b"


def test_find_slot_row_major_first_free():
    children = [{"id": "a", "position": [0, 0], "span": [1, 2]}]
    # Next free 1x1 in a 4-col grid is [0, 2].
    assert grid.find_slot(children, columns=4, rows=4, span=[1, 1]) == [0, 2]


def test_find_slot_respects_span_and_bounds():
    children = [{"id": "a", "position": [0, 0], "span": [1, 3]}]
    # A 1x2 block can't fit on row 0 (only col 3 free) -> goes to row 1.
    assert grid.find_slot(children, columns=4, rows=4, span=[1, 2]) == [1, 0]


def test_find_slot_returns_none_when_full():
    children = [{"id": "a", "position": [0, 0], "span": [2, 2]}]
    assert grid.find_slot(children, columns=2, rows=2, span=[1, 1]) is None


def test_validate_detects_overlap():
    children = [
        {"id": "a", "position": [0, 0], "span": [1, 2]},
        {"id": "b", "position": [0, 1]},
    ]
    issues = grid.validate_placement(children, columns=4, rows=4)
    kinds = {i["kind"] for i in issues}
    assert "overlap" in kinds
    overlap = next(i for i in issues if i["kind"] == "overlap")
    assert sorted(overlap["ids"]) == ["a", "b"]


def test_validate_detects_out_of_bounds():
    children = [{"id": "a", "position": [3, 3], "span": [2, 2]}]
    issues = grid.validate_placement(children, columns=4, rows=4)
    assert any(i["kind"] == "out_of_bounds" and i["id"] == "a" for i in issues)


def test_validate_clean_layout_has_no_issues():
    children = [
        {"id": "a", "position": [0, 0], "span": [1, 1]},
        {"id": "b", "position": [0, 1], "span": [1, 1]},
    ]
    assert grid.validate_placement(children, columns=4, rows=4) == []


def test_render_grid_shows_ids_and_free_count():
    children = [{"id": "battery", "position": [0, 0], "span": [1, 2]}]
    out = grid.render_grid(children, columns=4, rows=2)
    assert "batter" in out  # truncated id token
    assert "·" in out       # empty cells
    assert "6 free" in out  # 8 cells - 2 occupied


def test_group_and_tab_scale_kwarg():
    import pytest
    from carterkit import Layout
    ui = Layout("t")
    with ui.group("A", scale=0.8) as g:
        pass
    with ui.group("B", scale="auto"):
        pass
    ui.group("C")
    ui.tab("One")
    ui.tab("Two", scale=1.2)
    groups = {c.get("label"): c for c in ui._buf.tabs[0]["children"] if c.get("type") == "group"}
    assert groups["A"]["grid"]["scale"] == 0.8
    assert groups["B"]["grid"]["scale"] == "auto"
    assert "scale" not in groups["C"]["grid"]
    assert ui._buf.tabs[1]["grid"]["scale"] == 1.2
    with pytest.raises(ValueError):
        ui.group("D", scale=2.0)
