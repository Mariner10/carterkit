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
        build.button(id="b", position=[0, 0], action=bind.command("go")),
        build.gauge(id="g", position=[0, 1], min=0, max=100, sync=[bind.listen("g")]),
    ])
    kinds = _kinds(validate.validate_layout(lay, CAT))
    assert "bad_action" not in kinds and "bad_sync" not in kinds
    assert "dead_action" not in kinds


def test_custom_event_action_is_dead_error():
    # the relay forwards only its own verbs: event "go" never arrives anywhere
    lay = _layout([{"type": "button", "id": "b", "position": [0, 0],
                    "action": {"method": "meshsocket", "mode": "broadcast", "event": "go"}}])
    dead = [f for f in validate.validate_layout(lay, CAT) if f["kind"] == "dead_action"]
    assert dead and dead[0]["severity"] == "error"
    assert "silently drops" in dead[0]["detail"]


def test_relay_service_verbs_are_allowed():
    lay = _layout([{"type": "button", "id": "b", "position": [0, 0],
                    "action": {"method": "meshsocket", "mode": "request", "event": "ping"}}])
    assert "dead_action" not in _kinds(validate.validate_layout(lay, CAT))


def test_broadcast_request_mode_request_warns():
    lay = _layout([{"type": "button", "id": "b", "position": [0, 0],
                    "action": {"method": "meshsocket", "mode": "request",
                               "event": "broadcast_request",
                               "payload": {"msg_type": "go"}}}])
    fs = [f for f in validate.validate_layout(lay, CAT) if f["kind"] == "bad_action"]
    assert fs and fs[0]["severity"] == "warn" and "no" in fs[0]["detail"]


def test_broadcast_request_without_msg_type_warns():
    lay = _layout([{"type": "button", "id": "b", "position": [0, 0],
                    "action": bind.action("broadcast_request", payload={"x": 1})}])
    fs = [f for f in validate.validate_layout(lay, CAT) if f["kind"] == "bad_action"]
    assert fs and "msg_type" in fs[0]["detail"]


def test_route_msg_needs_target_id():
    lay = _layout([{"type": "button", "id": "b", "position": [0, 0],
                    "action": {"method": "meshsocket", "mode": "request",
                               "event": "route_msg",
                               "payload": {"target_name": "hub", "type": "go"}}}])
    fs = [f for f in validate.validate_layout(lay, CAT) if f["kind"] == "bad_action"]
    assert fs and fs[0]["severity"] == "error" and "target_id" in fs[0]["detail"]


def test_route_msg_noreply_needs_target_name():
    lay = _layout([{"type": "button", "id": "b", "position": [0, 0],
                    "action": {"method": "meshsocket", "mode": "broadcast",
                               "event": "route_msg_noreply",
                               "payload": {"type": "go"}}}])
    fs = [f for f in validate.validate_layout(lay, CAT) if f["kind"] == "bad_action"]
    assert fs and fs[0]["severity"] == "error" and "target_name" in fs[0]["detail"]
