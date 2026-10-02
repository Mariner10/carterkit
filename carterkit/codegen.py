"""Backend codegen — generate a runnable hub that speaks to a given layout.

A layout declares the commands its controls fire (actions) and the values its
display controls listen for (sync). The generated code drives both through
:class:`carterkit.Hub`, which derives every wire frame from the layout itself —
so the stub can't drift from the bindings the way hand-assembled frames do.
Pure string generation.

:func:`generate_hub` (``carterkit codegen``) is the current form: a starter-kit style
``hub.py`` with handlers, ``@hub.pages``, ``hub.confirm``, sheet helpers and push stubs.
:func:`generate_service_stub` is the older ``Hub(...)`` skeleton (``carterkit gen --stub``).
"""

from __future__ import annotations

import re
import textwrap

from .contract import is_group


def _walk_controls(layout: dict) -> list[dict]:
    from .sections import inline_view
    layout = inline_view(layout)          # a sectioned (v2) document's facets fold on
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
            if a.get("method") in ("mqtt", "http", "local"):
                continue          # app-direct outbound — the app performs it itself
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
            if s.get("method") in ("mqtt", "http", "sensor", "local", "derive"):
                continue          # app-direct (broker/REST/hardware/local store/derive) — no server serves it
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


# ═══ hub scripts: `carterkit codegen` ════════════════════════════════════════
# The service stub above predates the live-file workflow. `generate_hub` writes what a
# starter kit's hand-written hub.py looks like (scaffold_templates/kits/*/hub.py):
# `ui = Layout.load(...)`, `async def run(hub)` holding the handlers, and
# `livefile.main(__file__)`, so `python hub.py` pairs by QR and every save reaches the
# phone. The analysis is plain data so tests (and a connector) can read it too.

#: Inputs that write a form's draft instead of firing their own action.
_FORM_INPUTS = {"textInput", "stepper", "slider", "toggle", "picker", "segmentedControl",
                "datePicker", "colorPicker"}
#: Words that mark a command as hard to take back: the hub asks first (hub.confirm).
_DESTRUCTIVE = re.compile(r"delete|remove|clear|erase|wipe|destroy|purge|trash", re.IGNORECASE)
#: Display controls the hub feeds live (pushed from the periodic task).
_LIVE_TYPES = {"gauge", "sparkline", "progressRing", "label", "statusLight", "image",
               "qrCode", "logConsole", "keyValue"}
_TOKEN = re.compile(r"^\{\{\s*([\w.]+)\s*\}\}$")
_ITEM_TOKEN = re.compile(r"\{\{\s*item\.([\w]+)[\w.]*\s*\}\}")


def _hub_walk(layout: dict):
    """Yield ``(node, ctx)`` for every control, including the places `Hub` does not
    index (list row templates, expanded-only controls). ``ctx``: ``indexed`` (Hub
    resolves it by id), ``form`` (the enclosing form group's id), ``row_of`` (the list
    whose row template holds it)."""
    from .sections import inline_view
    layout = inline_view(layout)

    def walk(children, ctx):
        for ch in children or []:
            if not isinstance(ch, dict):
                continue
            yield ch, ctx
            inner = ctx
            if is_group(ch) and isinstance(ch.get("form"), dict):
                inner = dict(ctx, form=ch.get("id") or "form")
            if is_group(ch):
                yield from walk(ch.get("children"), inner)
            for panel in ch.get("panels") or []:
                if isinstance(panel, dict):
                    yield from walk(panel.get("children"), inner)
            popup = ch.get("longPressGroup")
            if isinstance(popup, dict):
                yield from walk(popup.get("children"), inner)
            cfg = ch.get("canvasConfig")
            if isinstance(cfg, dict):
                yield from walk([i.get("control") for i in cfg.get("items") or []
                                 if isinstance(i, dict)], inner)
            exp = ch.get("expand")
            if isinstance(exp, dict):        # expanded-only controls (not `ref` placements)
                yield from walk([c for c in exp.get("children") or []
                                 if isinstance(c, dict) and c.get("type")],
                                dict(inner, indexed=False))
            tpl = ch.get("itemTemplate")
            if isinstance(tpl, dict):
                row = dict(inner, indexed=False, row_of=ch.get("id"))
                yield from walk(tpl.get("children"), row)
                texp = tpl.get("expand")
                if isinstance(texp, dict):
                    yield from walk([c for c in texp.get("children") or []
                                     if isinstance(c, dict) and c.get("type")], row)

    base = {"indexed": True, "form": None, "row_of": None}
    for tab in layout.get("tabs", []):
        yield from walk(tab.get("children"), base)


def _is_hub_action(a) -> bool:
    return (isinstance(a, dict) and bool(a.get("event"))
            and a.get("method", "meshsocket") not in ("mqtt", "http", "local"))


def _broadcast_sync(ctrl: dict) -> dict | None:
    """The control's first meshsocket broadcast sync (what `hub.push` drives)."""
    syncs = ctrl.get("sync")
    if isinstance(syncs, dict):
        syncs = [syncs]
    for s in syncs or []:
        if (isinstance(s, dict) and s.get("method", "meshsocket") == "meshsocket"
                and (s.get("event") or "broadcast") == "broadcast"):
            return s
    return None


