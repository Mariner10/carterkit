"""Hub surfaces (progress, toast, haptic, log): exact frames, replies, coalescing, resend, kit."""
import asyncio
import logging

import pytest

from carterkit import Layout, ambient, scaffold
from carterkit.hub import HubError
from carterkit.testing import FakeHub, load_hub_module


def make(**kw):
    ui = Layout("Example")
    with ui.tab("T"):
        ui.label("l", text="x")
    fake = FakeHub(ui, **kw)
    fake.hub.progress_min_interval = 0.05
    return fake


def run(coro):
    return asyncio.run(coro)


def sent(fake, kind):
    return fake.routed(kind)


# ─── progress ───────────────────────────────────────────────────────────────
def test_progress_frame_shapes():
    async def go():
        fake = make()
        async with fake.hub.progress(
                "Installing Example package", total=48_000_000, done=20_000_000,
                unit="bytes", detail="Downloading", step=(2, 4, "Unpacking"),
                cancellable=True, ask="Stop installing Example package?", show="sheet",
                eta_s=90, id="task-7") as task:
            assert task.id == "task-7" and task.done == 20_000_000
        return fake
    fake = run(go())
    first, last = sent(fake, "progress")
    assert first == {
        "id": "task-7", "title": "Installing Example package", "unit": "bytes",
        "detail": "Downloading", "done": 20_000_000, "total": 48_000_000, "show": "sheet",
        "step": {"index": 2, "count": 4, "label": "Unpacking"}, "etaS": 90,
        "cancel": {"ask": "Stop installing Example package?"},
        "hub": fake.hub.name, "from": fake.hub.name}
    assert last["state"] == "done" and last["id"] == "task-7"


def test_progress_defaults_and_terminal_states():
    async def go():
        fake = make()
        async with fake.hub.progress("Example task", id="a") as t:
            await t.finish("Installed 1.2.0", haptic="success")
        t2 = await fake.hub.progress("Example two", id="b")
        await t2.fail("Example failure")
        t3 = await fake.hub.progress("Example three", id="c", cancellable=True)
        await t3.cancelled_ok()
        with pytest.raises(RuntimeError):
            async with fake.hub.progress("Example four", id="d"):
                raise RuntimeError("boom")
        async with fake.hub.progress("Example five", id="e") as t5:
            pass
        return fake
    fake = run(go())
    by = {}
    for f in sent(fake, "progress"):
        by.setdefault(f["id"], []).append(f)
    assert by["a"][0] == {"id": "a", "title": "Example task", "hub": fake.hub.name,
                          "from": fake.hub.name}
    assert by["a"][-1]["result"] == {"message": "Installed 1.2.0", "haptic": "success"}
    assert by["a"][-1]["state"] == "done" and len(by["a"]) == 2   # finish, not a second end
    assert by["b"][-1]["state"] == "failed" and by["b"][-1]["result"] == {"message": "Example failure"}
    assert by["c"][0]["cancel"] == {} and by["c"][-1]["state"] == "cancelled"
    assert by["d"][-1]["state"] == "failed"
    assert by["e"][-1]["state"] == "done"


def test_progress_value_and_validation():
    async def go():
        fake = make()
        t = fake.hub.progress("Example", id="v", value=0.25)
        await t.start()
        await t.update(value=7)                  # clamped
        await asyncio.sleep(0.07)
        await t.update(value=None)               # indeterminate
        await asyncio.sleep(0.07)
        for bad in (dict(value=-1), dict(done=float("nan")), dict(unit="mb"),
                    dict(state="weird"), dict(stale_s=1), dict(nope=1)):
            with pytest.raises(HubError):
                await t.update(**bad)
        with pytest.raises(HubError):
            fake.hub.progress("x", id="")
        await t.finish()
        return fake
    fake = run(go())
    values = [f.get("value", "absent") for f in sent(fake, "progress")]
    assert values[:3] == [0.25, 1.0, None]


