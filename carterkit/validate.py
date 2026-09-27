"""Schema-driven layout validation — catch broken layouts before pushing.

Drives off the control catalog (catalog.build_catalog(..., include_theme=True)) so
the field/enum schema stays in sync with the docs. Reports structural problems
(missing required keys), id collisions, unknown control types, unknown fields,
bad enum values, and grid overlaps/out-of-bounds (via grid.validate_placement).

Findings are dicts: {"severity": "error"|"warn", "kind", "where", "detail"}.

`validate_layout` NEVER raises on hostile input: a non-integer span/grid/position, a
non-finite number, absurd nesting or control counts, dangerous URL schemes, embedded
credentials and oversized strings all come back as findings (`bad_span`, `bad_grid`,
`bad_position`, `non_finite`, `too_deep`, `too_many_controls`, `bad_url`,
`embedded_secret`, `long_string`), and cell enumeration is capped so a 1500x1500 span
is reported, not built.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit

from . import grid as gridmod
from . import sections as sectionsmod
from .bind import WIRE_VERBS, RELAY_SERVICE_VERBS

# Base/shared properties every control may carry (from the layout schema /
# ChildDefinition), independent of its type. Type-specific fields come from the catalog.
SHARED_FIELDS = {
    "type", "id", "name", "position", "span", "label", "defaultValue", "icon", "tint",
    "hideLabel", "hideBackground", "action", "sync", "visible", "haptic",
    "animation", "longPressGroup", "longPressAction", "theme", "config",
    # Shared display/range/format properties the app decodes on ControlDefinition
    # (not per-control config) — any control may carry them; unused ones are ignored.
    # Mirrors CAR-TER/CAR-TER/Models/ControlDefinition.swift.
    "min", "max", "step", "formatValue", "controlHeight", "hideValue", "pulse",
    # Tool data (document-contract.md#Extensions): preserved, never interpreted.
    "extensions",
}
GROUP_FIELDS = {
    "type", "id", "name", "position", "span", "label", "grid", "children", "dynamic",
    "visible", "theme", "hideBackground", "pulse", "icon", "tint", "controlHeight",
    "extensions",
}


def _f(severity: str, kind: str, where: str, detail: str) -> dict:
    return {"severity": severity, "kind": kind, "where": where, "detail": detail}


#: The document contract's Limits table (controldocs/document-contract.md#Limits) is
#: the ONE source for the structural caps: the app's unit tests pin its sanitizer to the
#: same table, so a layout this lint accepts is a layout the device renders. The
#: fallback values below only matter if the vendored doc is missing or unparseable.
_LIMIT_DEFAULTS = {
    "maxTabs": 24, "maxControls": 2000, "maxNestingDepth": 8, "maxStringBytes": 4096,
    "maxDataImageBytes": 524288, "maxExtensionsBytes": 65536, "maxPosition": 256,
    "maxSpan": 64, "maxGridColumns": 64, "maxGridRows": 512, "minTimerSeconds": 0.25,
    "minSendRateSeconds": 0.02, "minPublisherIntervalSeconds": 0.05,
    "maxBufferPoints": 5000, "maxWireBytes": 2097152, "maxFileBytes": 8388608,
}


def _load_limits() -> dict:
    """Parse the `| `name` | value | … |` rows under `## Limits` in the vendored
    document-contract.md; unknown or missing rows keep their defaults."""
    limits = dict(_LIMIT_DEFAULTS)
    try:
        text = (Path(__file__).parent / "controldocs" / "document-contract.md").read_text("utf-8")
    except OSError:
        return limits
    in_limits = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_limits = line.strip() == "## Limits"
            continue
        if not in_limits or not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        name = cells[0].strip("`")
        try:
            value = float(cells[1])
        except ValueError:
            continue
        limits[name] = int(value) if value.is_integer() else value
    return limits


#: Every limit from the contract, by its table name.
LIMITS = _load_limits()
#: How many groups/containers may enclose a control (a tab's own children are nesting
#: 0). ONE number with the app: LayoutLimits.maxNestingDepth, which bounds both its
#: sanitizer and its renderer (carter-m7s.7) — past it the device refuses a pushed
#: layout and renders "Nested too deeply" for a stored one.
MAX_DEPTH = LIMITS["maxNestingDepth"]
MAX_CONTROLS = LIMITS["maxControls"]
MAX_STRING = LIMITS["maxStringBytes"]
MAX_DATA_IMAGE = LIMITS["maxDataImageBytes"]
MAX_EXTENSIONS = LIMITS["maxExtensionsBytes"]
# The device's LayoutSanitizer caps (CAR-TER/CAR-TER/Services/LayoutSanitizer.swift). A
# strict source (wire push, import, join) refuses a layout past any of them, so the kit
# reports each as an error. Pinned by the shared conformance fixtures (carter-c1n.11);
# the numbers come from the contract's Limits table like the rest.
MAX_TABS = LIMITS["maxTabs"]
MAX_GRID_COLUMNS = LIMITS["maxGridColumns"]
MAX_GRID_ROWS = LIMITS["maxGridRows"]
POSITION_RANGE = (0, LIMITS["maxPosition"])
SPAN_RANGE = (1, LIMITS["maxSpan"])
MIN_TIMER = LIMITS["minTimerSeconds"]
# Mirrors the app's LayoutSanitizer (carter-ml2 / carter-n1u): joystick `sendRate` is an
# event throttle (documented 0.05/0.1), sensor `publishers[].interval` has its own floor,
# and carousel `autoAdvance` / web `webRefreshInterval` 0 means "off".
MIN_SEND_RATE = LIMITS["minSendRateSeconds"]
MIN_PUBLISHER_INTERVAL = LIMITS["minPublisherIntervalSeconds"]
_TIMER_KEYS = {"interval", "webRefreshInterval", "autoAdvance", "sendRate"}
_OFF_TIMER_KEYS = {"autoAdvance", "webRefreshInterval"}


def _timer_floor(key: str, path: str) -> float:
    if key == "sendRate":
        return MIN_SEND_RATE
    if key == "interval" and ".publishers[" in path:
        return MIN_PUBLISHER_INTERVAL
    return MIN_TIMER
#: URL schemes a layout may point the phone at. `http` is allowed but warned.
SAFE_URL_SCHEMES = {"https", "mqtt", "mqtts", "ws", "wss"}
_WARN_URL_SCHEMES = {"http"}
_URL_KEYS = {"url", "baseURL", "imageURL", "avatarURL", "src", "href", "validator"}


def validate_layout(layout: dict, catalog: dict) -> list[dict]:
    """Validate a full layout against the catalog. `catalog` should be built with
    include_theme=True so per-control theme fields are recognized. Never raises:
    an unexpected failure is itself reported as an `internal_error` finding."""
    try:
        return _validate_layout(layout, catalog)
    except RecursionError:
        return [_f("error", "too_deep", "root", "layout nests too deeply to validate")]
    except Exception as e:                        # pragma: no cover - last resort
        return [_f("error", "internal_error", "root",
                   f"validator failed on this input ({type(e).__name__}: {e}); "
                   f"treat the layout as invalid")]


def _grid_dims(g, where, findings) -> tuple[int, int]:
    """(columns, rows) for a grid block, defaulting 4x8; a non-integer or absurd
    value is a `bad_grid` finding and falls back to the default."""
    if g is None:
        g = {}
    if not isinstance(g, dict):
        findings.append(_f("error", "bad_grid", where, f"'grid' must be an object, got {g!r}"))
        return 4, 8
    out = []
    for key, default, hi in (("columns", 4, MAX_GRID_COLUMNS), ("rows", 8, MAX_GRID_ROWS)):
        raw = g.get(key, default)
        v = gridmod.as_int(raw)
        if v is None or v < 1 or v > hi:
            findings.append(_f("error", "bad_grid", where,
                               f"grid.{key} must be an integer 1..{hi}, got {raw!r}"))
            v = default
        out.append(v)
    return out[0], out[1]


def _validate_layout(layout: dict, catalog: dict) -> list[dict]:
    findings: list[dict] = []
    if not isinstance(layout, dict):
        return [_f("error", "structure", "root", "layout must be a JSON object")]
    for key in ("name", "version", "tabs"):
        if key not in layout:
            findings.append(_f("error", "missing_field", "root", f"missing top-level '{key}'"))

    # Whole-tree hygiene first: non-finite numbers, oversized strings, URL schemes,
    # embedded credentials. Iterative, so hostile nesting cannot blow the stack.
    _scan_tree(layout, findings)

    # Declared data sources (name -> kind), so control bindings can be checked against
    # them (an mqtt/http `source:` must name a declared source). See sources.md.
    sources = _validate_sources_defs(layout, findings)
    _validate_top_level(layout, findings)
    _validate_contract(layout, findings)

    # A sectioned document (schemaVersion 2) is checked as the app sees it: sections
    # folded onto their children. Entries the app would drop are errors here.
    for where, why in sectionsmod.section_issues(layout):
        findings.append(_f("error", "bad_section", where, why))
    if sectionsmod.is_sectioned(layout):     # to_inline deep-copies; skip it for inline docs
        layout = sectionsmod.to_inline(layout)
    _validate_device_shape(layout, findings)

    tabs = layout.get("tabs")
    if not isinstance(tabs, list):
        findings.append(_f("error", "structure", "root", "'tabs' must be an array"))
        return findings

    seen_ids: dict[str, str] = {}
    seen_tab_ids: dict[str, str] = {}
    counter = {"n": 0}
    for ti, tab in enumerate(tabs):
        where = f"tab[{ti}]"
        if not isinstance(tab, dict):
            findings.append(_f("error", "structure", where, "tab must be an object"))
            continue
        # Optional stable tab id (the app keys selection/deep links on it, else the
        # title). Same rule as the device: non-empty and unique among tabs.
        if "id" in tab:
            tid = tab.get("id")
            if not isinstance(tid, str) or not tid:
                findings.append(_f("error", "missing_field", where,
                                   "tab 'id' must be a non-empty string (or omit it)"))
            elif tid in seen_tab_ids:
                findings.append(_f("error", "duplicate_id", where,
                                   f"tab id '{tid}' already used at {seen_tab_ids[tid]}"))
            else:
                seen_tab_ids[tid] = where
        g = tab.get("grid")
        cols, rows = _grid_dims(g, where, findings)
        children = tab.get("children") or []
        if not isinstance(children, list):
            findings.append(_f("error", "structure", where, "'children' must be an array"))
            continue
        _grid_findings(children, cols, rows, where, findings,
                       g.get("mode") if isinstance(g, dict) else None)
        for ch in children:
            _validate_child(ch, catalog, where, findings, seen_ids, sources, 1, counter)
    if counter["n"] > MAX_CONTROLS:
        findings.append(_f("warn", "too_many_controls", "root",
                           f"{counter['n']} controls — the app renders nothing usable past "
                           f"{MAX_CONTROLS}; this layout is broken or hostile"))

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


def _scan_tree(layout: dict, findings: list) -> None:
    """One iterative pass over the whole document for value-level hazards."""
    secret_paths = set()
    conn = layout.get("connection")
    if isinstance(conn, dict):
        for k in ("token", "e2eeKey", "k", "refresh"):
            if conn.get(k):
                secret_paths.add(f"connection.{k}")
    srcs = layout.get("sources")
    if isinstance(srcs, dict):
        for name, src in srcs.items():
            if not isinstance(src, dict):
                continue
            for k in ("password", "token", "apiKey"):
                if src.get(k):
                    secret_paths.add(f"sources.{name}.{k}")
            headers = src.get("headers")
            if isinstance(headers, dict):
                for hk in headers:
                    if any(w in str(hk).lower() for w in ("authorization", "token", "key", "secret", "cookie")):
                        secret_paths.add(f"sources.{name}.headers.{hk}")
    for path in sorted(secret_paths):
        findings.append(_f("warn", "embedded_secret", path,
                           "a credential is embedded in the layout — anyone who receives "
                           "this JSON (share, export, MCP readback) receives the secret"))

    stack = [(layout, "root", 0, None)]
    seen_urls = 0
    blobs = 0
    while stack:
        node, path, depth, key = stack.pop()
        if depth > 64:
            findings.append(_f("error", "too_deep", path, "document nests deeper than 64 levels"))
            continue
        if isinstance(node, dict):
            _check_object_bounds(node, path, findings)
            for k, v in node.items():
                sub = f"{path}.{k}"
                if k == "extensions":
                    continue            # opaque tool data; bounded by _validate_extensions
                if path == "root.connection" and k in ("url", "baseURL") and isinstance(v, str):
                    _check_socket_url(v, sub, findings)
                elif isinstance(v, str) and k in _URL_KEYS and depth > 0 and path != "root.connection":
                    seen_urls += 1
                    if seen_urls <= 500:
                        _check_url(v, sub, findings)
                stack.append((v, sub, depth + 1, k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                stack.append((v, f"{path}[{i}]", depth + 1, key))
        elif isinstance(node, float):
            if math.isnan(node) or math.isinf(node):
                findings.append(_f("error", "non_finite", path,
                                   f"{node!r} is not valid JSON — the app's decoder rejects the whole layout"))
        elif isinstance(node, str):
            blob = _blob_finding(node, key, path) if blobs < 50 else None
            if blob:
                blobs += 1
                findings.append(blob)
            if key in ("url", "baseURL") and node[:11].lower() == "data:image/":
                continue            # the app's own cap for these is MAX_DATA_IMAGE
            size = len(node.encode("utf-8"))
            if size > MAX_STRING:
                findings.append(_f("error", "long_string", path,
                                   f"string is {size} UTF-8 bytes (> {MAX_STRING}); a push is refused "
                                   f"and a disk load truncates it"))


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _check_object_bounds(node: dict, path: str, findings: list) -> None:
    """Per-object device bounds the renderer would trap or spin on (LayoutSanitizer)."""
    if ".theme" not in path and not path.endswith("theme"):
        for k in _TIMER_KEYS & node.keys():
            v = node[k]
            if not (_is_num(v) and v == v):
                continue
            if k in _OFF_TIMER_KEYS and v == 0:
                continue  # documented 0 = off (carousel autoAdvance, web webRefreshInterval)
            floor = _timer_floor(k, path)
            if v < floor:
                findings.append(_f("error", "bad_timer", f"{path}.{k}",
                                   f"timer {v}s is below the {floor}s floor; a push is "
                                   f"refused and a disk load raises it"))
    lo, hi = node.get("minLines"), node.get("maxLines")
    if _is_num(lo) and _is_num(hi) and lo > hi:
        findings.append(_f("error", "bad_range", path,
                           f"minLines {lo} > maxLines {hi} (crashes the renderer); a push "
                           f"is refused and a disk load swaps them"))


def _check_socket_url(value: str, path: str, findings: list) -> None:
    """connection.url: the phone only dials ws:// or wss:// there."""
    if not value or "{{" in value:
        return
    scheme = urlsplit(value).scheme.lower()
    if scheme and scheme not in ("ws", "wss"):
        findings.append(_f("error", "bad_url", path,
                           f"connection URL scheme {scheme!r} is not allowed; use ws or wss"))