def _item_fields(node) -> dict[str, set]:
    """``{field: {(control type, key), ...}}`` for every ``{{item.<field>}}`` under `node`."""
    out: dict[str, set] = {}

    def scan(v, ctype, key):
        if isinstance(v, str):
            for f in _ITEM_TOKEN.findall(v):
                out.setdefault(f, set()).add((ctype, key))
        elif isinstance(v, dict):
            t = v.get("type", ctype)
            for k, x in v.items():
                scan(x, t, k)
        elif isinstance(v, list):
            for x in v:
                scan(x, ctype, key)

    scan(node, "", "")
    return out


def _row_fields(ctrl: dict) -> dict[str, set]:
    """The fields a list's rows carry: what its template binds, else its columns;
    every row has an ``id`` (a row tap sends it as {{value}})."""
    fields = _item_fields(ctrl.get("itemTemplate") or {})
    for col in ctrl.get("listColumns") or []:
        if isinstance(col, dict) and col.get("key"):
            fields.setdefault(col["key"], set()).add(("column", col.get("format") or ""))
    fields.setdefault("id", set())
    return fields


def _label_of(ctrl: dict) -> str:
    for k in ("label", "text", "placeholder"):
        v = ctrl.get(k)
        if isinstance(v, str) and v and "{{" not in v:
            return v
    return ctrl.get("id") or ctrl.get("type", "control")


def _payload_fields(payload, ctrl: dict) -> dict[str, dict]:
    """``{key: {"kind", ...}}`` for an action payload's keys (minus the demux key):
    ``value`` ({{value}}, typed from the control's doc), ``item`` ({{item.<field>}}),
    ``form`` ({{form}} / {{form.<field>}}), ``token`` (another token) or ``const``."""
    from .contract import TOKEN_TYPES, value_spec
    out: dict[str, dict] = {}
    if not isinstance(payload, dict):
        return out
    for k, v in payload.items():
        if k in ("msg_type", "type"):
            continue
        m = _TOKEN.match(v) if isinstance(v, str) else None
        tok = m.group(1) if m else None
        if tok == "value":
            out[k] = {"kind": "value", "spec": value_spec(ctrl)}
        elif tok and tok.startswith("item."):
            out[k] = {"kind": "item", "field": tok[5:]}
        elif tok == "form" or (tok or "").startswith("form."):
            out[k] = {"kind": "form", "field": tok[5:] or None}
        elif tok:
            out[k] = {"kind": "token", "token": tok,
                      "spec": dict(TOKEN_TYPES.get(tok) or {"type": "string"})}
        else:
            out[k] = {"kind": "const", "values": [v]}
    return out


