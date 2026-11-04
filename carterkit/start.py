"""``carterkit start``: the instant door.

Serve a hub on this machine's LAN address, print a pairing QR, wait for the phone to
scan it, push the Playground layout, then open the live prompt with every control
bound. No account, no credential file, nothing to create in the app first.

The pairing (channel + relay key) is kept in ``.carterkit/session.json`` so the next
``carterkit start`` in the same folder reconnects the phone's Playground without a
new scan; ``--fresh`` starts over.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys

from .playground import build_playground

#: Where the last pairing is kept, relative to the working directory.
SESSION = os.path.join(".carterkit", "session.json")

#: Environment knobs shared with the scaffold's hello.py: the bind address
#: (``127.0.0.1`` keeps a demo off the LAN) and how long to wait for the phone.
HOST_ENV = "CARTERKIT_HOST"
TIMEOUT_ENV = "CARTERKIT_PAIR_TIMEOUT"

#: Where the scanner lives in the app, in the words the app uses.
SCAN_HINT = ("On the phone: open the layout list (tap the title) and tap Scan, "
             "or Settings -> Studio Session -> Open Scanner.")


def quiet_logs() -> None:
    """Keep the relay's INFO chatter off the pairing screen (``CARTERKIT_DEBUG=1`` keeps it)."""
    if os.environ.get("CARTERKIT_DEBUG"):
        return
    import logging
    for name in ("", "meshsocket", "carterkit", "websockets"):
        logging.getLogger(name).setLevel(logging.WARNING)


def default_host() -> str:
    return os.environ.get(HOST_ENV) or "0.0.0.0"


def default_timeout(fallback: float = 600.0) -> float:
    try:
        return float(os.environ.get(TIMEOUT_ENV) or fallback)
    except ValueError:
        return fallback


def load_session(path: str = SESSION) -> dict | None:
    """The saved pairing (``channel``, ``key``, ``port``) or None."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not data.get("channel") or not data.get("key"):
        return None
    return data


def save_session(connection, path: str = SESSION) -> None:
    """Remember this hub's pairing so the next start reuses it (owner-only file: it
    holds the relay key)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = {"channel": connection.channel, "key": connection.key, "port": connection.port}
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def session_gitignore_warning(path: str = SESSION) -> str | None:
    """One line when the session file sits in a git checkout that does not ignore it."""
    folder = os.path.dirname(os.path.abspath(path))
    top = folder
    while True:
        if os.path.isdir(os.path.join(top, ".git")):
            break
        parent = os.path.dirname(top)
        if parent == top:
            return None
        top = parent
    import subprocess
    try:
        ignored = subprocess.run(["git", "-C", top, "check-ignore", "-q", os.path.abspath(path)],
                                 capture_output=True, timeout=5).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return None
    if ignored:
        return None
    rel = os.path.relpath(folder, top)
    return (f"note: {rel}/ holds this pairing's relay key; add `{rel}/` to .gitignore "
            "so it is never committed.")


def pairing_lines(hub, *, reused: bool = False) -> list[str]:
    """What to print while waiting for the phone: the QR, its JSON, and where to scan."""
    from . import qr
    payload = hub.qr_json()
    lines = ["", "Scan this with the CAR-TER app:", ""]
    try:
        lines.append(qr.encode(payload, ecc="M").ascii())
    except Exception:  # noqa: BLE001 — a terminal that cannot show it still gets the JSON
        pass
    lines += ["", SCAN_HINT, f"(or paste the pairing JSON into the scanner: {payload})"]
    if reused:
        lines.append("Reusing the last pairing: a phone that still has the Playground reconnects "
                     "on its own while this machine keeps the address below; scan again if it does not.")
    lines.append(f"Hub: {hub.connection.app_url()}  channel: {hub.connection.channel}")
    return lines


def serve_playground(*, host: str | None = None, port: int | None = None,
                     session_path: str = SESSION, fresh: bool = False):
    """The Playground's hub, bound to the LAN, on the saved pairing when there is one.
    Returns ``(ui, hub, reused)``."""
    ui = build_playground()
    session = None if fresh else load_session(session_path)
    overrides: dict = {}
    if session:
        overrides = {"channel": session["channel"], "key": session["key"]}
        if port is None and session.get("port"):
            overrides["port"] = int(session["port"])
    if port is not None:
        overrides["port"] = port
    hub = ui.serve(host=host or default_host(), **overrides)
    save_session(hub.connection, session_path)
    return ui, hub, bool(session)


