import pytest
from carterkit.connection import Connection
from carterkit.codegen import generate_service_stub
from carterkit.cli import build_parser

DEVICE = {"url": "wss://relay.example", "channel": "home", "role": "hub",
          "token": "short.lived", "refresh": "-longsecret", "did": "dv_1"}


def test_device_credential_rejects_plaintext_validator():
    with pytest.raises(ValueError):
        Connection.parse({**DEVICE, "validator": "http://evil.example"})


def test_local_connection_has_a_generated_key():
    c = Connection.parse(None)
    assert c.key and len(c.key) >= 16                    # "" today (open relay)


def test_generated_stub_is_not_an_open_relay():
    layout = {"name": "Demo", "version": 1, "tabs": [{"title": "T", "children": [
        {"type": "gauge", "id": "g", "position": [0, 0],
         "sync": [{"method": "meshsocket", "type": "listen", "event": "broadcast",
                   "filter": {"msg_type": "m"}, "valuePath": "v"}]}]}]}
    code = generate_service_stub(layout)
    assert "key=" in code or "token_urlsafe" in code     # bare Hub("demo.json") today
    assert "logging" in code                             # print()s the pairing secret today


def test_relay_subcommand_requires_key_or_insecure():
    p = build_parser()
    args = p.parse_args(["relay"])
    assert hasattr(args, "key") and hasattr(args, "insecure")   # neither exists today
