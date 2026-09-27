"""Tests for pager.py — the fail-closed AgentPager daemon core (phase 0).

No network: notify is a fake (or a real Hub with no validator, which raises)."""

import asyncio
import json
import os
import shutil
import stat
import tempfile
import time

import pytest

from carterkit import Layout
from carterkit.pager import AgentPager, PendingStore, ask_via_socket


class FakeHub:
    def __init__(self, notify_exc=None):
        self.notifies = []
        self.broadcasts = []
        self.notif_handler = None
        self.handlers = {}
        self.notify_exc = notify_exc

    async def notify(self, title, body, **kw):
        self.notifies.append({"title": title, "body": body, **kw})
        if self.notify_exc is not None:
            raise self.notify_exc

    def on_notif_action(self, fn):
        self.notif_handler = fn

    def on(self, name, fn):
        self.handlers.setdefault(name, []).append(fn)

    async def broadcast(self, msg_type, data):
        self.broadcasts.append((msg_type, data))

    # what the app would send
    def tap(self, notif_id, action_id):
        return self.notif_handler({"msg_type": "notif_action", "notifId": notif_id,
                                   "actionId": action_id, "channel": "agents"})

    def press(self, decision, req):
        out = [fn({"msg_type": "action", "op": "pager_decide", "decision": decision,
                   "req": req}) for fn in self.handlers["action"]]
        return out[-1]


@pytest.fixture
def short_dir():
    # AF_UNIX paths must stay < ~104 bytes on macOS; pytest's tmp_path is too long.
    d = tempfile.mkdtemp(prefix="pg", dir="/tmp")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _pager(d, hub=None, **kw):
    hub = hub or FakeHub()
    kw.setdefault("timeout", 30)
    p = AgentPager(hub, store_path=os.path.join(d, "st", "pending.json"),
                   socket_path=os.path.join(d, "p.sock"), **kw)
    return p, hub


async def _settle():
    for _ in range(5):
        await asyncio.sleep(0)


async def _active(pager, agent):
    """ask() in a task; return (task, nonce). The nonce is captured at submit
    time, so a loaded machine can't race the test against the deadline."""
    reqs, orig = [], pager.submit

    def spy(*a, **k):
        reqs.append(orig(*a, **k))
        return reqs[-1]
    pager.submit = spy
    try:
        task = asyncio.ensure_future(pager.ask(agent, "Bash", "terraform apply"))
        await _settle()
    finally:
        pager.submit = orig
    return task, reqs[0].nonce


def test_approve_tap_allows_and_pages_with_nonce(short_dir):
    async def run():
        p, hub = _pager(short_dir)
        await p.start(serve_socket=False)
        task, nonce = await _active(p, "claude %3")
        n = hub.notifies[0]
        assert n["notif_id"] == nonce
        assert n["interruption"] == "time-sensitive"
        assert n["actions"]["approve"] == {"title": "Approve", "destructive": True,
                                           "authentication_required": True}
        assert "deny" in n["actions"]
        assert n["body"].startswith("Bash: terraform apply")
        assert hub.tap(nonce, "approve") == "allowed"
        assert await task == "allow"
        assert p.pending() == []
        assert p.audit[-1]["decision"] == "allow"
        assert p.audit[-1]["source"] == "notification"
    asyncio.run(run())


def test_deny_tap_and_in_app_decisions(short_dir):
    async def run():
        p, hub = _pager(short_dir)
        await p.start(serve_socket=False)
        task, nonce = await _active(p, "a")
        assert hub.tap(nonce, "deny") == "denied"
        assert await task == "deny"
        task, nonce = await _active(p, "a")
        assert hub.press("approve", nonce) == "allowed"
        assert await task == "allow"
        task, nonce = await _active(p, "a")
        assert hub.press("deny", nonce) == "denied"
        assert await task == "deny"
        # other `action` ops belong to other controls: untouched
        assert hub.handlers["action"][0]({"msg_type": "action", "op": "other"}) is None
    asyncio.run(run())


