"""carterkit tutorial: list, steps, --start, --check; the vendored tutorials; carterkit.testing."""
import asyncio
import json
import re
from pathlib import Path

import pytest

from carterkit import scaffold, tutorials
from carterkit.cli import main
from carterkit.testing import FakeHub, load_hub_module

CODE_TUTORIALS = [t for t, m in tutorials.index().items() if m["audience"] in ("code", "both")]
KITS_DIR = Path(scaffold.__file__).parent / "scaffold_templates" / "kits"


def test_list_and_steps(capsys):
    assert main(["tutorial"]) == 0
    out = capsys.readouterr().out
    assert "first-hub" in out and "live-dashboard" in out and "first-layout" in out
    assert main(["tutorial", "list"]) == 0
    assert main(["tutorial", "steps", "first-hub"]) == 0
    text = capsys.readouterr().out
    assert text.count("\nStep ") == len(tutorials.get("first-hub")["steps"])
    assert "You should see:" in text and "[[" not in text           # references rendered
    assert main(["tutorial", "first-hub"]) == 0                      # a bare id reads it too
    assert main(["tutorial", "nope"]) == 1
    assert "no tutorial 'nope'" in capsys.readouterr().err


def test_references_render_for_the_terminal():
    assert tutorials.render_ref("control.gauge") == "gauge (carterkit doc gauge)"
    assert tutorials.render_ref("gauge.max") == "max (carterkit doc gauge --field max)"
    assert tutorials.render_ref("gauge.max|the top of the dial") == "the top of the dial"
    assert tutorials.render_ref("tutorial:first-hub") == "carterkit tutorial steps first-hub"
    assert tutorials.render_ref("data-flow") == "data-flow"
    assert tutorials.render_ref("kit.hub.push").startswith("hub.push(")
    assert tutorials.render_ref("kit.layout.load").startswith("layout.load(")


def test_app_tutorial_reads_but_has_nothing_to_start_or_check(tmp_path, capsys):
    assert main(["tutorial", "steps", "first-layout"]) == 0
    assert "done in the app" in capsys.readouterr().out
    assert main(["tutorial", "--start", "first-layout", str(tmp_path / "x")]) == 1
    assert main(["tutorial", "--check", "first-layout", "--step", "1"]) == 1


@pytest.mark.parametrize("tid", CODE_TUTORIALS)
def test_regions_are_the_tutorials_code(tid):
    """Each step's python block is exactly the kit's marked region: the code exists once."""
    meta = tutorials.get(tid)
    hub = (KITS_DIR / meta["starterKit"] / "hub.py").read_text()
    regions = {m.group(1): m.group(2).strip("\n") for m in tutorials._REGION.finditer(hub)}
    secs = tutorials.sections(tid)
    named = {}
    for st in meta["steps"]:
        for lang, _flags, name, code in tutorials.blocks(secs[st["id"]]):
            if lang == "python":
                named[name] = code
    assert named and named == {k: v for k, v in regions.items() if k in named}
    assert set(regions) == set(named)                                 # no region the tutorial skips
    layout = next(code for st in meta["steps"] for lang, fl, _n, code in tutorials.blocks(secs[st["id"]])
                  if lang == "json" and "layout" in fl)
    kit_layout = json.loads((KITS_DIR / meta["starterKit"] / "layout.json").read_text())
    assert json.loads(layout) == json.loads(json.dumps(kit_layout).replace("__ID__", json.loads(layout)["id"]))


@pytest.mark.parametrize("tid", CODE_TUTORIALS)
def test_start_then_follow_every_step(tid, tmp_path):
    """--start gives the skeleton; typing each step's code in makes that step's check pass,
    and the start state fails step 1 until you do."""
    dest = tmp_path / "proj"
    tutorials.start(tid, str(dest))
    meta, secs = tutorials.get(tid), tutorials.sections(tid)
    assert "# tutorial:" not in (dest / "hub.py").read_text()
    assert [r[2] for r in tutorials.check(tid, 1, str(dest))] != [[]]            # not done yet
    skeleton = (dest / "hub.py").read_text()
    split = skeleton.index('if __name__ == "__main__":')
    head, tail, code = skeleton[:split], skeleton[split:], []
    for n, st in enumerate(meta["steps"], 1):
        for lang, flags, _name, text in tutorials.blocks(secs[st["id"]]):
            if lang == "json" and "layout" in flags:
                (dest / "layout.json").write_text(text + "\n")
            if lang == "python" and "run" in flags:
                code.append(text)
        (dest / "hub.py").write_text(head + "\n\n".join(code) + "\n\n\n" + tail)
        rows = tutorials.check(tid, n, str(dest))
        assert len(rows) == n and all(not bad for _, _, bad in rows), rows
    # the finished project is the starter kit's hub: same behaviour
    kit = tmp_path / "kit"
    scaffold.scaffold(str(kit), template=meta["starterKit"])
    assert all(not bad for _, _, bad in tutorials.check(tid, len(meta["steps"]), str(kit)))


