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
from . import local as localmod
from . import palette as palettemod
from . import sections as sectionsmod
from .bind import WIRE_VERBS, RELAY_SERVICE_VERBS
from .conditions import check_condition

# Base/shared properties every control may carry (from the layout schema /
# ChildDefinition), independent of its type. Type-specific fields come from the catalog.
SHARED_FIELDS = {
    "type", "id", "name", "position", "span", "label", "defaultValue", "icon", "tint",
    "hideLabel", "hideBackground", "action", "sync", "visible", "enabled", "haptic",
    "animation", "longPressGroup", "longPressAction", "theme", "config",
    # Shared display/range/format properties the app decodes on ControlDefinition
    # (not per-control config) — any control may carry them; unused ones are ignored.
    # Mirrors CAR-TER/CAR-TER/Models/ControlDefinition.swift.
    "min", "max", "step", "formatValue", "controlHeight", "hideValue", "pulse",
    # Per-presentation placement variants (grid-dimensions.md#Landscape and iPad).
    "landscape", "regular",
    # Tool data (document-contract.md#Extensions): preserved, never interpreted.
    "extensions",
    # What an older app shows when it doesn't know this type (layout-config.md
    # "Requires and fallback"); checked by _fallback_findings.
    "fallback",
}
GROUP_FIELDS = {
    "type", "id", "name", "position", "span", "label", "grid", "children", "dynamic",
    "visible", "enabled", "theme", "hideBackground", "pulse", "icon", "tint", "controlHeight",
    "landscape", "regular", "extensions",
}


#: Measurement units a control `unit` converts (values.md "Units"), and the symbols
#: that alias them. Mirrors CapabilityUnit in the app. Anything else is shown
#: literally, which is allowed — but a near-miss of a name is probably a typo.
UNIT_NAMES = {
    "degrees", "kilopascals", "hectopascals", "meters", "kilometers", "miles", "feet",
    "metersPerSecond", "kilometersPerHour", "milesPerHour", "gravity",
    "celsius", "fahrenheit", "kelvin", "seconds", "minutes", "hours", "percent",
}
UNIT_ALIASES = {
    "°": "degrees", "kPa": "kilopascals", "hPa": "hectopascals",
    "m": "meters", "km": "kilometers", "mi": "miles", "ft": "feet",
    "m/s": "metersPerSecond", "km/h": "kilometersPerHour", "kph": "kilometersPerHour",
    "mph": "milesPerHour", "°C": "celsius", "°F": "fahrenheit", "K": "kelvin",
    "s": "seconds", "min": "minutes", "h": "hours", "%": "percent",
}


def unit_name(unit: str) -> Optional[str]:
    """The values.md unit a control `unit` string means, or None for a literal."""
    if unit in UNIT_NAMES:
        return unit
    if unit in UNIT_ALIASES:
        return UNIT_ALIASES[unit]
    return next((n for n in UNIT_NAMES if n.lower() == unit.lower()), None)


def _unit_findings(ctype: str, value, spot: str, findings: list) -> None:
    """A known unit or a literal is fine; a near-miss of a unit name warns."""
    if not isinstance(value, str):
        findings.append(_f("warn", "bad_unit", spot,
                           f"{ctype}.unit must be a string, got {value!r}"))
        return
    if not value.strip() or unit_name(value.strip()):
        return
    import difflib
    close = difflib.get_close_matches(value.strip().lower(),
                                      [n.lower() for n in UNIT_NAMES], n=1, cutoff=0.8)
    if close:
        name = next(n for n in UNIT_NAMES if n.lower() == close[0])
        findings.append(_f("warn", "unit_typo", spot,
                           f"{ctype}.unit = '{value}' is shown literally, with no locale "
                           f"conversion — did you mean '{name}'?"))


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


