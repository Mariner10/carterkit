---
type: glance
label: Glance Surfaces
icon: platter.filled.top.and.arrow.up.iphone
category: system
fields:
  - name: enabled
    type: bool
    description: false suppresses every surface, including the auto-derived glance (default true)
  - name: title
    type: string
    description: Surface title (defaults to headerTitle / name)
  - name: icon
    type: string
    description: SF Symbol glyph for the layout (island leading slot, widget header)
  - name: tint
    type: string
    description: Hex accent for the surfaces (defaults to accentColor)
  - name: hero
    type: string
    description: Control id of the one value that represents the layout on the smallest surfaces
  - name: slots
    type: string[]
    description: Up to 3 control ids for secondary readouts
  - name: liveActivity
    type: bool
    description: Start a Live Activity (Dynamic Island + lock screen) while the layout is connected (default false)
  - name: controls
    type: object[]
    description: Control Center / lock-screen / Action-button controls (toggle, button, cycle, step, set)
  - name: live
    type: object
    description: How live each surface is — tier plus per-surface cadences, stale windows and refresh paths
  - name: widgets
    type: object[]
    description: Home/lock-screen widgets defined as tile scenes
  - name: island
    type: object
    description: Dynamic Island regions defined as tiles (compact, minimal, expanded)
  - name: lockScreen
    type: object
    description: Lock-screen Live Activity banner scene (defaults to island.expanded.bottom)
---

A layout already says what matters: its controls. The `glance` block projects them
onto every iOS surface *outside* the app — Home and Lock Screen widgets, the
Dynamic Island, the lock-screen Live Activity banner, StandBy, the watch Smart
Stack, CarPlay, and Control Center / the Action button — and keeps them live
**while the app is closed or force-quit**. The same JSON vocabulary as the layout:
tiles bound to control ids.

Every field is optional. A layout with no `glance` block still gets a best-effort
glance (hero + slots picked from gauges, rings, lights and server-fed numerics,
plus Control Center tiles derived from its own buttons, toggles, sliders and
steppers). Add the block when you want to choose.

## Definition

```json
"glance": {
  "title": "Printer", "icon": "printer.fill", "tint": "#FF9F0A",
  "hero": "nozzle", "slots": ["bed", "progress", "state"],
  "liveActivity": true,
  "live": { "tier": "fresh" },
  "controls": [
    { "id": "lights", "kind": "toggle", "label": "Lights", "control": "lights-toggle",
      "on":  { "label": "Lit",  "icon": "lightbulb.fill", "tint": "#FFD60A" },
      "off": { "label": "Dark", "icon": "lightbulb" } },
    { "id": "fan", "kind": "cycle", "label": "Fan", "control": "fan-mode",
      "states": [ { "value": "off",  "label": "Off",  "icon": "fan" },
                  { "value": "low",  "label": "Low",  "icon": "fan", "tint": "#64D2FF" },
                  { "value": "high", "label": "High", "icon": "fan.fill", "tint": "#0A84FF" } ] },
    { "id": "fan-up", "kind": "step", "label": "Fan +10", "control": "fan-speed", "delta": 10 }
  ],
  "widgets": [
    { "id": "temps", "title": "Temps", "families": ["systemMedium", "accessoryRectangular"],
      "scene": { "rows": [
        [ { "tile": "gauge", "control": "nozzle" }, { "tile": "gauge", "control": "bed" } ],
        [ { "tile": "sparkline", "control": "nozzle", "span": 2 } ],
        [ { "tile": "toggle", "control": "lights-toggle" }, { "tile": "step", "control": "fan-speed", "delta": 10 } ]
      ] } }
  ],
  "island": {
    "compactLeading":  { "tile": "icon", "effect": "bounce" },
    "compactTrailing": { "tile": "ring", "control": "progress" },
    "minimal":         { "tile": "light", "control": "state" },
    "expanded": {
      "leading":  { "tile": "icon" }, "trailing": { "tile": "freshness" },
      "center":   { "tile": "timer", "control": "eta" },
      "bottom":   { "rows": [ [ { "tile": "gauge", "control": "nozzle" }, { "tile": "gauge", "control": "bed" } ],
                              [ { "tile": "button", "control": "pause" }, { "tile": "step", "control": "fan-speed", "delta": 10 } ] ] }
    }
  }
}
```

## What iOS allows (read this before designing)