def test_progress_updates_coalesce_and_last_is_sent():
    async def go():
        fake = make()
        fake.hub.progress_min_interval = 0.1
        t = await fake.hub.progress("Example", total=100, id="c")
        for n in range(1, 301):
            await t.update(done=n % 100 or 99)
        await t.update(done=77, detail="Last")
        await asyncio.sleep(0.25)
        n_before_end = len(sent(fake, "progress"))
        await t.finish()
        return fake, n_before_end
    fake, n = run(go())
    frames = sent(fake, "progress")
    assert n <= 3                                # open + at most two trailing flushes
    assert frames[n - 1]["done"] == 77 and frames[n - 1]["detail"] == "Last"
    assert frames[-1]["state"] == "done"         # a terminal state is never deferred


def test_progress_heartbeat_resends_while_idle():
    async def go():
        fake = make()
        t = await fake.hub.progress("Example", id="h", stale_s=5)
        t.frame["staleS"] = 0.04                 # shrink the 2.5 s beat for the test
        t._beat.cancel(); t._beat = None
        t._ensure_beat()
        await asyncio.sleep(0.2)
        await t.finish()
        return fake
    fake = run(go())
    assert len(sent(fake, "progress")) >= 4


def test_progress_reply_cancel_dismissed_busy():
    async def go():
        fake = make()
        seen = []
        t = await fake.hub.progress("Example", id="p1", cancellable=True)
        t.on_cancel(lambda task: seen.append(task.id))
        other = await fake.hub.progress("Other", id="p2")
        await fake.dispatch({"msg_type": "progress_reply", "id": "nobody", "choice": "cancel"})
        assert not t.cancelled
        await fake.dispatch({"msg_type": "progress_reply", "id": "p1", "choice": "cancel"})
        assert t.cancelled and seen == ["p1"] and not other.cancelled
        await t.cancelled_ok()
        await fake.dispatch({"msg_type": "progress_reply", "id": "p2", "choice": "busy"})
        assert other.refused == "busy"
        await fake.dispatch({"msg_type": "progress_reply", "id": "p2", "choice": "dismissed"})
        assert other.dismissed and other.ended
        return fake
    fake = run(go())
    assert "p1" not in fake.hub._surfaces_live["progress"]


def test_progress_ended_reply_stops_the_task():
    async def go():
        fake = make()
        fake.sock.reply = None
        t = await fake.hub.progress("Example", id="e1")
        orig = fake.sock.request

        async def request(kind, payload=None, timeout=5.0):
            if kind == "route_msg":
                fake.sock.sent.append(("REQ:" + kind, payload))
                return {"ok": False, "id": "e1", "reason": "ended"}
            return await orig(kind, payload, timeout)
        fake.sock.request = request
        await t.update(detail="x")
        await asyncio.sleep(0.07)
        await t.update(detail="y")
        return t
    t = run(go())
    assert t.ended


def test_app_refusal_raises_busy_returns():
    async def go():
        fake = make()
        orig = fake.sock.request
        reasons = iter(["off", "busy"])

        async def request(kind, payload=None, timeout=5.0):
            if kind == "route_msg":
                return {"ok": False, "reason": next(reasons)}
            return await orig(kind, payload, timeout)
        fake.sock.request = request
        with pytest.raises(HubError, match="off"):
            await fake.hub.toast("Example")
        return await fake.hub.toast("Example")
    assert run(go()) == {"ok": False, "reason": "busy"}


def test_no_device_is_a_hub_error():
    async def go():
        fake = make()
        orig = fake.sock.request

        async def request(kind, payload=None, timeout=5.0):
            if kind == "get_nodes":
                return {"clients": []}
            return await orig(kind, payload, timeout)
        fake.sock.request = request
        await fake.hub.haptic("light")
    with pytest.raises(HubError, match="no device"):
        run(go())


