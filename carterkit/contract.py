"""Typed wire contract — the machine-readable API a layout exposes.

A layout is secretly an API: its interactive controls fire **triggers** (actions
on the mesh) and its display controls subscribe to **feeds** (broadcast frames
matched by filter + valuePath). :func:`extract_contract` walks a layout — through
groups, container panels, and canvas items, the same nesting the phone's Layout
Editor produces — and returns that API *type-defined*: every trigger with its
payload template, token types, and the native type of ``{{value}}``; every feed
with the scalar type it expects and a ready-to-send example frame.

This is what `carterkit explore` renders, what typed stubs are derived from, and
what an agent can read instead of reverse-engineering the JSON. Pure logic — no
network, no side effects. The connection block is included **redacted** (never a
token or key): a contract is meant to be shared.
"""

from __future__ import annotations

import copy
from typing import Any, Callable

# ── token vocabulary ─────────────────────────────────────────────────────────
# Substitution tokens an action payload may carry (ControlDocs/actions.md and
# the per-control docs). `{{value}}` resolves to the control's native value —
# its type comes from VALUE_SPECS below. The rest are fixed-type.

TOKEN_TYPES: dict[str, dict] = {
    "value":   {"type": "native", "description": "the control's current value (native type)"},
    "item":    {"type": "string", "description": "the dragged/tapped item's id"},
    "from":    {"type": "string", "description": "source zone id (sortboard)"},
    "to":      {"type": "string", "description": "destination zone id (sortboard)"},
    "index":   {"type": "number", "description": "position within the destination zone"},
    "x":       {"type": "number", "description": "normalized x (0–1)"},
    "y":       {"type": "number", "description": "normalized y (0–1)"},
    "bearing": {"type": "number", "description": "degrees, 0 = north, clockwise"},
    "total":   {"type": "number", "description": "sum of all pie segments"},
    "kind":    {"type": "string", "description": "camera detection kind (qr/barcode/text)"},
    "image":   {"type": "string", "description": "base64 JPEG snapshot (camera)"},
    "width":   {"type": "number", "description": "snapshot pixel width"},
    "height":  {"type": "number", "description": "snapshot pixel height"},
}


# ── native value of {{value}}, per emitting control type ─────────────────────
# Builders take the control dict so config (min/max/options/…) refines the type.

def _num(ctrl: dict, lo=0, hi=100, step=None) -> dict:
    spec = {"type": "number",
            "min": ctrl.get("min", lo), "max": ctrl.get("max", hi)}
    st = ctrl.get("step", step)
    if st is not None:
        spec["step"] = st
    return spec


def _enum(ctrl: dict, key: str = "options") -> dict:
    opts = ctrl.get(key)
    spec: dict = {"type": "string"}
    if isinstance(opts, list) and opts:
        spec["enum"] = [str(o) for o in opts]
    return spec


VALUE_SPECS: dict[str, Callable[[dict], dict]] = {
    "button":           lambda c: {"type": "none", "note": "static payload — button has no value"},
    "toggle":           lambda c: {"type": "boolean"},
    "slider":           lambda c: _num(c),
    "stepper":          lambda c: _num(c),
    "segmentedControl": lambda c: _enum(c),
    "picker":           lambda c: _enum(c),
    "textInput":        lambda c: {"type": "string"},
    "colorPicker":      lambda c: {"type": "string", "format": "hex-color"},
    "datePicker":       lambda c: {"type": "string", "format": "iso-date"},
    "camera":           lambda c: {"type": "string", "note": "scanned/recognized text"},
    "compass":          lambda c: {"type": "string", "note": "the pointed-at puck's id"},
    "joystick":         lambda c: {"type": "object", "shape": {"x": "number", "y": "number"},
                                   "note": "axes via $value.x / $value.y"},
    "chat":             lambda c: {"type": "string", "note": "chat_message protocol frame"},
    "canvas":           lambda c: {"type": "string", "note": "the moved item's id ({{item}}/{{x}}/{{y}} carry placement)"},
    "pinboard":         lambda c: {"type": "string", "note": "the placed marker's id ({{x}}/{{y}} carry position)"},
    "sortboard":        lambda c: {"type": "string", "note": "the dragged item's id ({{from}}/{{to}}/{{index}} carry the move)"},
    "pieChart":         lambda c: {"type": "number", "note": "tapped segment value ({{total}} = sum)"},
}

