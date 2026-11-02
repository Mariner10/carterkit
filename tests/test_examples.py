"""examples/*.py run against a fake hub and make the pushes they promise."""

import asyncio
import importlib.util
import pathlib
import subprocess
import sys

import pytest

from carterkit import Hub
from test_hub import _FakeSock

EX = pathlib.Path(__file__).resolve().parent.parent / "examples"
NAMES = ["push_value", "button_tap", "live_tab", "island", "notification", "pager"]


def _load(name):
    sys.path.insert(0, str(EX))
    try:
        spec = importlib.util.spec_from_file_location(f"ex_{name}", EX / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(EX))
    return mod


def _fake(hub):
    hub.client._sock = _FakeSock()
    calls = []

    async def record(name, *a, **kw):
        calls.append((name, a, kw))
        return {"ok": True}
    hub.notify = lambda *a, **kw: record("notify", *a, **kw)
    return calls


def _values(hub, key):
    """Values pushed under `key`, in order."""
    return [p[key] for t, p in hub.client._sock.sent
            if t == "broadcast_request" and key in p]


def test_push_value():
    mod = _load("push_value")
    hub = mod.ui.serve()
    _fake(hub)
    async def go():
        hub.push_layout = lambda: asyncio.sleep(0)
        await mod.run(hub)
    asyncio.run(go())
    assert _values(hub, "level") == [42]


def test_button_tap_counts():
    mod = _load("button_tap")
    hub = mod.ui.serve()
    _fake(hub)
    mod.taps = 0

    async def go():
        hub.push_layout = lambda: asyncio.sleep(0)
        await mod.run(hub, forever=False)
        for _ in range(2):
            await hub._dispatch({"msg_type": "tap"})
    asyncio.run(go())
    counts = _values(hub, "count")
    assert counts == [0, 1, 2]


def test_live_tab_adds_pushes_removes():
    mod = _load("live_tab")
    hub = mod.ui.serve()
    _fake(hub)
    before = [t.get("id") for t in hub.layout["tabs"]]

    async def go():
        hub.push_layout = lambda: asyncio.sleep(0)
        await mod.run(hub, seconds=0)
    asyncio.run(go())
    assert _values(hub, "temp") == [18, 21, 24]
    assert [t.get("id") for t in hub.layout["tabs"]] == before


def test_island_drives_activity():
    mod = _load("island")
    hub = mod.ui.serve()
    _fake(hub)
    seen = []

    async def rec(name):
        async def f(*a, **kw):
            seen.append(name)
            return {}
        return f

    async def go():
        hub.push_layout = lambda: asyncio.sleep(0)
        for name in ("start_activity", "update_activity", "end_activity"):
            setattr(hub.surfaces, name, await rec(name))
        await mod.run(hub, pause=0)
    asyncio.run(go())
    assert seen == ["start_activity"] + ["update_activity"] * 3 + ["end_activity"]
    assert _values(hub, "temp") == [20, 35, 60, 85]


def test_notification_sends():
    mod = _load("notification")
    hub = mod.ui.serve()
    calls = _fake(hub)
    asyncio.run(mod.run(hub, wait=0))
    (name, args, kw), = calls
    assert args == ("Hello from Python", "Tap Reply to answer")
    assert kw["actions"][0]["id"] == "demo.reply"


def test_pager_pages_and_returns_decision(tmp_path):
    mod = _load("pager")
    hub = Hub(mod.build_pager_layout())
    calls = _fake(hub)
    captured = []

    class Capture(mod.AgentPager):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            captured.append(self)
    mod.AgentPager = Capture

    async def go():
        task = asyncio.ensure_future(mod.run(
            hub, store_path=tmp_path / "p.json", refresh_interval=None))
        for _ in range(100):
            await asyncio.sleep(0.01)
            if calls and captured and captured[0]._active:
                break
        nonce = next(iter(captured[0]._active))
        captured[0].decide(nonce, "approve")
        return await task
    out = asyncio.run(go())
    assert out in ("allow", "deny")
    assert calls and calls[0][0] == "notify"


@pytest.mark.parametrize("name", NAMES)
def test_runs_and_prints_add_hub_hint(name, tmp_path):
    r = subprocess.run([sys.executable, str(EX / f"{name}.py")], cwd=tmp_path,
                       capture_output=True, text=True, timeout=60,
                       env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(EX.parent)})
    assert "Add Hub" in r.stdout, r.stderr