def analyze_hub(layout: dict) -> dict:
    """Everything a hub script for this layout must serve, as plain data.

    ``commands``: one entry per command the layout sends (``command``, ``register``: the
    control id or command name to give ``hub.on``, ``sources``, ``fields``, ``confirm``:
    the action's own ``confirm: "dialog"`` wording, ``ask``: the hub should
    ``hub.confirm`` first, ``echo``: the control whose state the hub sends back, ``form``).
    ``pages``: paged lists (``list``, ``request``, ``replyType``, ``fields``, ``pageSize``,
    ``queryFrom``). ``pushes``: controls the hub feeds (``id``, ``type``, ``role``:
    ``live``/``rows``/``state``/``status``, ``same_as``). ``sheets``: groups the hub can open
    with ``open_sheet(group_id=...)``. ``expand_verbs``: app-local expand/collapse
    actions. ``dynamic``: dynamic groups. ``status``: the status label's id or None."""
    from .contract import _command_of
    commands: dict[str, dict] = {}
    pages: list[dict] = []
    pushes: list[dict] = []
    sheets: list[dict] = []
    verbs: list[dict] = []
    dynamic: list[tuple[str, str]] = []
    ids = set()
    nodes = list(_hub_walk(layout))
    for ch, ctx in nodes:
        if ch.get("id") and ctx["indexed"]:
            ids.add(ch["id"])

    def add(cmd, a, ch, ctx, akey, form=None):
        e = commands.setdefault(cmd, {"command": cmd, "transport": _command_of(a)[1],
                                      "sources": [], "fields": {}, "confirm": None,
                                      "ask": False, "echo": None, "form": form})
        e["sources"].append({"id": ch.get("id"), "type": ch.get("type") or "group",
                             "label": _label_of(ch), "key": akey,
                             "indexed": ctx["indexed"] and akey != "form.submit",
                             "row_of": ctx["row_of"]})
        inner = a.get("payload")
        if e["transport"] == "routed" and isinstance(inner, dict):
            inner = inner.get("payload")
        for k, f in _payload_fields(inner, ch).items():
            have = e["fields"].get(k)
            if have and have["kind"] == "const" and f["kind"] == "const":
                if f["values"][0] not in have["values"]:
                    have["values"].append(f["values"][0])
            elif not have:
                e["fields"][k] = f
        if a.get("confirm") == "dialog" and not e["confirm"]:
            e["confirm"] = {k: a[k] for k in ("confirmTitle", "confirmMessage",
                                               "confirmLabel", "destructive") if k in a}
        if (a.get("destructive") is True or _DESTRUCTIVE.search(cmd)
                or _DESTRUCTIVE.search(str(ch.get("label") or ""))
                or "trash" in str(ch.get("icon") or "")):
            e["ask"] = True

    for ch, ctx in nodes:
        ctype = ch.get("type") or ("group" if is_group(ch) else "?")
        if is_group(ch) and ch.get("dynamic"):
            dynamic.append((ch.get("id", "?"), ch["dynamic"]))
        if is_group(ch) and isinstance(ch.get("expand"), dict) and ch.get("id") and ctx["indexed"]:
            exp = ch["expand"]
            sheets.append({"group": ch["id"], "label": _label_of(ch),
                           "title": exp.get("title") or ch.get("label"),
                           "style": exp.get("style") or "fullScreen",
                           "trigger": exp.get("trigger", "tap")})
        form = ch.get("form") if is_group(ch) else None
        if isinstance(form, dict) and _is_hub_action(form.get("submit")):
            cmd = _command_of(form["submit"])[0]
            if cmd:
                rules = form.get("fields") if isinstance(form.get("fields"), dict) else {}
                draft = [c.get("field") or c.get("id") for c, cx in nodes
                         if cx["form"] == ch.get("id") and c.get("type") in _FORM_INPUTS
                         and (c.get("field") or c.get("id"))]
                add(cmd, form["submit"], ch, ctx, "form.submit",
                    form={"group": ch.get("id"), "fields": draft, "rules": rules})
        for akey in ("action", "longPressAction"):
            a = ch.get(akey)
            if isinstance(a, dict):
                for verb in ("expand", "collapse", "toggleExpand"):
                    if isinstance(a.get(verb), str):
                        verbs.append({"id": ch.get("id"), "label": _label_of(ch),
                                      "verb": verb, "group": a[verb]})
            if not _is_hub_action(a):
                continue
            if ctx["form"] and ctype in _FORM_INPUTS and akey == "action":
                continue                      # a form input writes the draft, never sends
            cmd = _command_of(a)[0]
            if cmd:
                add(cmd, a, ch, ctx, akey)
        paging = ch.get("paging")
        if isinstance(paging, dict) and isinstance(paging.get("request"), dict):
            payload = paging["request"].get("payload")
            req = isinstance(payload, dict) and payload.get("msg_type")
            if req and paging.get("replyType"):
                pages.append({"list": ch.get("id"), "label": _label_of(ch), "request": req,
                              "replyType": paging["replyType"],
                              "pageSize": int(paging.get("pageSize") or 50),
                              "queryFrom": paging.get("queryFrom"),
                              "fields": _row_fields(ch)})
                continue                      # its rows come from the pages, not a push
        s = _broadcast_sync(ch)
        if s and ch.get("id") and ctx["indexed"] and not ctx["row_of"]:
            pushes.append({"id": ch["id"], "type": ctype, "label": _label_of(ch),
                           "filter": s.get("filter") or {}, "valuePath": s.get("valuePath"),
                           "fields": _row_fields(ch) if ctype in ("list", "cardList") else None,
                           "control": ch})

    status = next((p["id"] for p in pushes if p["type"] == "label" and p["valuePath"]
                   and "status" in p["id"].lower()), None)
    seen: dict[str, str] = {}
    for p in pushes:
        key = repr((sorted(p["filter"].items()), p["valuePath"]))
        p["same_as"] = seen.get(key)
        seen.setdefault(key, p["id"])
        acts = any(_is_hub_action(p["control"].get(k)) for k in ("action", "longPressAction"))
        p["role"] = ("status" if p["id"] == status
                     else "rows" if p["fields"] is not None
                     else "state" if acts
                     else "live" if p["valuePath"] and p["type"] in _LIVE_TYPES
                     else "other")

    by_id = {p["id"]: p for p in pushes}
    node_by_id = {c["id"]: c for c, cx in nodes if c.get("id") and cx["indexed"]}
    for e in commands.values():
        src = e["sources"]
        ctrl = node_by_id.get(src[0]["id"]) if len(src) == 1 and src[0]["indexed"] else None
        acts = sum(_is_hub_action(ctrl.get(k)) for k in ("action", "longPressAction")) if ctrl else 0
        one = ctrl is not None and acts == 1
        e["register"] = src[0]["id"] if one else e["command"]
        e["collides"] = not one and e["command"] in ids
        if one and src[0]["id"] in by_id and by_id[src[0]["id"]]["role"] == "state" \
                and any(f["kind"] == "value" for f in e["fields"].values()):
            e["echo"] = src[0]["id"]
        if e["confirm"]:
            e["ask"] = False                   # the app asks first already
    return {"name": layout.get("name") or "Layout", "commands": list(commands.values()),
            "pages": pages, "pushes": pushes, "sheets": sheets, "expand_verbs": verbs,
            "dynamic": dynamic, "status": status}


# ─── rendering helpers ──────────────────────────────────────────────────────────
_RESERVED = {"id", "type", "from", "list", "dict", "set", "str", "int", "float", "bool",
             "len", "max", "min", "filter", "format", "hash", "input", "map", "next",
             "object", "range", "sum", "value_", "frame", "hub", "choice", "form"}


def _var(key: str) -> str:
    import keyword
    s = re.sub(r"\W+", "_", key).strip("_") or "field"
    if s[0].isdigit():
        s = "f_" + s
    return s + "_" if keyword.iskeyword(s) or s in _RESERVED else s


