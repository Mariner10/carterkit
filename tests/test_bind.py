"""Tests for bind.py — sync/action/connection helper shapes."""

import pytest

from carterkit import bind


def test_listen_basic():
    assert bind.listen("cpu") == {
        "method": "meshsocket", "type": "listen", "event": "broadcast", "valuePath": "cpu"}


def test_listen_with_filter_and_event():
    s = bind.listen("battery", event="metrics", filter={"msg_type": "telemetry"})
    assert s["event"] == "metrics"
    assert s["filter"] == {"msg_type": "telemetry"}
    assert s["valuePath"] == "battery"


def test_action_broadcast_default():
    assert bind.action("refresh") == {
        "method": "meshsocket", "mode": "broadcast", "event": "refresh"}


def test_action_request_with_payload():
    a = bind.action("set_power", payload={"state": "{{value}}"}, mode="request")
    assert a["mode"] == "request"
    assert a["payload"] == {"state": "{{value}}"}


def test_action_rejects_bad_mode():
    with pytest.raises(ValueError):
        bind.action("x", mode="nope")


def test_connection():
    c = bind.connection("ws://h:8765", channel="lab", token="t")
    assert c["url"] == "ws://h:8765"
    assert c["identity"] == {"name": "CAR-TER", "channel": "lab", "role": "controller"}
    assert c["token"] == "t"


def test_command_default_payload_and_msg_type():
    assert bind.command("refresh") == {
        "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request",
        "payload": {"value": "{{value}}", "msg_type": "refresh"}}


def test_command_custom_payload_keeps_name():
    a = bind.command("play", payload={"id": "t1", "msg_type": "hijack"})
    assert a["payload"] == {"id": "t1", "msg_type": "play"}   # the name always wins


def test_sugar_request_true_raises_with_guidance():
    import pytest
    from carterkit import Layout
    with Layout("X", cols=4, rows=4) as ui:
        with pytest.raises(ValueError, match="round-trip"):
            ui.button("b", send="go", request=True)


def test_sugar_wire_verb_passes_through():
    from carterkit import Layout
    with Layout("X", cols=4, rows=4) as ui:
        b = ui.button("b", send="route_msg_noreply",
                      payload={"target_name": "player", "type": "cmd", "payload": {}})
    assert b.ref["action"]["event"] == "route_msg_noreply"
    assert b.ref["action"]["payload"]["target_name"] == "player"