def validate_layout(layout: dict, catalog: dict, target_app: Optional[str] = None) -> list[dict]:
    """Validate a full layout against the catalog. `catalog` should be built with
    include_theme=True so per-control theme fields are recognized. Never raises:
    an unexpected failure is itself reported as an `internal_error` finding.

    `target_app` is the oldest CAR-TER the author wants the layout to work on. The
    layout's own `requires.app` wins over it; with neither, DEFAULT_TARGET_APP. A
    control whose catalog `since` is newer than that target, with no usable
    `fallback`, is a `needs_newer_app` warning (see target_app_findings)."""
    try:
        findings = _validate_layout(layout, catalog)
        if isinstance(layout, dict):
            try:
                extra = fallback_findings(layout, catalog)
                extra += target_app_findings(layout, catalog, target_app)
            except RecursionError:   # hostile nesting: already reported as too_deep above
                extra = []
            findings.extend(extra)
        return findings
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


def _grid_reflow(g, where, findings) -> None:
    """`grid.reflow` is "auto" (default) or "stretch"; the app treats anything else as
    auto, so another value is a warning."""
    if isinstance(g, dict) and "reflow" in g and g["reflow"] not in ("auto", "stretch"):
        findings.append(_f("warn", "bad_grid", where,
                           f"grid.reflow must be \"auto\" or \"stretch\", got {g['reflow']!r}"))


def _placement_variants(ch: dict, where: str, findings) -> None:
    """`landscape` / `regular` on a child: `{position, span}` or `{hidden: true}`. The app
    drops a malformed variant with a warning (the default placement renders), so these
    are warnings, never errors."""
    for key in ("landscape", "regular"):
        if key not in ch:
            continue
        v = ch[key]
        spot = f"{where}.{key}"
        if not isinstance(v, dict):
            findings.append(_f("warn", "bad_placement", spot,
                               f"'{key}' must be an object {{position, span}} or {{hidden: true}}"))
            continue
        for k in v:
            if k not in ("position", "span", "hidden"):
                findings.append(_f("warn", "unknown_field", spot, f"{key}: unknown field '{k}'"))
        for k in ("position", "span"):
            if k in v and not (isinstance(v[k], list) and len(v[k]) == 2
                               and all(gridmod.as_int(n) is not None for n in v[k])):
                findings.append(_f("warn", "bad_placement", spot,
                                   f"{key}.{k} must be [int, int], got {v[k]!r}"))
        if "hidden" in v and not isinstance(v["hidden"], bool):
            findings.append(_f("warn", "bad_placement", spot,
                               f"{key}.hidden must be true or false, got {v['hidden']!r}"))


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
    # Palette tokens (carter-m7s.16): raw colours that equal a token, unknown `$name`
    # refs, ignored palette entries. Warnings only; run on the document as written so
    # `styles` refs are reported where they live.
    for kind, where, detail in palettemod.palette_findings(layout):
        findings.append(_f("warn", kind, where, detail))

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
        _grid_reflow(g, where, findings)
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


def _is_placeholder(v) -> bool:
    """A template slot like "<your-token>" is not a credential (samples ship with it)."""
    return isinstance(v, str) and len(v) > 2 and v.startswith("<") and v.endswith(">")