def _const(name: str) -> str:
    return re.sub(r"\W+", "_", name).strip("_").upper() or "ROWS"


def _unique(base: str, taken: set) -> str:
    name, n = base, 2
    while name in taken:
        name, n = f"{base}_{n}", n + 1
    taken.add(name)
    return name


def _field_expr(field: str, uses: set, name_field: str | None) -> str:
    """A placeholder value for a row field, as code over the row number `n`."""
    keys = {k for _, k in uses}
    types = {t for t, _ in uses}
    if field == "id":
        return 'f"item-{n}"'
    if keys & {"systemName", "icon"}:
        return '"star"'                                       # an SF Symbol name
    if keys & {"url", "src", "imageURL"}:
        return 'f"https://example.com/item-{n}.png"'
    if "number" in keys or (keys & {"value", "defaultValue"}
                            and types & {"gauge", "progressRing", "slider", "stepper"}):
        return "n"
    if keys & {"value", "defaultValue"} and "toggle" in types:
        return "n % 2 == 0"
    if field == name_field:
        return 'f"Item {n}"'
    return f'f"Example {field} {{n}}"'


def _name_field(fields: dict) -> str | None:
    for f in ("name", "title", "label"):
        if f in fields:
            return f
    return next((f for f, uses in fields.items() if ("label", "text") in uses), None)


def _rows_code(const: str, fields: dict, count: int, what: str, columns: bool = False) -> str:
    nf = _name_field(fields)
    order = ["id"] + sorted(f for f in fields if f != "id")
    body = ", ".join(f'"{f}": {_field_expr(f, fields[f], nf)}' for f in order)
    line = f"{const} = [{{{body}}}\n{' ' * (len(const) + 4)}for n in range(1, {count + 1})]"
    if len(line.split("\n")[0]) > 96:
        parts = [f'"{f}": {_field_expr(f, fields[f], nf)}' for f in order]
        line = (f"{const} = [\n    {{" + (",\n     ".join(parts)) + "}\n"
                f"    for n in range(1, {count + 1})]")
    reads = "the list's columns" if columns else "what the rows read as {{item.<field>}}"
    return (f"#: Placeholder rows for {what}.\n"
            f"#: Swap in your own (a database query, an API, files on disk). Every row needs\n"
            f"#: an \"id\"; the other fields are {reads}.\n{line}\n")


def _bad_value(var: str, spec: dict) -> str | None:
    """A condition that is True when `var` is not a value the control could send."""
    t = spec.get("type")
    if spec.get("enum"):
        return f"{var} not in {_lit(list(spec['enum']))}"
    if t == "number":
        cond = f"isinstance({var}, bool) or not isinstance({var}, (int, float))"
        lo, hi = spec.get("min"), spec.get("max")
        num = (int, float)
        if isinstance(lo, num) and isinstance(hi, num):
            cond += f"\n        or not {lo!r} <= {var} <= {hi!r}"
        elif isinstance(lo, num):
            cond += f"\n        or {var} < {lo!r}"
        elif isinstance(hi, num):
            cond += f"\n        or {var} > {hi!r}"
        return cond
    if t == "boolean":
        return f"not isinstance({var}, bool)"
    if t == "string":
        return f"not isinstance({var}, str) or len({var}) > 1024"
    return None


def _spec_note(spec: dict) -> str:
    if spec.get("type") == "none":
        return "no value (a button sends only its payload)"
    bits = [spec.get("type", "json")]
    if spec.get("enum"):
        bits.append(f"one of {_lit(list(spec['enum']))}")
    elif isinstance(spec.get("min"), (int, float)) or isinstance(spec.get("max"), (int, float)):
        bits.append(f"{spec.get('min')} to {spec.get('max')}")
    return ", ".join(str(b) for b in bits)


def _state_default(ctrl: dict):
    """A placeholder start value for a control the hub owns (off, mid-range, first option)."""
    from .contract import expects_spec, sample_value
    spec = expects_spec(ctrl)
    return False if spec.get("type") == "boolean" else sample_value(spec)


def _live_expr(p: dict) -> str | None:
    """Placeholder reading for a live readout, as code over `tick`; None = no safe guess."""
    from .contract import expects_spec
    spec = expects_spec(p["control"])
    t = spec.get("type")
    if p["type"] == "progressRing":
        return "round(random.random(), 2)"
    if spec.get("enum"):
        return f"random.choice({_lit(list(spec['enum']))})"
    if t == "number":
        lo = spec.get("min", 0) if isinstance(spec.get("min"), (int, float)) else 0
        hi = spec.get("max", 100) if isinstance(spec.get("max"), (int, float)) else 100
        return f"round(random.uniform({lo!r}, {hi!r}), 1)"
    if p["type"] == "logConsole":
        return 'f"Example log line {tick}"'
    if t == "string" and p["type"] in ("label", "qrCode", "keyValue"):
        return 'f"Example reading {tick}"'
    return None


def _fs(text) -> str:
    """`text` made safe inside a generated f"..." literal."""
    s = re.sub(r"\s+", " ", str(text)).replace("\\", "\\\\").replace('"', '\\"')
    return s.replace("{", "{{").replace("}", "}}")


def _cm(text) -> str:
    """`text` made safe inside a generated comment or docstring line."""
    return re.sub(r"\s+", " ", str(text)).replace('"""', "'''").replace("\\", "/")


