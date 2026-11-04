"""A live hub for a layout file: pair once, then every save reaches the phone.

``carterkit repl hello.py`` (prompt) and ``python hello.py`` (no prompt, via
``livefile.main(__file__)``) both do this: import the file, serve its Layout on a hub
(the file's own ``hub``, else ``secrets/hub.json``, else a LAN hub paired by QR),
push the layout, run the file's optional ``async def run(hub)``, and watch the
file. On every save the file is imported again, the new layout is pushed, the
handlers ``run()`` registered are re-armed and ``run()`` restarts; an import
error keeps the last good version running and prints one line.

The file's contract::

    with Layout("Demo", cols=4, rows=3) as ui:     # the layout (required)
        gauge = ui.gauge("level", ...)
        button = ui.button("reset", send="reset")

    async def run(hub):                           # optional: behaviour, restarted on save
        @button.on
        async def reset(frame): await gauge.push(0)
        while True: ...

    if __name__ == "__main__":
        from carterkit import live; raise SystemExit(livefile.main(__file__))
"""
from __future__ import annotations

import asyncio
import os
import sys

from .start import (SESSION, default_host, default_timeout, load_session, pairing_lines,
                    quiet_logs, save_session)

#: Keys the REPL namespace keeps for itself (not controls).
_NS_CONTROLS = "_controls"


def refresh_namespace(ns: dict, hub, ui) -> list[str]:
    """Rebind the REPL names after a reload: drop the old controls, add the new."""
    from .repl import build_namespace
    for name in ns.pop(_NS_CONTROLS, []):
        ns.pop(name, None)
    fresh, names = build_namespace(hub, ui)
    ns.update(fresh)
    ns[_NS_CONTROLS] = names
    return names


class LiveFile:
    """One layout file served live. ``serve()`` below drives it."""

    def __init__(self, path: str, *, session_path: str = SESSION, out=None):
        self.path = os.path.abspath(path)
        self.name = os.path.basename(self.path)
        self.session_path = session_path
        self.out = out or (lambda s: print(s, flush=True))
        self.hub = None
        self.ui = None
        self.run_task: asyncio.Task | None = None
        self.ns: dict | None = None
        self.mtime: int | None = None

    # ─── the file ────────────────────────────────────────────────────────────
    def load(self):
        """Import the file fresh: ``(ui, module_hub, run)``; SystemExit with one line when it
        cannot be used."""
        from .repl import find_targets, load_module
        mod = load_module(self.path)
        ui, hub = find_targets(mod)
        if ui is None:
            raise SystemExit(f"{self.name}: no Layout found; define one with "
                             "`with Layout(\"Name\", cols=4, rows=3) as ui:`")
        run = getattr(mod, "run", None)
        return ui, hub, (run if callable(run) else None)

    def stat(self) -> int | None:
        try:
            return os.stat(self.path).st_mtime_ns
        except OSError:
            return None

    # ─── the hub ─────────────────────────────────────────────────────────────
    def make_hub(self, ui, module_hub):
        """The file's own hub, else its credential, else a LAN hub on the saved pairing.
        Returns ``(hub, reused_pairing)``."""
        if module_hub is not None:
            return module_hub, False
        credential = os.path.join(os.path.dirname(self.path), "secrets", "hub.json")
        if os.path.isfile(credential):
            from .connection import Connection
            return ui.serve(Connection.parse(credential)), False
        session = load_session(self.session_path)
        overrides: dict = {}
        if session:
            overrides = {"channel": session["channel"], "key": session["key"]}
            if session.get("port"):
                overrides["port"] = int(session["port"])
        hub = ui.serve(host=default_host(), **overrides)
        save_session(hub.connection, self.session_path)
        return hub, bool(session)

    def attach(self, ui) -> None:
        """Make ``ui`` the layout this hub drives (push/on resolve against it)."""
        hub = self.hub
        hub._layout_obj = ui
        ui._active_hub = hub
        if "connection" not in ui.layout:
            ui._buf.layout["connection"] = hub.connection.layout_block()
        hub.adopt_layout(ui.layout)
        self.ui = ui

    # ─── run() ───────────────────────────────────────────────────────────────
    async def start_run(self, run) -> None:
        if run is None:
            return
        out, name = self.out, self.name

        async def guarded():
            try:
                await run(self.hub)
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001 — one line; the hub stays up
                out(f"{name}: run() stopped: {type(e).__name__}: {e}")

        self.run_task = asyncio.create_task(guarded())

    async def stop_run(self) -> None:
        task, self.run_task = self.run_task, None
        if task is None or task.done():
            return
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass

    # ─── reload ──────────────────────────────────────────────────────────────
    async def reload(self) -> bool:
        """Import the file again and put it on the phone; False when it did not import."""
        try:
            ui, _, run = self.load()
        except SystemExit as e:
            self.out(f"{e} (keeping the last good version)")
            return False
        await self.stop_run()
        self.hub.reset_handlers()
        self.attach(ui)
        try:
            await self.hub.push_layout()
        except Exception as e:  # noqa: BLE001
            self.out(f"{self.name}: push failed: {type(e).__name__}: {e}")
        await self.start_run(run)
        if self.ns is not None:
            refresh_namespace(self.ns, self.hub, ui)
        self.out(f"{self.name}: reloaded, {len(self.hub._index)} control(s) on the phone")
        return True

    async def watch(self, interval: float = 0.5) -> None:
        """Poll the file's mtime; reload on change (an editor's save lands in one tick)."""
        self.mtime = self.stat()
        while True:
            await asyncio.sleep(interval)
            m = self.stat()
            if m is None or m == self.mtime:
                continue
            self.mtime = m
            await asyncio.sleep(0.1)      # let the editor finish writing
            self.mtime = self.stat() or m
            await self.reload()


