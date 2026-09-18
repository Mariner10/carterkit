"""Builders for the `glance` block — the layout projected onto iOS surfaces.

A layout already says what matters: its controls. `glance` re-uses that vocabulary
outside the app — Home/Lock Screen widgets, the Dynamic Island, the lock-screen
Live Activity banner, StandBy, CarPlay and Control Center / the Action button. The
JSON is small enough to hand-write; these builders exist so an author gets the
**key spellings** and the **kind-specific required fields** checked at build time
instead of discovering on a phone that a surface silently rendered nothing.

Three shapes, and everything is one of them:

* a **tile** — one bound readout or button (:func:`tile`, and the `cc_*` helpers
  for the Control Center flavour, which is a different list with different rules);
* a **scene** — rows of tiles (:func:`scene`), which is what a widget, the island's
  expanded bottom and the lock screen each take;
* a **surface** — :func:`widget`, :func:`island`, and :func:`live` for how fresh
  the whole projection should be.

Every `control=` argument accepts a `Layout` control handle as well as an id
string, so an author never retypes an id:

    from carterkit import Layout, tile, scene, widget, live, cc_toggle

    with Layout("Printer", id="printer", cols=4, rows=6) as ui:
        with ui.tab("Main"):
            nozzle = ui.gauge("nozzle", min=0, max=300, listen="temps")
            lights = ui.toggle("lights", send="set_lights", listen="lights")
        ui.glance(
            hero=nozzle, live=live(tier="fresh"),
            widgets=[widget("temps", title="Temps", families=["systemMedium"],
                            scene=scene([tile("gauge", nozzle)],
                                        [tile("sparkline", nozzle, span=2)]))],
            controls=[cc_toggle("lights", label="Lights", control=lights)])

What iOS allows is not negotiable, and the ControlDocs `glance.md` table is the
reference: Control Center has toggles and buttons only (a slider becomes
`step`/`set`, a picker becomes `cycle`), widgets and Live Activities animate only
through Apple's own choreography — numeric transitions, symbol effects keyed to a
value, self-ticking timers — and a Live Activity update is capped at 4 KB.
"""

__all__ = [
    "TILE_KINDS", "WIDGET_FAMILIES", "CONTROL_KINDS", "LIVE_TIERS",
    "SYMBOL_EFFECTS", "TILE_TRANSITIONS", "ISLAND_TILE_REGIONS", "ISLAND_REGIONS",
    "tile", "scene", "widget", "island", "live", "state",
    "cc_toggle", "cc_button", "cc_cycle", "cc_step", "cc_set",
]

#: Tile kinds a scene may contain. An unknown kind renders as `value` plus a
#: diagnostic on-device; the builder refuses it outright, because in JSON authored
#: by hand a misspelled kind is always a mistake.
TILE_KINDS = ("value", "gauge", "ring", "bar", "light", "sparkline", "text",
              "icon", "spacer", "timer", "freshness", "toggle", "button",
              "step", "open")

#: WidgetKit families a `widgets[]` entry may declare, and the names a per-family
#: scene override may use.
WIDGET_FAMILIES = ("systemSmall", "systemMedium", "systemLarge", "systemExtraLarge",
                   "accessoryCircular", "accessoryRectangular", "accessoryInline")

#: Control Center / lock-screen / Action-button control kinds.
CONTROL_KINDS = ("toggle", "button", "cycle", "step", "set")

#: `live.tier` presets. Explicit fields override the tier's defaults.
LIVE_TIERS = ("realtime", "fresh", "periodic", "manual")

#: SF Symbol effects a tile may play once per value change. Apple's built-in
#: choreography only — a hand-rolled animation does not run on these surfaces.
SYMBOL_EFFECTS = ("bounce", "pulse", "wiggle", "rotate", "breathe", "variableColor")

#: How a tile appears and disappears.
TILE_TRANSITIONS = ("opacity", "slide", "push", "move")

#: Island regions that take exactly ONE tile — there is no room for a scene.
ISLAND_TILE_REGIONS = ("compactLeading", "compactTrailing", "minimal")