def test_deadline_denies_and_late_tap_is_expired(short_dir):
    async def run():
        p, hub = _pager(short_dir, timeout=0.05)
        await p.start(serve_socket=False)
        task, nonce = await _active(p, "a")
        assert await asyncio.wait_for(task, 10) == "deny"
        assert "timed out" in p.audit[-1]["reason"]
        assert hub.tap(nonce, "approve") == "expired"
        assert hub.press("approve", nonce) == "expired"
        assert all(e["decision"] == "deny" for e in p.audit)
        await _settle()
        assert any(d.get("event") == "expired" for _, d in hub.broadcasts)
    asyncio.run(run())


def test_deadline_passed_before_timer_fires_never_allows(short_dir):
    async def run():
        p, hub = _pager(short_dir)
        await p.start(serve_socket=False)
        task, nonce = await _active(p, "a")
        p._active[nonce].deadline = time.time() - 1   # timer hasn't fired yet
        assert hub.tap(nonce, "approve") == "expired"
        assert await task == "deny"
    asyncio.run(run())


def test_tap_after_resolution_is_expired(short_dir):
    async def run():
        p, hub = _pager(short_dir)
        await p.start(serve_socket=False)
        task, nonce = await _active(p, "a")
        hub.tap(nonce, "deny")
        assert await task == "deny"
        assert hub.tap(nonce, "approve") == "expired"
    asyncio.run(run())


@pytest.mark.parametrize("frame", [
    {"actionId": "approve"},                                   # missing nonce
    {"notifId": True, "actionId": "approve"},                  # old-build literal true
    {"notifId": None, "actionId": "approve"},
    {"notifId": ["x"], "actionId": "approve"},
    {"notifId": "pg-unknown", "actionId": "approve"},          # unknown nonce
    {"notifId": "NONCE", "actionId": "Approve"},               # unknown actionId
    {"notifId": "NONCE", "actionId": "allow"},
    {"notifId": "NONCE", "actionId": {"x": 1}},
    {"notifId": "NONCE"},
])
def test_malformed_taps_never_allow(short_dir, frame):
    async def run():
        p, hub = _pager(short_dir)
        await p.start(serve_socket=False)
        task, nonce = await _active(p, "a")
        f = {k: (nonce if v == "NONCE" else v) for k, v in frame.items()}
        assert p.handle_notif_action({"msg_type": "notif_action", **f}) == "ignored"
        assert not task.done()
        p._on_deadline(p._active[nonce])               # the timer firing
        assert await asyncio.wait_for(task, 10) == "deny"
    asyncio.run(run())


@pytest.mark.parametrize("req,decision", [
    (True, "approve"), (None, "approve"), ("pg-nope", "approve"),
    ("NONCE", "yes"), ("NONCE", None), ("NONCE", 1),
])
def test_malformed_in_app_decisions_never_allow(short_dir, req, decision):
    async def run():
        p, hub = _pager(short_dir)
        await p.start(serve_socket=False)
        task, nonce = await _active(p, "a")
        assert hub.press(decision, nonce if req == "NONCE" else req) == "ignored"
        assert not task.done()
        p._on_deadline(p._active[nonce])
        assert await asyncio.wait_for(task, 10) == "deny"
    asyncio.run(run())


def test_nonce_of_another_agent_only_affects_that_request(short_dir):
    async def run():
        p, hub = _pager(short_dir)
        await p.start(serve_socket=False)
        ta, na = await _active(p, "a")
        tb, nb = await _active(p, "b")
        assert na != nb
        hub.tap(nb, "approve")
        assert await tb == "allow"
        assert not ta.done()
        hub.tap(na, "deny")
        assert await ta == "deny"
    asyncio.run(run())

def test_notify_raising_still_resolves_in_app_or_by_deadline(short_dir):
    async def run():
        p, hub = _pager(short_dir, hub=FakeHub(notify_exc=RuntimeError("no validator")))
        await p.start(serve_socket=False)
        task, nonce = await _active(p, "a")
        # time-sensitive tried, then the `active` fallback, both failed: no crash
        assert [n["interruption"] for n in hub.notifies] == ["time-sensitive", "active"]
        assert hub.press("approve", nonce) == "allowed"
        assert await task == "allow"
        p.timeout = 0.05                               # now let the deadline decide
        task, nonce = await _active(p, "a")
        assert await asyncio.wait_for(task, 10) == "deny"
    asyncio.run(run())