def _lit(v) -> str:
    """A Python literal for `v`, strings in double quotes (the house style)."""
    import json
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_lit(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{_lit(k)}: {_lit(x)}" for k, x in v.items()) + "}"
    return repr(v)


def _shorten(values: list, n: int = 4) -> str:
    shown = ", ".join(_lit(v) for v in values[:n])
    return shown + (f", ... ({len(values)} in all)" if len(values) > n else "")


def _form_check_code(fn: str, form: dict, label: str) -> str:
    """`def fn(form) -> reason | None`: the form's own rules (form.fields), again on the hub."""
    lines = [f"def {fn}(form: dict) -> str | None:",
             f'    """The rules of the form "{label}" (its form.fields in the layout), checked',
             '    again here: the phone\'s checks are a convenience, the hub decides. Returns a',
             '    reason to refuse, or None. Add your own rules below."""']
    rules = form.get("rules") or {}
    for f in [*form.get("fields", []), *[k for k in rules if k not in form.get("fields", [])]]:
        r = rules.get(f) if isinstance(rules.get(f), dict) else {}
        if not r:
            continue
        v = _var(f)
        lines.append(f'    {v} = form.get("{f}")')
        if r.get("required"):
            lines.append(f'    if {v} is None or str({v}).strip() == "":')
            lines.append(f'        return "{f} is required"')
        body = []
        kind = r.get("kind")
        if kind in ("integer", "number") or "min" in r or "max" in r:
            conv = "int" if kind == "integer" else "float"
            body += ["try:", f"    {v} = {conv}({v})", "except (TypeError, ValueError):",
                     f'    return "{f} must be {"a whole number" if conv == "int" else "a number"}"']
            lo, hi = r.get("min"), r.get("max")
            if lo is not None and hi is not None:
                body += [f"if not {lo!r} <= {v} <= {hi!r}:", f'    return "{f} must be {lo} to {hi}"']
            elif lo is not None:
                body += [f"if {v} < {lo!r}:", f'    return "{f} must be at least {lo}"']
            elif hi is not None:
                body += [f"if {v} > {hi!r}:", f'    return "{f} must be at most {hi}"']
        if "minLength" in r:
            body += [f"if len(str({v})) < {r['minLength']!r}:",
                     f'    return "{f} needs at least {r["minLength"]} characters"']
        if "maxLength" in r:
            body += [f"if len(str({v})) > {r['maxLength']!r}:",
                     f'    return "{f} takes at most {r["maxLength"]} characters"']
        if isinstance(r.get("oneOf"), list):
            body += [f"if {v} not in {_lit(list(r['oneOf']))}:",
                     f'    return "{f} must be one of {", ".join(map(str, r["oneOf"]))}"']
        if kind in ("date", "email", "url"):
            body += [f"pass  # TODO: check that {f} is a {kind} (the phone checked its shape)"]
        if not body:
            if not r.get("required"):
                lines.pop()               # the read of a field with no rule to check
            continue
        if r.get("required"):             # never empty past the check above
            lines += ["    " + b for b in body]
        else:
            lines.append(f'    if {v} is not None and str({v}).strip() != "":')
            lines += ["        " + b for b in body]
    lines.append("    return None")
    return "\n".join(lines) + "\n"


def _confirm_lines(e: dict, label: str, subject: str | None, ind: str) -> list[str]:
    """hub.confirm before a command that is hard to take back — or, when the layout's
    action already asks in the app (confirm: "dialog"), a note (asking twice is worse)."""
    c = e["confirm"]
    if c is not None:
        title = c.get("confirmTitle") or f"{label}?"
        args = [_lit(title)]
        if c.get("confirmMessage"):
            args.append(_lit(c["confirmMessage"]))
        if c.get("confirmLabel"):
            args.append(f"confirm_label={_lit(c['confirmLabel'])}")
        if c.get("destructive"):
            args.append("destructive=True")
        return [f'{ind}# The app asks first (the action has confirm: "dialog"), so this frame',
                f"{ind}# means the user said yes. To ask from the hub instead (a widget or Siri",
                f'{ind}# press never fires a dialog action), drop "confirm" from the layout and use:',
                *textwrap.wrap(f"choice = await hub.confirm({', '.join(args)})", 88 - len(ind),
                               initial_indent=f"{ind}#     ",
                               subsequent_indent=f"{ind}#         "),
                f'{ind}#     if choice != "confirm":',
                f"{ind}#         return"]
    if not e["ask"]:
        return []
    what = f'f"{_fs(label)} {{{subject}}}?"' if subject else _lit(f"{label}?")
    return [f"{ind}# Hard to take back, so the hub asks on the phone first (it names this hub).",
            f"{ind}choice = await hub.confirm({what}, confirm_label={_lit(label)},",
            f"{ind}                           destructive=True, timeout_s=30)",
            f'{ind}if choice != "confirm":          # "cancel", "timeout" or "busy"',
            f'{ind}    await say(hub, f"Kept it ({{choice}})")',
            f"{ind}    return"]