#: Island regions in `expanded`. `leading`/`trailing`/`center` take one tile or a
#: scene; `bottom` takes a scene.
ISLAND_REGIONS = ("leading", "trailing", "center", "bottom")

# Tile fields, and the snake_case spellings accepted for the camelCase ones.
_TILE_FIELDS = {"tile", "control", "label", "icon", "tint", "span", "format",
                "delta", "presets", "value", "event", "payload", "effect",
                "transition", "tab"}
_ALIASES = {
    "value_control": "valueControl", "value_label": "valueLabel",
    "lock_screen": "lockScreen", "compact_leading": "compactLeading",
    "compact_trailing": "compactTrailing", "live_activity": "liveActivity",
    "pull_every": "pullEvery", "remote_cadence": "remoteCadence",
    "silent_push": "silentPush", "format_value": "format",
    "system_small": "systemSmall", "system_medium": "systemMedium",
    "system_large": "systemLarge", "system_extra_large": "systemExtraLarge",
    "accessory_circular": "accessoryCircular",
    "accessory_rectangular": "accessoryRectangular",
    "accessory_inline": "accessoryInline",
}


def _control_id(value, *, field="control"):
    """A control id from an id string or a `Layout` control handle."""
    if value is None:
        return None
    if isinstance(value, str):
        if not value:
            raise ValueError(f"{field} must be a non-empty control id")
        return value
    cid = getattr(value, "id", None)
    if isinstance(cid, str) and cid:
        return cid
    raise ValueError(f"{field} must be a control id or a Layout control handle, "
                     f"got {value!r}")


def _camel(key):
    return _ALIASES.get(key, key)


def _number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number, got {value!r}")
    return value


def _choice(value, allowed, field):
    if value not in allowed:
        raise ValueError(f"{field} must be one of {list(allowed)}, got {value!r}")
    return value


def _compact(pairs):
    return {k: v for k, v in pairs if v is not None}


# ── tiles and scenes ─────────────────────────────────────────────────────────

def tile(kind, control=None, **fields):
    """One tile: `tile("gauge", nozzle)`, `tile("step", fan, delta=10)`.

    `kind` is one of :data:`TILE_KINDS`; `control` is a control id or handle.
    Extra fields are the per-tile overrides from `glance.md` — `label`, `icon`,
    `tint`, `span`, `format`, `delta`, `presets`, `value`, `event`, `payload`,
    `effect`, `transition`, `tab` — and snake_case spellings are accepted for the
    camelCase ones. An unknown field raises rather than riding silently to a
    surface that ignores it."""
    _choice(kind, TILE_KINDS, "tile kind")
    out = {"tile": kind}
    cid = _control_id(control)
    if cid is not None:
        out["control"] = cid
    for key, value in fields.items():
        if value is None:
            continue
        name = _camel(key)
        if name not in _TILE_FIELDS or name == "tile":
            raise ValueError(f"unknown tile field {key!r}; allowed: "
                             f"{sorted(_TILE_FIELDS - {'tile'})}")
        if name == "control":
            value = _control_id(value)
        elif name == "span":
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError("span must be an integer >= 1")
        elif name == "delta":
            _number(value, "delta")
        elif name == "presets":
            value = [_number(v, "presets entry") for v in value]
        elif name == "effect":
            _choice(value, SYMBOL_EFFECTS, "effect")
        elif name == "transition":
            _choice(value, TILE_TRANSITIONS, "transition")
        elif name == "tab":
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("tab must be a non-negative integer")
        out[name] = value
    return out