def test_check_names_the_failing_step_in_the_steps_own_words(tmp_path, capsys):
    dest = tmp_path / "proj"
    scaffold.scaffold(str(dest), template="remote")
    hub = dest / "hub.py"
    hub.write_text(hub.read_text().replace("VOLUME_LIMIT = 80", "VOLUME_LIMIT = 90"))
    assert main(["tutorial", "--check", "first-hub", "--step", "3", "--dir", str(dest)]) == 1
    out = capsys.readouterr().out
    assert "ok    step 1" in out and "FAIL  step 3: Write the hub's rules" in out
    assert "You should see:" in out and "returned 'Volume stops at 90'" in out
    assert main(["tutorial", "--check", "first-hub", "--step", "99", "--dir", str(dest)]) == 1
    assert main(["tutorial", "--check", "first-hub"]) == 2


def test_check_reports_a_broken_project(tmp_path, capsys):
    (tmp_path / "hub.py").write_text("raise RuntimeError('boom')\n")
    (tmp_path / "layout.json").write_text("{not json")
    rows = tutorials.check("live-dashboard", 1, str(tmp_path))
    bad = " ".join(rows[0][2])
    assert "layout.json" in bad and "hub.py does not load: RuntimeError: boom" in bad


def test_start_refuses_a_non_empty_folder(tmp_path, capsys):
    (tmp_path / "x").mkdir()
    (tmp_path / "x" / "f").write_text("")
    assert main(["tutorial", "--start", "first-hub", str(tmp_path / "x")]) == 1
    assert "not empty" in capsys.readouterr().err


def test_index_matches_the_vendored_frontmatter():
    yaml = pytest.importorskip("yaml")
    for tid, meta in tutorials.index().items():
        raw = (Path(tutorials.__file__).parent / "tutorials" / f"{tid}.md").read_text()
        assert yaml.safe_load(re.match(r"---\n(.*?)\n---\n", raw, re.S).group(1)) == meta
        assert meta["id"] == tid


def test_vendored_tutorials_have_a_source_pin():
    src = (Path(tutorials.__file__).parent / "tutorials" / "SOURCE").read_text()
    assert re.search(r"^commit: [0-9a-f]{40}$", src, re.M) and "path: dev-guide/tutorials" in src


def test_fakehub_records_frames_and_answers_prompts():
    from carterkit import Layout
    ui = Layout.load({"name": "T", "tabs": [{"id": "t", "title": "T", "grid": {"columns": 2, "rows": 2},
                      "children": [{"type": "label", "id": "msg", "position": [0, 0], "label": "M", "text": "x",
                                    "sync": [{"method": "meshsocket", "type": "listen", "event": "broadcast",
                                              "valuePath": "text", "filter": {"msg_type": "m"}}]}]}]})

    async def go():
        fake = FakeHub(ui, answer="cancel")
        await fake.hub.push("msg", "hello")
        return fake

    fake = asyncio.run(go())
    assert fake.frames("m") == [{"msg_type": "m", "text": "hello"}] and fake.frames("other") == []
    assert fake.routed("prompt") == []


def test_fakehub_running_drives_a_hub_py(tmp_path):
    scaffold.scaffold(str(tmp_path / "r"), template="remote")
    mod = load_hub_module(tmp_path / "r" / "hub.py")
    fake = FakeHub(mod.ui)

    async def go():
        async with fake.running(mod.run):
            await fake.dispatch({"msg_type": "set_volume", "value": 95})

    asyncio.run(go())
    assert fake.frames("volume_state")[-1]["value"] == 80