def _source_note(e: dict) -> str:
    src = e["sources"]
    s = src[0]
    if e["form"]:
        who = f'the form "{s["label"]}" (Send)'
    elif s["row_of"]:
        who = f'{s["label"]} ({s["type"]}, in each row of list "{s["row_of"]}")'
    elif s["type"] in ("list", "cardList") and s["key"] == "action":
        who = f'a row tap on {s["type"]} "{s["id"]}"'
    else:
        who = f'{s["label"]} ({s["type"]})'
    if len(src) > 1:
        return _cm(f"{who} and {len(src) - 1} more send {e['command']}")
    return _cm(f"{who} sends {e['command']}")


def _handler_code(e: dict, fn: str, form_fn: str | None) -> str:
    ind = "        "
    s0 = e["sources"][0]
    label = s0["label"]
    if s0["type"] in ("list", "cardList") and s0["key"] == "action":
        label = "Tapped row"
    reg = e["register"]
    dec, note = f'    @hub.on("{reg}")', _source_note(e)
    head = ([dec.ljust(40) + f"# {note}"] if len(dec.ljust(40) + note) < 98
            else [f"    # {note}", dec])
    if e["collides"]:
        head.insert(0, f'    # NOTE: "{e["command"]}" is also a control id in the layout, so hub.on()')
        head.insert(1, "    # resolves it to that control: rename the command or that control.")
    if e["transport"] == "routed":
        head.insert(0, "    # A routed action: the frame is the routed payload.")
    body = [f"    async def {fn}(frame):"]
    said: list[str] = []
    subject = None
    if e["form"]:
        body.append(f'{ind}form = frame.get("form") if isinstance(frame.get("form"), dict) else {{}}')
        if form_fn:
            body.append(f"{ind}reason = {form_fn}(form)")
            body.append(f"{ind}if reason:")
            body.append(f'{ind}    await say(hub, f"Not saved: {{reason}}")')
            body.append(f"{ind}    return")
        first = (e["form"]["fields"] or [None])[0]
        said = [f"{{form.get({first!r})}}"] if first else []
    for key, f in e["fields"].items():
        if f["kind"] == "form" and f["field"] is None:
            continue
        v = _var(key)
        if f["kind"] == "value":
            spec = f["spec"]
            if s0["type"] in ("list", "cardList") and s0["key"] == "action":
                spec, note = {"type": "string"}, "the tapped row's id"
            else:
                note = _spec_note(spec)
            body.append(f'{ind}{v} = frame.get("{key}")'.ljust(44) + f"# {note}")
            bad = _bad_value(v, spec)
            if bad:
                if "\n" in bad:
                    first, rest = bad.split("\n", 1)
                    body.append(f"{ind}if ({first}")
                    body.append(f"{ind}{rest.strip().join(['        ', '):'])}")
                else:
                    body.append(f"{ind}if {bad}:")
                if e["echo"]:
                    body.append(f'{ind}    await hub.push("{e["echo"]}", STATE["{e["echo"]}"], force=True)'
                                "  # snap it back")
                else:
                    body.append(f'{ind}    print(f"{e["command"]}: ignoring {{{v}!r}}")')
                body.append(f"{ind}    return")
        elif f["kind"] == "item":
            body.append(f'{ind}{v} = frame.get("{key}")'.ljust(44) + f'# the row\'s "{f["field"]}"')
        elif f["kind"] == "form":
            body.append(f'{ind}{v} = frame.get("{key}")'.ljust(44) + f'# the form\'s "{f["field"]}"')
        elif f["kind"] == "token":
            body.append(f'{ind}{v} = frame.get("{key}")'.ljust(44)
                        + f"# {{{{{f['token']}}}}}: {_spec_note(f['spec'])}")
        else:
            body.append(f'{ind}{v} = frame.get("{key}")'.ljust(44) + f"# {_shorten(f['values'])}")
        if subject is None and f["kind"] in ("item", "const", "value"):
            subject = v
        said.append(f"{{{v}}}")
    body += _confirm_lines(e, label, subject, ind)
    if e["echo"]:
        cid = e["echo"]
        val = _var(next(k for k, f in e["fields"].items() if f["kind"] == "value"))
        body.append(f'{ind}STATE["{cid}"] = {val}'.ljust(44)
                    + "# TODO: set your device; keep what it reports")
        body.append(f'{ind}await hub.push("{cid}", STATE["{cid}"], force=True)'
                    "  # always resend")
    elif not e["form"]:
        body.append(f"{ind}# TODO: do the real work for {e['command']} here")
    else:
        body.append(f"{ind}# TODO: keep the entry (a database row, a file, a device setting)")
    verb = "Saved" if e["form"] else f"{_fs(label)}:"
    body.append(f'{ind}await say(hub, f"{verb} {" ".join(said)}")' if said
                else f'{ind}await say(hub, {_lit(label)})')
    return "\n".join(head + body) + "\n"