def test_time_sensitive_rejected_falls_back_to_active(short_dir):
    class Picky(FakeHub):
        async def notify(self, title, body, **kw):
            self.notifies.append(kw)
            if kw["interruption"] == "time-sensitive":
                raise ValueError("entitlement missing")
    async def run():
        p, hub = _pager(short_dir, hub=Picky())
        await p.start(serve_socket=False)
        task, nonce = await _active(p, "a")
        assert [n["interruption"] for n in hub.notifies] == ["time-sensitive", "active"]
        hub.tap(nonce, "deny")
        await task
    asyncio.run(run())


def test_real_hub_without_validator(short_dir):
    """A real carterkit Hub: notify raises (no validator), taps and in-app
    frames arrive through the client's broadcast dispatch."""
    class _FakeSock:
        def __init__(self):
            self.sent, self.handlers = [], {}

        def on(self, t, f):
            self.handlers[t] = f

        async def send(self, t, payload=None, reply_to=None):
            self.sent.append((t, payload))

    async def run():
        with Layout("Agents", cols=2, rows=2) as ui:
            with ui.tab("Main"):
                ui.label("pg-agent", text="-")
        hub = ui.serve()
        hub.client._sock = _FakeSock()
        hub.client._broadcast_registered = False   # re-arm on the fake socket
        p = AgentPager(hub, timeout=5, store_path=os.path.join(short_dir, "s.json"),
                       socket_path=os.path.join(short_dir, "p.sock"))
        await p.start(serve_socket=False)
        dispatch = hub.client._sock.handlers["broadcast"]
        task, nonce = await _active(p, "a")
        await dispatch({"msg_type": "notif_action", "notifId": True, "actionId": "approve"})
        assert not task.done()
        await dispatch({"msg_type": "notif_action", "notifId": nonce, "actionId": "approve"})
        assert await asyncio.wait_for(task, 10) == "allow"
        task, nonce = await _active(p, "a")
        await dispatch({"msg_type": "action", "op": "pager_decide",
                        "decision": "deny", "req": nonce})
        assert await asyncio.wait_for(task, 10) == "deny"
        sent = [pl for t, pl in hub.client._sock.sent if t == "broadcast_request"]
        assert any(pl.get("msg_type") == "pager" for pl in sent)
    asyncio.run(run())


def test_one_active_per_agent_fifo_queue(short_dir):
    async def run():
        p, hub = _pager(short_dir)
        await p.start(serve_socket=False)
        t1 = asyncio.ensure_future(p.ask("a", "Bash", "one"))
        t2 = asyncio.ensure_future(p.ask("a", "Bash", "two"))
        t3 = asyncio.ensure_future(p.ask("a", "Edit", "three"))
        await _settle()
        assert len(hub.notifies) == 1                  # only the head is paged
        states = [(r["summary"], r["state"]) for r in p.pending()]
        assert states == [("one", "waiting"), ("two", "queued"), ("three", "queued")]
        assert p.status()["agents"]["a"]["waiting"] == 2
        queued = [r["nonce"] for r in p.pending() if r["state"] == "queued"]
        assert hub.tap(queued[0], "approve") == "ignored"   # not active: never allows
        hub.tap(hub.notifies[0]["notif_id"], "deny")
        assert await t1 == "deny"
        await _settle()
        assert len(hub.notifies) == 2 and hub.notifies[1]["body"].startswith("Bash: two")
        hub.tap(hub.notifies[1]["notif_id"], "approve")
        assert await t2 == "allow"
        await _settle()
        hub.tap(hub.notifies[2]["notif_id"], "approve")
        assert await t3 == "allow"
    asyncio.run(run())