| Surface | Interaction | Motion | Hard limits |
|---|---|---|---|
| Control Center, lock-screen corners, Action button | **toggle** and **button** only — iOS has no slider or text control here. A slider becomes `step`/`set` buttons; a multi-state picker becomes a `cycle` button. | none | the user places every control by hand; the app can only *offer* them |
| Widgets (Home, Lock Screen, StandBy, CarPlay) | `toggle`, `button`, `step` tiles | numeric roll (`numericText`), symbol effects on change, timers | no scrolling, no free-running animation, refresh budgeted by iOS |
| Dynamic Island / lock-screen banner (Live Activity) | same interactive tiles (two-ish fit in the expanded bottom) | numeric roll, symbol effects on change, add/remove transitions, self-ticking timers and rings | 4 KB of state per update; 8 h max session; the user can disable Live Activities per app |

Custom `withAnimation` / `.animation` are ignored by the system on every one of
these surfaces. The `effect`, `transition`, `timer` and numeric tiles below are the
motion that *does* work — Apple's own choreography, keyed to your values.

## Control Center controls (`controls[]`)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable id within the layout (the registry key is `<layoutId>#<id>`) |
| `kind` | string | `toggle` · `button` (default) · `cycle` · `step` · `set` |
| `label` / `icon` | string | Gallery + control appearance (SF Symbol) |
| `control` | string | Layout control this tile mirrors and drives. Required for `cycle`/`step`/`set`; optional for `toggle`/`button`. Its live value is what the tile shows, and by default its own `action` (with `{{value}}` substituted) is what a press sends. |
| `event` / `payload` | string / object | Explicit MeshSocket action instead of the bound control's (`{{value}}` substituted; toggles also merge `{"value": <bool>}`) |
| `on` / `off` | object | `{ "label", "icon", "tint" }` styling per toggle state |
| `valueControl` | string | Show THIS control's formatted value as the toggle's value label (e.g. a lux reading beside the lights toggle) |
| `valueLabel` | string | Template over the value label; `{{value}}` is the bound (or `valueControl`) display value |
| `states` | object[] | `cycle`: `{ "value", "label", "icon", "tint" }` in order; a press sends the next state and the button shows the current one |
| `delta` | number | `step`: added to the control's current value (negative to decrement), clamped to the control's `min`/`max` |
| `value` | any | `set`: the value sent |

Presses work with the app closed: the control posts straight to the relay
(`POST /mesh/broadcast`) with the layout's own credential, exactly the frame the
in-app control would send. Offline presses queue for 24 h and deliver when the
layout next connects. The rendered state only flips once the relay confirms the
frame was published — a press that reached nothing is rolled back and reported.

## Tiles

Widgets, the island and the lock-screen banner are all **scenes**: rows of tiles.

```json
{ "rows": [ [ { "tile": "gauge", "control": "nozzle" }, { "tile": "value", "control": "bed", "span": 1 } ],
            [ { "tile": "sparkline", "control": "nozzle", "span": 2 } ] ] }
```

| Tile | Shows | Binds |
|------|-------|-------|
| `value` | the formatted value, big; numbers roll | any control |
| `gauge` / `ring` / `bar` | arc gauge / capacity ring / linear bar | numeric with `min`/`max` |
| `light` | status dot + state text (`statusColors`) | statusLight or string |
| `sparkline` | recent history (up to 24 points) | numeric |
| `text` / `icon` / `spacer` | static label / SF Symbol / flexible space | — (an `icon` may bind a control whose string value names the symbol) |
| `timer` | a self-ticking clock counting to or from a unix-seconds value | numeric |
| `freshness` | connection dot + age | — |
| `toggle` | interactive on/off, sends the control's action | toggle control |
| `button` | interactive press, sends the control's action (or inline `event`/`payload`) | button control |
| `step` | `−`/`+` buttons (`delta`) or `presets` | slider / stepper |
| `open` | deep-links into the layout (`tab` optional) | — |

| Tile field | Type | Description |
|------|------|-------------|
| `control` | string | Layout control id. Unknown id ⇒ the tile is omitted, never a crash |
| `label`, `icon`, `tint`, `format` | string | Overrides of the control's label / symbol / hex tint / `formatValue` |
| `span` | number | Columns spanned (default 1) |
| `delta`, `presets`, `value`, `event`, `payload`, `tab` | — | Per-tile action parameters (see the tile table) |
| `effect` | string | Symbol effect played **once per value change**: `bounce` (default for icons) · `pulse` · `wiggle` · `rotate` · `breathe` · `variableColor` |
| `transition` | string | When the tile appears or disappears: `opacity` (default) · `slide` · `push` · `move` |