def _scan_tree(layout: dict, findings: list) -> None:
    """One iterative pass over the whole document for value-level hazards."""
    secret_paths = set()
    conn = layout.get("connection")
    if isinstance(conn, dict):
        for k in ("token", "e2eeKey", "k", "refresh"):
            if conn.get(k) and not _is_placeholder(conn.get(k)):
                secret_paths.add(f"connection.{k}")
    srcs = layout.get("sources")
    if isinstance(srcs, dict):
        for name, src in srcs.items():
            if not isinstance(src, dict):
                continue
            for k in ("password", "token", "apiKey"):
                if src.get(k) and not _is_placeholder(src.get(k)):
                    secret_paths.add(f"sources.{name}.{k}")
            headers = src.get("headers")
            if isinstance(headers, dict):
                for hk in headers:
                    if any(w in str(hk).lower() for w in ("authorization", "token", "key", "secret", "cookie")) \
                            and not _is_placeholder(headers[hk]):
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
            if method not in ("mqtt", "http", "local"):
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

    # `visible` / `enabled`: the conditions-v2 tree (conditions.py mirrors the device).
    for ckey in ("visible", "enabled"):
        if ckey in ch:
            check_condition(ch[ckey], f"{spot}.{ckey}", findings)

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
        _grid_reflow(g, spot, findings)
        _placement_variants(ch, spot, findings)
        _grid_findings(sub_children, cols, rows, spot, findings,
                       g.get("mode") if isinstance(g, dict) else None)
        for sub in sub_children:
            _validate_child(sub, catalog, spot, findings, seen_ids, sources, depth + 1, counter)
        return

    # Containers (carousel/flipCard/accordion panels, longPressGroup, canvas items) nest
    # like groups on the device — one limit everywhere (carter-7np).
    if _hosted_too_deep(ch, depth):
        findings.append(_f("error", "too_deep", spot,
                           f"groups/containers nest deeper than {MAX_DEPTH} levels — the app refuses this"))

    if not ctype:
        return
    entry = catalog.get(ctype)
    if entry is None:
        findings.append(_f("error", "unknown_type", spot, f"unknown control type '{ctype}'"))
        return

    _validate_extensions(ch.get("extensions"), f"{spot}.extensions", findings)
    _placement_variants(ch, spot, findings)
    fields = {f["name"]: f for f in entry.get("fields", [])}
    theme_names = {f["name"] for f in entry.get("themeFields", [])}
    allowed = SHARED_FIELDS | set(fields) | theme_names

    for k, v in ch.items():
        if k not in allowed:
            findings.append(_f("warn", "unknown_field", spot,
                               f"{ctype}: unknown field '{k}'{_EXT_HINT}"))
            continue
        if k == "unit":
            _unit_findings(ctype, v, spot, findings)
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
    _validate_default_value(ch.get("defaultValue"), ctype, spot, findings)
    _validate_relative_format(ch, ctype, spot, findings)
    _validate_bindings(ch, ctype, spot, findings, sources)


def _hosted(node, depth):
    """(child, depth) pairs `node` (sitting in a children array at `depth`) hosts, counted
    like the app's LayoutSanitizer: each container is ONE level — a group's or a panel's
    `children` (the `panels` array itself is only a hop), a longPressGroup's `children`
    and `canvasConfig.items` — matching the renderer's one `depth + 1` per spawn."""
    out = []
    if node.get("type") == "group":
        subs = node.get("children")
        return [(c, depth + 1) for c in subs] if isinstance(subs, list) else []
    panels = node.get("panels")
    if isinstance(panels, list):
        for p in panels:
            if isinstance(p, dict) and isinstance(p.get("children"), list):
                out += [(c, depth + 1) for c in p["children"]]
    lpg = node.get("longPressGroup")
    if isinstance(lpg, dict) and isinstance(lpg.get("children"), list):
        out += [(c, depth + 1) for c in lpg["children"]]
    cc = node.get("canvasConfig")
    if isinstance(cc, dict) and isinstance(cc.get("items"), list):
        out += [(it["control"], depth + 1) for it in cc["items"]
                if isinstance(it, dict) and isinstance(it.get("control"), dict)]
    return out


def _hosted_too_deep(node, depth):
    """True when anything a container hosts has more than MAX_DEPTH enclosing levels
    (`depth - 1`, as in `_validate_child`). Stops at the limit, so a hostile chain costs
    at most MAX_DEPTH + 1 frames."""
    for sub, d in _hosted(node, depth):
        if not isinstance(sub, dict):
            continue
        if d - 1 > MAX_DEPTH or _hosted_too_deep(sub, d):
            return True
    return False


#: Controls whose value is a JSON document: a `defaultValue` object/array is their dataset
#: (the app stores it as the encoded string). Mirrors ControlType.jsonDocumentTypes.
_JSON_DOCUMENT_TYPES = {"chart", "pieChart", "heatmap", "radar", "boxPlot", "gantt", "sankey",
                        "treemap", "chord", "sortboard", "pinboard", "canvas", "map", "graph",
                        "cardList"}


