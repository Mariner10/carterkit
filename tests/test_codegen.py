"""Tests for codegen.py — the hub script (generate_hub), the service stub, the REST adapter."""

import asyncio
import importlib.util
import json
import os
import re
import subprocess
import sys

import pytest
from test_starter_kits import _frames, _load, _PhoneSock, _routed, _start, _stop

from carterkit import cli, codegen, scaffold

LAYOUT = {
    "name": "Rover", "version": 1,
    "connection": {"url": "ws://10.0.0.5:8765", "token": "tok"},
    "tabs": [{"title": "Main", "icon": "house.fill",
              "grid": {"columns": 4, "rows": 4}, "children": [
                  {"type": "gauge", "id": "battery", "position": [0, 0],
                   "sync": [{"method": "meshsocket", "type": "listen",
                             "event": "broadcast", "valuePath": "battery"}]},
                  {"type": "gauge", "id": "temp", "position": [0, 2],
                   "sync": [{"method": "meshsocket", "type": "listen",
                             "event": "broadcast", "valuePath": "sensors.cpu_temp"}]},
                  {"type": "button", "id": "stop", "position": [2, 0],
                   "action": {"method": "meshsocket", "mode": "request",
                              "event": "emergency_stop", "payload": {}}},
              ]}]}


def test_analyze_layout_contract():
    spec = codegen.analyze_layout(LAYOUT)
    assert spec["actions"] == {"emergency_stop": "request"}
    assert spec["emits"]["broadcast"] == ["battery", "sensors.cpu_temp"]


def test_service_stub_compiles_and_mentions_contract():
    code = codegen.generate_service_stub(LAYOUT)
    compile(code, "<stub>", "exec")  # must be valid Python
    assert "emergency_stop" in code
    assert "battery" in code and "sensors.cpu_temp" in code
    assert "ws://10.0.0.5:8765" in code  # connection carried through


def test_rest_adapter_compiles_and_maps_fields():
    code = codegen.generate_rest_adapter(LAYOUT, base_url="https://rover.local/api")
    compile(code, "<adapter>", "exec")
    assert "https://rover.local/api" in code
    assert "battery" in code and "cpu_temp" in code


def test_empty_layout_still_compiles():
    code = codegen.generate_service_stub({"name": "Empty", "version": 1, "tabs": []})
    compile(code, "<stub>", "exec")


# ── generate_hub: the hub script for a layout, checked against the six starter kits ──

#: Commands a kit's hub.py handles that its layout.json never sends: scaled-grid's Done
#: button lives in a sheet group the hub builds in code, so no generator can see it.
KIT_ONLY = {"scaled-grid": {"sheet_done"}}


