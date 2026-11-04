"""`carterkit start`: the Playground, the saved pairing, the pairing banner, the flow."""
import asyncio
import json

import pytest

from carterkit import cli, playground, start


def test_playground_validates_and_binds_the_four_controls():
    ui = playground.build_playground()
    assert ui.validate() == []
    ids = [c["id"] for t in ui.layout["tabs"] for c in t["children"]]
    assert ids == list(playground.CONTROL_IDS)
    kinds = {c["id"]: c["type"] for t in ui.layout["tabs"] for c in t["children"]}
    assert kinds == {"hello": "label", "level": "gauge", "dial": "slider", "tap": "button"}


def test_session_roundtrip_and_reuse(tmp_path, monkeypatch):
    monkeypatch.setenv(start.HOST_ENV, "127.0.0.1")
    path = str(tmp_path / ".carterkit" / "session.json")
    ui, hub, reused = start.serve_playground(session_path=path, port=18765)
    assert reused is False
    saved = json.load(open(path))
    assert saved == {"channel": hub.connection.channel, "key": hub.connection.key, "port": 18765}
    ui2, hub2, reused2 = start.serve_playground(session_path=path)
    assert reused2 is True
    assert (hub2.connection.channel, hub2.connection.key, hub2.connection.port) == (
        hub.connection.channel, hub.connection.key, 18765)
    _, hub3, reused3 = start.serve_playground(session_path=path, fresh=True)
    assert reused3 is False and hub3.connection.key != hub.connection.key


def test_load_session_rejects_junk(tmp_path):
    p = tmp_path / "s.json"
    assert start.load_session(str(p)) is None
    p.write_text("not json")
    assert start.load_session(str(p)) is None
    p.write_text(json.dumps({"channel": "x"}))
    assert start.load_session(str(p)) is None


def test_pairing_lines_carry_qr_json_and_the_scan_hint(tmp_path, monkeypatch):
    monkeypatch.setenv(start.HOST_ENV, "127.0.0.1")
    _, hub, _ = start.serve_playground(session_path=str(tmp_path / "s.json"))
    text = "\n".join(start.pairing_lines(hub, reused=True))
    payload = json.loads(hub.qr_json())
    assert "Scan this with the CAR-TER app" in text
    assert hub.qr_json() in text                      # the JSON fallback
    assert "█" in text or "▀" in text       # the half-block QR
    assert start.SCAN_HINT in text
    assert "Reusing the last pairing" in text
    assert payload["url"].startswith("ws://") and payload["channel"] == hub.connection.channel


class _FakeHub:
    """Stands in for Hub: records the order start.run drives it in."""

    def __init__(self, *, join: bool):
        self.calls, self.join = [], join
        from carterkit.connection import Connection
        self.connection = Connection.parse(None)
        self.connection.host = "127.0.0.1"

    def qr_json(self, role="controller"):
        return self.connection.qr_json(role=role)

    async def start(self):
        self.calls.append("start")

    async def close(self):
        self.calls.append("close")

    async def wait_for_device(self, timeout=120.0):
        self.calls.append(f"wait:{timeout:.0f}")
        if not self.join:
            from carterkit.hub import HubError
            raise HubError("no device joined")
        return {"name": "Thunk"}

    async def push_layout(self, *, install=False):
        self.calls.append("push_layout")
        return {"ok": True, "linked": True}

    def _control(self, target):
        return {"id": target}

    def on(self, target, fn=None):
        return fn

    async def push(self, target, value):
        self.calls.append(f"push:{target}")
        return {"ok": True}


def _fake_serve(join):
    def serve_playground(**kw):
        hub = _FakeHub(join=join)
        return object(), hub, False
    return serve_playground


def test_run_pairs_pushes_and_opens_the_prompt(monkeypatch):
    monkeypatch.setattr(start, "serve_playground", _fake_serve(join=True))
    seen = []

    async def serve_console(hub, ui=None, *, intro=None):
        seen.append(("console", hub.calls[:], intro))

    import carterkit.repl as repl
    monkeypatch.setattr(repl, "serve_console", serve_console)
    out = []
    rc = asyncio.run(start.run(timeout=7, out=out.append))
    assert rc == 0
    assert seen and seen[0][1] == ["start", "wait:7", "push_layout"]
    assert any("Paired with Thunk" in s for s in out)
    assert any("linked on the phone" in s for s in out)


def test_run_no_phone_is_exit_1_with_a_fix(monkeypatch):
    monkeypatch.setattr(start, "serve_playground", _fake_serve(join=False))
    out = []
    rc = asyncio.run(start.run(timeout=3, out=out.append))
    assert rc == 1
    assert any("No phone joined in 3 s" in s for s in out)


def test_cli_start_is_registered():
    p = cli.build_parser()
    a = p.parse_args(["start", "--fresh", "--no-repl", "--timeout", "5", "--port", "9000"])
    assert a.cmd == "start" and a.fresh and a.no_repl and a.timeout == 5 and a.port == 9000
    assert a.host is None
    assert p.parse_args(["start"]).fn is cli._cmd_start