def _validate_default_value(dv, ctype, spot, findings):
    """control-def.md#defaultValue per type: scalars everywhere; an array/object seed only on
    buffer (sparkline/list/logConsole) and dataset controls. The app drops any other seed on
    load with a repair note (carter-7vs), so this is a warning."""
    if not isinstance(dv, (list, dict)):
        return
    if ctype == "sparkline":
        ok = isinstance(dv, list) and any(_is_number(v) for v in dv) \
            and all(v is None or _is_number(v) for v in dv)
        need = "an array of numbers"
    elif ctype == "list":
        ok = isinstance(dv, list) and all(isinstance(v, dict) for v in dv)
        need = "an array of row objects"
    elif ctype == "logConsole" or ctype in _JSON_DOCUMENT_TYPES:
        ok, need = True, ""
    else:
        ok, need = False, "a bool, number or string"
    if not ok:
        findings.append(_f("warn", "bad_default_value", spot,
                           f"{ctype}.defaultValue should be {need} — the app drops this seed on load"))
    elif len(json.dumps(dv, separators=(",", ":"))) > 4096:
        findings.append(_f("warn", "bad_default_value", spot,
                           f"{ctype}.defaultValue seed is over 4 KB encoded — the app drops it on load"))


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


#: `formatValue` tokens that read the value as a DATE ("4 days ago", "Today").
RELATIVE_FORMATS = {"relative", "relative:day"}
#: Controls whose readout renders a relative date (label; its glance/widget slot
#: follows the same control). Numeric controls treat the value as a number.
_RELATIVE_TYPES = {"label"}


def _validate_relative_format(ch, ctype, spot, findings):
    """Lint the time-since formats (`formatValue: "relative"` / `"relative:day"`):
    a misspelled variant silently falls back to the raw value, and a numeric control
    (gauge, slider, …) cannot draw a date. `placeholder` only matters with them."""
    fmt = ch.get("formatValue")
    if not isinstance(fmt, str) or not fmt.startswith("relative"):
        return
    if fmt not in RELATIVE_FORMATS:
        findings.append(_f("warn", "bad_relative_format", spot,
                           f"{ctype}.formatValue = '{fmt}' — use 'relative' or 'relative:day'; "
                           f"the app shows the raw value otherwise"))
        return
    if ctype not in _RELATIVE_TYPES:
        findings.append(_f("warn", "relative_format_type", spot,
                           f"{ctype}.formatValue = '{fmt}' — relative dates render on a label "
                           f"(and its widget slot); a {ctype} reads its value as a number"))


# Transports whose sync/action carry a transport address (topic/path) instead of a
# MeshSocket `event` — these are APP-side runtimes (see sources.md / sensors.md).
_ADDRESSED_METHODS = {"mqtt", "http", "sensor", "local"}


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
    elif method in ("mqtt", "local") and len(declared) != 1:
        # HTTP can use an absolute `url` with no source at all; MQTT always needs a broker
        # and a local binding always needs a declared store (there is nothing else to read).
        detail = (f"no {method} source declared" if not declared
                  else f"{len(declared)} {method} sources declared — name one with 'source'")
        findings.append(_f("error" if method == "local" else "warn", "bad_source", spot,
                           f"{ctype}.{what}: {detail}"))


def _local_schema_for(binding, sources):
    """The normalized local-source schema a binding resolves to (explicit `source`, else
    the single declared local source), or None when it cannot be resolved — the source
    reference findings already explain why."""
    schemas = getattr(sources, "local", {})
    ref = binding.get("source")
    if ref is not None:
        return schemas.get(ref)
    return next(iter(schemas.values())) if len(schemas) == 1 else None


def _local_problems(problems, kind, spot, prefix, findings):
    for sev, msg in problems:
        findings.append(_f(sev, kind, spot, f"{prefix}: {msg}"))


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
    if method == "local":
        _validate_local_sync(s, ctype, spot, i, findings, sources)
        return
    # MeshSocket (default): a listen needs a valuePath to extract from the frame.
    if not s.get("valuePath"):
        findings.append(_f("warn", "bad_sync", spot,
                           f"{ctype}.sync[{i}] is missing a 'valuePath'"))