_DATUM_TAP = {"type": "number", "note": "tapped datum value"}
for _t in ("chart", "heatmap", "radar", "boxPlot", "gantt", "sankey", "treemap", "chord", "graph"):
    VALUE_SPECS[_t] = lambda c, _d=_DATUM_TAP: dict(_d)


# ── scalar a feed's valuePath must resolve to, per listening control type ────

EXPECTS_SPECS: dict[str, Callable[[dict], dict]] = {
    "gauge":        lambda c: _num(c),
    "progressRing": lambda c: {"type": "number", "min": 0, "max": 1},
    "sparkline":    lambda c: {"type": "number", "note": "each value appends to the rolling buffer"},
    "slider":       lambda c: _num(c),
    "stepper":      lambda c: _num(c),
    "toggle":       lambda c: {"type": "boolean"},
    "statusLight":  lambda c: (
        {"type": "string", "enum": sorted(c["statusColors"])}
        if isinstance(c.get("statusColors"), dict) and c["statusColors"]
        else {"type": "string", "note": "status word or color"}),
    "label":        lambda c: {"type": "string", "note": "numbers/bools are stringified"},
    "textInput":    lambda c: {"type": "string"},
    "segmentedControl": lambda c: _enum(c),
    "picker":       lambda c: _enum(c),
    "image":        lambda c: {"type": "string", "format": "url-or-base64"},
    "qrCode":       lambda c: {"type": "string", "note": "encoded into the QR"},
    "colorPicker":  lambda c: {"type": "string", "format": "hex-color"},
    "map":          lambda c: {"type": "number", "note": "coordinate — bind lat and lng valuePaths"},
    "list":         lambda c: {"type": "array", "items": "object", "note": "rows replace"},
    "cardList":     lambda c: {"type": "array", "items": "object", "note": "cards replace"},
    "logConsole":   lambda c: {"type": "string", "note": "or {text, level}, or an array of either"},
    "graph":        lambda c: {"type": "object", "shape": {"nodes": "array", "edges": "array"}},
    "chart":        lambda c: {"type": "json", "note": "dataset — see the chart ControlDoc"},
    "heatmap":      lambda c: {"type": "json", "note": "matrix/cells — see the heatmap ControlDoc"},
    "radar":        lambda c: {"type": "json", "note": "vertex values — see the radar ControlDoc"},
    "canvas":       lambda c: {"type": "object", "note": "{frames:{id:{x,y,w,h}}} placement state"},
    "pinboard":     lambda c: {"type": "object", "note": "marker placement state"},
    "sortboard":    lambda c: {"type": "object", "note": "zone/item placement state"},
    "compass":      lambda c: {"type": "object", "note": "puck bearings"},
    "chat":         lambda c: {"type": "object", "note": "chat_message frames"},
}

_GENERIC = lambda c: {"type": "json"}  # noqa: E731 — table default, not a def


def value_spec(ctrl: dict) -> dict:
    """The native type of ``{{value}}`` for this control."""
    return VALUE_SPECS.get(ctrl.get("type", ""), _GENERIC)(ctrl)


def expects_spec(ctrl: dict) -> dict:
    """The type this control's sync valuePath must resolve to."""
    return EXPECTS_SPECS.get(ctrl.get("type", ""), _GENERIC)(ctrl)


# ── layout traversal (breadcrumbed) ──────────────────────────────────────────

def is_group(node: dict) -> bool:
    """Whether a layout child is a group.

    Normally that's ``type == "group"``. But a node that *carries children* is a group
    whatever it says: the app's `get-current-layout` echo re-encodes its model, and
    older builds emit group nodes with no `type` at all (the Swift `GroupDefinition`
    has no such field). Treating those as unknown controls made every walker stop at
    the group and silently drop everything nested inside it — so accept the implicit
    shape too. Container controls (carousel/flipCard/accordion) nest under `panels`,
    not `children`, so they are not caught by this.
    """
    return node.get("type") == "group" or (
        node.get("type") is None and isinstance(node.get("children"), list)
    )


