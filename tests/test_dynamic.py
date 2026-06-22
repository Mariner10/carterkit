"""Tests for the dynamic-group traffic lint."""

import carterkit
from carterkit import Layout, Fragment, dynamic


def _layout_with_dynamic(event="player_state"):
    with Layout("Player", cols=4, rows=4) as ui:
        ui.group("Now Playing", span=(3, 4), cols=4, rows=3, dynamic=event)
    return ui.layout


def test_dynamic_groups_discovery():
    groups = dynamic.dynamic_groups(_layout_with_dynamic())
    assert len(groups) == 1
    g = groups[0]
    assert g["event"] == "player_state" and g["columns"] == 4 and g["rows"] == 3


def test_event_never_seen_warns():
    lay = _layout_with_dynamic()
    findings = carterkit.lint_dynamic_traffic(lay, observed=[{"msg_type": "other", "x": 1}])
    kinds = {f["kind"] for f in findings}
    assert "event_never_seen" in kinds


def test_missing_children_array_errors():
    lay = _layout_with_dynamic()
    findings = carterkit.lint_dynamic_traffic(lay, observed=[{"msg_type": "player_state"}])
    errs = [f for f in findings if f["severity"] == "error"]
    assert any(f["kind"] == "missing_children" for f in errs)


def test_valid_fragment_payload_is_clean():
    lay = _layout_with_dynamic()
    frag = Fragment(cols=4, rows=3)
    frag.label("title", text="Song", span=(1, 4))
    frag.button("play", label="Play", send="play")
    findings = carterkit.lint_dynamic_traffic(lay, observed=[frag.payload("player_state")])
    assert [f for f in findings if f["severity"] == "error"] == []
    # the listened event was seen, so no event_never_seen warning either
    assert not any(f["kind"] == "event_never_seen" for f in findings)


def test_invalid_injected_child_is_flagged():
    lay = _layout_with_dynamic()
    bad = {"msg_type": "player_state", "children": [
        {"type": "nonsense", "id": "x", "position": [0, 0]}]}
    findings = carterkit.lint_dynamic_traffic(lay, observed=[bad])
    assert any(f["kind"] == "unknown_type" for f in findings)


def test_overflowing_child_placement_flagged():
    lay = _layout_with_dynamic()                       # group grid is 4x3
    over = {"msg_type": "player_state", "children": [
        {"type": "label", "id": "x", "text": "hi", "position": [5, 0]}]}
    findings = carterkit.lint_dynamic_traffic(lay, observed=[over])
    assert any(f["kind"] == "out_of_bounds" for f in findings)


def test_orphan_payload_warns():
    lay = _layout_with_dynamic()
    orphan = {"msg_type": "typo_state", "children": [
        {"type": "label", "id": "x", "text": "hi", "position": [0, 0]}]}
    findings = carterkit.lint_dynamic_traffic(lay, observed=[
        {"msg_type": "player_state", "children": []}, orphan])
    assert any(f["kind"] == "orphan_payload" for f in findings)
