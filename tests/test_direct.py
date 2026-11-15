"""HubDirect: signaling handlers, rpc bridge, sidecar supervision (fake sidecar, no Go)."""
import asyncio
import json
import os
import sys

import pytest

import carterkit.direct as direct
from carterkit import Hub

FAKE = os.path.join(os.path.dirname(__file__), "fake_sidecar.py")


@pytest.fixture
def fake_bin(tmp_path, monkeypatch):
    shim = tmp_path / "carter-direct"
    shim.write_text(f"#!/bin/sh\nexec {sys.executable} {FAKE}\n")
    shim.chmod(0o755)
    log = tmp_path / "log.jsonl"
    monkeypatch.setenv("CARTERKIT_DIRECT_BIN", str(shim))
    monkeypatch.setenv("FAKE_LOG", str(log))
    monkeypatch.setattr(direct, "BACKOFF_MIN", 0.05)
    return log


def _logs(log):
    return [json.loads(l) for l in log.read_text().splitlines()] if log.exists() else []


async def _until(pred, t=5.0):
    end = asyncio.get_running_loop().time() + t
    while not pred():
        assert asyncio.get_running_loop().time() < end, "timeout"
        await asyncio.sleep(0.02)


def _hub():
    return Hub()


async def _offer(hub, session="s1", sender="phone", **kw):
    ctx = {"_relayFrom": sender} if sender else {}
    return await hub.client.dispatch_request(
        "direct_offer", {"msg_type": "direct_offer", "v": 1, "session": session, "sdp": "offer",
                         "want": {"video": [], "data": True}, **kw}, ctx, sealed=False)


async def _inject_rpc(hub, log, session, rid, mtype, payload=None):
    hdr = {"id": rid, "type": mtype, "payload": payload or {}}
    await hub._dx()["sidecar"].send({"op": "inject", "frame": {
        "op": "rpc_request", "session": session, "header": hdr}})


def test_offer_answer_round_trip(fake_bin):
    async def go():
        hub = _hub()
        await hub._direct_start()
        try:
            r = await _offer(hub)
            assert r == {"msg_type": "direct_answer", "session": "s1", "sdp": "fake-answer-s1"}
            await _until(lambda: hub.direct_sessions["s1"]["state"] == "connected")
        finally:
            await hub._direct_stop()
    asyncio.run(go())


def test_offer_without_relay_sender_is_denied(fake_bin):
    async def go():
        hub = _hub()
        await hub._direct_start()
        try:
            assert (await _offer(hub, sender=None))["error"] == "denied"
            r = await hub.client.dispatch_request(
                "direct_offer", {"session": "s", "sdp": "x"}, {"_from": "victim"}, sealed=False)
            assert r["error"] == "denied"
        finally:
            await hub._direct_stop()
    asyncio.run(go())


def test_rpc_reaches_same_handler(fake_bin):
    async def go():
        hub = _hub()
        hub.client.on("audio_read", lambda d: {"data": b"\x00" * 131072})
        await hub._direct_start()
        try:
            await _offer(hub)
            await _inject_rpc(hub, fake_bin, "s1", "r1", "audio_read")
            await _until(lambda: any(e["h"]["op"] == "rpc_reply" for e in _logs(fake_bin)))
            e = [e for e in _logs(fake_bin) if e["h"]["op"] == "rpc_reply"][0]
            assert e["n"] == 131072
            assert e["h"]["header"]["body"] == "data"
            assert e["h"]["header"]["reply_to"] == "r1"
        finally:
            await hub._direct_stop()
    asyncio.run(go())


def test_rpc_identity_is_bound_peer(fake_bin):
    seen = {}

    async def go():
        hub = _hub()
        hub.client.on("who", lambda d: seen.update(d) or {"ok": True})
        await hub._direct_start()
        try:
            await _offer(hub, sender="phoneA")
            await hub._dx()["sidecar"].send({"op": "inject", "frame": {
                "op": "rpc_request", "session": "s1",
                "header": {"id": "r", "type": "who",
                           "payload": {"_relayFrom": "evil", "_from": "evil"}}}})
            await _until(lambda: seen)
            assert seen["_relayFrom"] == "phoneA" and seen["_from"] == "phoneA"
        finally:
            await hub._direct_stop()
    asyncio.run(go())


def test_bytes_data_base64_over_meshsocket():
    import base64
    hub = _hub()
    hub.client._session = None
    hub.client.on("audio_read", lambda d: {"data": b"\x01\x02"})
    out = asyncio.run(hub.client._sock._handlers["audio_read"]({"msg_type": "audio_read"})
                      if hasattr(hub.client._sock, "_handlers") else _call(hub))
    assert out["data"] == base64.b64encode(b"\x01\x02").decode()


async def _call(hub):
    return await hub.client.dispatch_request("audio_read", {}, {}, sealed=True)


def test_direct_hello_advertises(fake_bin, monkeypatch):
    async def go():
        hub = _hub()
        hub.camera("printer", "http://x")
        await hub._direct_start()
        try:
            r = await hub.client.dispatch_request("direct_hello", {"v": 1}, {"_relayFrom": "p"},
                                                  sealed=False)
            assert r == {"v": 1, "data": True,
                         "video": [{"id": "printer", "name": "printer", "status": "idle"}]}
        finally:
            await hub._direct_stop()
        monkeypatch.setenv("CARTERKIT_DIRECT_BIN", "/nonexistent")
        hub2 = _hub()
        await hub2._direct_start()
        assert hub2.direct_capabilities() is None
        assert await hub2.client.dispatch_request("direct_hello", {}, {}, sealed=False) is None
    asyncio.run(go())


def test_sidecar_crash_restarts_and_fails_sessions(fake_bin):
    async def go():
        hub = _hub()
        await hub._direct_start()
        try:
            await _offer(hub)
            await _until(lambda: hub.direct_sessions["s1"]["state"] == "connected")
            old = hub._dx()["sidecar"].proc
            old.kill()
            await _until(lambda: hub.direct_sessions["s1"]["state"] == "failed")
            await _until(lambda: hub._dx()["sidecar"].proc not in (None, old))
            r = await _offer(hub, session="s2")
            assert r["sdp"] == "fake-answer-s2"
            cfgs = [e for e in _logs(fake_bin) if e["h"]["op"] == "config"]
            assert len(cfgs) >= 2 and len({e["pid"] for e in cfgs}) >= 2
        finally:
            await hub._direct_stop()
    asyncio.run(go())
