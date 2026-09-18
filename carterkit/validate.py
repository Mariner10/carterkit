"""Schema-driven layout validation — catch broken layouts before pushing.

Drives off the control catalog (catalog.build_catalog(..., include_theme=True)) so
the field/enum schema stays in sync with the docs. Reports structural problems
(missing required keys), id collisions, unknown control types, unknown fields,
bad enum values, and grid overlaps/out-of-bounds (via grid.validate_placement).

Findings are dicts: {"severity": "error"|"warn", "kind", "where", "detail"}.
"""

from __future__ import annotations

from typing import Optional

from . import grid as gridmod
from .bind import WIRE_VERBS, RELAY_SERVICE_VERBS

# Base/shared properties every control may carry (from the layout schema /
# ChildDefinition), independent of its type. Type-specific fields come from the catalog.
SHARED_FIELDS = {
    "type", "id", "position", "span", "label", "defaultValue", "icon", "tint",
    "hideLabel", "hideBackground", "action", "sync", "visible", "haptic",
    "animation", "longPressGroup", "longPressAction", "theme", "config",
    # Shared display/range/format properties the app decodes on ControlDefinition
    # (not per-control config) — any control may carry them; unused ones are ignored.
    # Mirrors CAR-TER/CAR-TER/Models/ControlDefinition.swift.
    "min", "max", "step", "formatValue", "controlHeight", "hideValue", "pulse",
}
GROUP_FIELDS = {
    "type", "id", "position", "span", "label", "grid", "children", "dynamic",
    "visible", "theme", "hideBackground", "pulse", "icon", "tint", "controlHeight",
}


def _f(severity: str, kind: str, where: str, detail: str) -> dict:
    return {"severity": severity, "kind": kind, "where": where, "detail": detail}


def validate_layout(layout: dict, catalog: dict) -> list[dict]:
    """Validate a full layout against the catalog. `catalog` should be built with
    include_theme=True so per-control theme fields are recognized."""
    findings: list[dict] = []
    if not isinstance(layout, dict):
        return [_f("error", "structure", "root", "layout must be a JSON object")]
    for key in ("name", "version", "tabs"):
        if key not in layout:
            findings.append(_f("error", "missing_field", "root", f"missing top-level '{key}'"))

    # Declared data sources (name -> kind), so control bindings can be checked against
    # them (an mqtt/http `source:` must name a declared source). See sources.md.
    sources = _validate_sources_defs(layout, findings)
    _validate_top_level(layout, findings)

    tabs = layout.get("tabs")
    if not isinstance(tabs, list):
        findings.append(_f("error", "structure", "root", "'tabs' must be an array"))
        return findings

    seen_ids: dict[str, str] = {}
    for ti, tab in enumerate(tabs):
        where = f"tab[{ti}]"
        if not isinstance(tab, dict):
            findings.append(_f("error", "structure", where, "tab must be an object"))
            continue
        g = tab.get("grid") or {}
        cols, rows = int(g.get("columns", 4)), int(g.get("rows", 8))
        children = tab.get("children") or []
        _grid_findings(children, cols, rows, where, findings, g.get("mode"))
        for ch in children:
            _validate_child(ch, catalog, where, findings, seen_ids, sources)

    # A declared source that nothing binds to is dead weight (and usually a typo in a
    # binding's `source`/`topic`) — flag it so authors notice the disconnect.
    referenced: set = set()
    for tab in tabs:
        if isinstance(tab, dict):
            _collect_source_refs(tab.get("children") or [], sources, referenced)
    for name in sources:
        if name not in referenced:
            findings.append(_f("warn", "unused_source", f"sources.{name}",
                               f"source '{name}' is declared but never referenced by any "
                               f"control binding"))

    glance = layout.get("glance")
    if isinstance(glance, dict):
        _validate_glance(glance, seen_ids, findings)
    return findings


# ── glance: the layout projected onto iOS surfaces (see controldocs/glance.md) ──
#
# Everything here is a WARNING unless the surface cannot work at all. A tile whose
# control id is missing is simply omitted on-device — annoying, not fatal — while a
# `step` with nothing to step is a control the user can press forever with no
# effect, which is worth failing a push for.