# ─── reconnect ──────────────────────────────────────────────────────────────
def test_reconnect_resends_live_tasks_and_log_titles():
    async def go():
        fake = make()
        hub = fake.hub
        t = await hub.progress("Example", total=10, done=4, id="r1", cancellable=True)
        done = await hub.progress("Finished", id="r2")
        await done.finish()
        lg = hub.log("r-log", title="Example log", progress="r1")
        await lg.info("a line that is not resent")
        await lg.flush()
        fake.sock.sent.clear()
        await fake.sock.on_reconnect_callback()
        return fake, t
    fake, t = run(go())
    (p,) = sent(fake, "progress")
    assert p == t.frame | {"hub": fake.hub.name, "from": fake.hub.name} and p["done"] == 4
    (l,) = sent(fake, "log")
    assert l == {"id": "r-log", "title": "Example log", "progress": "r1",
                 "hub": fake.hub.name, "from": fake.hub.name}


def test_reconnect_chains_the_previous_callback():
    async def go():
        fake = make()
        called = []
        fake.sock.on_reconnect_callback = lambda: called.append("prev")
        await fake.hub.progress("Example", id="x")
        await fake.sock.on_reconnect_callback()
        return called
    assert run(go()) == ["prev"]


# ─── toast and haptic ───────────────────────────────────────────────────────
def test_toast_frame_shapes():
    async def go():
        fake = make()
        await fake.hub.toast("Example package installed", message="Version 1.2.0",
                             style="success", duration_s=4, haptic="success",
                             icon="checkmark", action=("Show log", {"log": "task-7-log"}),
                             id="task-7-done")
        await fake.hub.toast("Plain")
        await fake.hub.toast("Open", action=("Show", {"progress": "task-7"}))
        await fake.hub.toast("Ask", action=("Undo", "reply"), id="t9")
        return fake
    fake = run(go())
    a, b, c, d = sent(fake, "toast")
    n = fake.hub.name
    assert a == {"id": "task-7-done", "title": "Example package installed",
                 "message": "Version 1.2.0", "style": "success", "icon": "checkmark",
                 "durationS": 4, "haptic": "success",
                 "action": {"label": "Show log", "opens": {"log": "task-7-log"}},
                 "hub": n, "from": n}
    assert b == {"title": "Plain", "hub": n, "from": n}
    assert c["action"] == {"label": "Show", "opens": {"progress": "task-7"}}
    assert d["action"] == {"label": "Undo", "reply": True}


def test_toast_validation_and_caps():
    async def go():
        fake = make()
        await fake.hub.toast("T" * 100, message="m" * 200)
        for bad in (dict(style="loud"), dict(duration_s=1), dict(duration_s=11),
                    dict(haptic="buzz"), dict(action=("x", {"url": "http://e"})),
                    dict(on_action=lambda f: None)):
            with pytest.raises(HubError):
                await fake.hub.toast("Example", **bad)
        return fake
    fake = run(go())
    (f,) = sent(fake, "toast")
    assert len(f["title"]) == 60 and len(f["message"]) == 120


def test_toast_reply_reaches_hub_on_and_on_action():
    async def go():
        fake = make()
        got, via_on = [], []
        fake.hub.on("toast_reply", lambda d: via_on.append(d["choice"]))
        await fake.hub.toast("Example", action=("Undo", "reply"), id="t1",
                             on_action=lambda d: got.append(d["id"]))
        await fake.dispatch({"msg_type": "toast_reply", "id": "t1", "choice": "action"})
        await fake.dispatch({"msg_type": "toast_reply", "id": "other", "choice": "action"})
        return got, via_on
    got, via_on = run(go())
    assert got == ["t1"] and via_on == ["action", "action"]


def test_haptic_frame_and_played():
    async def go():
        fake = make()
        ok = await fake.hub.haptic("success")
        orig = fake.sock.request

        async def request(kind, payload=None, timeout=5.0):
            if kind == "route_msg":
                fake.sock.sent.append(("REQ:" + kind, payload))
                return {"ok": True, "played": False, "reason": "coalesced"}
            return await orig(kind, payload, timeout)
        fake.sock.request = request
        dropped = await fake.hub.haptic("light")
        with pytest.raises(HubError):
            await fake.hub.haptic("buzz")
        return fake, ok, dropped
    fake, ok, dropped = run(go())
    assert [f["pattern"] for f in sent(fake, "haptic")] == ["success", "light"]
    assert sent(fake, "haptic")[0] == {"pattern": "success", "hub": fake.hub.name,
                                       "from": fake.hub.name}
    assert ok is False        # FakeHub's phone says {"ok": True} with no `played`
    assert dropped is False