async def serve(path: str, *, repl: bool = False, timeout: float | None = None,
                session_path: str = SESSION, out=None) -> int:
    """Serve ``path`` live until Ctrl-C (or EOF at the prompt). Returns an exit code."""
    from .hub import HubError
    live = LiveFile(path, session_path=session_path, out=out)
    out = live.out
    quiet_logs()
    ui, module_hub, run = live.load()
    hub, reused = live.make_hub(ui, module_hub)
    live.hub = hub
    live.attach(ui)
    try:
        await hub.start()
    except OSError as e:
        out(f"{live.name}: cannot serve on {hub.connection.app_url()}: {e}")
        return 1
    try:
        if hub.connection.kind == "local" and not await hub._first_peer():
            timeout = default_timeout() if timeout is None else timeout
            for line in pairing_lines(hub, reused=reused):
                out(line)
            out(f"Waiting for the phone (up to {timeout:.0f} s; Ctrl-C stops)...")
            try:
                peer = await hub.wait_for_device(timeout=timeout)
            except HubError:
                out(f"No phone joined in {timeout:.0f} s. Keep the app on the scanner and run it again.")
                return 1
            out(f"Paired with {peer.get('name') or 'your phone'}.")
        await hub.push_layout()
        out(f"{live.name} is on the phone ({len(hub._index)} control(s)); watching it for saves.")
        await live.start_run(run)
        watcher = asyncio.create_task(live.watch())
        try:
            if repl:
                from .repl import build_namespace, serve_console
                ns, names = build_namespace(hub, ui)
                ns[_NS_CONTROLS] = names
                live.ns = ns
                await serve_console(hub, ui, ns=ns, intro=[
                    f"editing {live.name}? every save is pushed to the phone",
                ])
            else:
                out("Ctrl-C stops.")
                await asyncio.Event().wait()
        finally:
            watcher.cancel()
            await live.stop_run()
        return 0
    finally:
        await hub.close()


def main(path: str, *, repl: bool = False) -> int:
    """Entry point for a file's ``if __name__ == "__main__":`` block."""
    try:
        return asyncio.run(serve(path, repl=repl))
    except KeyboardInterrupt:
        print("", file=sys.stderr)
        return 0
