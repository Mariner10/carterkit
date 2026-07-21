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

    # glance `hero`/`slots` surface an EXISTING control's value, so those ids must exist.
    # (`glance.controls[]` are standalone glance-surface controls with their own ids — a
    # Control Center button / Dynamic Island element — not references, so they're skipped.)
    glance = layout.get("glance")
    if isinstance(glance, dict):
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
    return findings


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