def scene(*rows, columns=None):
    """A scene: `scene([tile(...), tile(...)], [tile(...)])`.

    Each argument is one row — a list of tiles, or a bare tile for a row of one.
    `columns` defaults on-device to the longest row, so pass it only to leave a
    row deliberately short."""
    out_rows = []
    for index, row in enumerate(rows):
        if isinstance(row, dict):
            row = [row]
        if not isinstance(row, (list, tuple)):
            raise ValueError(f"row {index} must be a tile or a list of tiles")
        for item in row:
            if not isinstance(item, dict) or "tile" not in item:
                raise ValueError(f"row {index} must contain tiles — build them "
                                 f"with tile()")
        out_rows.append(list(row))
    out = {"rows": out_rows}
    if columns is not None:
        if isinstance(columns, bool) or not isinstance(columns, int) or columns < 1:
            raise ValueError("columns must be an integer >= 1")
        out["columns"] = columns
    return out


def _as_scene(value, where):
    """Accept a scene, a single tile, or a list of rows."""
    if isinstance(value, dict) and "rows" in value:
        return value
    if isinstance(value, dict) and "tile" in value:
        return scene(value)
    if isinstance(value, (list, tuple)):
        return scene(*value)
    raise ValueError(f"{where} must be a scene (see scene()), a tile, or a list of rows")


# ── surfaces ─────────────────────────────────────────────────────────────────

def widget(id, title=None, families=None, scene=None, icon=None, **per_family):
    """One `widgets[]` entry — a scene the user can place on the Home or Lock Screen.

    `families` lists the WidgetKit families the widget offers (see
    :data:`WIDGET_FAMILIES`). `scene` renders for every family without an
    override; pass an override as a keyword, `system_small=…` or
    `systemSmall=…`. Without one, iOS-side fallback applies: small renders the
    first row, `accessoryRectangular` the first row as values, `accessoryCircular`
    the first gauge/ring/value, `accessoryInline` a "label value" pair."""
    if not isinstance(id, str) or not id:
        raise ValueError("widget id must be a non-empty string")
    out = {"id": id}
    if title is not None:
        out["title"] = title
    if icon is not None:
        out["icon"] = icon
    if families is not None:
        if isinstance(families, str):
            families = [families]
        out["families"] = [_choice(f, WIDGET_FAMILIES, "family") for f in families]
    if scene is not None:
        out["scene"] = _as_scene(scene, "widget scene")
    for key, value in per_family.items():
        name = _camel(key)
        if name not in WIDGET_FAMILIES:
            raise ValueError(f"unknown widget field {key!r}; per-family overrides "
                             f"must name a family: {list(WIDGET_FAMILIES)}")
        out[name] = _as_scene(value, f"widget {name} scene")
    if "scene" not in out and not set(out) & set(WIDGET_FAMILIES):
        raise ValueError(f"widget {id!r} has no scene — pass scene= or at least "
                         f"one per-family override")
    return out


def island(compact_leading=None, compact_trailing=None, minimal=None, expanded=None):
    """The Dynamic Island regions.

    `compact_leading`, `compact_trailing` and `minimal` take exactly ONE tile —
    the compact presentations are a few points wide and a scene cannot fit.
    `expanded` is a dict of `leading`/`trailing`/`center` (one tile or a scene)
    and `bottom` (a scene). Keep the bottom to two rows; the island clips."""
    out = {}
    for name, value in (("compactLeading", compact_leading),
                        ("compactTrailing", compact_trailing),
                        ("minimal", minimal)):
        if value is None:
            continue
        if not isinstance(value, dict) or "tile" not in value:
            raise ValueError(f"island {name} takes exactly one tile — the compact "
                             f"presentations have no room for a scene")
        out[name] = value
    if expanded is not None:
        if not isinstance(expanded, dict):
            raise ValueError("expanded must be a dict of island regions")
        region_out = {}
        for key, value in expanded.items():
            name = _camel(key)
            if name not in ISLAND_REGIONS:
                raise ValueError(f"unknown expanded region {key!r}; allowed: "
                                 f"{list(ISLAND_REGIONS)}")
            if value is None:
                continue
            if name == "bottom":
                region_out[name] = _as_scene(value, "expanded.bottom")
            elif isinstance(value, dict) and "tile" in value:
                region_out[name] = value
            else:
                region_out[name] = _as_scene(value, f"expanded.{name}")
        if region_out:
            out["expanded"] = region_out
    if not out:
        raise ValueError("island() needs at least one region")
    return out