def _glance_ref(cid, where, what, seen_ids, findings):
    """A glance field that names an EXISTING layout control. Unknown id ⇒ the
    surface silently renders without it, so say so at authoring time."""
    if isinstance(cid, str) and cid and cid not in seen_ids:
        findings.append(_f("warn", "bad_glance", where,
                           f"{what} references control id '{cid}' that isn't in the layout"))


def _validate_glance_tile(t, where, seen_ids, findings):
    from .glance import TILE_KINDS
    if not isinstance(t, dict):
        findings.append(_f("error", "bad_glance_tile", where,
                           "a tile must be an object — see glance.md"))
        return
    kind = t.get("tile")
    if kind is not None and kind not in TILE_KINDS:
        findings.append(_f("warn", "bad_glance_tile", where,
                           f"unknown tile kind '{kind}' — it renders as a plain value; "
                           f"expected one of {list(TILE_KINDS)}"))
    _glance_ref(t.get("control"), where, "tile", seen_ids, findings)
    if "delta" in t and (isinstance(t["delta"], bool) or not isinstance(t["delta"], (int, float))):
        findings.append(_f("error", "bad_glance_control", where,
                           f"delta must be a number, got {t['delta']!r}"))


def _validate_glance_scene(sc, where, seen_ids, findings):
    if not isinstance(sc, dict):
        findings.append(_f("error", "bad_glance_tile", where,
                           "a scene must be an object with 'rows'"))
        return
    rows = sc.get("rows")
    if not isinstance(rows, list):
        findings.append(_f("error", "bad_glance_tile", where,
                           "a scene needs a 'rows' array of tile rows"))
        return
    widths, lengths = [], []
    for ri, row in enumerate(rows):
        if not isinstance(row, list):
            findings.append(_f("error", "bad_glance_tile", f"{where}.rows[{ri}]",
                               "each row must be an array of tiles"))
            widths.append(0)
            lengths.append(0)
            continue
        widths.append(sum(_span(t) for t in row))
        lengths.append(len(row))
        for ti, t in enumerate(row):
            _validate_glance_tile(t, f"{where}.rows[{ri}][{ti}]", seen_ids, findings)
    # `columns` defaults on-device to the longest row — its tile COUNT, not its
    # summed spans, or an over-wide tile would silently define the grid it
    # overflows and nothing would ever be reported.
    declared = sc.get("columns")
    columns = declared if isinstance(declared, int) and declared > 0 else (max(lengths) if lengths else 0)
    if not columns:
        return
    for ri, row in enumerate(rows):
        if not isinstance(row, list):
            continue
        for ti, t in enumerate(row):
            span = _span(t)
            if span > columns:
                findings.append(_f("warn", "bad_glance_span", f"{where}.rows[{ri}][{ti}]",
                                   f"span {span} is wider than the scene's {columns} "
                                   f"column(s) — it is clamped when rendered"))
        if widths[ri] > columns:
            findings.append(_f("warn", "bad_glance_span", f"{where}.rows[{ri}]",
                               f"row spans {widths[ri]} column(s) but the scene has "
                               f"{columns} — the overflow is dropped"))


def _span(t) -> int:
    span = t.get("span") if isinstance(t, dict) else None
    return span if isinstance(span, int) and not isinstance(span, bool) and span > 0 else 1


