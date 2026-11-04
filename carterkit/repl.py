"""``carterkit repl [hello.py]``: a live, asyncio-aware prompt with the hub connected.

Imports the module, finds its Layout and Hub (or builds a Hub from
``secrets/hub.json``), connects, then opens a stdlib ``code`` console with
top-level ``await``. ``hub``, ``ui`` and every control (by id) are bound as names,
Tab completes them (and their methods), and ``help(<control>)`` says what one can
do. With no file and no credential the prompt opens on the Playground instead
(``carterkit start``: LAN hub + pairing QR), so nothing has to exist first.
Ctrl-D disconnects cleanly; errors print as one line, never a traceback.
"""
from __future__ import annotations

import ast
import asyncio
import builtins
import code
import importlib.util
import inspect
import keyword
import os
import re
import sys

HUB_JSON = os.path.join("secrets", "hub.json")
_RESERVED = {"hub", "ui", "asyncio"}


class _Handle:
    """A control on the phone, by id.

    ``await <control>.push(value)`` sends a value into it (a gauge level, a label's
    text); ``@<control>.on`` registers the handler for what it sends back (a button
    tap, a slider move). ``<control>.ref`` is its layout JSON.
    """

    def __init__(self, hub, d: dict):
        self._hub, self.ref = hub, d

    @property
    def id(self) -> str:
        return self.ref["id"]

    async def push(self, value):
        return await self._hub.push(self.ref, value)

    def on(self, fn=None):
        return self._hub.on(self.ref, fn)

    def __repr__(self) -> str:
        return f"<Control {self.ref.get('type', '?')} {self.id!r}>"


def _name_for(cid: str, taken) -> str | None:
    name = re.sub(r"\W", "_", cid)
    if not name or name[0].isdigit():
        name = "_" + name
    if keyword.iskeyword(name) or name in _RESERVED or name in taken or hasattr(builtins, name):
        return None
    return name


def build_namespace(hub, ui=None) -> tuple[dict, list[str]]:
    """The REPL namespace and the sorted control names bound in it."""
    from .hub import _walk_children
    ns: dict = {"asyncio": asyncio, "hub": hub}
    if ui is not None:
        ns["ui"] = ui
    layout = getattr(hub, "layout", None) or {}
    names: list[str] = []
    for ch in _walk_children(layout):
        cid = ch.get("id")
        if not isinstance(cid, str):
            continue
        name = _name_for(cid, ns)
        if name is None:
            continue
        if ui is not None and hasattr(ui, "_scope"):
            from .layout import Control
            ns[name] = Control(ui._scope, ch)
        else:
            ns[name] = _Handle(hub, ch)
        names.append(name)
    return ns, sorted(names)


def banner_lines(ns: dict, names: list[str]) -> list[str]:
    shown = ", ".join(names[:30]) + (f", … (+{len(names) - 30})" if len(names) > 30 else "")
    return [
        "carterkit repl: hub connected" + ("" if "ui" in ns else " (no layout loaded)"),
        f"bound: hub{', ui' if 'ui' in ns else ''} · {len(names)} control(s): {shown or '(none)'}",
        "top-level await works, e.g. `await temp.push(21.5)`; Tab completes names; "
        "help(<control>) explains one; Ctrl-D disconnects",
    ]


class _AsyncConsole(code.InteractiveConsole):
    """InteractiveConsole run in a worker thread; code executes on the event loop."""

    def __init__(self, ns: dict, loop):
        super().__init__(ns)
        self.loop = loop
        self.compile.compiler.flags |= ast.PyCF_ALLOW_TOP_LEVEL_AWAIT

    def runcode(self, codeobj):
        import types

        async def run():
            res = types.FunctionType(codeobj, self.locals)()
            if inspect.iscoroutine(res):
                await res

        try:
            asyncio.run_coroutine_threadsafe(run(), self.loop).result()
        except SystemExit:
            raise
        except BaseException as e:  # noqa: BLE001 — one line, never a traceback
            msg = str(e).splitlines()[0] if str(e) else ""
            print(f"error: {type(e).__name__}{': ' + msg if msg else ''}", file=sys.stderr)

    def showtraceback(self):
        e = sys.exc_info()[1]
        print(f"error: {type(e).__name__}: {e}".rstrip(": "), file=sys.stderr)


def make_completer(ns: dict):
    """A readline-style ``complete(text, state)`` over `ns` (no TTY needed)."""
    import rlcompleter
    return rlcompleter.Completer(ns).complete