def _validate_local_sync(s, ctype, spot, i, findings, sources):
    """A `method: local` sync is a query stage over a declared collection or view (see
    local-store.md). The stage is linted against the declared fields so an undeclared
    field, a bad op or an out-of-range limit fails here, not as a `failed` pipe."""
    what = f"{ctype}.sync[{i}]"
    coll = s.get("collection")
    if not isinstance(coll, str) or not coll:
        findings.append(_f("error", "bad_sync", spot, f"{what} local sync needs a 'collection'"))
    for key in ("event", "topic", "url", "path", "sensor"):
        if key in s:
            findings.append(_f("warn", "bad_sync", spot,
                               f"{what}: '{key}' means nothing on a local sync (no wire)"))
    _source_ref_findings(s, "local", spot, ctype, f"sync[{i}]", findings, sources)
    schema = _local_schema_for(s, sources)
    if schema is None or not isinstance(coll, str):
        return
    fields = localmod.fields_for(schema, coll)
    if fields is None:
        findings.append(_f("error", "unknown_collection", spot,
                           f"{what}: '{coll}' is not a collection or view of the local source"))
        return
    stage = {k: s[k] for k in ("where", "groupBy", "aggregate", "orderBy", "limit") if k in s}
    _local_problems(localmod.lint_stage(stage, fields), "bad_stage", spot, what, findings)


def _validate_action_entry(a, ctype, akey, spot, findings, sources):
    method = a.get("method", "meshsocket")
    if method == "local":
        _source_ref_findings(a, "local", spot, ctype, akey, findings, sources)
        _local_problems(localmod.lint_op(a, _local_schema_for(a, sources)), "bad_action", spot,
                        f"{ctype}.{akey}", findings)
        return
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


class _SourceMap(dict):
    """{name: kind} for every declared source, plus `.local` = {name: normalized schema}
    for the local stores (so binding lint can check collections and fields)."""
    local: dict


def _validate_sources_defs(layout, findings) -> dict:
    """Validate top-level `sources` (mqtt/http/local source definitions) and return a
    {name: kind} map for binding checks. See sources.md and local-store.md."""
    out = _SourceMap()
    out.local = {}
    raw = layout.get("sources")
    if raw is None:
        return out
    if not isinstance(raw, dict):
        findings.append(_f("error", "bad_sources", "root", "'sources' must be an object of {name: source}"))
        return out
    namespaces: dict[str, str] = {}
    for name, sdef in raw.items():
        where = f"sources.{name}"
        if not isinstance(sdef, dict):
            findings.append(_f("error", "bad_sources", where, "source must be an object"))
            continue
        kind = sdef.get("type")
        if kind not in ("mqtt", "http", "local"):
            findings.append(_f("error", "bad_sources", where,
                               f"source 'type' must be 'mqtt', 'http' or 'local', got {kind!r}"))
            continue
        out[name] = kind
        _lint_mirror_placement(sdef, kind, where, findings)
        if kind == "mqtt" and not sdef.get("url"):
            findings.append(_f("error", "bad_sources", where, "mqtt source needs a broker 'url'"))
        # http `baseURL` is optional — syncs may use absolute `url`s instead.
        if kind == "local":
            problems, schema = localmod.lint_source(sdef)
            for sev, msg in problems:
                findings.append(_f(sev, "bad_sources", where, msg))
            out.local[name] = schema
            ns = schema.get("namespace")
            if ns is not None:
                if ns in namespaces:
                    findings.append(_f("error", "bad_sources", where,
                                       f"namespace '{ns}' is already used by source '{namespaces[ns]}'"))
                namespaces[ns] = name
    # A layout with several local stores must name each namespace explicitly — only one
    # may fall back to the layout's own id/name (LocalSourceSchema.schemas rule).
    implicit = [n for n, sc in out.local.items() if sc.get("namespace") is None]
    if len(out.local) > 1 and implicit:
        for n in implicit:
            findings.append(_f("error", "bad_sources", f"sources.{n}",
                               "a second local source needs an explicit 'namespace'"))
    return out