def test_cancel_withdraws_active_and_queued(short_dir):
    async def run():
        p, hub = _pager(short_dir)
        await p.start(serve_socket=False)
        t1 = asyncio.ensure_future(p.ask("a", "Bash", "one"))
        t2 = asyncio.ensure_future(p.ask("a", "Bash", "two"))
        t3 = asyncio.ensure_future(p.ask("a", "Bash", "three"))
        await _settle()
        n1 = hub.notifies[0]["notif_id"]
        t2.cancel()                                    # queued one withdraws
        await _settle()
        assert [r["summary"] for r in p.pending()] == ["one", "three"]
        t1.cancel()                                    # active one withdraws
        await _settle()
        assert hub.tap(n1, "approve") == "expired"
        assert [r["state"] for r in p.pending()] == ["waiting"]
        assert "withdrawn" in p.audit[0]["reason"]
        hub.tap(hub.notifies[-1]["notif_id"], "approve")
        assert await t3 == "allow"
    asyncio.run(run())


def test_restart_denies_every_persisted_request(short_dir):
    async def run():
        p, hub = _pager(short_dir)
        await p.start(serve_socket=False)
        ta, na = await _active(p, "a")
        tq = asyncio.ensure_future(p.ask("a", "Bash", "queued"))
        await _settle()
        p.store.update(na, deadline=time.time() - 5)   # one already past deadline
        on_disk = json.loads(open(p.store.path).read())
        assert len(on_disk) == 2 and on_disk[na]["agent"] == "a"
        ta.cancel(); tq.cancel()
        return na, set(on_disk)
    # simulate a crash: write the store as it was, then a fresh pager starts
    def crash_store():
        store = PendingStore(os.path.join(short_dir, "st", "pending.json"))
        store.put("pgold1", {"agent": "a", "tool": "Bash", "summary": "x",
                             "created": 1, "deadline": time.time() - 10, "state": "waiting"})
        store.put("pgold2", {"agent": "b", "tool": "Bash", "summary": "y",
                             "created": 1, "deadline": time.time() + 60, "state": "waiting"})
        store.put("pgold3", {"agent": "b", "tool": "Edit", "summary": "z",
                             "created": 1, "deadline": None, "state": "queued"})
    asyncio.run(run())
    crash_store()

    async def restart():
        p, hub = _pager(short_dir)
        await p.start(serve_socket=False)
        assert p.pending() == []
        assert json.loads(open(p.store.path).read()) == {}
        reasons = {e["nonce"]: (e["decision"], e["reason"], e["source"]) for e in p.audit}
        assert reasons["pgold1"] == ("deny", "expired before restart", "restart")
        assert reasons["pgold2"] == ("deny", "orphaned by restart", "restart")
        assert reasons["pgold3"][0] == "deny"
        assert hub.tap("pgold2", "approve") == "expired"   # late tap after restart
        assert all(e["decision"] == "deny" for e in p.audit)
    asyncio.run(restart())


