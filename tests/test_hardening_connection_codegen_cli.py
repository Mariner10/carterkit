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


def test_local_relay_keyless_requires_insecure():
    import asyncio
    import socket
    import warnings
    from carterkit.relay import LocalRelay
    with pytest.raises(ValueError):
        LocalRelay(key="")                                   # open relay without opting in
    with pytest.raises(ValueError):
        LocalRelay(key="", host="0.0.0.0")                   # ...and never on a LAN bind
    assert len(LocalRelay().key) >= 24                       # default: a generated key
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    async def run():
        # An explicit insecure relay starts without the meshsocket "open server" warning.
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            async with LocalRelay(port=port, key="", insecure=True) as r:
                assert r.key == "" and r.insecure
    asyncio.run(run())


def test_hub_passes_e2ee_and_backpressure_settings_to_client():
    from carterkit.hub import Hub
    hub = Hub(None, None, port=18999)                      # defaults
    assert hub.client.strict_e2ee is True
    hub = Hub(None, None, port=18999, strict_e2ee=False, max_inflight=4, rate_per_type=5)
    assert hub.client.strict_e2ee is False
    assert hub.client._inflight._value == 4 and hub.client._rate_per_type == 5.0


def test_local_qr_is_honest_about_loopback():
    import json
    from carterkit.hub import Hub
    loop = Hub(None, None, port=18999)                     # loopback-bound relay
    assert json.loads(loop.qr_json())["url"] == "ws://127.0.0.1:18999"
    assert loop.connection.layout_block()["url"] == "ws://127.0.0.1:18999"
    lan = Hub(None, None, port=18999, host="0.0.0.0")
    assert "127.0.0.1" not in json.loads(lan.qr_json())["url"] or lan.connection.app_url().startswith("ws://")
    assert not lan.connection.is_loopback_relay()