def walk_with_location(layout: dict):
    """Yield ``(control, tab_title, breadcrumb)`` for every control, recursing
    through groups, container panels (carousel/flipCard/accordion), and
    canvas-hosted items — the same nesting the phone's Layout Editor produces."""

    def walk(children, tab, crumb):
        for ch in children or []:
            if not isinstance(ch, dict):
                continue
            yield ch, tab, crumb
            label = ch.get("label") or ch.get("id") or ch.get("type", "?")
            if is_group(ch):
                yield from walk(ch.get("children"), tab, crumb + [label])
            for i, panel in enumerate(ch.get("panels") or []):
                if isinstance(panel, dict):
                    ptitle = panel.get("title") or f"page {i + 1}"
                    yield from walk(panel.get("children"), tab, crumb + [label, ptitle])
            cfg = ch.get("canvasConfig")
            if isinstance(cfg, dict):
                for item in cfg.get("items") or []:
                    if isinstance(item, dict) and isinstance(item.get("control"), dict):
                        yield item["control"], tab, crumb + [label]

    for tab in layout.get("tabs", []):
        yield from walk(tab.get("children"), tab.get("title") or "?", [])


# ── frame/example helpers ────────────────────────────────────────────────────

def _set_path(obj: dict, path: str, value) -> None:
    parts = path.split(".")
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
        if not isinstance(obj, dict):
            return
    obj[parts[-1]] = value


_SAMPLES = {"number": 42, "boolean": True, "string": "hello",
            "array": [], "object": {}, "json": {}, "none": None}


def sample_value(spec: dict):
    """A plausible example value for a spec (midpoint for bounded numbers,
    first enum member for enums)."""
    if spec.get("enum"):
        return spec["enum"][0]
    if spec.get("type") == "number" and isinstance(spec.get("min"), (int, float)) \
            and isinstance(spec.get("max"), (int, float)):
        mid = (spec["min"] + spec["max"]) / 2
        return round(mid, 2) if isinstance(mid, float) and mid != int(mid) else int(mid)
    return _SAMPLES.get(spec.get("type", "json"), {})


def example_frame(feed: dict) -> dict:
    """The broadcast frame that would drive this feed: its filter keys plus a
    sample value planted at the valuePath."""
    frame = copy.deepcopy(feed.get("filter") or {})
    path = feed.get("valuePath")
    if path:
        _set_path(frame, path, sample_value(feed.get("expects", {})))
    return frame


def _tokens_in(payload: Any) -> set[str]:
    found: set[str] = set()

    def scan(v):
        if isinstance(v, str):
            for name in TOKEN_TYPES:
                if "{{" + name + "}}" in v:
                    found.add(name)
            if "$value." in v:
                found.add("value")
        elif isinstance(v, dict):
            for x in v.values():
                scan(x)
        elif isinstance(v, list):
            for x in v:
                scan(x)

    scan(payload)
    return found


# ── the contract ─────────────────────────────────────────────────────────────

def _redacted_connection(layout: dict) -> dict | None:
    conn = layout.get("connection")
    if not isinstance(conn, dict):
        return None
    out = {k: conn[k] for k in ("url", "mode") if k in conn}
    ident = conn.get("identity")
    if isinstance(ident, dict):
        out["channel"] = ident.get("channel")
        out["role"] = ident.get("role")
    for secret in ("token", "e2eeKey"):
        if secret in conn:
            out[secret] = "••• redacted"
    return out


def _command_of(action: dict) -> tuple[str | None, str]:
    """(command name, transport) for an action binding — broadcast_request
    demuxes on payload.msg_type, routed actions on the inner type."""
    ev, payload = action.get("event"), action.get("payload")
    if ev == "broadcast_request":
        name = payload.get("msg_type") if isinstance(payload, dict) else None
        return name, "broadcast"
    if ev in ("route_msg", "route_msg_noreply"):
        name = payload.get("type") if isinstance(payload, dict) else None
        return name, "routed"
    return ev, "legacy"


