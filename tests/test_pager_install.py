"""Tests for the pager hook script and `carterkit pager install|uninstall` (K3).

Every test runs in a temporary HOME; nothing touches the real ~/.claude or ~/.carter.
"""
import asyncio
import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

import pytest

import carterkit
from carterkit import cli, pager_hook, pager_install
from carterkit.pager import AgentPager

HOOK = Path(pager_hook.__file__)
PR_INPUT = {"session_id": "abc12345-6789", "hook_event_name": "PermissionRequest",
            "tool_name": "Bash", "tool_input": {"command": "terraform apply -target=x"},
            "cwd": "/tmp", "permission_mode": "default"}


@pytest.fixture
def home(monkeypatch):
    d = Path(tempfile.mkdtemp(prefix="ckh", dir="/tmp"))
    monkeypatch.setenv("HOME", str(d))
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def sock_dir():
    d = tempfile.mkdtemp(prefix="pg", dir="/tmp")      # AF_UNIX paths must stay short
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


class FakeDaemon:
    """Answers one-line requests with a fixed reply (or hangs / closes)."""

    def __init__(self, path, reply=None, *, hang=False):
        self.path, self.reply, self.hang = str(path), reply, hang
        self.requests = []
        self.srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.srv.bind(self.path)
        self.srv.listen(4)
        self._stop = threading.Event()
        self.t = threading.Thread(target=self._loop, daemon=True)
        self.t.start()

    def _loop(self):
        self.srv.settimeout(0.2)
        while not self._stop.is_set():
            try:
                conn, _ = self.srv.accept()
            except (socket.timeout, OSError):
                continue
            with conn:
                buf = b""
                while not buf.endswith(b"\n"):
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                self.requests.append(json.loads(buf))
                if self.hang:
                    self._stop.wait(10)
                elif self.reply is not None:
                    conn.sendall(self.reply)

    def close(self):
        self._stop.set()
        self.srv.close()
        self.t.join(2)


def run_hook(sock, *, event="PermissionRequest", timeout=90, stdin=None, env=None):
    e = dict(os.environ, TMUX_PANE="%3", **(env or {}))
    p = subprocess.run([sys.executable, str(HOOK), "--event", event, "--socket", str(sock),
                        "--timeout", str(timeout)],
                       input=json.dumps(PR_INPUT) if stdin is None else stdin,
                       capture_output=True, text=True, env=e, timeout=60)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout) if p.stdout.strip() else None


# ─── hook script ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("decision", ["allow", "deny"])
def test_hook_permission_request_relays_daemon_decision(sock_dir, decision):
    d = FakeDaemon(sock_dir / "s", json.dumps({"decision": decision, "reason": "tap"}).encode()
                   + b"\n")
    try:
        out = run_hook(sock_dir / "s")
    finally:
        d.close()
    dec = out["hookSpecificOutput"]["decision"]
    assert out["hookSpecificOutput"]["hookEventName"] == "PermissionRequest"
    assert dec["behavior"] == decision
    if decision == "deny":
        assert "CAR-TER" in dec["message"]
    req = d.requests[0]
    assert req["agent"] == "claude %3 · abc12345"
    assert req["tool"] == "Bash" and req["summary"] == "terraform apply -target=x"


@pytest.mark.parametrize("decision", ["allow", "deny"])
def test_hook_pretooluse_relays_daemon_decision(sock_dir, decision):
    d = FakeDaemon(sock_dir / "s", json.dumps({"decision": decision}).encode() + b"\n")
    try:
        out = run_hook(sock_dir / "s", event="PreToolUse")
    finally:
        d.close()
    assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert out["hookSpecificOutput"]["permissionDecision"] == decision


def test_hook_no_daemon_asks(sock_dir):
    assert run_hook(sock_dir / "missing") is None                      # prompt as usual
    out = run_hook(sock_dir / "missing", event="PreToolUse")
    assert out["hookSpecificOutput"]["permissionDecision"] == "ask"


@pytest.mark.parametrize("reply", [b"", b"garbage\n", b'{"decision": "yes"}\n',
                                   b'{"decision": true}\n', b'["allow"]\n'])
