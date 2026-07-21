"""Tests for connection.py — the one-parser-for-every-artifact story."""

import json

import pytest

from carterkit import Connection
from carterkit.connection import DEFAULT_VALIDATOR


DEVICE_CRED = {
    "url": "wss://relay.example.net", "channel": "tmux", "role": "hub",
    "token": "short.lived.jwt", "refresh": "-longsecret", "did": "dv_abc",
    "k": "AAAA+base64key=",
}


def test_parse_none_is_local():
    c = Connection.parse(None)
    assert c.kind == "local"
    kw = c.client_kwargs()
    assert kw["gateway_url"] == "ws://127.0.0.1:8765"


def test_parse_ws_url_selfhosted_roundtrips_both_sides():
    c = Connection.parse("ws://192.168.1.50:8765", channel="lab", token="key")
    assert c.kind == "selfhosted"
    block = c.layout_block()
    assert block["url"] == "ws://192.168.1.50:8765"
    assert block["identity"]["channel"] == "lab"
    assert block["token"] == "key"            # shared key: symmetric, embeds
    kw = c.client_kwargs(name="my-hub")
    assert kw["gateway_url"] == "ws://192.168.1.50:8765"
    assert kw["token"] == "key" and kw["name"] == "my-hub"


def test_parse_device_credential():
    c = Connection.parse(dict(DEVICE_CRED))
    assert c.kind == "device"
    kw = c.client_kwargs()
    assert kw["device_id"] == "dv_abc"
    assert kw["refresh_token"] == "-longsecret"
    assert kw["validator_url"] == DEFAULT_VALIDATOR
    assert kw["e2ee_key"] == "AAAA+base64key=" and kw["room"] is True
    assert kw["role"] == "hub" and kw["channel"] == "tmux"


def test_device_credential_embedded_validator_wins():
    c = Connection.parse({**DEVICE_CRED, "validator": "https://dev.validator"})
    assert c.client_kwargs()["validator_url"] == "https://dev.validator"


def test_device_token_never_embeds_into_layout():
    c = Connection.parse(dict(DEVICE_CRED))
    block = c.layout_block()
    assert "token" not in block               # the phone joins with its own account
    assert block["url"] == "wss://relay.example.net"
    assert block["mode"] == "room" and block["e2eeKey"] == "AAAA+base64key="


def test_parse_layout_block_and_whole_layout():
    block = {"url": "ws://h:1", "token": "t",
             "identity": {"name": "CAR-TER", "channel": "home", "role": "controller"}}
    c = Connection.parse(block)
    assert c.kind == "selfhosted" and c.token == "t" and c.channel == "home"
    layout = {"name": "X", "version": 1, "tabs": [], "connection": block}
    assert Connection.parse(layout).url == "ws://h:1"


def test_parse_account_block_cannot_serve():
    room = {"mode": "room", "e2eeKey": "kk", "identity": {"channel": "c", "role": "member"}}
    c = Connection.parse(room)
    assert c.kind == "account"
    with pytest.raises(ValueError, match="Add Hub"):
        c.client_kwargs()


def test_parse_file_and_overrides(tmp_path):
    p = tmp_path / "device.json"
    p.write_text(json.dumps(DEVICE_CRED))
    c = Connection.parse(str(p), channel="other")
    assert c.kind == "device" and c.channel == "other"


def test_parse_garbage_raises():
    with pytest.raises(ValueError):
        Connection.parse("not-a-url-or-file")
    with pytest.raises(ValueError):
        Connection.parse({"bogus": 1})
    with pytest.raises(TypeError):
        Connection.parse(42)


def test_qr_json_shape():
    c = Connection.parse("ws://h:1", channel="lab", token="k")
    qr = json.loads(c.qr_json())
    assert qr == {"url": "ws://h:1", "channel": "lab", "role": "controller", "token": "k"}