def completions(ns: dict, text: str) -> list[str]:
    """Every completion of `text`, in order."""
    fn, out = make_completer(ns), []
    while (m := fn(text, len(out))) is not None:
        out.append(m)
    return out


def enable_completion(ns: dict) -> bool:
    """Tab completion over the REPL names and their attributes (``level.pu<Tab>``).
    Returns False where readline is unavailable (then the prompt still works)."""
    try:
        import readline
    except ImportError:
        return False
    readline.set_completer(make_completer(ns))
    if "libedit" in (getattr(readline, "__doc__", "") or ""):
        readline.parse_and_bind("bind ^I rl_complete")       # macOS editline
    else:
        readline.parse_and_bind("tab: complete")
    return True


async def serve_console(hub, ui=None, *, intro: list[str] | None = None,
                        ns: dict | None = None) -> None:
    """The prompt on an already-connected `hub`, until EOF (no connect, no close).
    ``ns`` is a namespace to serve in place (a live file refreshes it on reload)."""
    if ns is None:
        ns, names = build_namespace(hub, ui)
    else:
        names = sorted(n for n, v in ns.items()
                       if not n.startswith("_") and n not in ("hub", "ui", "asyncio"))
    for line in banner_lines(ns, names) + list(intro or []):
        print(line, file=sys.stderr)
    enable_completion(ns)
    loop = asyncio.get_running_loop()
    console = _AsyncConsole(ns, loop)
    try:
        await loop.run_in_executor(None, lambda: console.interact(banner="", exitmsg=""))
    except (SystemExit, KeyboardInterrupt):
        pass


async def run_repl(hub, ui=None) -> None:
    """Connect `hub`, serve the prompt until EOF, then disconnect."""
    await hub.start()
    try:
        await serve_console(hub, ui)
    finally:
        await hub.close()


def load_module(path: str):
    path = os.path.abspath(path)
    sys.path.insert(0, os.path.dirname(path))
    spec = importlib.util.spec_from_file_location("carterkit_repl_target", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"carterkit repl: cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"carterkit repl: importing {path} failed: {type(e).__name__}: {e}")
    return mod


def find_targets(mod):
    """(layout, hub) from a module: a ``ui``/``hub`` attribute, else the first instance."""
    from .hub import Hub
    from .layout import Layout
    attrs = vars(mod)
    layout = attrs.get("ui") if isinstance(attrs.get("ui"), Layout) else None
    hub = attrs.get("hub") if isinstance(attrs.get("hub"), Hub) else None
    for v in attrs.values():
        if layout is None and isinstance(v, Layout):
            layout = v
        if hub is None and isinstance(v, Hub):
            hub = v
    return layout, hub


def prepare(path: str | None, hub_json: str = HUB_JSON):
    """Resolve (hub, ui) for the CLI; SystemExit with a one-line fix when impossible."""
    from .hub import Hub
    ui = hub = None
    if path:
        if not os.path.isfile(path):
            raise SystemExit(f"carterkit repl: no such file {path!r}")
        ui, hub = find_targets(load_module(path))
        if hub is not None and ui is None and getattr(hub, "_layout_obj", None) is not None:
            ui = hub._layout_obj
        if hub is not None and ui is not None and hub._layout_obj is None:
            hub._layout_obj = ui
            ui._active_hub = hub
    if hub is None:
        if not os.path.isfile(hub_json):
            raise SystemExit(f"carterkit repl: no Hub in {path or 'the command'} and no "
                             f"{hub_json}; add `hub = ui.serve(...)` or create {hub_json}")
        hub = Hub(ui, connection=hub_json) if ui is not None else Hub(connection=hub_json)
    return hub, ui


def main(path: str | None = None, hub_json: str = HUB_JSON) -> int:
    if path is None and not os.path.isfile(hub_json):
        # Nothing to attach to: open the prompt on the Playground (LAN hub + QR).
        from . import start
        print("carterkit repl: no file and no secrets/hub.json; starting the Playground "
              "(`carterkit start`) instead.", file=sys.stderr)
        return asyncio.run(start.run())
    if path is not None:
        # A file: serve it live (QR pairing when needed, every save pushed), with the prompt.
        from . import livefile as live
        if not os.path.isfile(path):
            raise SystemExit(f"carterkit repl: no such file {path!r}")
        return live.main(path, repl=True)
    hub, ui = prepare(path, hub_json)
    try:
        asyncio.run(run_repl(hub, ui))
    except KeyboardInterrupt:
        pass
    return 0