def _check_url(value: str, path: str, findings: list) -> None:
    if not value or "{{" in value:              # templated at runtime; scheme unknown here
        return
    if value[:11].lower() == "data:image/":     # the one allowed inline blob (see _blob_finding)
        return
    if value.startswith("/") or "://" not in value and ":" not in value.split("/", 1)[0]:
        return                                  # a relative path against a source baseURL
    scheme = urlsplit(value).scheme.lower()
    if scheme in SAFE_URL_SCHEMES:
        return
    if scheme in _WARN_URL_SCHEMES:
        findings.append(_f("warn", "bad_url", path,
                           f"plain http URL — data and any credentials travel in the clear"))
        return
    findings.append(_f("error", "bad_url", path,
                       f"URL scheme {scheme or '(none)'!r} is not allowed here; use one of "
                       f"{sorted(SAFE_URL_SCHEMES | _WARN_URL_SCHEMES)}"))


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


def _validate_child(ch, catalog, where, findings, seen_ids, sources=None, depth=1, counter=None):
    if not isinstance(ch, dict):
        findings.append(_f("error", "structure", where, "child must be an object"))
        return
    if counter is not None:
        counter["n"] += 1
        if counter["n"] > MAX_CONTROLS:
            return                      # counted and reported once at the root
    # `depth` is 1 for a tab's own children, so the child's nesting is depth - 1.
    if depth - 1 > MAX_DEPTH:
        findings.append(_f("error", "too_deep", where,
                           f"groups nest deeper than {MAX_DEPTH} levels — the app refuses it on "
                           f"push and renders a stored copy as a 'Nested too deeply' placeholder"))
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
                findings.append(_f("warn", "unknown_field", spot,
                                   f"group: unknown field '{k}'{_EXT_HINT}"))
        _validate_extensions(ch.get("extensions"), f"{spot}.extensions", findings)
        sub_children = ch.get("children") or []
        if not isinstance(sub_children, list):
            findings.append(_f("error", "structure", spot, "group 'children' must be an array"))
            return
        g = ch.get("grid")
        cols, rows = _grid_dims(g, spot, findings)
        _grid_findings(sub_children, cols, rows, spot, findings,
                       g.get("mode") if isinstance(g, dict) else None)
        for sub in sub_children:
            _validate_child(sub, catalog, spot, findings, seen_ids, sources, depth + 1, counter)
        return

    if not ctype:
        return
    entry = catalog.get(ctype)
    if entry is None:
        findings.append(_f("error", "unknown_type", spot, f"unknown control type '{ctype}'"))
        return

    _validate_extensions(ch.get("extensions"), f"{spot}.extensions", findings)
    fields = {f["name"]: f for f in entry.get("fields", [])}
    theme_names = {f["name"] for f in entry.get("themeFields", [])}
    allowed = SHARED_FIELDS | set(fields) | theme_names

    for k, v in ch.items():
        if k not in allowed:
            findings.append(_f("warn", "unknown_field", spot,
                               f"{ctype}: unknown field '{k}'{_EXT_HINT}"))
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


