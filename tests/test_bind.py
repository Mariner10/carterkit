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