def extract_contract(layout: dict) -> dict:
    """The type-defined API this layout exposes on the mesh."""
    triggers: dict[str, dict] = {}
    feeds: list[dict] = []
    dynamic: list[dict] = []
    app_direct: list[dict] = []   # mqtt/http/sensor bindings the APP serves — not the hub

    for ctrl, tab, crumb in walk_with_location(layout):
        ctype = ctrl.get("type", "?")
        label = ctrl.get("label") or ctrl.get("id") or ctype
        where = " › ".join([tab] + crumb)

        if is_group(ctrl) and ctrl.get("dynamic"):
            dynamic.append({"id": ctrl.get("id", "?"), "event": ctrl["dynamic"],
                            "tab": tab, "where": where})

        for akey, gesture in (("action", "tap"), ("longPressAction", "long-press")):
            a = ctrl.get(akey)
            if isinstance(a, dict) and a.get("method") in ("mqtt", "http"):
                # App-direct outbound: the app publishes/requests it itself, no server.
                app_direct.append({"id": ctrl.get("id"), "type": ctype, "label": label,
                                   "where": where, "direction": "out", "gesture": gesture,
                                   "transport": a["method"],
                                   "address": a.get("topic") or a.get("path") or a.get("url")})
                continue
            if not (isinstance(a, dict) and a.get("event")):
                continue
            command, transport = _command_of(a)
            if not command:
                continue
            tokens = {name: (value_spec(ctrl) if name == "value"
                             else dict(TOKEN_TYPES[name]))
                      for name in sorted(_tokens_in(a.get("payload")))}
            entry = triggers.setdefault(command, {
                "command": command,
                "wire": {"event": a.get("event"), "transport": transport,
                         "mode": a.get("mode", "broadcast")},
                "sources": [], "payloadTemplate": a.get("payload"),
                "tokens": {},
            })
            entry["sources"].append({"id": ctrl.get("id"), "type": ctype,
                                     "label": label, "gesture": gesture,
                                     "where": where, "value": value_spec(ctrl)})
            entry["tokens"].update(tokens)

        syncs = ctrl.get("sync")
        if isinstance(syncs, dict):
            syncs = [syncs]
        for s in syncs or []:
            if not isinstance(s, dict):
                continue
            method = s.get("method", "meshsocket")
            if method in ("mqtt", "http", "sensor"):
                # App-direct inbound: the app subscribes/polls/reads it itself, no server.
                app_direct.append({"id": ctrl.get("id"), "type": ctype, "label": label,
                                   "where": where, "direction": "in", "transport": method,
                                   "address": s.get("topic") or s.get("path") or s.get("url")
                                              or s.get("sensor")})
                continue
            feed = {"id": ctrl.get("id"), "type": ctype, "label": label,
                    "where": where,
                    "event": s.get("event") or "broadcast",
                    "filter": s.get("filter") or {},
                    "valuePath": s.get("valuePath") or "",
                    "expects": expects_spec(ctrl)}
            feed["example"] = example_frame(feed)
            feeds.append(feed)

    publishers = [{"sensor": p.get("sensor"), "msg_type": "sensor",
                   "note": "the phone streams readings tagged with this sensor name"}
                  for p in layout.get("publishers") or [] if isinstance(p, dict)]

    return {
        "layout": {"name": layout.get("name", "layout"),
                   "tabs": [t.get("title") or "?" for t in layout.get("tabs", [])],
                   "controls": sum(1 for _ in walk_with_location(layout))},
        "connection": _redacted_connection(layout),
        "triggers": [triggers[k] for k in sorted(triggers)],
        "feeds": feeds,
        "dynamicGroups": dynamic,
        "publishers": publishers,
        # MQTT/HTTP/sensor bindings the APP handles directly (broker, REST, hardware) —
        # a generated server stub must NOT try to serve these; they need no server code.
        "appDirect": app_direct,
    }