def generate_hub(layout: dict, layout_ref: str = "layout.json") -> str:
    """A hub script for `layout`, shaped like a starter kit's hub.py: one handler per
    command its controls send, ``@hub.pages`` for paged lists, ``hub.confirm`` before
    commands that are hard to take back, ``hub.open_sheet`` helpers for groups that
    expand, and ``hub.push`` stubs (state, rows, a periodic task for live readouts).
    ``layout_ref`` is where the script finds the layout, relative to the script."""
    a = analyze_hub(layout)
    name = a["name"]
    pushes = a["pushes"]
    live = [p for p in pushes if p["role"] == "live" and not p["same_as"]]
    live_exprs = [(p, _live_expr(p)) for p in live]
    loop = any(x for _, x in live_exprs)
    other = [p for p in pushes if p["role"] == "other"] + [p for p, x in live_exprs if not x]
    state = {p["id"]: _state_default(p["control"]) for p in pushes if p["role"] == "state"}
    rows = [p for p in pushes if p["role"] == "rows"]
    taken = {"run", "say", "publish", "matches", "ui", "main", "hub", "frame"}
    consts = {}
    for item in [*a["pages"], *rows]:
        cid = item.get("list") or item.get("id")
        consts[cid] = _unique(_const(cid), taken)

    out: list[str] = []
    # ── docstring ──
    doc = [f'"""{_cm(name)}: the hub side of {_cm(layout_ref)}, written by `carterkit codegen`.',
           "",
           "Run:  python hub.py   then scan the QR it prints with the CAR-TER app.",
           "Edit this file or the layout while it runs: every save reaches the phone.",
           "",
           "What the layout sends the hub, and what this file does with it:"]
    width = max([len(e["command"]) for e in a["commands"]]
                + [len(p["request"]) for p in a["pages"]] + [12])
    for p in a["pages"]:
        doc.append(f'  {p["request"].ljust(width)}  pages of list "{_cm(p["list"])}" '
                   f'-> @hub.pages, answered as {p["replyType"]}')
    for e in a["commands"]:
        extra = (" (asks first: hub.confirm)" if e["ask"]
                 else " (the app asks first)" if e["confirm"] else "")
        doc += textwrap.wrap(f"{_source_note(e)}{extra}", 92,
                             initial_indent=f"  {e['command'].ljust(width)}  ",
                             subsequent_indent=" " * (width + 6))
    if a["sheets"]:
        doc.append(f"  {'sheet_closed'.ljust(width)}  the app closed a sheet the hub opened")
    if not (a["pages"] or a["commands"]):
        doc.append("  (nothing: this layout sends the hub no commands)")
    fed = [p for p in pushes if p["role"] != "other"]
    if fed:
        doc += ["", "What the hub sends back (hub.push, by control id):"]
        what = {"live": "a live reading, every INTERVAL seconds", "rows": "its rows",
                "state": "the hub's value (the hub owns it)", "status": "what the hub just did"}
        for p in fed:
            note = f'the same frame as "{p["same_as"]}"' if p["same_as"] else what[p["role"]]
            doc.append(f'  {p["id"].ljust(width)}  {p["type"]}: {note}')
    app_side = []
    for v in a["expand_verbs"]:
        app_side.append(f'{_cm(v["label"])} ({v["id"]}) runs {v["verb"]} on group "{v["group"]}"')
    for p in a["pages"]:
        tpl = None
        for ch, _ in _hub_walk(layout):
            if ch.get("id") == p["list"] and isinstance(ch.get("itemTemplate"), dict):
                tpl = ch["itemTemplate"]
        if tpl and isinstance(tpl.get("expand"), dict):
            app_side.append(f'each row of list "{p["list"]}" expands into a page')
    for gid, ev in a["dynamic"]:
        app_side.append(f'dynamic group "{gid}": hub.fill("{gid}", children) replaces its '
                        f"children (broadcast {ev})")
    if app_side:
        doc += ["", "The app does these on its own (no hub code needed):"]
        doc += [f"  - {x}" for x in app_side]
    doc += ["", "Every value marked TODO or Example is a placeholder: put your real data there.",
            '"""']
    out.append("\n".join(doc))

    # ── imports, layout ──
    imports = []
    if loop:
        imports += ["import asyncio", "import random"]
    imports.append("from pathlib import Path")
    kit = "HubError, Layout" if a["sheets"] else "Layout"
    out.append("\n".join(imports) + f"\n\nfrom carterkit import {kit}\n")
    if "/" not in layout_ref and "\\" not in layout_ref:
        out.append(f'ui = Layout.load(Path(__file__).with_name("{layout_ref}"))\n')
    else:
        out.append(f'ui = Layout.load(Path(__file__).parent / "{layout_ref}")\n')

    # ── module state ──
    if loop:
        out.append("INTERVAL = 1.0          # seconds between live readings\n")
    if state:
        body = ", ".join(f'"{k}": {_lit(v)}' for k, v in state.items())
        out.append("#: The hub's copy of every control it owns (the phone only asks to change it).\n"
                   "#: Placeholder start values: read them from your device.\n"
                   f"STATE = {{{body}}}\n")
    for p in a["pages"]:
        out.append(_rows_code(consts[p["list"]], p["fields"], 200,
                              f'the paged list "{p["list"]}" (200, sent {p["pageSize"]} at a time)'))
    for p in rows:
        out.append(_rows_code(consts[p["id"]], p["fields"], 6, f'the list "{p["id"]}"',
                              columns=not isinstance(p["control"].get("itemTemplate"), dict)))

    # ── helpers ──
    if a["pages"]:
        out.append('\ndef matches(row: dict, query: str) -> bool:\n'
                   '    """Search on the hub: a row matches when any field contains the text."""\n'
                   '    q = (query or "").strip().lower()\n'
                   '    return not q or any(q in str(v).lower() for v in row.values())\n')
    form_fns = {}
    for e in a["commands"]:
        if e["form"] and e["form"].get("rules"):
            fn = _unique(f"check_{_var(e['form']['group'] or 'form').rstrip('_')}", taken)
            form_fns[e["command"]] = fn
            out.append("\n" + _form_check_code(fn, e["form"], e["sources"][0]["label"]))
    if a["status"]:
        out.append(f'\nasync def say(hub, text: str) -> None:\n'
                   f'    """Tell the phone (the "{a["status"]}" label) and this terminal what the hub did."""\n'
                   f'    print(text)\n'
                   f'    await hub.push("{a["status"]}", text, force=True)   # even when it says the same\n')
    else:
        out.append('\nasync def say(hub, text: str) -> None:\n'
                   '    """Tell this terminal what the hub did (the layout has no status label)."""\n'
                   '    print(text)\n')
    if live or other:
        lines = ['\nasync def publish(hub, tick: int) -> None:',
                 '    """One reading for every live readout. Placeholder values: read your real ones here."""']
        for p, x in live_exprs:
            twins = [q["id"] for q in pushes if q["same_as"] == p["id"]]
            note = f"  # also moves {', '.join(twins)} (same frame)" if twins else ""
            if x:
                lines.append(f'    await hub.push("{p["id"]}", {x}){note}')
        for p in other:
            from .contract import expects_spec
            lines.append(f'    # await hub.push("{p["id"]}", ...)  # TODO: a {p["type"]} value '
                         f"({_cm(_spec_note(expects_spec(p['control'])))}): "
                         f"see `carterkit doc {p['type']}`")
        if not loop:
            lines.append("    pass")
        out.append("\n".join(lines) + "\n")
    for sh in a["sheets"]:
        fn = _unique(f"open_{_var(sh['group']).rstrip('_')}", taken)
        sh["fn"] = fn
        args = [f'group_id="{sh["group"]}"']
        if sh["title"]:
            args.append(f"title={_lit(sh['title'])}")
        args.append(f'style="{sh["style"]}"')
        args.append(f'id="{sh["group"]}"')
        out.append(f'\nasync def {fn}(hub) -> str | None:\n'
                   f'    """Open group "{sh["group"]}" in the app\'s {sh["style"]} container, laid out by its\n'
                   f'    expand block. The app opens it on its own too (trigger: {_cm(sh["trigger"])});\n'
                   f'    call this when the hub decides to (from a handler). Sending the same id again\n'
                   f'    replaces the open sheet; hub.close_sheet("{sh["group"]}") closes it."""\n'
                   f'    try:\n'
                   f'        return await hub.open_sheet({", ".join(args[:2])},\n'
                   f'                                    {", ".join(args[2:])})\n'
                   f'    except HubError as e:          # not-hub, invalid, not-found, busy\n'
                   f'        await say(hub, f"No sheet: {{e}}")\n'
                   f'        return None\n')

    # ── run(hub) ──
    run = ['\nasync def run(hub):', '    """Handlers; restarted on every save."""']
    for p in a["pages"]:
        fn = _unique(f"{_var(p['list']).rstrip('_')}_page", taken)
        q = (f'  # query: the text in "{p["queryFrom"]}"' if p.get("queryFrom") else "")
        run += ["",
                f'    @hub.pages("{p["list"]}")'.ljust(40)
                + f'# the list asks for {p["pageSize"]} rows at a time ({p["request"]})',
                f"    def {fn}(offset, limit, cursor, query):{q}",
                f"        rows = [r for r in {consts[p['list']]} if matches(r, query)]",
                ("        return rows[offset:offset + limit], None, len(rows)"
                 "    # (items, next cursor, total)")]
    for e in a["commands"]:
        fn = _unique(_var(e["command"]).rstrip("_") or "on_command", taken)
        run += ["", _handler_code(e, fn, form_fns.get(e["command"])).rstrip("\n")]
    if a["sheets"]:
        run += ["",
                '    @hub.on("sheet_closed")'.ljust(40) + "# the app closed a sheet the hub opened",
                "    async def sheet_closed(frame):     # {\"id\", \"reason\": user|hub|replaced|busy}",
                "        await say(hub, f\"Closed {frame.get('id')} ({frame.get('reason')})\")"]
        run += ["", (f'    # From any handler, `await {a["sheets"][0]["fn"]}(hub)` opens group '
                     f'"{a["sheets"][0]["group"]}" from the hub.')]
    start = []
    if state:
        start.append("    for key, value in STATE.items():       # the hub's values, from the start")
        start.append("        await hub.push(key, value)")
    for p in rows:
        start.append(f'    await hub.push("{p["id"]}", {consts[p["id"]]})')
    if a["status"]:
        start.append(f'    await hub.push("{a["status"]}", "Hub ready")')
    if start:
        run += [""] + start
    if loop:
        run += ["", "    tick = 0", "    while True:                            # the live readings",
                "        tick += 1", "        await publish(hub, tick)",
                "        await asyncio.sleep(INTERVAL)"]
    if len(run) == 2:
        run.append("    pass")
    out.append("\n".join(run) + "\n")
    out.append('\nif __name__ == "__main__":\n'
               "    from carterkit import livefile\n"
               "    raise SystemExit(livefile.main(__file__))\n")
    return "\n".join(out)
