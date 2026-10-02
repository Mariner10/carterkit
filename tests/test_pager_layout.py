"""K4 (carter-n4x.4): the Agents layout + the pager's in-app queue, sync re-fill,
acks and decision metrics. No network: a fake hub, or a real Hub never started."""

import asyncio
import functools
import json
import os
import shutil
import tempfile

import pytest

from carterkit import validate_layout
from carterkit.hub import Hub
from carterkit.pager import (LOG_MSG_TYPE, QUEUE_EVENT, AgentPager, build_pager_layout)


def arun(fn):
    """Run an async test on a fresh loop (the suite has no pytest-asyncio)."""
    @functools.wraps(fn)
    def wrapper(*a, **k):
        return asyncio.run(fn(*a, **k))
    return wrapper


class FakeHub:
    def __init__(self):
        self.broadcasts = []
        self.handlers = {}
        self.notif_handler = None
        self.sync_handler = None

    async def notify(self, title, body, **kw):
        pass

    def on_notif_action(self, fn):
        self.notif_handler = fn

    def on(self, name, fn):
        self.handlers.setdefault(name, []).append(fn)

    def on_sync_request(self, fn):
        self.sync_handler = fn

    async def broadcast(self, msg_type, data):
        self.broadcasts.append((msg_type, data))

    def press(self, decision, req):
        return [fn({"msg_type": "action", "op": "pager_decide", "decision": decision,
                    "req": req}) for fn in self.handlers["action"]][-1]

    def last(self, msg_type):
        for mt, data in reversed(self.broadcasts):
            if mt == msg_type:
                return data
        return None


@pytest.fixture
def short_dir():
    d = tempfile.mkdtemp(prefix="pgl", dir="/tmp")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _pager(d, hub=None, **kw):
    hub = hub or FakeHub()
    kw.setdefault("timeout", 30)
    kw.setdefault("metrics_path", os.path.join(d, "metrics.jsonl"))
    p = AgentPager(hub, store_path=os.path.join(d, "st", "pending.json"),
                   socket_path=os.path.join(d, "p.sock"), **kw)
    p.restore()
    p.wire()
    return p, hub


async def _settle():
    for _ in range(10):
        await asyncio.sleep(0)


def _children(layout):
    return {c["id"]: c for c in layout["tabs"][0]["children"]}


def _buttons(children):
    return [c for c in children if c.get("type") == "button"]


def _metrics(d):
    with open(os.path.join(d, "metrics.jsonl")) as fh:
        return [json.loads(line) for line in fh]


# ─── the layout ──────────────────────────────────────────────────────────────
def test_layout_validates_clean():
    layout = build_pager_layout()
    findings = validate_layout(layout)
    assert [f for f in findings if f.get("severity") == "error"] == []
    assert findings == []


def test_layout_has_every_part():
    layout = build_pager_layout()
    kids = _children(layout)
    assert layout["state"] == {"acks": True}
    assert "glance" not in layout
    assert kids["pg-status"]["type"] == "statusLight"
    for lid in ("pg-agent", "pg-step", "pg-req"):
        assert kids[lid]["type"] == "label"
    assert kids["pg-queue"]["type"] == "group"
    assert kids["pg-queue"]["dynamic"] == QUEUE_EVENT
    assert kids["pg-waiting"]["type"] == "list"
    assert kids["pg-log"]["type"] == "logConsole"
    assert kids["pg-log"]["sync"][0]["filter"] == {"msg_type": LOG_MSG_TYPE}
    # full-width queue + log (iPad: one column across the whole content width)
    assert kids["pg-queue"]["span"][1] == layout["tabs"][0]["grid"]["columns"]
    assert layout["tabs"][0]["grid"]["mode"] == "flow"
    # plain JSON, no code smuggled in
    json.loads(json.dumps(layout))


# ─── the queue fill ──────────────────────────────────────────────────────────
@arun
async def test_fill_payload_carries_literal_nonce(short_dir):
    p, hub = _pager(short_dir)
    req = p.submit("claude %3", "Bash", "terraform plan")
    await _settle()
    fill = hub.last(QUEUE_EVENT)
    assert fill is not None
    payload = p.queue_payload()
    assert payload["msg_type"] == _children(build_pager_layout())["pg-queue"]["dynamic"]
    assert payload["children"] == fill["children"]
    buttons = _buttons(fill["children"])
    assert {b["action"]["payload"]["decision"] for b in buttons} == {"approve", "deny"}
    for b in buttons:
        a = b["action"]
        assert a["event"] == "broadcast_request"
        assert a["payload"]["msg_type"] == "action"
        assert a["payload"]["op"] == "pager_decide"
        assert a["payload"]["req"] == req.nonce          # literal, not {{value}}
    # the fragment is a valid, collision-free deck for the layout
    from carterkit.dynamic import fragment_id_findings
    assert fragment_id_findings(fill["children"], build_pager_layout(), "q") == []
    # a press with that payload resolves the request
    assert hub.press("approve", buttons[0]["action"]["payload"]["req"]) == "allowed"
    assert await req.future == ("allow", "approved from CAR-TER")
    await _settle()
    assert _buttons(hub.last(QUEUE_EVENT)["children"]) == []   # buttons gone


@arun
async def test_status_view_and_waiting_rows(short_dir):
    p, hub = _pager(short_dir)
    p.submit("a", "Bash", "ls")
    p.submit("a", "Edit", "file.py")
    p.submit("a", "Write", "x")
    await _settle()
    view = hub.last("pager")["view"]
    assert view["status"] == "waiting"
    assert (view["agent"], view["step"], view["req"]) == ("a", "Bash", "ls")
    assert view["waiting"] == 2 and view["waitingText"] == "+2 waiting"
    assert view["queue"] == [{"id": "a", "agent": "a", "next": "Edit", "waiting": "+2"}]
    await p.stop()