def _validate_glance_controls(controls, seen_ids, findings):
    from .glance import CONTROL_KINDS
    for i, c in enumerate(controls):
        where = f"glance.controls[{i}]"
        if not isinstance(c, dict):
            findings.append(_f("error", "bad_glance_control", where,
                               "a glance control must be an object"))
            continue
        kind = c.get("kind", "button")
        if kind not in CONTROL_KINDS:
            findings.append(_f("warn", "bad_glance_control", where,
                               f"unknown control kind '{kind}'; expected one of "
                               f"{list(CONTROL_KINDS)}"))
        _glance_ref(c.get("control"), where, "control", seen_ids, findings)
        _glance_ref(c.get("valueControl"), where, "valueControl", seen_ids, findings)
        if kind in ("cycle", "step", "set") and not c.get("control"):
            findings.append(_f("error", "bad_glance_control", where,
                               f"a '{kind}' drives a layout control — it needs "
                               f"'control'; without one a press does nothing"))
        if kind == "cycle":
            states = c.get("states")
            if not isinstance(states, list) or len(states) < 2:
                findings.append(_f("error", "bad_glance_control", where,
                                   "a 'cycle' needs at least two states to cycle through"))
        if "delta" in c and (isinstance(c["delta"], bool) or not isinstance(c["delta"], (int, float))):
            findings.append(_f("error", "bad_glance_control", where,
                               f"delta must be a number, got {c['delta']!r}"))


def _validate_glance(glance: dict, seen_ids: dict, findings: list) -> None:
    from .glance import (ISLAND_REGIONS, ISLAND_TILE_REGIONS, LIVE_TIERS,
                         WIDGET_FAMILIES)
    # hero/slots surface an EXISTING control's value, so those ids must exist.
    # (`glance.controls[]` are standalone surface controls with their own ids — a
    # Control Center button, not a reference — so only their `control` is checked.)
    refs: list[str] = []
    if isinstance(glance.get("hero"), str):
        refs.append(glance["hero"])
    for gid in (glance.get("slots") or []):
        if isinstance(gid, str):
            refs.append(gid)
    for gid in refs:
        if gid not in seen_ids:
            findings.append(_f("warn", "bad_glance", "glance",
                               f"glance hero/slot references control id '{gid}' that isn't "
                               f"in the layout"))

    controls = glance.get("controls")
    if isinstance(controls, list):
        _validate_glance_controls(controls, seen_ids, findings)

    widgets = glance.get("widgets")
    if isinstance(widgets, list):
        for i, w in enumerate(widgets):
            where = f"glance.widgets[{i}]"
            if not isinstance(w, dict):
                findings.append(_f("error", "bad_glance_tile", where,
                                   "a widget must be an object"))
                continue
            families = w.get("families")
            if isinstance(families, list):
                for fam in families:
                    if fam not in WIDGET_FAMILIES:
                        findings.append(_f("warn", "bad_glance_family", where,
                                           f"unknown widget family '{fam}'; expected "
                                           f"one of {list(WIDGET_FAMILIES)}"))
            if w.get("scene") is not None:
                _validate_glance_scene(w["scene"], f"{where}.scene", seen_ids, findings)
            for fam in WIDGET_FAMILIES:
                if w.get(fam) is not None:
                    _validate_glance_scene(w[fam], f"{where}.{fam}", seen_ids, findings)

    isl = glance.get("island")
    if isinstance(isl, dict):
        for region in ISLAND_TILE_REGIONS:
            value = isl.get(region)
            if value is None:
                continue
            if isinstance(value, dict) and "rows" in value:
                findings.append(_f("warn", "bad_glance_island", f"glance.island.{region}",
                                   f"'{region}' shows exactly one tile — a scene here is "
                                   f"reduced to its first tile"))
                _validate_glance_scene(value, f"glance.island.{region}", seen_ids, findings)
            else:
                _validate_glance_tile(value, f"glance.island.{region}", seen_ids, findings)
        expanded = isl.get("expanded")
        if isinstance(expanded, dict):
            for region in ISLAND_REGIONS:
                value = expanded.get(region)
                if value is None:
                    continue
                where = f"glance.island.expanded.{region}"
                if region == "bottom" or (isinstance(value, dict) and "rows" in value):
                    _validate_glance_scene(value, where, seen_ids, findings)
                else:
                    _validate_glance_tile(value, where, seen_ids, findings)

    if glance.get("lockScreen") is not None:
        _validate_glance_scene(glance["lockScreen"], "glance.lockScreen", seen_ids, findings)

    live = glance.get("live")
    if isinstance(live, dict) and live.get("tier") is not None:
        if live["tier"] not in LIVE_TIERS:
            findings.append(_f("warn", "bad_glance_live", "glance.live",
                               f"unknown tier '{live['tier']}'; expected one of "
                               f"{list(LIVE_TIERS)} — the app falls back to 'fresh'"))


