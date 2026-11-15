import json, os, stat
from carterkit import cli, provision
from carterkit.hub import Hub


def _hub_with_peers(clients, studio_id):
    h = Hub({"name": "x", "tabs": []})
    class S:
        sent = []
        async def request(self, t, payload=None, timeout=5.0):
            S.sent.append((t, payload))
            if t == "get_nodes":
                return {"clients": clients}
            if payload.get("type") == "get-device-info":
                return {"ok": True} if payload["target_id"] == studio_id else None
            return {"ok": True}
    h.client._sock = S()
    return h, S


def test_peer_selection_probes_for_studio_socket():
    import asyncio
    # real roster shape: id + name only; the layout socket does not answer studio verbs
    h, S = _hub_with_peers([{"id": "L", "name": "p"}, {"id": "S", "name": "p"}], "S")
    asyncio.run(h.route("get-control-state"))
    assert S.sent[-1][1]["target_id"] == "S"


def test_parser_push_and_add_hub():
    p = cli.build_parser()
    a = p.parse_args(["push", "l.json", "--install", "--via", "studio"])
    assert a.fn is cli._cmd_push and a.install and a.via == "studio"
    b = p.parse_args(["add-hub", "--channel", "c"])
    assert b.fn is cli._cmd_add_hub and b.channel == "c"


def test_write_device_0600_and_summary_hides_secrets(tmp_path):
    cred = {"did": "d1", "channel": "c", "token": "SECRET", "k": "KEY", "role": "hub"}
    path = tmp_path / "device.json"
    provision.write_device(str(path), cred)
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    s = provision.summary({"credential": cred, "key_reuse": "fresh"})
    assert "d1" in s and "SECRET" not in s and "KEY" not in s


def test_provision_polls_until_credential():
    import asyncio
    class H:
        n = 0
        async def route(self, verb, payload=None, timeout=5.0):
            if verb == "provision-device":
                return {"ok": True, "status": "pending", "request_id": "r"}
            H.n += 1
            return {"ok": True, "status": "pending"} if H.n < 2 else {"ok": True, "credential": {"did": "d"}}
    r = asyncio.run(provision.provision(H(), "c", poll=0.01, out=lambda *_: None))
    assert r["credential"]["did"] == "d"
