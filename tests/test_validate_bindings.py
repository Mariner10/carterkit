"""Tests for the richer sync/action binding validation."""

import carterkit
from carterkit import validate, build, bind

CAT = carterkit.controls(include_theme=True)


def _layout(children):
    return {"name": "T", "version": 1,
            "tabs": [{"title": "Main", "icon": "house.fill",
                      "grid": {"columns": 4, "rows": 4}, "children": children}]}


def _kinds(findings):
    return {f["kind"] for f in findings}


def test_action_missing_event_is_error():
    lay = _layout([{"type": "button", "id": "b", "position": [0, 0],
                    "action": {"method": "meshsocket", "mode": "broadcast"}}])
    findings = validate.validate_layout(lay, CAT)
    assert "bad_action" in _kinds(findings)
    assert any(f["severity"] == "error" for f in findings if f["kind"] == "bad_action")


def test_sync_missing_valuepath_is_warning():
    lay = _layout([{"type": "gauge", "id": "g", "position": [0, 0], "min": 0, "max": 100,
                    "sync": [{"method": "meshsocket", "type": "listen", "event": "broadcast"}]}])
    bs = [f for f in validate.validate_layout(lay, CAT) if f["kind"] == "bad_sync"]
    assert bs and bs[0]["severity"] == "warn"


def test_helper_built_bindings_are_clean():
    lay = _layout([
        build.button(id="b", position=[0, 0], action=bind.action("go")),
        build.gauge(id="g", position=[0, 1], min=0, max=100, sync=[bind.listen("g")]),
    ])
    kinds = _kinds(validate.validate_layout(lay, CAT))
    assert "bad_action" not in kinds and "bad_sync" not in kinds