def _lint_mirror_placement(sdef, kind, where, findings):
    """`mirror` (studio change-notice, readback spec §4) is a bool on a collection inside
    a `type: "local"` source — nowhere else. The bool check on local collections lives in
    `local.lint_source`; this catches every misplaced `mirror`."""
    if "mirror" in sdef:
        findings.append(_f("error", "bad_sources", where,
                           "'mirror' belongs on a collection (collections.<name>.mirror), "
                           "not on the source"))
    if kind == "local":
        return
    colls = sdef.get("collections")
    if isinstance(colls, dict):
        for cname, cdef in colls.items():
            if isinstance(cdef, dict) and "mirror" in cdef:
                findings.append(_f("error", "bad_sources", f"{where}.collections.{cname}",
                                   f"'mirror' is only valid on a collection of a "
                                   f"type:'local' source, not a {kind} source"))


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
    if req is not None and not isinstance(req, dict):
        findings.append(_f("warn", "bad_requires", "root.requires",
                           "'requires' should be an object like "
                           "{\"app\": \"1.3\", \"features\": [...]}; the app ignores it"))
    if isinstance(req, dict):
        for k in req:
            if k not in ("app", "features"):
                findings.append(_f("warn", "bad_requires", f"root.requires.{k}",
                                   f"unknown key '{k}' (requires takes 'app' and 'features')"))
        if "app" in req and not _is_app_version(req["app"]):
            findings.append(_f("warn", "bad_requires", "root.requires.app",
                               f"'app' should be a dotted version string like \"1.3\", "
                               f"not {req['app']!r}; the app ignores it"))
        if "features" in req and not isinstance(req["features"], list):
            findings.append(_f("warn", "bad_requires", "root.requires.features",
                               "'features' should be an array of 'name' / 'name@N' strings"))
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


# ─── Device support (carter-5sn.1, decision carter-4fb) ──────────────────────
#
# An app that doesn't know a control type draws a quiet "Update CAR-TER" tile in
# its cell (or the control's `fallback`, when it has one) and lists it in the
# update banner. That is never an error: the layout still loads. It IS worth a
# warning, so the author knows the phone's app is older than the layout. The
# kit never auto-wraps a fallback; the author decides.

def _feature_names(features) -> set:
    """`name` / `name@N` strings (the app's get-device-info `features`) → names."""
    out = set()
    for f in features or ():
        if isinstance(f, str) and f.strip():
            out.add(f.strip().split("@", 1)[0])
    return out


def _walk_controls(children, where, out):
    """(control dict, where) for every placed control: tab/group children, container
    `panels`, `longPressGroup`, and canvas items. Groups recurse, never yield."""
    if not isinstance(children, list):
        return
    for i, ch in enumerate(children):
        if not isinstance(ch, dict):
            continue
        spot = f"{where}/{ch.get('id') or ch.get('type') or i}"
        if ch.get("type") == "group":
            _walk_controls(ch.get("children"), spot, out)
            continue
        out.append((ch, spot))
        for p, panel in enumerate(ch.get("panels") or [] if isinstance(ch.get("panels"), list) else []):
            if isinstance(panel, dict):
                _walk_controls(panel.get("children"), f"{spot}/panels[{p}]", out)
        lpg = ch.get("longPressGroup")
        if isinstance(lpg, dict):
            _walk_controls(lpg.get("children"), f"{spot}/longPressGroup", out)
        canvas = ch.get("canvasConfig")
        items = canvas.get("items") if isinstance(canvas, dict) else None
        for item in items if isinstance(items, list) else []:
            if isinstance(item, dict) and isinstance(item.get("control"), dict):
                _walk_controls([item["control"]], f"{spot}/canvas", out)


def _in_canvas(ch: dict, spot: str) -> bool:
    """True for a canvas item's hosted control (as `_walk_controls` names it)."""
    return spot.endswith("/canvas/" + str(ch.get("id") or ch.get("type")))


#: Fallback hops the app follows before a node counts as unsupported
#: (LayoutForwardCompat.maxFallbackDepth).
MAX_FALLBACK_DEPTH = 4


def _usable_fallback(node: dict, have: set, in_canvas: bool = False):
    """The type the app will draw from `node`'s `fallback` chain, or None."""
    current = node
    for _ in range(MAX_FALLBACK_DEPTH):
        nxt = current.get("fallback")
        if not isinstance(nxt, dict):
            return None
        t = nxt.get("type")
        if t == "group":
            return None if in_canvas else "group"   # a canvas card hosts one control
        if isinstance(t, str) and f"control.{t}" in have:
            return t
        current = nxt
    return None