def live(tier=None, activity=None, widgets=None, controls=None, background=None):
    """The `live` block — how fresh each surface should be.

    `tier` is a preset (:data:`LIVE_TIERS`, default `fresh`) and the sub-dicts
    override individual fields of it. snake_case keys are translated, so
    `activity=dict(remote_cadence=5, start="onConnect")` and
    `widgets=dict(refresh="push", pull_every=900)` both work.

    The floors are enforced by the app *and* the relay, so asking for a faster
    cadence than a tier allows does not get you one — it gets you the floor and a
    diagnostic."""
    out = {}
    if tier is not None:
        out["tier"] = _choice(tier, LIVE_TIERS, "live.tier")
    for name, value, allowed in (
            ("activity", activity,
             {"cadence", "remoteCadence", "stale", "priority", "start"}),
            ("widgets", widgets, {"refresh", "pullEvery", "stale"}),
            ("controls", controls, {"refresh"}),
            ("background", background, {"silentPush"})):
        if value is None:
            continue
        if not isinstance(value, dict):
            raise ValueError(f"live.{name} must be a dict")
        block = {}
        for key, item in value.items():
            field = _camel(key)
            if field not in allowed:
                raise ValueError(f"unknown live.{name} field {key!r}; allowed: "
                                 f"{sorted(allowed)}")
            if field in ("cadence", "remoteCadence", "stale", "pullEvery"):
                _number(item, f"live.{name}.{field}")
            elif field == "priority":
                _choice(item, ("immediate", "opportunistic"), f"live.{name}.priority")
            elif field == "start":
                _choice(item, ("onConnect", "remote", "never"), "live.activity.start")
            elif field == "refresh":
                allowed_refresh = ("push", "pull", "app") if name == "widgets" else ("push", "app")
                _choice(item, allowed_refresh, f"live.{name}.refresh")
            elif field == "silentPush" and not isinstance(item, bool):
                raise ValueError("live.background.silentPush must be a bool")
            block[field] = item
        if block:
            out[name] = block
    if not out:
        raise ValueError("live() needs a tier or at least one surface block")
    return out


# ── Control Center controls ──────────────────────────────────────────────────

def state(value, label=None, icon=None, tint=None):
    """One step of a `cycle`: the value it sends and how the button looks there.

    `cc_cycle(..., states=[state("off", "Off", "fan"), state("high", "High",
    "fan.fill", "#0A84FF")])`. The `on`/`off` faces of a toggle carry no value —
    pass those as plain `{"label", "icon", "tint"}` dicts."""
    out = _compact((("value", value), ("label", label), ("icon", icon), ("tint", tint)))
    if not out:
        raise ValueError("a state needs at least a value or a label")
    return out