def test_sync_twins_from_another_thread():
    async def go():
        fake = make()
        fake.hub._loop = asyncio.get_running_loop()
        t = await fake.hub.progress("Example", id="s")
        res = await asyncio.get_running_loop().run_in_executor(
            None, lambda: (fake.hub.toast_sync("Example"), fake.hub.haptic_sync("light"),
                           t.update_sync(state="paused")))
        with pytest.raises(HubError, match="block"):
            fake.hub.toast_sync("Example")
        return fake, res
    fake, res = run(go())
    assert len(sent(fake, "toast")) == 1 and len(sent(fake, "haptic")) == 1
    assert sent(fake, "progress")[-1]["state"] == "paused"


# ─── log ────────────────────────────────────────────────────────────────────
def test_log_frame_shapes_and_batching():
    async def go():
        fake = make()
        lg = fake.hub.log("task-7-log", title="Install log", progress="task-7")
        await lg.info("Unpacking Example package (1.2.0)")
        await lg.warn("Example warning")
        await asyncio.sleep(0.2)                # one batch per 100 ms
        await lg.error("Example error")
        assert await lg.open() is False         # FakeHub does not say opened
        await lg.clear()
        await lg.close()
        return fake
    fake = run(go())
    first, second, opened, cleared, closed = sent(fake, "log")
    n = fake.hub.name
    assert [l["text"] for l in first["lines"]] == ["Unpacking Example package (1.2.0)",
                                                    "Example warning"]
    assert [l["level"] for l in first["lines"]] == ["info", "warn"]
    assert all(isinstance(l["at"], float) for l in first["lines"])
    assert first["id"] == "task-7-log" and first["title"] == "Install log"
    assert first["progress"] == "task-7" and first["hub"] == n
    assert "title" not in second and second["lines"][0]["level"] == "error"
    assert opened["open"] is True and "lines" not in opened
    assert cleared["clear"] is True and closed["close"] is True


def test_log_pace_is_capped_hub_side():
    async def go():
        fake = make()
        lg = fake.hub.log("big", title="Big")
        for n in range(500):
            await lg.info(f"Example line {n}")
        await asyncio.sleep(0.35)
        mid = [len(f["lines"]) for f in sent(fake, "log")]
        await lg.close()
        return fake, mid
    fake, mid = run(go())
    assert mid and all(n <= 20 for n in mid) and sum(mid) < 500    # 20 lines per 100 ms
    frames = sent(fake, "log")
    text = [l["text"] for f in frames if "lines" in f for l in f["lines"]]
    assert text == [f"Example line {n}" for n in range(500)]      # nothing lost, in order
    assert frames[-1]["close"] is True


def test_log_skipped_reply_is_counted_and_level_checked():
    async def go():
        fake = make()
        orig = fake.sock.request

        async def request(kind, payload=None, timeout=5.0):
            if kind == "route_msg":
                fake.sock.sent.append(("REQ:" + kind, payload))
                return {"ok": True, "lines": 1, "skipped": 4}
            return await orig(kind, payload, timeout)
        fake.sock.request = request
        lg = fake.hub.log("s")
        await lg.info("Example")
        await lg.flush()
        with pytest.raises(HubError):
            await lg.write("x", "loud")
        return lg
    assert run(go()).skipped == 4


def test_log_python_logging_handler():
    async def go():
        fake = make()
        fake.hub._loop = asyncio.get_running_loop()
        lg = fake.hub.log("py", title="Job")
        logger = logging.getLogger("example.job")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        h = lg.handler()
        logger.addHandler(h)
        logger.info("from the logger")
        logger.warning("careful")
        logger.debug("below the handler level")
        await asyncio.get_running_loop().run_in_executor(None, logger.error, "from a thread")
        logger.removeHandler(h)
        await asyncio.sleep(0.02)
        await lg.close()
        return fake
    fake = run(go())
    lines = [(l["level"], l["text"]) for f in sent(fake, "log") for l in f.get("lines", [])]
    assert lines == [("info", "from the logger"), ("warn", "careful"), ("error", "from a thread")]