def device_support_findings(layout: dict, features) -> list[dict]:
    """Warn about controls the paired phone's app doesn't know.

    `features` is the device's reported feature list (`control.<type>`, `sync.<m>`, …;
    `get-device-info` → `features`). None or empty means "unknown" and returns [] —
    an older app that doesn't report features can't be judged this way (the
    `since`/target-version lint covers that case). Each unknown type is a `warn`
    finding of kind `needs_newer_app`: the phone shows its `fallback` if the control
    has a usable one, else an "Update CAR-TER" placeholder tile in its cell."""
    have = _feature_names(features)
    if not have or not isinstance(layout, dict):
        return []
    found: list = []
    for t, tab in enumerate(layout.get("tabs") or [] if isinstance(layout.get("tabs"), list) else []):
        if isinstance(tab, dict):
            _walk_controls(tab.get("children"), f"tabs[{t}]", found)
    findings = []
    for ch, spot in found:
        ctype = ch.get("type")
        if not isinstance(ctype, str) or f"control.{ctype}" in have:
            continue
        fb_type = _usable_fallback(ch, have, in_canvas=_in_canvas(ch, spot))
        if fb_type:
            shows = f"shows its fallback ({fb_type}) instead"
        else:
            shows = "shows an 'Update CAR-TER' placeholder in its place"
        findings.append(_f("warn", "needs_newer_app", spot,
                           f"the phone's CAR-TER app is older than control '{ctype}': it {shows}"))
    return findings


# ─── Target app: `since` + `fallback` (carter-0gj.27, decision carter-4fb) ────
#
# Without a paired phone, the kit judges a layout against a target app version:
# the layout's `requires.app`, else the caller's `target_app`, else the oldest
# supported app. A control doc's frontmatter `since: "1.3"` says which app first
# knows it (absent = every supported app). Warn-only: the kit never auto-wraps a
# fallback (carter-4fb); the author adds one or raises requires.app.

#: The oldest app the kit targets when nothing else says (the 1.2.4 App Store build).
DEFAULT_TARGET_APP = "1.2.4"

_APP_VERSION = re.compile(r"^[0-9]+(\.[0-9]+)*$")


def _is_app_version(v) -> bool:
    """A dotted numeric version string ("1.3", "1.2.4") — what `requires.app` takes."""
    return isinstance(v, str) and bool(_APP_VERSION.match(v.strip()))


def _version_newer(a: str, b: str) -> bool:
    """a > b, number by number, missing parts = 0 (the app's compareVersions)."""
    pa = [int(x) for x in a.strip().split(".")]
    pb = [int(x) for x in b.strip().split(".")]
    n = max(len(pa), len(pb))
    pa += [0] * (n - len(pa))
    pb += [0] * (n - len(pb))
    return pa > pb


def effective_target_app(layout, target_app: Optional[str] = None) -> tuple[str, str]:
    """(version, where it came from): `requires.app` if well formed, else
    `target_app` if well formed, else DEFAULT_TARGET_APP."""
    req = layout.get("requires") if isinstance(layout, dict) else None
    app = req.get("app") if isinstance(req, dict) else None
    if _is_app_version(app):
        return app.strip(), "requires.app"
    if _is_app_version(target_app):
        return target_app.strip(), "target_app"
    return DEFAULT_TARGET_APP, "the kit's default target"


def _since(catalog: dict, ctype) -> Optional[str]:
    spec = catalog.get(ctype) if isinstance(ctype, str) else None
    since = spec.get("since") if isinstance(spec, dict) else None
    return since if _is_app_version(since) else None


def _placed_controls(layout: dict) -> list:
    found: list = []
    tabs = layout.get("tabs")
    for t, tab in enumerate(tabs if isinstance(tabs, list) else []):
        if isinstance(tab, dict):
            _walk_controls(tab.get("children"), f"tabs[{t}]", found)
    return found