def _style(value, field):
    """Accept a `{label, icon, tint}` dict for an on/off face."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a dict of label/icon/tint")
    unknown = sorted(set(value) - {"label", "icon", "tint"})
    if unknown:
        raise ValueError(f"unknown {field} key(s) {unknown}; allowed: "
                         f"['icon', 'label', 'tint']")
    return dict(value)


def _cc(kind, id, label, icon, tint, control, event, payload,
        value_control=None, value_label=None, **rest):
    if not isinstance(id, str) or not id:
        raise ValueError("a glance control needs a non-empty id")
    # Key order follows glance.md's own examples, so a built block and a
    # hand-written one diff cleanly against each other.
    out = {"id": id, "kind": kind}
    out.update(_compact((("label", label), ("icon", icon), ("tint", tint),
                         ("control", _control_id(control)))))
    out.update(rest)
    out.update(_compact((
        ("valueControl", _control_id(value_control, field="value_control")),
        ("valueLabel", value_label),
        ("event", event), ("payload", payload))))
    if event is None and payload is not None:
        raise ValueError(f"control {id!r}: payload without event — an action needs "
                         f"the verb the relay forwards (usually 'broadcast_request')")
    return out


def cc_toggle(id, label=None, control=None, *, on=None, off=None, icon=None,
              tint=None, value_control=None, value_label=None, event=None,
              payload=None):
    """A Control Center / Action-button toggle mirroring a layout control.

    `on`/`off` style each state — `on={"label": "Lit", "icon": "lightbulb.fill",
    "tint": "#FFD60A"}`. `value_control` shows a DIFFERENT control's formatted
    value as the toggle's value label (a lux reading beside a lights toggle), and
    `value_label` templates it with `{{value}}`.

    Without `event` the press sends the bound control's own action, which is
    almost always what you want."""
    extra = _compact((("on", _style(on, "on")), ("off", _style(off, "off"))))
    return _cc("toggle", id, label, icon, tint, control, event, payload,
               value_control=value_control, value_label=value_label, **extra)


def cc_button(id, label=None, control=None, *, icon=None, tint=None, event=None,
              payload=None, value=None):
    """A one-shot Control Center / Action-button press.

    Either bind a layout `control` (its own action fires) or pass `event` +
    `payload` for an explicit MeshSocket action. `value` sends a fixed value
    through the bound control's action."""
    extra = {} if value is None else {"value": value}
    return _cc("button", id, label, icon, tint, control, event, payload, **extra)


def cc_cycle(id, label=None, control=None, *, states, icon=None, tint=None,
             value_control=None, value_label=None, event=None, payload=None):
    """A button that walks a layout control through `states` in order.

    This is what a picker or segmented control becomes outside the app — iOS has
    no multi-state control in Control Center. `states` is at least two
    `{"value", "label"?, "icon"?, "tint"?}` entries (see :func:`state`); the
    button shows the current one and a press sends the next."""
    if isinstance(states, dict) or not isinstance(states, (list, tuple)):
        raise ValueError("cycle states must be a list of state dicts")
    out_states = []
    for index, item in enumerate(states):
        if not isinstance(item, dict) or "value" not in item:
            raise ValueError(f"cycle state {index} needs a 'value' "
                             f"— build it with state(value, label, icon)")
        out_states.append(dict(item))
    if len(out_states) < 2:
        raise ValueError("a cycle needs at least two states — one state is a button")
    if control is None:
        raise ValueError("a cycle drives a layout control — pass control=")
    return _cc("cycle", id, label, icon, tint, control, event, payload,
               value_control=value_control, value_label=value_label,
               states=out_states)


def cc_step(id, label=None, control=None, *, delta, icon=None, tint=None,
            value_control=None, value_label=None, event=None, payload=None):
    """A button that adds `delta` to a layout control, clamped to its min/max.

    This is what a slider or stepper becomes outside the app. Negative `delta`
    decrements — a pair of these is the usual `−`/`+`."""
    if control is None:
        raise ValueError("a step drives a layout control — pass control=")
    _number(delta, "delta")
    return _cc("step", id, label, icon, tint, control, event, payload,
               value_control=value_control, value_label=value_label, delta=delta)


def cc_set(id, label=None, control=None, *, value, icon=None, tint=None,
           value_control=None, value_label=None, event=None, payload=None):
    """A button that sets a layout control to a fixed `value` (a scene preset)."""
    if control is None:
        raise ValueError("a set drives a layout control — pass control=")
    if value is None:
        raise ValueError("a set needs the value it sends — pass value=")
    return _cc("set", id, label, icon, tint, control, event, payload,
               value_control=value_control, value_label=value_label, value=value)


# ── normalisation (used by Layout.glance) ────────────────────────────────────

def normalize(value):
    """Deep-copy a glance fragment, replacing `Layout` control handles with ids.

    An author who built a block by hand — `{"tile": "gauge", "control": nozzle}` —
    gets the same result as one who used :func:`tile`, so a handle never reaches
    the JSON as an unserialisable object."""
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize(item) for item in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    cid = getattr(value, "id", None)
    if isinstance(cid, str) and cid:
        return cid
    return value