def test_env_knobs(monkeypatch):
    monkeypatch.delenv(start.HOST_ENV, raising=False)
    monkeypatch.delenv(start.TIMEOUT_ENV, raising=False)
    assert start.default_host() == "0.0.0.0" and start.default_timeout() == 600
    monkeypatch.setenv(start.HOST_ENV, "127.0.0.1")
    monkeypatch.setenv(start.TIMEOUT_ENV, "2.5")
    assert start.default_host() == "127.0.0.1" and start.default_timeout() == 2.5
    monkeypatch.setenv(start.TIMEOUT_ENV, "soon")
    assert start.default_timeout(9) == 9


def test_default_host_qr_carries_the_lan_address(tmp_path, monkeypatch):
    monkeypatch.delenv(start.HOST_ENV, raising=False)
    from carterkit.relay import lan_ip
    _, hub, _ = start.serve_playground(session_path=str(tmp_path / "s.json"), port=18799)
    payload = json.loads(hub.qr_json())
    assert payload["url"] == f"ws://{lan_ip()}:18799"
    assert payload["token"] == hub.connection.key and hub.relay_host == "0.0.0.0"


def test_session_file_is_owner_only_and_warns_in_an_unignored_repo(tmp_path, monkeypatch):
    import os, stat, subprocess
    monkeypatch.setenv(start.HOST_ENV, "127.0.0.1")
    repo = tmp_path / "proj"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    path = str(repo / ".carterkit" / "session.json")
    start.serve_playground(session_path=path, port=18798)
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    warning = start.session_gitignore_warning(path)
    assert warning and ".gitignore" in warning
    (repo / ".gitignore").write_text(".carterkit/\n")
    assert start.session_gitignore_warning(path) is None
    assert start.session_gitignore_warning(str(tmp_path / "nogit" / "s.json")) is None


def test_start_hub_names_a_held_port(monkeypatch):
    import carterkit.relay as relay

    class Conn:
        kind, port = "local", 18797
        def app_url(self): return "ws://127.0.0.1:18797"

    class Hub:
        connection = Conn()
        async def start(self):
            await asyncio.sleep(60)          # a relay that never accepts our key

    monkeypatch.setattr(relay, "port_in_use", lambda port, host="127.0.0.1": True)
    out = []

    assert asyncio.run(start.start_hub(Hub(), out.append, timeout=0.05)) is False
    assert any("held by another relay" in s and "--port" in s for s in out)


def test_run_reports_a_failed_first_push(monkeypatch):
    class Hub(_FakeHub):
        async def push_layout(self, *, install=False):
            from carterkit.hub import HubError
            raise HubError("no device on the channel")

    monkeypatch.setattr(start, "serve_playground", lambda **kw: (object(), Hub(join=True), False))
    out = []
    rc = asyncio.run(start.run(timeout=3, out=out.append))
    assert rc == 1 and any("did not land" in s for s in out)


def test_run_passes_install_through_and_reports_the_reply(monkeypatch):
    class Hub(_FakeHub):
        async def push_layout(self, *, install=False):
            self.calls.append(f"push:{install}")
            return {"ok": True, "installed": True} if install else {"ok": True, "linked": True}

    hubs = []

    def serve_playground(**kw):
        hub = Hub(join=True)
        hubs.append(hub)
        return object(), hub, False

    monkeypatch.setattr(start, "serve_playground", serve_playground)
    out = []
    assert asyncio.run(start.run(timeout=3, repl=False, demo_seconds=0, out=out.append,
                                 install=True)) == 0
    assert "push:True" in hubs[-1].calls and any("installed on the phone" in s for s in out)
    out.clear()
    assert asyncio.run(start.run(timeout=3, repl=False, demo_seconds=0, out=out.append)) == 0
    assert "push:False" in hubs[-1].calls and any("linked on the phone" in s for s in out)


def test_cli_install_flags():
    p = cli.build_parser()
    assert p.parse_args(["start", "--install"]).install is True
    assert p.parse_args(["repl", "--install", "x.py"]).install is True
    assert p.parse_args(["repl"]).install is False


def test_demo_layout_from_example_validates():
    ui = start.demo_layout("gauge")
    kids = [c for t in ui.layout["tabs"] for c in t["children"]]
    assert kids and kids[0]["type"] == "gauge"
    with pytest.raises(ValueError):
        start.demo_layout("gauge", "no such example")
    with pytest.raises(ValueError):
        start.demo_layout("nope")


def test_demo_pushes_the_example(monkeypatch):
    monkeypatch.setattr(start, "serve_playground", _fake_serve(join=True))

    async def fake_sleep(_):
        raise asyncio.CancelledError

    monkeypatch.setattr(start.asyncio, "sleep", fake_sleep)
    out = []
    rc = asyncio.run(start.demo("gauge", timeout=5, out=out.append))
    assert rc == 0 and any("gauge demo" in s for s in out)
    assert any("linked on the phone" in s for s in out)


def test_cli_demo_registered():
    a = cli.build_parser().parse_args(["demo", "gauge", "--example", "x"])
    assert a.fn is cli._cmd_demo and a.example == "x"