# ── the document contract (controldocs/document-contract.md) ─────────────────

_EXT_HINT = (" — if this is your tool's own data, move it under "
             "'extensions': {\"<reverse.dns.name>\": {...}} (see document-contract)")

#: Top-level keys the app models or the contract defines. Anything else is a core-key
#: guess: tolerated by the app, but a later grammar may give that name a meaning.
TOP_LEVEL_KEYS = {
    "name", "headerTitle", "version", "accentColor", "appearance", "connection", "tabs",
    "pollGroups", "dynamicTabs", "theme", "alerts", "state", "id", "glance", "publishers",
    "batchPublishers", "sources", "sensorSetup", "keepAwake",
    # document contract
    "schemaVersion", "format", "extensions", "provenance", "requires", "fallback",
    "placements", "styles", "connectivity",
    # a wire frame's discriminator, when a pushed payload is linted as-is
    "msg_type",
}
#: Reserved for a later grammar — never author them (document-contract.md).
RESERVED_TOP_LEVEL = {"revision", "attestations"}
#: The newest grammar this kit understands (1 = inline, 2 = sectioned).
KNOWN_SCHEMA_VERSION = 2
_REVERSE_DNS = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)+$", re.IGNORECASE)
_FEATURE = re.compile(r"^[a-z][a-z0-9_-]*(\.[a-z0-9_-]+)*(@[1-9][0-9]*)?$")
_PROVENANCE_RELATIONS = {"copy", "package", "remix", "import"}
_DATA_URL = re.compile(r"^data:[a-z]+/[a-z0-9.+-]+(;[^,]{0,200})?,", re.IGNORECASE)
_BASE64_RUN = re.compile(r"^[A-Za-z0-9+/_-]+={0,2}$")
#: A string this long made only of base64 characters is an inline blob, not text.
_BLOB_MIN = 1024