# ─── reconnect, acks ─────────────────────────────────────────────────────────
@arun
async def test_sync_request_refills_queue(short_dir):
    p, hub = _pager(short_dir)
    req = p.submit("a", "Bash", "ls")
    await _settle()
    assert hub.sync_handler is not None
    hub.broadcasts.clear()
    await hub.sync_handler({"from": "phone", "dynamic": [QUEUE_EVENT]})
    fill = hub.last(QUEUE_EVENT)
    assert fill is not None
    assert {b["action"]["payload"]["req"] for b in _buttons(fill["children"])} == {req.nonce}
    assert hub.last("pager")["event"] == "sync"
    await p.stop()


@arun
async def test_real_hub_acks_and_sync_wiring(short_dir):
    hub = Hub(build_pager_layout(), name="carter-pager")
    assert hub.client._ack_commands is True              # state.acks honoured
    p = AgentPager(hub, timeout=30, store_path=os.path.join(short_dir, "pending.json"),
                   socket_path=os.path.join(short_dir, "p.sock"))
    p.wire()
    assert hub.client._join_handler == p.handle_sync_request
    sent = []

    async def capture(frame):
        sent.append(frame)
    hub.client.broadcast_frame = capture
    req = p.submit("a", "Bash", "ls")
    handled = await hub._dispatch({"msg_type": "action", "op": "pager_decide",
                                   "decision": "deny", "req": req.nonce})
    assert handled is True                                # -> command_ack ok:true
    assert await req.future == ("deny", "denied from CAR-TER")
    await _settle()
    assert any(f.get("msg_type") == QUEUE_EVENT for f in sent)
    assert any(f.get("msg_type") == LOG_MSG_TYPE and "DENY" in f["line"]["text"]
               for f in sent)


# ─── stale nonces ────────────────────────────────────────────────────────────
@arun
async def test_stale_nonce_is_denied(short_dir):
    p, hub = _pager(short_dir)
    a = p.submit("a", "Bash", "first")
    await _settle()
    stale = _buttons(hub.last(QUEUE_EVENT)["children"])
    assert hub.press("deny", a.nonce) == "denied"
    b = p.submit("a", "Bash", "second")
    await _settle()
    # Carter's finger was still on A's Approve: rejected, B untouched
    approve_a = next(x for x in stale if x["action"]["payload"]["decision"] == "approve")
    assert hub.press("approve", approve_a["action"]["payload"]["req"]) == "expired"
    assert await a.future == ("deny", "denied from CAR-TER")
    assert not b.future.done()
    assert hub.press("approve", "pg" + "0" * 32) == "ignored"
    assert not b.future.done()
    await p.stop()
    assert b.future.result()[0] == "deny"


# ─── metrics ─────────────────────────────────────────────────────────────────
@arun
async def test_one_metrics_line_per_decision(short_dir):
    p, hub = _pager(short_dir, timeout=0.05)
    r1 = p.submit("a", "Bash", "ls")
    await _settle()
    hub.press("approve", r1.nonce)
    r2 = p.submit("b", "Edit", "x")
    assert (await asyncio.wait_for(r2.future, 2))[0] == "deny"   # deadline
    hub.press("approve", r2.nonce)                                # late: no new line
    lines = _metrics(short_dir)
    assert [(m["nonce"], m["decision"], m["timed_out"]) for m in lines] == [
        (r1.nonce, "allow", False), (r2.nonce, "deny", True)]
    for m in lines:
        assert isinstance(m["latency"], float) and m["latency"] >= 0
        assert {"ts", "agent", "tool", "source", "queued"} <= set(m)
    assert lines[1]["latency"] >= 0.04
    assert oct(os.stat(os.path.join(short_dir, "metrics.jsonl")).st_mode & 0o777) == "0o600"


def test_metrics_off_by_default(short_dir):
    p = AgentPager(FakeHub(), store_path=os.path.join(short_dir, "pending.json"),
                   socket_path=os.path.join(short_dir, "p.sock"))
    assert p.metrics_path is None


@arun
async def test_queue_fits_the_group_grid(short_dir):
    from carterkit.pager import QUEUE_SHOWN
    p, hub = _pager(short_dir)
    reqs = [p.submit(f"agent{i}", "Bash", f"cmd {i}") for i in range(QUEUE_SHOWN + 2)]
    kids = p.queue_children()
    rows = _children(build_pager_layout())["pg-queue"]["grid"]["rows"]
    assert max(c["position"][0] + c["span"][0] for c in kids) <= rows   # never clipped
    shown = {b["action"]["payload"]["req"] for b in _buttons(kids)}
    assert shown == {r.nonce for r in reqs[:QUEUE_SHOWN]}
    assert any(c["id"] == "pgq-more" and "+2 more" in c["text"] for c in kids)
    await p.stop()


@arun
async def test_refresh_repushes_only_while_waiting(short_dir):
    p, hub = _pager(short_dir, refresh_interval=0.02)
    await p.start(serve_socket=False)
    await asyncio.sleep(0.07)
    assert not any(d.get("event") == "refresh" for _, d in hub.broadcasts)   # idle: silent
    req = p.submit("a", "Bash", "ls")
    await asyncio.sleep(0.07)
    refreshed = [d for _, d in hub.broadcasts if d.get("event") == "refresh"]
    assert refreshed and refreshed[-1]["view"]["status"] == "waiting"
    hub.press("deny", req.nonce)
    await p.stop()