def test_hook_bad_reply_never_allows(sock_dir, reply):
    d = FakeDaemon(sock_dir / "s", reply)
    try:
        assert run_hook(sock_dir / "s") is None
        out = run_hook(sock_dir / "s", event="PreToolUse")
    finally:
        d.close()
    assert out["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_hook_timeout_asks(sock_dir, monkeypatch):
    monkeypatch.setattr(pager_hook, "GRACE", 0.0)
    d = FakeDaemon(sock_dir / "s", hang=True)
    try:
        out = pager_hook.run(json.dumps(PR_INPUT), event="PreToolUse",
                             socket_path=str(sock_dir / "s"), timeout=0.3, env={})
        assert pager_hook.run(json.dumps(PR_INPUT), event="PermissionRequest",
                              socket_path=str(sock_dir / "s"), timeout=0.3, env={}) is None
    finally:
        d.close()
    assert out["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_hook_bad_stdin_and_bad_args_ask(sock_dir):
    assert run_hook(sock_dir / "s", stdin="not json") is None
    assert run_hook(sock_dir / "s", stdin="[1,2]") is None
    p = subprocess.run([sys.executable, str(HOOK), "--event", "Bogus"], input="{}",
                       capture_output=True, text=True, timeout=30)
    assert p.returncode == 0 and p.stdout == ""


def test_hook_against_real_pager_deadline_denies(sock_dir):
    """End to end: the real AgentPager (fake hub) times out and the hook prints deny."""
    class Hub:
        async def notify(self, *a, **k):
            raise RuntimeError("no validator")

        def on_notif_action(self, fn):
            pass

        def on(self, name, fn):
            pass

        async def broadcast(self, *a):
            pass

    async def main():
        pager = AgentPager(Hub(), timeout=0.5, store_path=sock_dir / "p.json",
                           socket_path=sock_dir / "s")
        await pager.start()
        try:
            return await asyncio.get_running_loop().run_in_executor(
                None, lambda: run_hook(sock_dir / "s", timeout=0.5))
        finally:
            await pager.stop()

    out = asyncio.run(main())
    assert out["hookSpecificOutput"]["decision"]["behavior"] == "deny"


def test_hook_is_stdlib_only():
    src = HOOK.read_text()
    assert "carterkit" not in src.split('"""', 2)[2]         # no package imports after docstring


# ─── install / uninstall ────────────────────────────────────────────────────
OTHER = {
    "model": "opus",
    "permissions": {"allow": ["Bash(ls)"]},
    "hooks": {
        "PermissionRequest": [{"matcher": "Bash", "hooks": [
            {"type": "command", "command": "/usr/local/bin/other-hook"}]}],
        "Stop": [{"hooks": [{"type": "command", "command": "say done"}]}],
    },
}


def _settings(home):
    return home / ".claude" / "settings.json"


def _write_other(home):
    p = _settings(home)
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(OTHER, indent=4))
    return p


def _ours(settings):
    return [(ev, h) for ev, groups in settings.get("hooks", {}).items() for g in groups
            for h in g["hooks"] if pager_install.HOOK_MARKER in h.get("command", "")]


def test_install_backs_up_merges_and_keeps_other_hooks(home, capsys):
    p = _write_other(home)
    assert cli.main(["pager", "install"]) == 0
    s = json.loads(p.read_text())
    assert s["model"] == "opus" and s["permissions"] == OTHER["permissions"]
    assert s["hooks"]["Stop"] == OTHER["hooks"]["Stop"]
    assert OTHER["hooks"]["PermissionRequest"][0] in s["hooks"]["PermissionRequest"]
    ours = _ours(s)
    assert len(ours) == 1 and ours[0][0] == "PermissionRequest"
    assert ours[0][1]["timeout"] == 90 + pager_install.HOOK_GRACE
    assert "--timeout 90" in ours[0][1]["command"]
    backups = list(p.parent.glob("settings.json.bak-*"))
    assert len(backups) == 1 and json.loads(backups[0].read_text()) == OTHER
    hook = home / ".carter" / "pager" / "hook.py"
    assert hook.read_text() == HOOK.read_text()
    assert stat.S_IMODE(hook.stat().st_mode) == 0o700
    lay = home / ".carter" / "pager" / "agents-layout.json"
    assert stat.S_IMODE(lay.stat().st_mode) == 0o600
    assert carterkit.validate_layout(json.loads(lay.read_text())) == []
    assert "push_layout(layout_path=" in capsys.readouterr().out


def test_install_is_idempotent(home):
    p = _write_other(home)
    assert cli.main(["pager", "install"]) == 0
    first = p.read_text()
    assert cli.main(["pager", "install"]) == 0
    assert p.read_text() == first
    assert len(list(p.parent.glob("settings.json.bak-*"))) == 1       # no-op wrote nothing
    assert len(_ours(json.loads(first))) == 1


def test_install_switching_event_moves_the_entry(home):
    p = _write_other(home)
    assert cli.main(["pager", "install"]) == 0
    assert cli.main(["pager", "install", "--event", "PreToolUse", "--matcher", "Bash",
                     "--timeout", "30"]) == 0
    s = json.loads(p.read_text())
    ours = _ours(s)
    assert [ev for ev, _ in ours] == ["PreToolUse"]
    assert "--event PreToolUse" in ours[0][1]["command"]
    assert s["hooks"]["PermissionRequest"] == OTHER["hooks"]["PermissionRequest"]


def test_install_creates_missing_settings(home):
    assert cli.main(["pager", "install"]) == 0
    s = json.loads(_settings(home).read_text())
    assert len(_ours(s)) == 1
    assert not list(_settings(home).parent.glob("settings.json.bak-*"))


def test_dry_run_shows_diff_and_writes_nothing(home, capsys):
    p = _write_other(home)
    before = p.read_text()
    assert cli.main(["pager", "install", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "+++" in out and "hook.py --event PermissionRequest" in out
    assert p.read_text() == before
    assert not (home / ".carter").exists()
    assert not list(p.parent.glob("settings.json.bak-*"))


def test_invalid_settings_json_is_left_alone(home):
    p = _settings(home)
    p.parent.mkdir(parents=True)
    p.write_text("{not json")
    assert cli.main(["pager", "install"]) == 2
    assert p.read_text() == "{not json"


def test_uninstall_removes_only_our_entry(home):
    p = _write_other(home)
    assert cli.main(["pager", "install"]) == 0
    assert cli.main(["pager", "uninstall"]) == 0
    assert json.loads(p.read_text()) == OTHER
    assert cli.main(["pager", "uninstall"]) == 0          # nothing left: no-op


def test_remove_entry_keeps_shared_group_siblings():
    s = {"hooks": {"PreToolUse": [{"matcher": "*", "hooks": [
        {"type": "command", "command": "/x/.carter/pager/hook.py --event PreToolUse"},
        {"type": "command", "command": "keep-me"}]}]}}
    out, n = pager_install.remove_entry(s)
    assert n == 1 and out["hooks"]["PreToolUse"][0]["hooks"] == [
        {"type": "command", "command": "keep-me"}]
    assert len(s["hooks"]["PreToolUse"][0]["hooks"]) == 2               # input untouched


@pytest.mark.parametrize("cred", [
    {"url": "wss://relay.example", "channel": "c", "token": "t", "did": "d",
     "refresh": "r", "k": "A" * 43 + "="},
    {"url": "ws://10.0.0.2:8765", "channel": "c", "k": "A" * 43 + "="},
])
def test_room_credentials_refused(home, cred, capsys):
    f = home / "cred.json"
    f.write_text(json.dumps(cred))
    assert cli.main(["pager", "install", "--connection", str(f)]) == 2
    assert "room" in capsys.readouterr().err
    assert not _settings(home).exists() and not (home / ".carter").exists()
    assert cli.main(["pager", "run", "--connection", str(f)]) == 2


def test_non_room_connection_embeds_block(home):
    assert cli.main(["pager", "install", "--connection", "ws://10.0.0.2:8765"]) == 0
    lay = json.loads((home / ".carter" / "pager" / "agents-layout.json").read_text())
    assert lay["connection"]["url"] == "ws://10.0.0.2:8765"
    assert carterkit.validate_layout(lay) == []
    cfg = json.loads((home / ".carter" / "pager" / "config.json").read_text())
    assert cfg["connection"] == "ws://10.0.0.2:8765" and cfg["timeout"] == 90.0