# ─── ambient ────────────────────────────────────────────────────────────────
def test_ambient_task_and_content_state_tasks():
    eta = ambient.apple_date(1_730_000_000)
    row = ambient.task("task-7", "Installing Example package " * 3, hub="hub-a" * 8,
                       detail="Downloading", fraction=0.42, eta_at=eta, cancel=True)
    assert row == {"id": "task-7", "title": row["title"], "state": "running",
                   "hub": row["hub"], "detail": "Downloading", "fraction": 0.42,
                   "etaAt": eta, "stale": False, "cancel": True}
    assert len(row["title"]) == 40 and len(row["hub"]) == 24
    assert ambient.task("a", "t", fraction=3)["fraction"] == 1.0
    assert "fraction" not in ambient.task("a", "t")
    now = ambient.apple_date(1_730_000_100)
    rows = [ambient.task(f"t{i}", f"Example {i}", hub="hub-a") for i in range(5)]
    state = ambient.content_state(updated_at=now, tasks=rows, tasks_more=1)
    assert [t["id"] for t in state["tasks"]] == ["t0", "t1", "t2"] and state["tasksMore"] == 3
    assert "tasks" not in ambient.content_state(updated_at=now)
    assert "tasksMore" not in ambient.content_state(updated_at=now, tasks=rows[:2])
    for bad in (dict(state="weird"), dict(eta_at=1_730_000_000)):
        with pytest.raises(ValueError):
            ambient.task("a", "t", **bad)
    with pytest.raises(ValueError):
        ambient.content_state(updated_at=now, tasks=[{"nope": 1}])


# ─── the kit ────────────────────────────────────────────────────────────────
def test_progress_kit_runs_cancels_and_finishes(tmp_path):
    d = tmp_path / "kit"
    scaffold.scaffold(str(d), template="progress")
    mod = load_hub_module(d / "hub.py", "kit_progress")
    assert all(f["severity"] != "error" for f in mod.ui.validate())
    mod.TICK, mod.CHUNK = 0.01, 12_000_000

    async def go(cancel):
        fake = FakeHub(mod.ui)
        fake.hub.progress_min_interval = 0.0
        fake.hub._loop = asyncio.get_running_loop()
        async with fake.running(mod.run):
            await fake.dispatch({"msg_type": "task_start"})
            await asyncio.sleep(0.015)
            if cancel:
                (first, *_) = fake.routed("progress")
                await fake.dispatch({"msg_type": "progress_reply", "id": first["id"],
                                     "choice": "cancel"})
            await asyncio.sleep(0.3)
            await fake.dispatch({"msg_type": "task_toast"})
            await fake.dispatch({"msg_type": "task_haptic"})
        return fake
    ok = asyncio.run(go(False))
    frames = ok.routed("progress")
    assert frames[0]["cancel"] == {"ask": "Stop installing Example package?"}
    assert frames[0]["total"] == mod.TOTAL and frames[0]["show"] == "sheet"
    assert frames[0]["log"] == "example-log"
    assert frames[-1]["state"] == "done" and frames[-1]["result"]["message"] == "Installed 1.2.0"
    assert [f["step"]["label"] for f in frames if "step" in f and "label" in f["step"]][0] == "Downloading"
    assert ok.routed("toast")[0]["action"] == {"label": "Show log", "opens": {"log": "example-log"}}
    assert ok.routed("toast")[-1]["title"] == "Example toast"
    assert ok.routed("haptic")[-1]["pattern"] == "success"
    assert any(l.get("close") for l in ok.routed("log"))
    assert ok.frames("task_status")[-1]["text"] == "Haptic not played (app in background?)"
    cancelled = asyncio.run(go(True))
    assert cancelled.routed("progress")[-1]["state"] == "cancelled"
    assert "Task cancelled" in [f["text"] for f in cancelled.frames("task_status")]
