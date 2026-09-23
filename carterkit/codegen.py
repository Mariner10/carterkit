"""Backend codegen — generate a runnable hub that speaks to a given layout.

A layout declares the commands its controls fire (actions) and the values its
display controls listen for (sync). The generated code drives both through
:class:`carterkit.Hub`, which derives every wire frame from the layout itself —
so the stub can't drift from the bindings the way hand-assembled frames do.
Pure string generation.
"""

from __future__ import annotations

import re


def _walk_controls(layout: dict) -> list[dict]:
    out: list[dict] = []

    def walk(children):
        for ch in children or []:
            if not isinstance(ch, dict):
                continue
            out.append(ch)
            if ch.get("type") == "group":
                walk(ch.get("children"))

    for tab in layout.get("tabs", []):
        walk(tab.get("children"))
    return out


def analyze_layout(layout: dict) -> dict:
    """Extract the wire contract.

    Returns ``{"actions": {command: mode}, "emits": {event: [valuePaths]},
    "pushes": [(control_id, valuePath)], "dynamic": [(group_id, event)]}``.
    A command is what a server handles: a broadcast_request action's payload
    ``msg_type``, a routed action's inner ``type``, or (legacy) a bare custom
    event name. ``pushes`` lists the controls `Hub.push` can drive."""
    actions: dict[str, str] = {}
    emits: dict[str, set] = {}
    pushes: list[tuple[str, str]] = []
    dynamic: list[tuple[str, str]] = []
    for ch in _walk_controls(layout):
        if ch.get("type") == "group" and ch.get("dynamic"):
            dynamic.append((ch.get("id", "?"), ch["dynamic"]))
        for akey in ("action", "longPressAction"):
            a = ch.get(akey)
            if not (isinstance(a, dict) and a.get("event")):
                continue
            ev, payload = a["event"], a.get("payload")
            if ev == "broadcast_request":
                name = isinstance(payload, dict) and payload.get("msg_type")
            elif ev in ("route_msg", "route_msg_noreply"):
                name = isinstance(payload, dict) and payload.get("type")
            else:
                name = ev                     # legacy custom event
            if name:
                actions.setdefault(name, a.get("mode", "broadcast"))
        pushed = False
        for s in ch.get("sync") or []:
            if not (isinstance(s, dict) and s.get("valuePath")):
                continue
            if s.get("method") in ("mqtt", "http", "sensor"):
                continue          # app-direct (broker/REST/hardware) — no server serves it
            emits.setdefault(s.get("event") or "broadcast", set()).add(s["valuePath"])
            if not pushed and (s.get("event") or "broadcast") == "broadcast" and ch.get("id"):
                pushes.append((ch["id"], s["valuePath"]))
                pushed = True
    return {"actions": actions, "emits": {k: sorted(v) for k, v in emits.items()},
            "pushes": pushes, "dynamic": dynamic}


def _ident(event: str) -> str:
    s = re.sub(r"\W+", "_", event).strip("_")
    return s or "evt"


def _slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return s or "layout"


def generate_service_stub(layout: dict, layout_path: str | None = None) -> str:
    """A runnable hub skeleton for this layout, built on `carterkit.Hub` — the
    frames come from the layout's own bindings, so they can't drift from it."""
    spec = analyze_layout(layout)
    name = layout.get("name", "service")
    path = layout_path or f"{_slug(name)}.json"
    conn = layout.get("connection") or {}
    if conn.get("url"):
        conn_note = (f"# relay: {conn.get('url')} (from the layout's connection block).\n"
                     f"# KEY/HOST apply only to the embedded relay, so they are unused here.")
        hub_line = f'hub = Hub("{path}")'
    else:
        conn_note = ("# No connection block: Hub serves an embedded MeshSocket relay. It is keyed\n"
                     "# with KEY (from CARTER_RELAY_KEY, or generated fresh per run) and bound to\n"
                     "# HOST — 127.0.0.1 by default; set CARTER_RELAY_HOST=0.0.0.0 so a phone on\n"
                     "# the LAN can pair. The pairing QR printed at startup carries both.")
        hub_line = f'hub = Hub("{path}", key=KEY, host=HOST)'

    handlers = []
    for cmd, mode in sorted(spec["actions"].items()):
        fn = f"on_{_ident(cmd)}"
        ctrl = _control_for_command(layout, cmd)
        expects = _expects_note(ctrl)
        handlers.append(
            f'@hub.on("{cmd}")\n'
            f'async def {fn}(data):\n'
            f'    # a control fired "{cmd}" (mode={mode}). data["value"] is its value{expects}.\n'
            f'    # Frames come from the mesh: check the value before acting on it.\n'
            f'    value = data.get("value")\n'
            f'{_guard_lines(ctrl)}'
            f'    log.info("[action] {cmd}: %r", value)\n')
    handlers_block = "\n".join(handlers) if handlers else "# (this layout fires no actions)\n"

    push_lines = [
        f'            await hub.push("{cid}", round(random.uniform(0, 100), 2))'
        f'  # -> {path_}'
        for cid, path_ in spec["pushes"]]
    push_block = "\n".join(push_lines) if push_lines else "            pass  # no sync-bound controls"

    dyn_lines = "".join(
        f'\n# dynamic group "{gid}": hub.fill("{gid}", fragment) replaces its children'
        f' (broadcast "{ev}")' for gid, ev in spec["dynamic"])

    return f'''#!/usr/bin/env python3
"""Auto-generated carterkit hub for layout "{name}".

Handles the commands its controls fire and pushes the values they listen for —
all derived from the layout's own bindings via carterkit.Hub. Fill in the TODOs
with your real device/data logic.
"""
import asyncio
import logging
import os
import random
import secrets

from carterkit import Hub  # pip install carterkit

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"),
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("{_slug(name)}")

{conn_note}
KEY = os.environ.get("CARTER_RELAY_KEY") or secrets.token_urlsafe(24)
HOST = os.environ.get("CARTER_RELAY_HOST", "127.0.0.1")
{hub_line}
{dyn_lines}

{handlers_block}

async def telemetry_loop():
    while True:
        try:
            # TODO: replace the random values with real readings
{push_block}
        except Exception:
            log.exception("telemetry tick failed")   # one bad read must not end the hub
        await asyncio.sleep(1.0)


async def main():
    async with hub:
        # The pairing payload contains the relay key: show it as a QR on the terminal
        # instead of printing the JSON (stdout usually ends up in a service log).
        from carterkit.qr import encode as qr_encode
        print(qr_encode(hub.qr_json(), ecc="M").ascii())
        print("scan with CAR-TER (Settings → Studio Session → Open Scanner)")
        await telemetry_loop()


if __name__ == "__main__":
    asyncio.run(main())
'''


