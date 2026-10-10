"""``carterkit pager install|uninstall|run`` — wire Claude Code to the AgentPager.

``install`` copies the stdlib hook (``pager_hook.py``) to ``~/.carter/pager/hook.py``,
merges ONE command-hook entry into Claude Code's ``settings.json`` (backup first,
idempotent, every other key and hook preserved), and writes the "Agents" layout
JSON next to it. ``uninstall`` removes only our entry. ``run`` starts the daemon.

Nothing here ever makes the hook auto-allow: with no daemon the hook returns no
decision (``PermissionRequest``) or ``ask`` (``PreToolUse``) and the normal
terminal prompt appears.
"""
from __future__ import annotations

import copy
import difflib
import json
import os
import shlex
import shutil
import sys
import tempfile
import time
from pathlib import Path

from . import pager as _pager

EVENTS = ("PermissionRequest", "PreToolUse")
DEFAULT_EVENT = "PermissionRequest"
DEFAULT_MATCHER = "*"
HOOK_GRACE = 15          # settings timeout = pager timeout + this (hook gives up at +5)
HOOK_MARKER = "/.carter/pager/hook.py"


def pager_dir() -> Path:
    return _pager.DEFAULT_DIR.expanduser()


def hook_path() -> Path:
    return pager_dir() / "hook.py"


def layout_path() -> Path:
    return pager_dir() / "agents-layout.json"


def config_path() -> Path:
    return pager_dir() / "config.json"


def default_settings_path() -> Path:
    return Path("~/.claude/settings.json").expanduser()


class RoomConnectionError(ValueError):
    """The pager refuses E2EE room connections: the app's notification taps
    arrive as plaintext and a room hub (``strict_e2ee``) drops them."""


def check_connection(source):
    """Parse ``source`` (None = local relay) and refuse room credentials."""
    from .connection import Connection
    conn = Connection.parse(source)
    if conn.e2ee_key and conn.room:
        raise RoomConnectionError(
            "refusing an E2EE room connection: the phone's Approve/Deny taps reach "
            "the hub as plaintext and a room hub drops them, so every request would "
            "time out and deny. Use a personal, non-room channel credential "
            "(no 'k'/'e2eeKey').")
    return conn


# ─── settings.json merge ────────────────────────────────────────────────────
def hook_command(*, event, timeout, python=None, hook=None, socket=None) -> str:
    parts = [python or sys.executable, str(hook or hook_path()), "--event", event,
             "--timeout", f"{float(timeout):g}"]
    if socket:
        parts += ["--socket", str(socket)]
    return " ".join(shlex.quote(p) for p in parts)


def _is_ours(hook) -> bool:
    return (isinstance(hook, dict) and isinstance(hook.get("command"), str)
            and HOOK_MARKER in hook["command"])


def remove_entry(settings: dict) -> tuple[dict, int]:
    """A copy of ``settings`` without our hook anywhere, plus how many were removed.
    Other hooks in a shared matcher group stay; groups we empty are dropped, and an
    event list we empty is dropped (an empty ``hooks`` object too)."""
    out = copy.deepcopy(settings)
    hooks = out.get("hooks")
    if not isinstance(hooks, dict):
        return out, 0
    removed = 0
    for event in list(hooks):
        groups = hooks[event]
        if not isinstance(groups, list):
            continue
        kept_groups = []
        for group in groups:
            inner = group.get("hooks") if isinstance(group, dict) else None
            if not isinstance(inner, list):
                kept_groups.append(group)
                continue
            kept = [h for h in inner if not _is_ours(h)]
            removed += len(inner) - len(kept)
            if kept or not inner:
                kept_groups.append({**group, "hooks": kept} if len(kept) != len(inner)
                                   else group)
        if kept_groups:
            hooks[event] = kept_groups
        else:
            del hooks[event]
    if not hooks:
        del out["hooks"]
    return out, removed