def _collect_source_refs(children, sources, referenced):
    """Record every source a binding references — explicitly (`source:`) or implicitly
    (an mqtt/http binding with no `source` but exactly one declared source of that kind)."""
    for ch in children:
        if not isinstance(ch, dict):
            continue
        if ch.get("type") == "group":
            _collect_source_refs(ch.get("children") or [], sources, referenced)
            continue
        bindings = list(ch.get("sync") or [])
        for akey in ("action", "longPressAction", "datumAction", "snapshotAction", "nodeAction"):
            a = ch.get(akey)
            if isinstance(a, dict):
                bindings.append(a)
        for b in bindings:
            if not isinstance(b, dict):
                continue
            method = b.get("method")
            if method not in ("mqtt", "http"):
                continue
            ref = b.get("source")
            if ref:
                referenced.add(ref)
            else:
                kind = [n for n, k in sources.items() if k == method]
                if len(kind) == 1:
                    referenced.add(kind[0])


def _grid_findings(children, cols, rows, where, findings, mode=None):
    # A `flow`-mode grid stacks its children vertically and ignores 2-D position/span
    # (controlHeight-driven) — the app never bounds-checks or overlap-checks it, so we
    # must not either (see the grid mode:flow gotcha). Only 2-D grids get placement lint.
    if mode == "flow":
        return
    for issue in gridmod.validate_placement(children, cols, rows):
        ids = issue.get("ids") or [issue.get("id")]
        findings.append(_f("error", issue["kind"], where,
                           f"{', '.join(str(i) for i in ids)}: {issue['detail']}"))


def _validate_child(ch, catalog, where, findings, seen_ids, sources=None):
    if not isinstance(ch, dict):
        findings.append(_f("error", "structure", where, "child must be an object"))
        return
    sources = sources or {}
    ctype = ch.get("type")
    cid = ch.get("id")
    spot = f"{where}/{cid or ctype or '?'}"

    if not ctype:
        findings.append(_f("error", "missing_field", spot, "control missing 'type'"))
    if not cid:
        findings.append(_f("error", "missing_field", spot, "control missing 'id'"))
    elif cid in seen_ids:
        findings.append(_f("error", "duplicate_id", spot,
                           f"id '{cid}' already used at {seen_ids[cid]}"))
    elif cid:
        seen_ids[cid] = spot

    if ctype == "group":
        for k in ch:
            if k not in GROUP_FIELDS:
                findings.append(_f("warn", "unknown_field", spot, f"group: unknown field '{k}'"))
        sub_children = ch.get("children") or []
        g = ch.get("grid") or {}
        _grid_findings(sub_children, int(g.get("columns", 4)), int(g.get("rows", 8)),
                       spot, findings, g.get("mode"))
        for sub in sub_children:
            _validate_child(sub, catalog, spot, findings, seen_ids, sources)
        return

    if not ctype:
        return
    entry = catalog.get(ctype)
    if entry is None:
        findings.append(_f("error", "unknown_type", spot, f"unknown control type '{ctype}'"))
        return

    fields = {f["name"]: f for f in entry.get("fields", [])}
    theme_names = {f["name"] for f in entry.get("themeFields", [])}
    allowed = SHARED_FIELDS | set(fields) | theme_names

    for k, v in ch.items():
        if k not in allowed:
            findings.append(_f("warn", "unknown_field", spot, f"{ctype}: unknown field '{k}'"))
            continue
        fd = fields.get(k)
        if fd and fd.get("type") == "enum" and fd.get("values") and isinstance(v, str):
            # The app never rejects a layout for an unrecognized enum — it renders the
            # control with the field's default (e.g. CARGauge treats anything != "full"
            # as half). So this is a WARNING, not an error. Parameterized values like
            # `formatValue: "decimal:2"` (decimal with N places) match on their base token.
            base = v.split(":", 1)[0]
            if v not in fd["values"] and base not in fd["values"]:
                findings.append(_f("warn", "bad_enum", spot,
                                   f"{ctype}.{k} = '{v}' is not one of {fd['values']} — "
                                   f"the app will fall back to the default"))
    _validate_bindings(ch, ctype, spot, findings, sources)


