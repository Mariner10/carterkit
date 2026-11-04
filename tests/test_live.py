"""carterkit.live: a layout file served live; a save reaches the phone."""
import asyncio
import os
import textwrap

import pytest

from carterkit import livefile as live, repl
from carterkit.hub import Hub


FILE_V1 = textwrap.dedent('''
    import asyncio
    from carterkit import Layout
    with Layout("Demo", cols=4, rows=3) as ui:
        gauge = ui.gauge("level", label="Level", min=0, max=100, listen="level")
        button = ui.button("reset", label="Reset", send="reset")
    STARTS = []
    async def run(hub):
        @button.on
        async def reset(frame): return {"ok": True}
        STARTS.append(1)
        await asyncio.sleep(3600)
''')

FILE_V2 = FILE_V1.replace('button = ui.button("reset", label="Reset", send="reset")',
                          'button = ui.button("reset", label="Reset", send="reset")\n'
                          '    note = ui.label("note", text="new", listen="note")')


class _Pushes:
    """Counts push_layout calls on a real (unconnected) Hub."""

    def __init__(self):
        self.count = 0

    async def __call__(self):
        self.count += 1
        return {"ok": True}


def _write(path, text):
    path.write_text(text)
    os.utime(path, None)


def test_load_requires_a_layout(tmp_path):
    f = tmp_path / "nolayout.py"
    f.write_text("x = 1\n")
    with pytest.raises(SystemExit) as e:
        live.LiveFile(str(f)).load()
    assert "no Layout found" in str(e.value)
    f.write_text("import nope_module\n")
    with pytest.raises(SystemExit) as e:
        live.LiveFile(str(f)).load()
    assert "importing" in str(e.value)


def test_make_hub_uses_the_saved_pairing(tmp_path, monkeypatch):
    monkeypatch.setenv("CARTERKIT_HOST", "127.0.0.1")
    f = tmp_path / "hello.py"
    f.write_text(FILE_V1)
    session = str(tmp_path / ".carterkit" / "session.json")
    lf = live.LiveFile(str(f), session_path=session)
    ui, module_hub, run = lf.load()
    assert module_hub is None and callable(run)
    hub, reused = lf.make_hub(ui, None)
    assert isinstance(hub, Hub) and reused is False
    hub2, reused2 = live.LiveFile(str(f), session_path=session).make_hub(ui, None)
    assert reused2 is True and hub2.connection.key == hub.connection.key


def test_reload_pushes_rebinds_and_restarts_run(tmp_path, monkeypatch):
    monkeypatch.setenv("CARTERKIT_HOST", "127.0.0.1")
    f = tmp_path / "hello.py"
    _write(f, FILE_V1)
    lf = live.LiveFile(str(f), session_path=str(tmp_path / "s.json"), out=lambda s: None)
    ui, _, run = lf.load()
    hub, _ = lf.make_hub(ui, None)
    lf.hub = hub
    lf.attach(ui)
    pushes = _Pushes()
    monkeypatch.setattr(hub, "push_layout", pushes)

    async def go():
        await lf.start_run(run)
        await asyncio.sleep(0.05)
        first_task = lf.run_task
        assert first_task is not None and not first_task.done()
        assert "reset" in hub._demux             # run() armed the button handler
        ns, names = repl.build_namespace(hub, lf.ui)
        ns[live._NS_CONTROLS] = names
        lf.ns = ns
        assert "note" not in ns
        _write(f, FILE_V2)
        assert await lf.reload() is True
        await asyncio.sleep(0.05)
        assert pushes.count == 1
        assert "note" in hub._index and "note" in ns and ns["note"].id == "note"
        assert first_task.cancelled() and lf.run_task is not first_task
        assert "reset" in hub._demux and len(hub._demux["reset"]) == 1   # re-armed once
        # A broken save keeps the last good version.
        _write(f, "import nope_module\n")
        assert await lf.reload() is False
        assert "note" in hub._index and pushes.count == 1
        await lf.stop_run()

    asyncio.run(go())


def test_watch_reloads_on_mtime_change(tmp_path, monkeypatch):
    monkeypatch.setenv("CARTERKIT_HOST", "127.0.0.1")
    f = tmp_path / "hello.py"
    _write(f, FILE_V1)
    lf = live.LiveFile(str(f), session_path=str(tmp_path / "s.json"), out=lambda s: None)
    ui, _, _ = lf.load()
    hub, _ = lf.make_hub(ui, None)
    lf.hub = hub
    lf.attach(ui)
    monkeypatch.setattr(hub, "push_layout", _Pushes())
    seen = []

    async def fake_reload():
        seen.append(1)
        return True

    monkeypatch.setattr(lf, "reload", fake_reload)

    async def go():
        task = asyncio.create_task(lf.watch(interval=0.05))
        await asyncio.sleep(0.15)
        assert seen == []
        f.write_text(FILE_V2)
        os.utime(f, (1, 2))                     # a different mtime for sure
        await asyncio.sleep(0.4)
        task.cancel()
        assert seen == [1]

    asyncio.run(go())


def test_refresh_namespace_drops_removed_controls():
    class H:
        layout = {"tabs": [{"children": [{"id": "a", "type": "label"}]}]}
    ns = {"hub": H(), "old": 1, live._NS_CONTROLS: ["old"]}
    names = live.refresh_namespace(ns, H(), None)
    assert names == ["a"] and "old" not in ns and "a" in ns


def test_scaffold_hello_matches_the_live_contract():
    from importlib.resources import files
    text = (files("carterkit") / "scaffold_templates" / "hello.py").read_text()
    assert "async def run(hub)" in text and "livefile.main(__file__)" in text
    assert "hub.json" in text and "Add Hub" not in text


def test_reload_survives_an_attach_error(tmp_path, monkeypatch):
    monkeypatch.setenv("CARTERKIT_HOST", "127.0.0.1")
    f = tmp_path / "hello.py"
    _write(f, FILE_V1)
    out = []
    lf = live.LiveFile(str(f), session_path=str(tmp_path / "s.json"), out=out.append)
    ui, _, _ = lf.load()
    hub, _ = lf.make_hub(ui, None)
    lf.hub = hub
    lf.attach(ui)

    def boom(ui):
        raise RuntimeError("attach exploded")

    monkeypatch.setattr(lf, "attach", boom)
    assert asyncio.run(lf.reload()) is False
    assert any("reload failed" in s and "still watching" in s for s in out)


def test_watch_survives_a_reload_exception(tmp_path, monkeypatch):
    monkeypatch.setenv("CARTERKIT_HOST", "127.0.0.1")
    f = tmp_path / "hello.py"
    _write(f, FILE_V1)
    out = []
    lf = live.LiveFile(str(f), session_path=str(tmp_path / "s.json"), out=out.append)
    calls = []

    async def bad_reload():
        calls.append(1)
        raise RuntimeError("boom")

    monkeypatch.setattr(lf, "reload", bad_reload)

    async def go():
        task = asyncio.create_task(lf.watch(interval=0.05))
        await asyncio.sleep(0.12)
        f.write_text(FILE_V2)
        os.utime(f, (1, 2))
        await asyncio.sleep(0.4)
        f.write_text(FILE_V1)
        os.utime(f, (3, 4))
        await asyncio.sleep(0.4)
        task.cancel()

    asyncio.run(go())
    assert calls == [1, 1] and any("still watching" in s for s in out)