def merge_entry(settings: dict, *, event, matcher, command, timeout) -> dict:
    """A copy of ``settings`` with exactly one pager hook, on ``event``."""
    if event not in EVENTS:
        raise ValueError(f"event must be one of {EVENTS}, got {event!r}")
    out, _ = remove_entry(settings)
    hooks = out.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("settings 'hooks' is not an object; refusing to touch it")
    groups = hooks.setdefault(event, [])
    if not isinstance(groups, list):
        raise ValueError(f"settings hooks.{event} is not a list; refusing to touch it")
    groups.append({"matcher": matcher,
                   "hooks": [{"type": "command", "command": command,
                              "timeout": int(timeout)}]})
    return out


def load_settings(path: Path) -> tuple[dict, str]:
    """``(settings, original_text)``; a missing file is ``({}, "")``. Invalid JSON
    raises — never overwrite a file we can't parse."""
    if not path.exists():
        return {}, ""
    text = path.read_text()
    if not text.strip():
        return {}, text
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data, text


def dump_settings(settings: dict) -> str:
    return json.dumps(settings, indent=2) + "\n"


def diff_text(old: str, new: str, path: Path) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True), new.splitlines(keepends=True),
        fromfile=str(path), tofile=f"{path} (new)"))


def _atomic_write(path: Path, text: str, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_settings(path: Path, old_text: str, new_text: str) -> Path | None:
    """Back up (when the file exists) and write atomically, keeping its mode.
    Returns the backup path. No-op (``None``) when nothing changes."""
    if new_text == old_text:
        return None
    backup = None
    mode = 0o600
    if path.exists():
        mode = path.stat().st_mode & 0o777
        backup = path.with_name(f"{path.name}.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        n = 1
        while backup.exists():
            backup = path.with_name(f"{path.name}.bak-{time.strftime('%Y%m%d-%H%M%S')}-{n}")
            n += 1
        shutil.copy2(path, backup)
    _atomic_write(path, new_text, mode)
    return backup


# ─── commands ───────────────────────────────────────────────────────────────
def _hook_source() -> str:
    return (Path(__file__).with_name("pager_hook.py")).read_text()


def _say(msg, out):
    print(msg, file=out)


def install(*, event=DEFAULT_EVENT, matcher=DEFAULT_MATCHER, timeout=_pager.DEFAULT_TIMEOUT,
            settings=None, dry_run=False, connection=None, python=None, out=None) -> int:
    """Install the hook + layout and merge the settings entry. Returns an exit code."""
    out = out or sys.stdout
    if event not in EVENTS:
        _say(f"--event must be one of {', '.join(EVENTS)}", sys.stderr)
        return 2
    if timeout is None or timeout <= 0:
        _say("--timeout must be > 0", sys.stderr)
        return 2
    try:
        conn = check_connection(connection)
    except (ValueError, TypeError, OSError) as e:
        _say(f"pager install: {e}", sys.stderr)
        return 2
    settings_path = Path(settings).expanduser() if settings else default_settings_path()
    try:
        current, old_text = load_settings(settings_path)
        command = hook_command(event=event, timeout=timeout, python=python)
        merged = merge_entry(current, event=event, matcher=matcher, command=command,
                             timeout=int(timeout) + HOOK_GRACE)
    except (ValueError, OSError) as e:
        _say(f"pager install: can't use {settings_path}: {e}", sys.stderr)
        return 2
    new_text = dump_settings(merged)
    layout = _pager.build_pager_layout(conn if connection is not None else None)
    from . import validate_layout
    errors = [f for f in validate_layout(layout) if f.get("severity") == "error"]
    if errors:                                   # a bug in build_pager_layout, not user error
        _say(f"pager install: the Agents layout failed validation: {errors}", sys.stderr)
        return 1
    config = {"event": event, "matcher": matcher, "timeout": float(timeout),
              "connection": (str(Path(connection).expanduser().resolve())
                             if connection and os.path.exists(str(connection))
                             else connection)}

    diff = diff_text(old_text, new_text, settings_path) if new_text != old_text else ""
    if dry_run:
        _say(f"[dry run] would write {hook_path()} (hook, 0700)", out)
        _say(f"[dry run] would write {layout_path()} (Agents layout, 0600)", out)
        _say(f"[dry run] would write {config_path()} (pager config, 0600)", out)
        if diff:
            verb = "back up and update" if settings_path.exists() else "create"
            _say(f"[dry run] would {verb} {settings_path}:", out)
            _say(diff.rstrip("\n"), out)
        else:
            _say(f"[dry run] {settings_path} already has this hook entry (no change)", out)
        return 0

    d = pager_dir()
    d.mkdir(mode=0o700, parents=True, exist_ok=True)
    _atomic_write(hook_path(), _hook_source(), 0o700)
    _atomic_write(layout_path(), json.dumps(layout, indent=2) + "\n", 0o600)
    _atomic_write(config_path(), json.dumps(config, indent=2) + "\n", 0o600)
    backup = write_settings(settings_path, old_text, new_text)
    _say(f"hook:     {hook_path()}", out)
    _say(f"layout:   {layout_path()}", out)
    if diff:
        _say(f"settings: {settings_path} updated ({event}, matcher {matcher!r}, "
             f"auto-deny after {timeout:g}s)" + (f"; backup {backup}" if backup else ""), out)
    else:
        _say(f"settings: {settings_path} already up to date", out)
    _say("next:", out)
    _say("  1. carterkit pager run" + (f" --connection {connection}" if connection else ""), out)
    _say("  2. push the layout with the carter MCP: "
         f'push_layout(layout_path="{layout_path()}")', out)
    return 0


def uninstall(*, settings=None, dry_run=False, out=None) -> int:
    out = out or sys.stdout
    settings_path = Path(settings).expanduser() if settings else default_settings_path()
    try:
        current, old_text = load_settings(settings_path)
    except (ValueError, OSError) as e:
        _say(f"pager uninstall: can't use {settings_path}: {e}", sys.stderr)
        return 2
    cleaned, removed = remove_entry(current)
    if not removed:
        _say(f"{settings_path}: no pager hook entry (nothing to do)", out)
        return 0
    new_text = dump_settings(cleaned)
    if dry_run:
        _say(f"[dry run] would back up and update {settings_path}:", out)
        _say(diff_text(old_text, new_text, settings_path).rstrip("\n"), out)
        return 0
    backup = write_settings(settings_path, old_text, new_text)
    _say(f"removed {removed} pager hook entr{'y' if removed == 1 else 'ies'} from "
         f"{settings_path}; backup {backup}", out)
    return 0


def load_config() -> dict:
    try:
        data = json.loads(config_path().read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def run(*, connection=None, timeout=None, out=None) -> int:
    """Start the daemon (a Hub + AgentPager) and serve until interrupted."""
    import asyncio
    out = out or sys.stdout
    cfg = load_config()
    connection = connection if connection is not None else cfg.get("connection")
    timeout = float(timeout if timeout is not None else cfg.get("timeout")
                    or _pager.DEFAULT_TIMEOUT)
    try:
        conn = check_connection(connection)
    except (ValueError, TypeError, OSError) as e:
        _say(f"pager run: {e}", sys.stderr)
        return 2

    async def main():
        from .hub import Hub
        layout = _pager.build_pager_layout(conn if connection else None)
        async with Hub(layout, connection=conn, name="carter-pager") as hub:
            pager = _pager.AgentPager(hub, timeout=timeout,
                                      metrics_path=_pager.DEFAULT_METRICS)
            await pager.start()
            _say(f"carter-pager listening on {pager.socket_path} "
                 f"(auto-deny after {timeout:g}s)", out)
            if conn.kind == "local":
                _say(f"pair the phone with: {hub.qr_json()}", out)
            try:
                await asyncio.Event().wait()
            finally:
                await pager.stop()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    return 0