# Transports whose sync/action carry a transport address (topic/path) instead of a
# MeshSocket `event` — these are APP-side runtimes (see sources.md / sensors.md).
_ADDRESSED_METHODS = {"mqtt", "http", "sensor"}


def _validate_bindings(ch, ctype, spot, findings, sources=None):
    """Shape-check the data bindings across every transport (`method`): MeshSocket
    syncs need a `valuePath` and actions need a relay `event`; MQTT/HTTP/sensor carry
    a transport address instead (topic / path|url / sensor name) and no `event`."""
    sources = sources or {}
    sync = ch.get("sync")
    if sync is not None:
        if not isinstance(sync, list):
            findings.append(_f("warn", "bad_sync", spot, f"{ctype}.sync should be a list"))
        else:
            for i, s in enumerate(sync):
                _validate_sync_entry(s, ctype, spot, i, findings, sources)
    for akey in ("action", "longPressAction"):
        a = ch.get(akey)
        if a is None:
            continue
        if not isinstance(a, dict):
            findings.append(_f("error", "bad_action", spot, f"{ctype}.{akey} must be an object"))
            continue
        _validate_action_entry(a, ctype, akey, spot, findings, sources)
    # Secondary action carriers (charts' datumAction, camera's snapshotAction,
    # graph's nodeAction) ride the same rules.
    for akey in ("datumAction", "snapshotAction", "nodeAction"):
        a = ch.get(akey)
        if isinstance(a, dict):
            _validate_action_entry(a, ctype, akey, spot, findings, sources)


def _source_ref_findings(binding, method, spot, ctype, what, findings, sources):
    """An mqtt/http binding's optional `source:` must name a declared source of that
    kind; with several sources of the kind, `source` is required (sources.md rule)."""
    declared = [n for n, k in sources.items() if k == method]
    ref = binding.get("source")
    if ref is not None:
        if ref not in sources:
            findings.append(_f("error", "unknown_source", spot,
                               f"{ctype}.{what}: source '{ref}' is not declared in top-level 'sources'"))
        elif sources[ref] != method:
            findings.append(_f("error", "bad_source", spot,
                               f"{ctype}.{what}: source '{ref}' is {sources[ref]}, not {method}"))
    elif method == "mqtt" and len(declared) != 1:
        # HTTP can use an absolute `url` with no source at all; MQTT always needs a broker.
        detail = ("no mqtt source declared" if not declared
                  else f"{len(declared)} mqtt sources declared — name one with 'source'")
        findings.append(_f("warn", "bad_source", spot, f"{ctype}.{what}: {detail}"))


def _validate_sync_entry(s, ctype, spot, i, findings, sources):
    if not isinstance(s, dict):
        findings.append(_f("warn", "bad_sync", spot, f"{ctype}.sync[{i}] must be an object"))
        return
    method = s.get("method", "meshsocket")
    if method == "sensor":
        if not s.get("sensor"):
            findings.append(_f("warn", "bad_sync", spot,
                               f"{ctype}.sync[{i}] method 'sensor' needs a 'sensor' name"))
        return
    if method == "mqtt":
        if not s.get("topic"):
            findings.append(_f("error", "bad_sync", spot,
                               f"{ctype}.sync[{i}] mqtt sync needs a 'topic'"))
        _source_ref_findings(s, "mqtt", spot, ctype, f"sync[{i}]", findings, sources)
        return          # valuePath optional (bare payloads bind directly)
    if method == "http":
        if not (s.get("path") or s.get("url")):
            findings.append(_f("error", "bad_sync", spot,
                               f"{ctype}.sync[{i}] http sync needs a 'path' or 'url'"))
        _source_ref_findings(s, "http", spot, ctype, f"sync[{i}]", findings, sources)
        return          # valuePath optional
    # MeshSocket (default): a listen needs a valuePath to extract from the frame.
    if not s.get("valuePath"):
        findings.append(_f("warn", "bad_sync", spot,
                           f"{ctype}.sync[{i}] is missing a 'valuePath'"))


