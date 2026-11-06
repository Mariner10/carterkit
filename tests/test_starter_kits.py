"""Each starter kit's hub.py imports and its handlers answer a fake hub (no relay, no phone)."""
import asyncio
import importlib.util
import json
import os
import subprocess
import sys

import pytest

from carterkit import Layout, scaffold
from carterkit.livefile import LiveFile
from test_hub import _FakeSock


class _PhoneSock(_FakeSock):
    """One phone on the channel; it answers confirm prompts with `answer` and accepts sheets."""

    def __init__(self, holder, answer="confirm"):
        super().__init__()
        self.holder, self.answer = holder, answer

    async def request(self, t, payload=None, timeout=5.0):
        self.sent.append(("REQ:" + t, payload))
        if t == "get_nodes":
            return {"clients": [{"id": "dev1", "name": "phone"}]}
        if t == "route_msg" and payload["type"] == "prompt":
            pid = payload["payload"]["id"]
            reply = {"msg_type": "prompt_reply", "id": pid, "choice": self.answer}
            asyncio.get_running_loop().call_later(
                0.01, lambda: asyncio.ensure_future(self.holder[0]._dispatch(reply)))
            return {"ok": True, "queued": 0}
        if t == "route_msg":
            return {"ok": True}
        return None


def _load(tmp_path, kit, answer="confirm"):
    d = tmp_path / kit
    scaffold.scaffold(str(d), template=kit)
    spec = importlib.util.spec_from_file_location(f"kit_{kit.replace('-', '_')}", d / "hub.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert all(f["severity"] != "error" for f in mod.ui.validate())
    hub = mod.ui.serve()
    hub.client._sock = _PhoneSock([hub], answer)
    return mod, hub


def _frames(hub, msg_type=None):
    out = [p for t, p in hub.client._sock.sent if t == "broadcast_request"]
    return [p for p in out if msg_type is None or p.get("msg_type") == msg_type]


def _routed(hub, kind):
    return [p["payload"] for t, p in hub.client._sock.sent
            if t == "REQ:route_msg" and p["type"] == kind]


async def _start(mod, hub):
    task = asyncio.create_task(mod.run(hub))
    await asyncio.sleep(0.02)
    return task


async def _stop(task):
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


def test_paged_cards_pages_searches_and_answers_taps(tmp_path):
    mod, hub = _load(tmp_path, "paged-cards")

    async def go():
        task = await _start(mod, hub)
        await hub._dispatch({"msg_type": "cards_pages", "offset": 0, "limit": 20,
                             "cursor": None, "query": "", "req": "r1"})
        await hub._dispatch({"msg_type": "cards_pages", "offset": 0, "limit": 20,
                             "cursor": None, "query": "item 12", "req": "r2"})
        await hub._dispatch({"msg_type": "card_star", "id": "item-3"})
        await hub._dispatch({"msg_type": "card_open", "id": "item-3"})
        await _stop(task)
    asyncio.run(go())
    first, search = _frames(hub, "cards_page")
    assert first["req"] == "r1" and len(first["items"]) == 20 and first["more"] is True
    assert first["total"] == len(mod.ITEMS) and first["items"][0]["name"] == "Item 1"
    assert search["req"] == "r2" and search["query"] == "item 12"
    assert {r["name"] for r in search["items"]} >= {"Item 12", "Item 120"}
    assert all("12" in r["name"] for r in search["items"])
    status = [f["text"] for f in _frames(hub, "cards_status")]
    assert status == ["Starred Item 3", "Opened Item 3"]


@pytest.mark.parametrize("answer", ["confirm", "cancel"])
def test_confirm_delete_asks_first(tmp_path, answer):
    mod, hub = _load(tmp_path, "confirm-delete", answer)

    async def go():
        task = await _start(mod, hub)
        await hub._dispatch({"msg_type": "thing_delete", "id": "thing-2"})
        await _stop(task)
    asyncio.run(go())
    (prompt,) = _routed(hub, "prompt")
    assert prompt["title"] == "Delete Thing 2?"
    assert prompt["confirm"] == {"label": "Delete", "role": "destructive"}
    ids = [t["id"] for t in mod.things]
    status = _frames(hub, "things_status")[-1]["text"]
    if answer == "confirm":
        assert "thing-2" not in ids and status == "Deleted Thing 2"
        assert [t["id"] for t in _frames(hub, "things")[-1]["items"]] == ids
    else:
        assert "thing-2" in ids and status == "Kept Thing 2 (cancel)"


def test_confirm_delete_all_and_restore(tmp_path):
    mod, hub = _load(tmp_path, "confirm-delete")

    async def go():
        task = await _start(mod, hub)
        await hub._dispatch({"msg_type": "things_clear"})
        assert mod.things == []
        await hub._dispatch({"msg_type": "things_restore"})
        await _stop(task)
    asyncio.run(go())
    assert len(_routed(hub, "prompt")) == 1 and len(mod.things) == 6
    assert _frames(hub, "things_status")[-1]["text"] == "Restored the placeholder rows"


def test_live_dashboard_streams_and_resets(tmp_path):
    mod, hub = _load(tmp_path, "live-dashboard")
    mod.INTERVAL = 0.005

    async def go():
        task = await _start(mod, hub)
        await asyncio.sleep(0.05)
        await hub._dispatch({"msg_type": "reset"})
        await _stop(task)
    asyncio.run(go())
    levels = [f["level"] for f in _frames(hub, "metrics")]
    assert len(levels) >= 3 and all(0 <= v <= 100 for v in levels)
    assert 50.0 in levels
    assert all(f["text"].startswith(tuple("0123456789")) for f in _frames(hub, "readout"))
    gauge, trend = hub._index["level"], hub._index["trend"]
    assert gauge["sync"][0]["filter"] == trend["sync"][0]["filter"]   # one push, both move


def test_hub_form_saves_and_refuses(tmp_path):
    mod, hub = _load(tmp_path, "hub-form")
    good = {"name": "Example", "count": 3, "choice": "Option B", "urgent": True}

    async def go():
        task = await _start(mod, hub)
        await hub._dispatch({"msg_type": "form_submit", "form": good})
        await hub._dispatch({"msg_type": "form_submit", "form": dict(good, name="example")})
        await hub._dispatch({"msg_type": "form_submit", "form": dict(good, name="Other", count=40)})
        await _stop(task)
    asyncio.run(go())
    assert mod.entries == [{"name": "Example", "count": 3, "choice": "Option B", "urgent": "Yes"}]
    assert _frames(hub, "form_entries")[-1]["items"] == mod.entries
    status = [f["text"] for f in _frames(hub, "form_status")]
    assert status == ["Saved Example (1 so far)", "Not saved: example is already in the list",
                      "Not saved: Count must be 1 to 10"]
    submit = hub._index["entry-form"]["form"]["submit"]
    assert submit["payload"] == {"msg_type": "form_submit", "form": "{{form}}"}


def test_scaled_grid_scale_and_hub_sheet(tmp_path):
    mod, hub = _load(tmp_path, "scaled-grid")
    rows = [c for c in mod.ui.layout["tabs"][0]["children"] if c["type"] == "group"]
    assert rows and all(g["span"] == [1, 5] and g["grid"] == {"columns": 15, "rows": 3, "scale": "auto"}
                        for g in rows)

    async def go():
        task = await _start(mod, hub)
        await hub._dispatch({"msg_type": "slot_power", "slot": "b2", "value": True})
        await hub._dispatch({"msg_type": "slot_open", "slot": "b2"})
        await hub._dispatch({"msg_type": "sheet_done", "sheet": "card-b2"})
        await hub._dispatch({"msg_type": "sheet_closed", "id": "card-b2", "reason": "hub"})
        await _stop(task)
    asyncio.run(go())
    opened, closed = _routed(hub, "sheet")
    assert opened["id"] == "card-b2" and opened["style"] == "sheet" and opened["title"] == "Card B2"
    assert opened["group"]["type"] == "group"
    assert [c["text"] for c in opened["group"]["children"] if c["type"] == "label"] == ["B2", "On"]
    assert closed == {"id": "card-b2", "close": True, "from": hub.name}
    status = [f["text"] for f in _frames(hub, "grid_status")]
    assert status == ["B2 is on", "Opened card B2", "Closed card-b2 (hub)"]


def test_remote_hub_owns_the_state(tmp_path):
    mod, hub = _load(tmp_path, "remote")

    async def go():
        task = await _start(mod, hub)
        await hub._dispatch({"msg_type": "set_volume", "value": 95})
        await hub._dispatch({"msg_type": "set_power", "value": False})
        await hub._dispatch({"msg_type": "set_brightness", "value": 10})
        await _stop(task)
    asyncio.run(go())
    assert mod.STATE == {"power": False, "mute": False, "volume": 80, "brightness": 70}
    volumes = [f["value"] for f in _frames(hub, "volume_state")]
    assert volumes[0] == 30 and 80 in volumes
    # refused while off: the hub still resends its brightness so the slider snaps back
    assert [f["value"] for f in _frames(hub, "brightness_state")][-1] == 70
    assert len(_frames(hub, "brightness_state")) == 4
    status = [f["text"] for f in _frames(hub, "remote_status")]
    assert status == ["Ready", "Volume stops at 80", "Power off",
                      "Power is off: brightness stays as it was"]


@pytest.mark.parametrize("kit", list(scaffold.KITS))
def test_kit_runs_with_python_and_prints_the_qr(tmp_path, kit):
    d = tmp_path / "demo"
    scaffold.scaffold(str(d), template=kit)
    env = {"PYTHONPATH": os.getcwd(), "PATH": "", "CARTERKIT_HOST": "127.0.0.1",
           "CARTERKIT_PAIR_TIMEOUT": "1"}
    r = subprocess.run([sys.executable, str(d / "hub.py")], capture_output=True, text=True,
                       env=env, cwd=str(d), timeout=60)
    assert "Scan this with the CAR-TER app" in r.stdout, r.stdout + r.stderr
    assert "No phone joined" in r.stdout and r.returncode == 1
    assert (d / ".carterkit" / "session.json").is_file()


def test_layout_load_from_a_file_or_a_dict(tmp_path):
    src = {"name": "Saved", "tabs": [{"id": "t", "title": "T", "grid": {"columns": 3, "rows": 5},
                                      "children": [{"type": "button", "id": "b", "position": [0, 0],
                                                    "label": "B", "action": {
                                                        "method": "meshsocket",
                                                        "event": "broadcast_request",
                                                        "payload": {"msg_type": "b"}}}]}]}
    path = tmp_path / "layout.json"
    path.write_text(json.dumps(src))
    ui = Layout.load(path)
    assert ui.layout == src and ui._source_path == str(path)
    hub = ui.serve()
    assert "b" in hub._index and ui.layout["connection"]
    assert src.get("connection") is None                   # a copy, the source is untouched
    with ui.tab("More"):
        ui.label("extra", text="x")
    assert [t["title"] for t in ui.layout["tabs"]] == ["T", "More"]
    assert Layout.load(src).layout["tabs"][0]["grid"] == {"columns": 3, "rows": 5}
    with pytest.raises(ValueError):
        Layout.load({"name": "Empty", "tabs": []})


def test_livefile_watches_the_loaded_layout_json(tmp_path):
    d = tmp_path / "w"
    scaffold.scaffold(str(d), template="remote")
    live = LiveFile(str(d / "hub.py"))
    live.ui, _, _ = live.load()
    before = live.stat()
    os.utime(d / "layout.json", ns=(before + 5_000_000_000, before + 5_000_000_000))
    assert live.stat() == before + 5_000_000_000


def test_push_force_resends_an_identical_frame(tmp_path):
    mod, hub = _load(tmp_path, "remote")

    async def go():
        await hub.push("volume", 30)
        await hub.push("volume", 30)                       # skipped: same as the last push
        await hub.push("volume", 30, force=True)
    asyncio.run(go())
    assert len(_frames(hub, "volume_state")) == 2