def fallback_findings(layout: dict, catalog: dict) -> list[dict]:
    """Shape checks for every control's `fallback` chain, as the app reads it
    (LayoutForwardCompat): each hop an object with a known `type` (a control or a
    `group`), at most MAX_FALLBACK_DEPTH hops, no `group` in a canvas item, and no
    `id`/`position`/`span` (the app replaces them with the original's). All `warn`:
    a bad fallback only costs the older app its substitute, never the load."""
    findings: list = []
    if not isinstance(layout, dict):
        return findings
    for ch, spot in _placed_controls(layout):
        if "fallback" not in ch:
            continue
        in_canvas = _in_canvas(ch, spot)
        current, where = ch, f"{spot}.fallback"
        for hop in range(MAX_FALLBACK_DEPTH + 1):
            if "fallback" not in current:
                break
            fb = current["fallback"]
            if hop == MAX_FALLBACK_DEPTH:
                findings.append(_f("warn", "bad_fallback", where,
                                   f"the app follows at most {MAX_FALLBACK_DEPTH} fallback "
                                   f"hops; this one is never used"))
                break
            if not isinstance(fb, dict):
                findings.append(_f("warn", "bad_fallback", where,
                                   "'fallback' must be a control object like "
                                   "{\"type\": \"slider\", ...}; the app ignores it"))
                break
            t = fb.get("type")
            if not isinstance(t, str) or not t:
                findings.append(_f("warn", "bad_fallback", where,
                                   "a fallback needs a 'type'; the app ignores it"))
                break
            if t == "group":
                if in_canvas:
                    findings.append(_f("warn", "bad_fallback", where,
                                       "a canvas item hosts one control, so a group "
                                       "fallback is never used there"))
            elif t not in catalog:
                findings.append(_f("warn", "bad_fallback", where,
                                   f"unknown control type '{t}' — no app draws it, so "
                                   f"the chain moves on to its own fallback (if any)"))
            placed = [k for k in ("id", "position", "span") if k in fb]
            if placed:
                findings.append(_f("warn", "bad_fallback", where,
                                   f"{', '.join(repr(k) for k in placed)} on a fallback "
                                   f"is ignored: it takes the original control's "
                                   f"id, position and span"))
            current, where = fb, f"{where}.fallback"
    return findings


def _target_fallback(node: dict, catalog: dict, target: str, in_canvas: bool):
    """The type the target app draws from `node`'s fallback chain, or None. Mirrors
    `_usable_fallback`, judging "known" by catalog `since` instead of device features."""
    current = node
    for _ in range(MAX_FALLBACK_DEPTH):
        nxt = current.get("fallback")
        if not isinstance(nxt, dict):
            return None
        t = nxt.get("type")
        if t == "group":
            return None if in_canvas else "group"
        if isinstance(t, str) and t in catalog:
            since = _since(catalog, t)
            if since is None or not _version_newer(since, target):
                return t
        current = nxt
    return None


def target_app_findings(layout: dict, catalog: dict, target_app: Optional[str] = None) -> list[dict]:
    """`needs_newer_app` warnings for controls newer than the target app (see
    effective_target_app) that have no fallback that app can draw. Silent when the
    catalog carries no `since`, when the target covers it, or with a usable fallback."""
    if not isinstance(layout, dict) or not isinstance(catalog, dict):
        return []
    target, source = effective_target_app(layout, target_app)
    findings = []
    for ch, spot in _placed_controls(layout):
        ctype = ch.get("type")
        since = _since(catalog, ctype)
        if since is None or not _version_newer(since, target):
            continue
        if _target_fallback(ch, catalog, target, _in_canvas(ch, spot)):
            continue
        why = ("its fallback chain has nothing that app can draw"
               if "fallback" in ch else "it has no 'fallback'")
        findings.append(_f("warn", "needs_newer_app", spot,
                           f"control '{ctype}' needs CAR-TER {since}, newer than the "
                           f"target {target} ({source}), and {why}: that app shows an "
                           f"'Update CAR-TER' placeholder. Add a fallback, or set "
                           f"requires.app to \"{since}\" if older apps don't matter"))
    return findings