def _validate_action_entry(a, ctype, akey, spot, findings, sources):
    method = a.get("method", "meshsocket")
    if method == "mqtt":
        if not a.get("topic"):
            findings.append(_f("error", "bad_action", spot,
                               f"{ctype}.{akey} mqtt action needs a 'topic'"))
        _source_ref_findings(a, "mqtt", spot, ctype, akey, findings, sources)
        return
    if method == "http":
        if not (a.get("path") or a.get("url")):
            findings.append(_f("error", "bad_action", spot,
                               f"{ctype}.{akey} http action needs a 'path' or 'url'"))
        _source_ref_findings(a, "http", spot, ctype, akey, findings, sources)
        return
    # MeshSocket (default): the `event` is the wire frame type — must be a relay verb.
    if not a.get("event"):
        findings.append(_f("error", "bad_action", spot,
                           f"{ctype}.{akey} is missing an 'event'"))
        return
    _validate_action_wire(a, ctype, akey, spot, findings)


def _validate_action_wire(a, ctype, akey, spot, findings):
    """The action's `event` goes on the wire as the frame type verbatim, and the
    relay forwards only its own verbs — any other name is silently dropped (the
    control does nothing). Catch that dead-button class before it ships."""
    ev = a.get("event")
    payload = a.get("payload")
    if ev not in WIRE_VERBS:
        if ev in RELAY_SERVICE_VERBS:
            return  # answered by the relay itself (ping etc.) — legal
        findings.append(_f("error", "dead_action", spot,
                           f"{ctype}.{akey} event '{ev}' is not a relay verb — the relay "
                           f"silently drops it and the control does nothing. Use "
                           f"send='{ev}' / bind.command('{ev}') to ride broadcast_request "
                           f"with msg_type='{ev}'"))
        return
    if ev == "broadcast_request":
        if a.get("mode") == "request":
            findings.append(_f("warn", "bad_action", spot,
                               f"{ctype}.{akey}: mode 'request' on a broadcast gets no "
                               f"reply (the tap silently waits out the timeout) — use "
                               f"mode 'broadcast'"))
        if not (isinstance(payload, dict) and payload.get("msg_type")):
            findings.append(_f("warn", "bad_action", spot,
                               f"{ctype}.{akey}: broadcast_request without a payload "
                               f"msg_type — servers demux broadcasts on msg_type, so "
                               f"this frame is very hard to handle"))
    elif ev == "route_msg" and not (isinstance(payload, dict) and payload.get("target_id")):
        findings.append(_f("error", "bad_action", spot,
                           f"{ctype}.{akey}: route_msg needs payload.target_id (a live "
                           f"relay-assigned id; target_name is NOT resolved) — for "
                           f"name-targeted sends use route_msg_noreply"))
    elif ev == "route_msg_noreply" and not (isinstance(payload, dict) and payload.get("target_name")):
        findings.append(_f("error", "bad_action", spot,
                           f"{ctype}.{akey}: route_msg_noreply needs payload.target_name"))


def _validate_sources_defs(layout, findings) -> dict:
    """Validate top-level `sources` (mqtt/http source definitions) and return a
    {name: kind} map for binding checks. See sources.md."""
    raw = layout.get("sources")
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        findings.append(_f("error", "bad_sources", "root", "'sources' must be an object of {name: source}"))
        return {}
    out: dict[str, str] = {}
    for name, sdef in raw.items():
        where = f"sources.{name}"
        if not isinstance(sdef, dict):
            findings.append(_f("error", "bad_sources", where, "source must be an object"))
            continue
        kind = sdef.get("type")
        if kind not in ("mqtt", "http"):
            findings.append(_f("error", "bad_sources", where,
                               f"source 'type' must be 'mqtt' or 'http', got {kind!r}"))
            continue
        out[name] = kind
        if kind == "mqtt" and not sdef.get("url"):
            findings.append(_f("error", "bad_sources", where, "mqtt source needs a broker 'url'"))
        # http `baseURL` is optional — syncs may use absolute `url`s instead.
    return out