def _control_for_command(layout: dict, cmd: str) -> dict | None:
    """The control whose action fires `cmd` (first match), for typed handler notes."""
    for ch in _walk_controls(layout):
        for akey in ("action", "longPressAction"):
            a = ch.get(akey)
            if not (isinstance(a, dict) and a.get("event")):
                continue
            payload = a.get("payload")
            name = (payload.get("msg_type") if a["event"] == "broadcast_request"
                    else payload.get("type") if a["event"] in ("route_msg", "route_msg_noreply")
                    else a["event"]) if isinstance(payload, dict) else a["event"]
            if name == cmd:
                return ch
    return None


def _expects_note(ctrl: dict | None) -> str:
    if not ctrl:
        return ""
    from .contract import value_spec
    spec = value_spec(ctrl)
    bits = [spec.get("type", "json")]
    if spec.get("enum"):
        bits.append(f"one of {spec['enum']!r}")
    if "min" in spec or "max" in spec:
        bits.append(f"range {spec.get('min')}..{spec.get('max')}")
    return f" ({', '.join(str(b) for b in bits)})"


def _guard_lines(ctrl: dict | None) -> str:
    """A type/range/enum guard derived from the control's value spec — handlers
    should never act on a value the layout could not have produced."""
    if not ctrl:
        return ""
    from .contract import value_spec
    spec = value_spec(ctrl)
    t = spec.get("type")
    lines = []
    if spec.get("enum"):
        lines.append(f'    if value not in {list(spec["enum"])!r}:')
    elif t == "number":
        cond = "not isinstance(value, (int, float)) or isinstance(value, bool)"
        if spec.get("min") is not None:
            cond += f" or value < {spec['min']!r}"
        if spec.get("max") is not None:
            cond += f" or value > {spec['max']!r}"
        lines.append(f"    if {cond}:")
    elif t == "boolean":
        lines.append("    if not isinstance(value, bool):")
    elif t == "string":
        lines.append("    if not isinstance(value, str) or len(value) > 1024:")
    if not lines:
        return ""
    lines.append('        log.warning("ignoring out-of-spec value %r", value)')
    lines.append("        return")
    return "\n".join(lines) + "\n"


def generate_rest_adapter(layout: dict, base_url: str = "https://api.example.com",
                          layout_path: str | None = None) -> str:
    """A REST-poll → mesh adapter template: fetch an API, push the fields the
    layout's controls listen for (field names guessed from the valuePaths)."""
    spec = analyze_layout(layout)
    name = layout.get("name", "layout")
    path = layout_path or f"{_slug(name)}.json"
    mapping = "\n".join(
        f'            await hub.push("{cid}", data.get("{vpath.split(".")[-1]}"))'
        f'  # -> {vpath}'
        for cid, vpath in spec["pushes"]) or "            pass  # map API fields here"

    return f'''#!/usr/bin/env python3
"""Auto-generated REST -> mesh adapter for "{name}".

Polls a REST API and pushes the fields the layout's controls listen for.
"""
import asyncio
import json
import logging
import os
import secrets
import urllib.request

from carterkit import Hub  # pip install carterkit

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
log = logging.getLogger("{_slug(name)}")

API = "{base_url}"
# Embedded relay (used only when the layout has no connection block): keyed and
# loopback by default; CARTER_RELAY_HOST=0.0.0.0 lets a phone on the LAN pair.
KEY = os.environ.get("CARTER_RELAY_KEY") or secrets.token_urlsafe(24)
HOST = os.environ.get("CARTER_RELAY_HOST", "127.0.0.1")
hub = Hub("{path}", key=KEY, host=HOST)


def fetch():
    with urllib.request.urlopen(API, timeout=10) as r:
        return json.loads(r.read())


async def loop():
    while True:
        try:
            data = await asyncio.to_thread(fetch)
            # TODO: adjust the field mapping to your API's real shape
{mapping}
        except Exception:
            log.exception("poll failed")
        await asyncio.sleep(2.0)


async def main():
    async with hub:
        await loop()


if __name__ == "__main__":
    asyncio.run(main())
'''
