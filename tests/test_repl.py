"""carterkit repl: driven over stdin with a fake hub."""
import asyncio
import io

import pytest

from carterkit import Layout, cli, repl


class FakeHub:
    def __init__(self, layout):
        self.layout = layout.layout
        self._layout_obj = layout
        self.started = self.closed = False
        self.pushed = []

    async def start(self):
        self.started = True

    async def close(self):
        self.closed = True

    async def push(self, target, value):
        if value == "bad":
            raise RuntimeError("no device on the channel\nsecond line")
        self.pushed.append((target.id, value))
        return {}


def _ui():
    with Layout("T", id="t") as ui:
        with ui.tab("Main"):
            ui.gauge("temp", label="T", listen="temp")
            ui.toggle("fan-1", label="F", listen="fan")
    return ui


def _drive(monkeypatch, capsys, text):
    ui = _ui()
    hub = FakeHub(ui)
    ui._active_hub = hub
    monkeypatch.setattr("sys.stdin", io.StringIO(text))
    asyncio.run(repl.run_repl(hub, ui))
    return hub, capsys.readouterr()


def test_namespace_and_banner(monkeypatch, capsys):
    hub, out = _drive(monkeypatch, capsys, "")
    lines = out.err.strip().splitlines()
    assert hub.started and hub.closed
    assert "hub connected" in lines[0]
    assert "temp" in lines[1] and "fan_1" in lines[1]
    assert len([l for l in lines if l.startswith(("carterkit repl", "bound", "top-level"))]) == 3


def test_await_push_and_clean_disconnect(monkeypatch, capsys):
    hub, out = _drive(monkeypatch, capsys, "await temp.push(21.5)\nawait fan_1.push(True)\n1+1\n")
    assert hub.pushed == [("temp", 21.5), ("fan-1", True)]
    assert "2" in out.out
    assert hub.closed


def test_push_error_is_one_line(monkeypatch, capsys):
    hub, out = _drive(monkeypatch, capsys, 'await temp.push("bad")\nawait temp.push(1)\n')
    assert "Traceback" not in out.err
    errs = [l for l in out.err.splitlines() if l.startswith("error:")]
    assert errs == ["error: RuntimeError: no device on the channel"]
    assert hub.pushed == [("temp", 1)]      # the prompt survives the error


def test_plain_exception_one_line(monkeypatch, capsys):
    _, out = _drive(monkeypatch, capsys, "1/0\n")
    assert "Traceback" not in out.err and "error: ZeroDivisionError" in out.err


def test_cli_registered_and_missing_hub_opens_the_playground(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from carterkit import start
    called = []

    async def fake_run(**kw):
        called.append(kw)
        return 0

    monkeypatch.setattr(start, "run", fake_run)
    assert cli.main(["repl"]) == 0
    assert called == [{}]


def test_missing_hub_with_a_file_still_says_so(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "empty.py").write_text("x = 1\n")
    with pytest.raises(SystemExit) as e:
        cli.main(["repl", "empty.py"])
    assert "no Layout found" in str(e.value)


def test_completion_binds_the_namespace(monkeypatch):
    pytest.importorskip("readline")
    import readline
    ns = {"level": object(), "hub": object()}
    assert repl.enable_completion(ns) is True
    comp = readline.get_completer()
    assert comp is not None and comp("lev", 0) == "level"


def test_handle_help_says_what_a_control_does():
    assert "push" in repl._Handle.__doc__ and ".on" in repl._Handle.__doc__


def test_find_targets_from_module(tmp_path):
    pytest.importorskip("meshsocket")
    f = tmp_path / "hello.py"
    f.write_text("from carterkit import Layout\nwith Layout('H', id='h') as ui:\n"
                 "    with ui.tab('A'):\n        ui.gauge('g', label='G', listen='g')\n"
                 "hub = ui.serve()\n")
    hub, ui = repl.prepare(str(f))
    ns, names = repl.build_namespace(hub, ui)
    assert names == ["g"] and ns["hub"] is hub