def test_store_is_0600_and_writes_are_atomic(short_dir, monkeypatch):
    path = os.path.join(short_dir, "st", "pending.json")
    s = PendingStore(path)
    s.put("n1", {"agent": "a"})
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    assert stat.S_IMODE(os.stat(os.path.dirname(path)).st_mode) == 0o700
    # a failure mid-write leaves the previous file intact and no temp litter
    import carterkit.pager as pager_mod
    def boom(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(pager_mod.os, "replace", boom)
    with pytest.raises(OSError):
        s.put("n2", {"agent": "b"})
    monkeypatch.undo()
    assert json.loads(open(path).read()) == {"n1": {"agent": "a"}}
    assert os.listdir(os.path.dirname(path)) == ["pending.json"]
    # a corrupt store is tolerated (treated as empty), never crashes startup
    open(path, "w").write("{not json")
    assert PendingStore(path).load() == {}


def test_timeout_must_be_positive():
    with pytest.raises(ValueError):
        AgentPager(FakeHub(), timeout=0)

async def _sock_ask(path, obj):
    r, w = await asyncio.open_unix_connection(path)
    w.write((obj if isinstance(obj, bytes) else json.dumps(obj).encode()) + b"\n")
    await w.drain()
    return r, w


def test_unix_socket_round_trip_approve_and_deny(short_dir):
    async def run():
        p, hub = _pager(short_dir)
        await p.start()
        path = str(p.socket_path)
        assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
        assert stat.S_ISSOCK(os.stat(path).st_mode)
        r, w = await _sock_ask(path, {"agent": "claude %3", "tool": "Bash",
                                      "summary": "terraform apply -target=x"})
        await _settle(); await asyncio.sleep(0.05)
        hub.tap(hub.notifies[0]["notif_id"], "approve")
        reply = json.loads(await asyncio.wait_for(r.readline(), 10))
        assert reply == {"decision": "allow", "reason": "approved from CAR-TER"}
        w.close()
        # the stdlib client (what the K3 hook uses), in a thread
        fut = asyncio.ensure_future(asyncio.to_thread(
            ask_via_socket, "claude %3", "Bash", "rm -rf build", socket_path=path, timeout=5))
        for _ in range(1000):
            await asyncio.sleep(0.01)
            if len(hub.notifies) == 2:
                break
        hub.press("deny", hub.notifies[1]["notif_id"])
        assert await fut == ("deny", "denied from CAR-TER")
        await p.stop()
        assert not os.path.exists(path)
    asyncio.run(run())


def test_unix_socket_deadline_and_bad_requests(short_dir):
    async def run():
        p, hub = _pager(short_dir, timeout=0.05)
        await p.start()
        path = str(p.socket_path)
        r, w = await _sock_ask(path, {"agent": "a", "tool": "Bash", "summary": "x"})
        reply = json.loads(await asyncio.wait_for(r.readline(), 10))
        assert reply["decision"] == "deny" and "timed out" in reply["reason"]
        w.close()
        for bad in (b"not json", b"[1,2]", json.dumps({"agent": "a"}).encode(),
                    json.dumps({"agent": True, "tool": "Bash"}).encode()):
            r, w = await _sock_ask(path, bad)
            reply = json.loads(await asyncio.wait_for(r.readline(), 10))
            assert reply["decision"] == "deny" and reply["reason"].startswith("bad request")
            w.close()
        await p.stop()
    asyncio.run(run())


def test_unix_socket_disconnect_withdraws(short_dir):
    async def run():
        p, hub = _pager(short_dir)
        await p.start()
        path = str(p.socket_path)
        r1, w1 = await _sock_ask(path, {"agent": "a", "tool": "Bash", "summary": "one"})
        r2, w2 = await _sock_ask(path, {"agent": "a", "tool": "Bash", "summary": "two"})
        for _ in range(1000):
            await asyncio.sleep(0.01)
            if len(p.pending()) == 2:
                break
        n1 = hub.notifies[0]["notif_id"]
        w1.close()                                         # hook died
        for _ in range(1000):
            await asyncio.sleep(0.01)
            if len(p.pending()) == 1:
                break
        assert [r["summary"] for r in p.pending()] == ["two"]
        assert p.audit[-1]["source"] == "withdraw"
        assert hub.tap(n1, "approve") == "expired"
        await _settle()
        hub.tap(hub.notifies[-1]["notif_id"], "approve")
        reply = json.loads(await asyncio.wait_for(r2.readline(), 10))
        assert reply["decision"] == "allow"
        w2.close()
        await p.stop()
    asyncio.run(run())


def test_socket_refuses_live_daemon_and_replaces_stale(short_dir):
    async def run():
        p1, _ = _pager(short_dir)
        await p1.start()
        p2, _ = _pager(short_dir)
        with pytest.raises(RuntimeError):
            await p2.serve()
        await p1.stop()
        # a stale socket file left by a dead daemon is replaced
        import socket as s
        dead = s.socket(s.AF_UNIX, s.SOCK_STREAM)
        dead.bind(str(p1.socket_path)); dead.close()
        await p2.serve()
        assert stat.S_IMODE(os.stat(p2.socket_path).st_mode) == 0o600
        await p2.stop()
    asyncio.run(run())


def test_stop_denies_everything_outstanding(short_dir):
    async def run():
        p, hub = _pager(short_dir)
        await p.start(serve_socket=False)
        t1 = asyncio.ensure_future(p.ask("a", "Bash", "one"))
        t2 = asyncio.ensure_future(p.ask("a", "Bash", "two"))
        await _settle()
        await p.stop()
        assert await t1 == "deny" and await t2 == "deny"
        assert len(hub.notifies) == 1                 # stopping never pages the queue
        assert json.loads(open(p.store.path).read()) == {}
    asyncio.run(run())