def _validate_extensions(ext, where: str, findings: list) -> None:
    """`extensions`: an object of reverse-DNS keys, at most MAX_EXTENSIONS bytes of
    compact JSON — the app refuses (strict) or drops (disk) anything else."""
    if ext is None:
        return
    if not isinstance(ext, dict):
        findings.append(_f("error", "bad_extensions", where,
                           "'extensions' must be an object keyed by reverse-DNS tool names"))
        return
    try:
        size = len(json.dumps(ext, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    except (TypeError, ValueError):
        size = None
    if size is None:
        findings.append(_f("error", "bad_extensions", where, "'extensions' is not valid JSON"))
    elif size > MAX_EXTENSIONS:
        findings.append(_f("error", "bad_extensions", where,
                           f"extensions block is {size} bytes (> {MAX_EXTENSIONS}); the app "
                           f"refuses it on push and drops it from a stored copy"))
    for k in ext:
        if k == "editor":
            continue                # the app's own editor state (outside the digest)
        if not isinstance(k, str) or not _REVERSE_DNS.match(k):
            findings.append(_f("warn", "bad_extensions", f"{where}.{k}",
                               f"extension key '{k}' should be a reverse-DNS tool name "
                               f"(e.g. 'com.example.tool')"))


def _blob_finding(value: str, key, path: str):
    """An inline binary payload other than a bounded data:image URL in a url field."""
    if _DATA_URL.match(value[:256]):
        if value[:11].lower() == "data:image/" and key in ("url", "baseURL"):
            if len(value.encode("utf-8")) > MAX_DATA_IMAGE:
                # The device refuses a push past its data:image cap (carter-c1n.11).
                return _f("error", "inline_blob", path,
                          f"data:image URL is {len(value)} bytes (> {MAX_DATA_IMAGE}); the app "
                          f"refuses or truncates it — host the image and link it by https URL")
            return None
        return _f("warn", "inline_blob", path,
                  "inline data: URL — only a data:image URL in a 'url'/'baseURL' field is "
                  "allowed; host the file and link it by https URL (see document-contract)")
    if len(value) >= _BLOB_MIN and _BASE64_RUN.match(value):
        return _f("warn", "inline_blob", path,
                  f"{len(value)}-char base64 string — documents carry no blobs; host the "
                  f"file and link it by https URL (see document-contract)")
    return None


def _validate_contract(layout: dict, findings: list) -> None:
    """The envelope rules: schemaVersion, format, extensions, reserved keys,
    provenance, requires.features, and core-key guesses at the top level."""
    sv = layout.get("schemaVersion")
    if sv is not None:
        if isinstance(sv, bool) or not isinstance(sv, int) or sv < 1:
            findings.append(_f("error", "bad_schema_version", "root",
                               "'schemaVersion' must be a positive integer (omit it for 1)"))
        elif sv > KNOWN_SCHEMA_VERSION:
            findings.append(_f("warn", "bad_schema_version", "root",
                               f"schemaVersion {sv} is newer than this kit knows "
                               f"({KNOWN_SCHEMA_VERSION}); older apps open it read-only"))
    if sectionsmod.is_sectioned(layout) and sv != 2:
        findings.append(_f("warn", "bad_schema_version", "root",
                           "sections (placements / styles / connectivity) "
                           "need \"schemaVersion\": 2 so older apps open the file read-only"))
    fmt = layout.get("format")
    if fmt is not None and fmt != "carter":
        findings.append(_f("warn", "bad_top_level", "root", "'format' should be \"carter\""))
    _validate_extensions(layout.get("extensions"), "root.extensions", findings)

    for k in layout:
        if k in RESERVED_TOP_LEVEL:
            findings.append(_f("warn", "reserved_key", f"root.{k}",
                               f"'{k}' is reserved for a later grammar — don't author it"))
        elif k not in TOP_LEVEL_KEYS:
            findings.append(_f("warn", "unknown_field", "root",
                               f"unknown top-level key '{k}'{_EXT_HINT}"))

    prov = layout.get("provenance")
    if prov is not None:
        parents = prov.get("parents") if isinstance(prov, dict) else None
        if not isinstance(prov, dict) or (parents is not None and not isinstance(parents, list)):
            findings.append(_f("warn", "bad_provenance", "root.provenance",
                               "'provenance' should be {\"parents\": [...], \"package\"?: {...}}"))
        else:
            for i, p in enumerate(parents or []):
                rel = p.get("relation") if isinstance(p, dict) else None
                if not isinstance(p, dict) or not p.get("id") or rel not in _PROVENANCE_RELATIONS:
                    findings.append(_f("warn", "bad_provenance", f"root.provenance.parents[{i}]",
                                       f"a parent needs an 'id' and a 'relation' in "
                                       f"{sorted(_PROVENANCE_RELATIONS)}"))

    req = layout.get("requires")
    feats = req.get("features") if isinstance(req, dict) else None
    if isinstance(feats, list):
        for i, feat in enumerate(feats):
            if not isinstance(feat, str) or not _FEATURE.match(feat):
                findings.append(_f("warn", "bad_requires", f"root.requires.features[{i}]",
                                   f"feature {feat!r} should be 'name' or 'name@N' "
                                   f"(e.g. 'local.store@2')"))


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


def _validate_device_shape(layout, findings):
    """What the app's Codable model requires and its LayoutSanitizer bounds, beyond the
    catalog lint: `version` is an integer; at most MAX_TABS tabs; every tab has title,
    icon, grid and children; every tab/group grid names integer columns and rows; span
    and position stay inside the device's ranges. A layout missing any of these fails
    to decode on the phone (or is refused by a strict source), so each is an error.
    Pinned by the shared conformance fixtures (carter-c1n.11)."""
    if "version" in layout:
        v = layout["version"]
        whole = (isinstance(v, int) and not isinstance(v, bool)) or (
            isinstance(v, float) and math.isfinite(v) and v.is_integer())
        non_finite = isinstance(v, float) and not math.isfinite(v)   # reported by _scan_tree
        if not whole and not non_finite:
            findings.append(_f("error", "bad_top_level", "root",
                                   f"'version' must be an integer, got {v!r}"))
    tabs = layout.get("tabs")
    if not isinstance(tabs, list):
        return
    if len(tabs) > MAX_TABS:
        findings.append(_f("error", "too_many_tabs", "root",
                           f"{len(tabs)} tabs; the app keeps at most {MAX_TABS}"))

    def need_grid(node, where):
        g = node.get("grid")
        if g is None:
            findings.append(_f("error", "missing_field", where, "missing 'grid' block"))
        elif isinstance(g, dict):
            for key in ("columns", "rows"):
                if key not in g:
                    findings.append(_f("error", "missing_field", where, f"grid missing '{key}'"))

    def check_range(ch, key, lo, hi, kind, where):
        val = ch.get(key)
        if not isinstance(val, list):
            return
        for i, x in enumerate(val):
            n = gridmod.as_int(x)
            if n is not None and not lo <= n <= hi:
                findings.append(_f("error", kind, where,
                                   f"{key}[{i}] = {n} is outside {lo}..{hi}"))

    stack = []
    for ti, tab in enumerate(tabs):
        if not isinstance(tab, dict):
            continue
        where = f"tab[{ti}]"
        for key in ("title", "icon", "children"):
            if key not in tab:
                findings.append(_f("error", "missing_field", where, f"tab missing '{key}'"))
        need_grid(tab, where)
        if isinstance(tab.get("children"), list):
            stack.append((tab["children"], where, 1))
    while stack:
        children, where, depth = stack.pop()
        if depth > MAX_DEPTH + 1:
            continue                      # too_deep is reported by _validate_child
        for ch in children:
            if not isinstance(ch, dict):
                continue
            spot = f"{where}/{ch.get('id') or ch.get('type') or '?'}"
            check_range(ch, "span", *SPAN_RANGE, "bad_span", spot)
            check_range(ch, "position", *POSITION_RANGE, "bad_position", spot)
            if ch.get("type") == "group":
                need_grid(ch, spot)
                if isinstance(ch.get("children"), list):
                    stack.append((ch["children"], spot, depth + 1))


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