async def start_hub(hub, out, *, name: str = "carterkit start", timeout: float = 8.0) -> bool:
    """``hub.start()`` with the two first-run failures named: the bind failing, and a relay
    already on the port that does not know our key (another project folder, usually), which
    otherwise retries silently."""
    from .relay import port_in_use
    port = hub.connection.port
    taken = hub.connection.kind == "local" and port_in_use(port)
    try:
        if taken:
            await asyncio.wait_for(hub.start(), timeout=timeout)
        else:
            await hub.start()
    except (asyncio.TimeoutError, TimeoutError):      # before OSError: TimeoutError is one
        out(f"{name}: port {port} is held by another relay that does not accept this pairing "
            "(another carterkit folder?). Stop it, or run again with --port <other> "
            "(and --fresh to pair anew).")
        return False
    except OSError as e:
        out(f"{name}: cannot serve on {hub.connection.app_url()}: {e}")
        return False
    except Exception as e:  # noqa: BLE001 — one line, never a traceback on the first run
        out(f"{name}: could not connect to {hub.connection.app_url()}: {type(e).__name__}: {e}")
        return False
    return True


async def run(*, host: str | None = None, port: int | None = None, session_path: str = SESSION,
              fresh: bool = False, timeout: float | None = None, repl: bool = True,
              demo_seconds: float | None = None, out=None) -> int:
    """Serve, pair, push the Playground, then the prompt (or a value loop with
    ``repl=False``). Returns a process exit code."""
    from .hub import HubError
    out = out or (lambda s: print(s, flush=True))
    timeout = default_timeout() if timeout is None else timeout
    quiet_logs()
    ui, hub, reused = serve_playground(host=host, port=port, session_path=session_path, fresh=fresh)
    warning = session_gitignore_warning(session_path)
    if warning:
        out(warning)
    if not await start_hub(hub, out):
        return 1
    try:
        for line in pairing_lines(hub, reused=reused):
            out(line)
        out(f"Waiting for the phone (up to {timeout:.0f} s; Ctrl-C stops)...")
        try:
            peer = await hub.wait_for_device(timeout=timeout)
        except HubError:
            out(f"No phone joined in {timeout:.0f} s. Keep the app on the scanner and run "
                "`carterkit start` again (same QR while this folder keeps .carterkit/session.json).")
            return 1
        out(f"Paired with {peer.get('name') or 'your phone'}. Sending the Playground...")
        try:
            await hub.push_layout()
        except Exception as e:  # noqa: BLE001
            out(f"carterkit start: the Playground did not land: {type(e).__name__}: {e}")
            return 1
        out("The Playground is on the phone.")
        if repl:
            from .repl import serve_console
            await serve_console(hub, ui, intro=[
                "try: await level.push(42)   await hello.push('hi')   @tap.on",
            ])
            return 0
        return await _demo_loop(hub, ui, demo_seconds, out)
    finally:
        await hub.close()


async def _demo_loop(hub, ui, seconds: float | None, out) -> int:
    """No prompt: echo the phone's actions and sweep the gauge until Ctrl-C."""
    import random
    level = hub._control("level")

    async def on_tap(frame):
        out("tap!")
        return {"ok": True}

    async def on_dial(frame):
        out(f"dial: {frame.get('data', frame)}")
        return {"ok": True}

    hub.on("tap", on_tap)
    hub.on("dial", on_dial)
    out("Sweeping the gauge every 2 s; Ctrl-C stops.")
    loop = asyncio.get_running_loop()
    end = None if seconds is None else loop.time() + seconds
    try:
        while end is None or loop.time() < end:
            await hub.push(level, random.randint(0, 100))
            await asyncio.sleep(min(2.0, max(0.0, end - loop.time())) if end else 2.0)
    except KeyboardInterrupt:
        pass
    return 0


def main(args) -> int:
    try:
        return asyncio.run(run(host=args.host, port=args.port, fresh=args.fresh,
                               timeout=args.timeout, repl=not args.no_repl))
    except KeyboardInterrupt:
        print("", file=sys.stderr)
        return 0