## Widgets (`widgets[]`)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable id; the widget gallery offers "<title> · <layout>" per id |
| `title` / `icon` | string | Gallery name and glyph |
| `families` | string[] | Any of `systemSmall` `systemMedium` `systemLarge` `systemExtraLarge` `accessoryCircular` `accessoryRectangular` `accessoryInline` |
| `scene` | object | The scene rendered for every family without an override |
| `<family>` | object | Optional per-family scene override, e.g. `"systemSmall": { "rows": [[ … ]] }` |

Without an override, `systemSmall` renders the first row, `accessoryRectangular`
renders the first row as values, `accessoryCircular` the first gauge/ring/value,
and `accessoryInline` "label value" of the first bound tile.

The user adds the **CAR-TER Scene** widget and picks a scene; the zero-config
**Layout Glance** (hero + slots) and **Control Value** (any single control) widgets
remain for layouts that declare no `widgets`.

## Dynamic Island and lock screen (`island`, `lockScreen`)

| Region | Takes | Default |
|--------|-------|---------|
| `compactLeading` | one tile | layout icon (bounces on update) |
| `compactTrailing` | one tile | the hero value / ring / dot |
| `minimal` | one tile | freshness ring around the connection dot |
| `expanded.leading` / `.trailing` / `.center` | one tile or a scene | icon + title / freshness / the LIVE session clock |
| `expanded.bottom` | a scene | hero + slot chips + hero sparkline + two controls |
| `lockScreen` | a scene | `expanded.bottom` |

Requires `"liveActivity": true` (or `live.activity.start`). Keep the expanded
bottom to two rows — the island has a hard height budget and clips.

## Liveness (`live`)

| Tier | Live Activity (in app / remote) | Widgets | Controls | Cost |
|------|------|------|------|------|
| `realtime` | 1 s / 2 s, immediate priority | pushed on change, ≥ 60 s apart | pushed on change | burns the Live Activity and widget budgets; for genuinely live sessions only |
| `fresh` (default) | 1 s / 5 s, immediate | pushed on change, ≥ 5 min apart | pushed on change | safe indefinitely |
| `periodic` | 1 s / 30 s, opportunistic | pulled every `pullEvery` (15 min) | pulled on system reload | near zero |
| `manual` | app-driven only | app-driven only | app-driven only | the old behaviour |

| Field | Type | Description |
|-------|------|-------------|
| `tier` | string | Preset above; explicit fields override it |
| `activity.cadence` / `.remoteCadence` | number | Seconds between updates while the app is open / when pushed by the relay (floors 1 / 2) |
| `activity.stale` | number | Seconds until the surface marks its data stale (default 120, floor 30) |
| `activity.priority` | string | `immediate` (budgeted) or `opportunistic` |
| `activity.start` | string | `onConnect` (default) · `remote` (only a hub starts it, via push-to-start) · `never` |
| `widgets.refresh` | string | `push` (relay pokes the widget, iOS 26) · `pull` (widget fetches on its own schedule) · `app` |
| `widgets.pullEvery` / `.stale` | number | Seconds (floors 300 / 30) |
| `controls.refresh` | string | `push` (iOS 18) or `app` |
| `background.silentPush` | bool | Also wake the app with a silent push on relay updates (heavily throttled by iOS; off by default) |

Floors are enforced by the app *and* the relay; the connection console shows the
granted cadence. A surface always shows how old its data is — a stale window ends
the LIVE clock and greys the freshness dot rather than pretending.

## How values reach a closed app

1. **Live Activity** — the relay pushes the island directly (ActivityKit push, and
   push-to-start for layouts the app is not showing).
2. **Widgets** (iOS 26) and **Control Center controls** (iOS 18) — the relay pokes
   them with a "content changed" push; the surface then pulls the layout's latest
   values from the relay's retained state.
3. **Alert pushes** — any alert rule fire also carries a `glance` refresh (the
   notification extension applies it), which works even after a force-quit.
4. **Bindings** — the relay watches the layout's `listen` syncs on the mesh, so an
   existing hub that just broadcasts telemetry drives every surface with no code
   change (not available in end-to-end-encrypted rooms — there, the hub publishes
   explicitly with `hub.surfaces.publish(...)` in carterkit).

## Notes

- Ids: the relay addresses a layout by its stable `id`; give shared layouts one.
- Everything here is a *request* — the user places widgets and controls, may
  disable Live Activities, and iOS budgets every refresh path.
- Sliders, text entry, scrolling and continuous animation exist only inside the app.
