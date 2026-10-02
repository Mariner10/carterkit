"""Tests for the dynamic-group traffic lint."""

import json

import pytest

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


# carter-mmpe — dynamic tab payloads get the same fragment identity lint as decks.
def test_dynamic_tab_payload_id_collision_is_an_error():
    from carterkit import Layout
    from carterkit.dynamic import lint_dynamic_traffic, fragment_id_findings
    with Layout("T", cols=2, rows=2) as ui:
        with ui.tab("Main"):
            ui.label("status", text="x")
    ui.dynamic_tab("extra")
    lay = ui.layout
    tab = {"msg_type": "extra", "title": "Extra", "icon": "star",
           "grid": {"columns": 2, "rows": 2},
           "children": [{"type": "label", "id": "status", "position": [0, 0]}]}
    kinds = [(f["kind"], f["severity"]) for f in lint_dynamic_traffic(lay, [tab])]
    assert ("duplicate_id", "error") in kinds
    assert ("orphan_payload", "warn") not in kinds
    assert fragment_id_findings([{"type": "label", "id": "fresh", "position": [0, 0]}], lay) == []


# ── chunk_deck: the {rev, part, parts} wire contract (group-def.md → Chunked decks) ──
from carterkit.dynamic import chunk_deck  # noqa: E402


def _kids(n, pad=300):
    return [{"type": "label", "id": f"k{i}", "position": [0, 0], "text": "y" * pad} for i in range(n)]


def test_chunk_deck_small_deck_is_one_plain_frame():
    frames = chunk_deck("ev", _kids(2))
    assert frames == [{"msg_type": "ev", "children": _kids(2)}]


def test_chunk_deck_parts_are_one_based_and_reassemble_in_order():
    kids = _kids(12)
    frames = chunk_deck("ev", kids, max_bytes=1200)
    n = len(frames)
    assert n > 1
    for i, f in enumerate(frames, start=1):
        assert f["msg_type"] == "ev" and f["part"] == i and f["parts"] == n
        assert len(f["rev"].encode()) <= 256
        assert len(json.dumps(f).encode()) <= 1200
    assert [c for f in frames for c in f["children"]] == kids


def test_chunk_deck_rev_is_stable_for_the_same_deck_and_overridable():
    a = chunk_deck("ev", _kids(12), max_bytes=1200)
    b = chunk_deck("ev", _kids(12), max_bytes=1200)
    assert a[0]["rev"] == b[0]["rev"]
    c = chunk_deck("ev", _kids(12), max_bytes=1200, rev="r7")
    assert {f["rev"] for f in c} == {"r7"}


def test_chunk_deck_refuses_what_the_app_would_drop():
    with pytest.raises(ValueError, match="frame budget"):
        chunk_deck("ev", _kids(2, pad=5000), max_bytes=1200)
    with pytest.raises(ValueError, match="at most 64"):
        chunk_deck("ev", _kids(70, pad=900), max_bytes=1200)
    with pytest.raises(ValueError, match="256"):
        chunk_deck("ev", _kids(12), max_bytes=1200, rev="r" * 300)