def _gen(tmp_path, kit, answer="confirm"):
    """Scaffold `kit`, generate generated.py beside its layout.json, import it and serve it
    on the fake phone socket."""
    d = tmp_path / f"gen-{kit}"
    scaffold.scaffold(str(d), template=kit)
    layout = json.loads((d / "layout.json").read_text())
    (d / "generated.py").write_text(codegen.generate_hub(layout))
    spec = importlib.util.spec_from_file_location(f"gen_{kit.replace('-', '_')}", d / "generated.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert all(f["severity"] != "error" for f in mod.ui.validate())
    hub = mod.ui.serve()
    hub.client._sock = _PhoneSock([hub], answer)
    return mod, hub, layout


def _handled(mod, hub):
    """The commands a hub's run() registers (broadcast demux), read while it runs."""
    async def go():
        task = await _start(mod, hub)
        found = set(hub._demux)
        await _stop(task)
        return found
    return asyncio.run(go())


def _sent_frames(layout):
    """One frame per command the layout sends, filled in by hand (not by the generator)."""
    out = {}

    def fill(v, ctrl):
        if not isinstance(v, str):
            return v
        if v == "{{value}}":
            return {"toggle": True, "slider": 10}.get(ctrl.get("type"), "item-1")
        if v == "{{form}}":
            return {"name": "Example", "count": 3, "choice": "Option B", "urgent": True}
        return "item-1" if v.startswith("{{item.") else v

    def scan(node, ctrl):
        if isinstance(node, dict):
            if node.get("type") or node.get("id"):
                ctrl = node
            for key in ("action", "longPressAction", "submit"):
                a = node.get(key)
                if isinstance(a, dict) and a.get("event") == "broadcast_request":
                    p = a.get("payload") or {}
                    out.setdefault(p["msg_type"], {k: fill(v, ctrl) for k, v in p.items()})
            for k, v in node.items():
                if k != "paging":
                    scan(v, ctrl)
        elif isinstance(node, list):
            for v in node:
                scan(v, ctrl)
    scan(layout, {})
    return out


@pytest.mark.parametrize("kit", list(scaffold.KITS))
def test_generated_handlers_match_the_kits_hub(tmp_path, kit):
    kmod, khub = _load(tmp_path, kit)
    gmod, ghub, layout = _gen(tmp_path, kit)
    if kit == "live-dashboard":
        kmod.INTERVAL = gmod.INTERVAL = 0.005
    kit_set, gen_set = _handled(kmod, khub), _handled(gmod, ghub)
    only = KIT_ONLY.get(kit, set())
    assert gen_set == kit_set - only
    assert not any(c in json.dumps(layout) for c in only)


@pytest.mark.parametrize("kit", list(scaffold.KITS))
def test_generated_hub_answers_every_command(tmp_path, kit):
    mod, hub, layout = _gen(tmp_path, kit)
    frames = _sent_frames(layout)
    assert frames
    ran = []

    async def go():
        task = await _start(mod, hub)
        for frame in frames.values():
            ran.append(await hub._dispatch(dict(frame)))
        await _stop(task)
    asyncio.run(go())
    assert all(ran) and len(ran) == len(frames)
    spec = codegen.analyze_hub(layout)
    if spec["status"]:                     # each handler says what it did on the status label
        status_type = hub._index[spec["status"]]["sync"][0]["filter"]["msg_type"]
        said = [f["text"] for f in _frames(hub, status_type)]
        assert said[0] == "Hub ready" and len(said) == 1 + len(frames)


def test_generated_paged_list_serves_the_template_fields(tmp_path):
    mod, hub, layout = _gen(tmp_path, "paged-cards")
    tpl = json.dumps(layout["tabs"][0]["children"][1]["itemTemplate"])
    bound = set(re.findall(r"\{\{item\.(\w+)\}\}", tpl)) | {"id"}

    async def go():
        task = await _start(mod, hub)
        await hub._dispatch({"msg_type": "cards_pages", "offset": 0, "limit": 20,
                             "cursor": None, "query": "", "req": "r1"})
        await hub._dispatch({"msg_type": "cards_pages", "offset": 0, "limit": 20,
                             "cursor": None, "query": "item 12", "req": "r2"})
        await _stop(task)
    asyncio.run(go())
    first, search = _frames(hub, "cards_page")
    assert first["req"] == "r1" and len(first["items"]) == 20 and first["more"] is True
    assert all(set(row) == bound for row in first["items"])
    assert first["items"][0]["name"] == "Item 1" and first["items"][0]["id"] == "item-1"
    assert search["req"] == "r2" and {r["name"] for r in search["items"]} >= {"Item 12", "Item 120"}


@pytest.mark.parametrize("answer", ["confirm", "cancel"])
def test_generated_delete_asks_first(tmp_path, answer):
    mod, hub, _ = _gen(tmp_path, "confirm-delete", answer)

    async def go():
        task = await _start(mod, hub)
        await hub._dispatch({"msg_type": "thing_delete", "id": "item-2"})
        await hub._dispatch({"msg_type": "things_clear"})
        await hub._dispatch({"msg_type": "things_restore"})
        await _stop(task)
    asyncio.run(go())
    prompts = _routed(hub, "prompt")
    assert [p["title"] for p in prompts] == ["Delete item-2?", "Delete all?"]
    assert all(p["confirm"]["role"] == "destructive" for p in prompts)
    said = [f["text"] for f in _frames(hub, "things_status")]
    if answer == "confirm":
        assert said[1:] == ["Delete: item-2", "Delete all", "Restore"]
    else:
        assert said[1:] == ["Kept it (cancel)", "Kept it (cancel)", "Restore"]
    rows = _frames(hub, "things")[0]["items"]
    assert len(rows) == 6 and set(rows[0]) == {"id", "name", "detail"}


def test_generated_remote_owns_the_state(tmp_path):
    mod, hub, _ = _gen(tmp_path, "remote")

    async def go():
        task = await _start(mod, hub)
        await hub._dispatch({"msg_type": "set_volume", "value": 95})
        await hub._dispatch({"msg_type": "set_volume", "value": 150})     # out of range
        await hub._dispatch({"msg_type": "set_power", "value": "yes"})    # not a bool
        await _stop(task)
    asyncio.run(go())
    assert [f["value"] for f in _frames(hub, "volume_state")] == [50, 95, 95]
    assert [f["value"] for f in _frames(hub, "power_state")] == [False, False]
    assert mod.STATE["volume"] == 95 and mod.STATE["power"] is False


def test_generated_form_checks_the_rules_again(tmp_path):
    mod, hub, _ = _gen(tmp_path, "hub-form")
    good = {"name": "Example", "count": 3, "choice": "Option B", "urgent": True}

    async def go():
        task = await _start(mod, hub)
        for form in (good, dict(good, count=40), dict(good, name=" "), dict(good, choice="Other")):
            await hub._dispatch({"msg_type": "form_submit", "form": form})
        await _stop(task)
    asyncio.run(go())
    assert [f["text"] for f in _frames(hub, "form_status")][1:] == [
        "Saved Example", "Not saved: count must be 1 to 10", "Not saved: name is required",
        "Not saved: choice must be one of Option A, Option B, Option C"]
    assert set(_frames(hub, "form_entries")[0]["items"][0]) == {"id", "name", "count",
                                                                "choice", "urgent"}


def test_generated_dashboard_streams_live_readings(tmp_path):
    mod, hub, _ = _gen(tmp_path, "live-dashboard")
    mod.INTERVAL = 0.005

    async def go():
        task = await _start(mod, hub)
        await asyncio.sleep(0.05)
        await _stop(task)
    asyncio.run(go())
    levels = [f["level"] for f in _frames(hub, "metrics")]
    assert len(levels) >= 3 and all(0 <= v <= 100 for v in levels)
    assert all(f["text"].startswith("Example reading") for f in _frames(hub, "readout"))


def test_generated_sheet_helpers_open_the_layouts_groups(tmp_path):
    mod, hub, _ = _gen(tmp_path, "scaled-grid")

    async def go():
        task = await _start(mod, hub)
        assert await mod.open_row_b(hub) == "row-b"
        await hub._dispatch({"msg_type": "sheet_closed", "id": "row-b", "reason": "user"})
        await _stop(task)
    asyncio.run(go())
    (opened,) = _routed(hub, "sheet")
    assert opened == {"id": "row-b", "groupId": "row-b", "title": "Row B at full size",
                      "style": "sheet", "from": hub.name}
    assert _frames(hub, "grid_status")[-1]["text"] == "Closed row-b (user)"


@pytest.mark.parametrize("kit", list(scaffold.KITS))
def test_generated_hub_runs_with_python_and_prints_the_qr(tmp_path, kit):
    d = tmp_path / "demo"
    scaffold.scaffold(str(d), template=kit)
    assert cli.main(["codegen", str(d / "layout.json"), "-o", str(d / "generated.py")]) == 0
    env = {"PYTHONPATH": os.getcwd(), "PATH": "", "CARTERKIT_HOST": "127.0.0.1",
           "CARTERKIT_PAIR_TIMEOUT": "1"}
    r = subprocess.run([sys.executable, str(d / "generated.py")], capture_output=True, text=True,
                       env=env, cwd=str(d), timeout=60, check=False)
    assert "Scan this with the CAR-TER app" in r.stdout, r.stdout + r.stderr
    assert "No phone joined" in r.stdout and r.returncode == 1


def test_cli_codegen_writes_a_script_that_finds_its_layout(tmp_path, capsys):
    src = tmp_path / "layouts" / "remote.json"
    src.parent.mkdir()
    src.write_text((scaffold.files("carterkit") / "scaffold_templates" / "kits" / "remote"
                    / "layout.json").read_text())
    out = tmp_path / "hubs" / "remote_hub.py"
    out.parent.mkdir()
    assert cli.main(["codegen", str(src), "-o", str(out)]) == 0
    assert 'Path(__file__).parent / "../layouts/remote.json"' in out.read_text()
    assert "5 handler(s)" in capsys.readouterr().out
    assert cli.main(["codegen", str(src), "-o", str(out)]) == 1          # never overwrites
    assert cli.main(["gen", str(src)]) == 0                              # printed, beside it
    printed = capsys.readouterr().out
    assert 'with_name("remote.json")' in printed and "@hub.on(\"power\")" in printed


EVERYTHING = {"name": "Everything", "version": 1, "tabs": [{"id": "t", "title": "Main",
    "grid": {"columns": 4, "rows": 8}, "children": [
        {"type": "button", "id": "remove", "position": [0, 0], "label": "Remove",
         "action": {"method": "meshsocket", "event": "broadcast_request",
                    "payload": {"msg_type": "item.remove", "id": "x"},
                    "confirm": "dialog", "confirmTitle": "Remove this item?",
                    "confirmLabel": "Remove", "destructive": True}},
        {"type": "button", "id": "more", "position": [0, 1], "label": "More",
         "action": {"expand": "pkg"}},
        {"type": "button", "id": "ping", "position": [0, 2], "label": "Ping",
         "action": {"method": "meshsocket", "event": "route_msg",
                    "payload": {"type": "ping", "payload": {"n": "{{value}}"}}},
         "longPressAction": {"method": "meshsocket", "event": "broadcast_request",
                             "payload": {"msg_type": "ping_hold"}}},
        {"type": "progressRing", "id": "ring", "position": [1, 0],
         "sync": [{"method": "meshsocket", "type": "listen", "event": "broadcast",
                   "valuePath": "v", "filter": {"msg_type": "ring"}}]},
        {"type": "chart", "id": "chart", "position": [1, 1],
         "sync": [{"method": "meshsocket", "type": "listen", "event": "broadcast",
                   "valuePath": "data", "filter": {"msg_type": "chart"}}]},
        {"type": "picker", "id": "mode", "position": [1, 2], "options": ["Low", "High"],
         "action": {"method": "meshsocket", "event": "broadcast_request",
                    "payload": {"msg_type": "set_mode", "value": "{{value}}"}}},
        {"type": "group", "id": "pkg", "label": "Package", "position": [2, 0], "span": [2, 4],
         "dynamic": "pkg_children", "grid": {"columns": 4, "rows": 1},
         "expand": {"style": "sheet", "title": "Example package"}, "children": []},
    ]}]}


def test_generate_hub_covers_every_hub_facing_kind():
    spec = codegen.analyze_hub(EVERYTHING)
    cmds = {e["command"]: e for e in spec["commands"]}
    assert set(cmds) == {"item.remove", "ping", "ping_hold", "set_mode"}
    assert cmds["item.remove"]["confirm"]["confirmLabel"] == "Remove"
    assert cmds["item.remove"]["ask"] is False            # the app asks; the hub must not ask again
    assert cmds["ping"]["register"] == "ping"             # two actions on one control: by command
    assert cmds["set_mode"]["register"] == "mode"
    assert spec["expand_verbs"] == [{"id": "more", "label": "More", "verb": "expand", "group": "pkg"}]
    assert [s["group"] for s in spec["sheets"]] == ["pkg"]
    assert {p["id"]: p["role"] for p in spec["pushes"]} == {"ring": "live", "chart": "other"}
    code = codegen.generate_hub(EVERYTHING)
    compile(code, "<everything>", "exec")
    assert 'confirm: "dialog"' in code and "hub.confirm(" in code      # as a note, not a call
    assert re.search(r"^\s+choice = await hub.confirm", code, re.MULTILINE) is None
    assert 'hub.fill("pkg", children)' in code and 'runs expand on group "pkg"' in code
    assert 'round(random.random(), 2)' in code and '# await hub.push("chart"' in code
    assert 'if value not in ["Low", "High"]:' in code