_ALERT_OPERATORS = {"eq", "neq", "gt", "lt", "gte", "lte"}
_SENSOR_PIPELINES = {"heading", "motion", "barometer", "device", "audio", "location"}


def _validate_top_level(layout, findings):
    """Light shape checks for the optional top-level blocks the app renders. Never
    rejects unknown top-level keys (the app tolerates them); only flags a block that
    is present but the wrong container type, plus schema checks for the authored blocks
    with a clear model (alerts, publishers)."""
    for key, typ, label in (("alerts", list, "an array"),
                            ("publishers", list, "an array"),
                            ("glance", dict, "an object"),
                            ("state", dict, "an object"),
                            ("appearance", dict, "an object"),
                            ("theme", dict, "an object"),
                            ("pollGroups", dict, "an object"),
                            ("dynamicTabs", list, "an array")):
        v = layout.get(key)
        if v is not None and not isinstance(v, typ):
            findings.append(_f("warn", "bad_top_level", "root", f"'{key}' should be {label}"))
    # batchPublishers — a bare bool, like keepAwake.
    batch = layout.get("batchPublishers")
    if batch is not None and not isinstance(batch, bool):
        findings.append(_f("warn", "bad_top_level", "root", "'batchPublishers' should be true or false"))
    if batch is True and not layout.get("publishers"):
        findings.append(_f("info", "bad_top_level", "root", "'batchPublishers' has no effect without a 'publishers' block"))

    # keepAwake — a bare bool (Swift decodes `Bool?`; "true"/1 would fail on the phone).
    keep_awake = layout.get("keepAwake")
    if keep_awake is not None and not isinstance(keep_awake, bool):
        findings.append(_f("warn", "bad_top_level", "root", "'keepAwake' should be true or false"))

    # alerts — relay-watcher push rules (AlertRule). Each needs the fields the watcher
    # matches on (event + valuePath + operator + value) and the push copy (title/body).
    alerts = layout.get("alerts")
    if isinstance(alerts, list):
        for i, rule in enumerate(alerts):
            where = f"alerts[{i}]"
            if not isinstance(rule, dict):
                findings.append(_f("error", "bad_alert", where, "alert rule must be an object"))
                continue
            for req in ("event", "valuePath", "operator", "value", "title", "body"):
                if req not in rule:
                    findings.append(_f("error", "bad_alert", where, f"alert rule missing '{req}'"))
            op = rule.get("operator")
            if op is not None and op not in _ALERT_OPERATORS:
                findings.append(_f("error", "bad_alert", where,
                                   f"operator '{op}' is not one of {sorted(_ALERT_OPERATORS)}"))

    # publishers — device sensor streams (SensorPublisherDefinition).
    publishers = layout.get("publishers")
    if isinstance(publishers, list):
        for i, pub in enumerate(publishers):
            where = f"publishers[{i}]"
            if not isinstance(pub, dict) or not pub.get("sensor"):
                findings.append(_f("error", "bad_publisher", where, "publisher needs a 'sensor'"))
                continue
            base = str(pub["sensor"]).split(".", 1)[0]
            if base not in _SENSOR_PIPELINES:
                findings.append(_f("warn", "bad_publisher", where,
                                   f"sensor '{pub['sensor']}' base '{base}' is not a known "
                                   f"pipeline {sorted(_SENSOR_PIPELINES)}"))


def format_findings(findings: list[dict]) -> str:
    """Render findings as a readable report."""
    if not findings:
        return "✓ No issues found."
    errors = [f for f in findings if f["severity"] == "error"]
    warns = [f for f in findings if f["severity"] == "warn"]
    lines = [f"{len(errors)} error(s), {len(warns)} warning(s):"]
    for f in errors:
        lines.append(f"  ✗ [{f['kind']}] {f['where']} — {f['detail']}")
    for f in warns:
        lines.append(f"  ⚠ [{f['kind']}] {f['where']} — {f['detail']}")
    return "\n".join(lines)
