"""Soft size tiers (aif-cr7ip): advisory warnings below the hard caps."""
from carterkit.validate import soft_tier_findings


def _kinds(layout):
    return [(f["severity"], f["kind"]) for f in soft_tier_findings(layout)]


def _lay(children):
    return {"version": 1, "tabs": [{"title": "T", "icon": "x", "children": children}]}


def _labels(n):
    return [{"type": "label", "id": f"l{i}"} for i in range(n)]


def _nest(levels):
    node = {"type": "label", "id": "leaf"}
    for i in range(levels):
        node = {"type": "group", "id": f"g{i}", "children": [node]}
    return node


def test_small_layout_clean():
    assert _kinds(_lay(_labels(5))) == []


def test_heavy_boundary():
    assert _kinds(_lay(_labels(150))) == []
    assert _kinds(_lay(_labels(151))) == [("warn", "tab_heavy")]


def test_weights():
    assert _kinds(_lay([{"type": "gauge"}] * 50)) == []
    assert _kinds(_lay([{"type": "gauge"}] * 50 + [{"type": "label"}])) == [("warn", "tab_heavy")]
    assert _kinds(_lay([{"type": "map"}] * 75)) == []


def test_very_heavy():
    assert _kinds(_lay(_labels(400))) == [("warn", "tab_heavy")]
    assert _kinds(_lay(_labels(401))) == [("warn", "tab_very_heavy")]


def test_canvas_items_count():
    cc = {"type": "canvas", "canvasConfig": {"items": [{"control": {"type": "label"}}] * 151}}
    assert _kinds(_lay([cc])) == [("warn", "tab_heavy")]


def test_nesting():
    assert _kinds(_lay([_nest(4)])) == []
    assert _kinds(_lay([_nest(5)])) == [("warn", "deep_nesting")]


def test_document_too_large():
    big = _lay([{"type": "label", "text": "x" * 1000} for _ in range(2200)])
    assert ("warn", "document_too_large") in _kinds(big)


def test_where_path():
    f = soft_tier_findings(_lay(_labels(151)))[0]
    assert f["where"] == "$.tabs[0]"
