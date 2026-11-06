---
type: statTile
depth: complete
label: Stat Tile
icon: number.square
category: controls
defaultSpan: [3, 2]
addIntent: show
pickerCategory: Readouts
friendlyName: Stat tile
oneLiner: A big number, its change, and a faint trend
aliases: [kpi, metric, stat, number, counter, big number]
starterPreset: {"label": "Downloads","unit": "today","statTileConfig": {"reference": 1000}}
io:
  - emits: none
  - receives: value
    role: show
    type: number
    from: [hub, mqtt, http, sensor, store, derive, default]
    says: a number to show large, or a list of numbers that becomes the trend and shows its last point
    reacts: the number updates and joins the faint trend under it; a list replaces the trend
    example: 40
    since: next
  - sample: 40
    next: 75
fields:
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Title above the number
    summary: "The caption above the number"
    does: "Shows this text as the tile's title in the title text size."
  - name: hideLabel
    edit: part
    depth: hold
    under: label
    type: bool
    default: false
    description: Hide the title
    summary: "Number without a caption"
    does: "Removes the title line when on, leaving the number alone."
  - name: unit
    edit: inline
    depth: surface
    title: Unit
    type: string
    description: "Measurement unit the value arrives in ([[values#Units]] name or symbol, e.g. milliseconds, celsius). Shown small beside the number and converted to the device locale; thresholds, reference and delta stay in this unit. Unknown strings show literally."
    summary: "What the number is measured in"
    does: "Shows the unit small beside the number in the viewer's local unit, e.g. celsius reads \u00b0F in the US."
  - name: valueSize
    edit: scrub
    depth: hold
    under: unit
    unit: pt
    title: Number size
    tab: style
    min: 14
    max: 80
    step: 1
    type: number
    default: 34
    description: Point size of the big number
    summary: "How big the number is"
    does: "Sets the big number's size from 14 to 80 points."
  - name: formatValue
    title: Number format
    simple: hide
    tab: data
    type: string
    description: Number format for the big number (see the formatValue table, e.g. decimal:1)
    summary: "How the number is written"
    does: "Formats the big number, e.g. decimal:1 shows 72.5 and decimal:0 shows 73."
  - name: step
    title: Decimal places
    bounds: none
    type: number
    description: Determines decimal formatting of the number when formatValue is unset
    summary: "How many digits after the point"
    does: "Rounds the number when no format is set, e.g. 1 shows 72.5 and 0 shows 73."
  - name: sparklinePoints
    title: History length
    min: 5
    max: 500
    step: 5
    type: number
    default: 50
    description: Max values kept in the faint history sparkline
    summary: "How far back the faint trend reaches"
    does: "Keeps the last 5 to 500 readings in the trend line; more points show a longer history."
  - name: lineWidth
    edit: scrub
    depth: hold
    under: tint
    unit: pt
    title: Line width
    tab: style
    min: 0.5
    max: 12
    step: 0.5
    type: number
    default: 2
    description: Stroke width of the faint trend line, in points
    summary: "How thick the trend line is"
    does: "Sets the trend line stroke from 0.5 to 12 points."
  - name: tint
    edit: color
    title: Color
    tab: style
    type: color
    description: Sparkline colour when no thresholds are set
    summary: "The trend line color"
    does: "Paints the faint trend line in one color when there are no color zones."
  - name: glowRadius
    edit: scrub
    depth: hold
    under: tint
    title: Glow
    unit: pt
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    default: 0
    description: Soft glow behind the history curve in its own colour, in points (0 = none). Cross-control, same on every control
    summary: "A soft halo around the trend line"
    does: "Adds a glow behind the trend line from 0 (off) to 30 points wide."
  - name: lineCap
    edit: look
    depth: hold
    under: tint
    title: Line ends
    tab: style
    type: enum
    values: [round, butt, square]
    default: round
    description: End shape of the history curve. Cross-control, same on every control
    summary: "The shape of the trend line's ends"
    does: "Rounds, flattens or squares the two ends of the trend line."
    valueHelp: {"round": "soft rounded ends", "butt": "flat ends cut exactly at the data point", "square": "flat ends that stick out half a stroke past the data point"}
  - name: hideBackground
    tab: style
    type: bool
    default: false
    description: Remove the card (and its threshold tint)
    summary: "The card behind the number"
    does: "Removes the card fill and its zone tint when on so the number floats on the layout."
  - name: animation
    title: Motion
    tab: style
    type: enum
    values: [smooth, snappy, bouncy, gentle, instant]
    description: Motion profile for the number roll
    summary: "How the number moves when it changes"
    does: "The number rolls to each new value; instant swaps it with no roll."
    valueHelp: {"smooth": "an even roll and the default", "snappy": "a quick roll that settles fast", "bouncy": "overshoots slightly then springs back", "gentle": "a slow and soft roll", "instant": "swaps straight to the new number with no roll"}
  - name: reference
    chip: Compare
    bounds: none
    title: Compare against
    tab: data
    type: number
    description: The value the change is measured against (yesterday, target…)
    summary: "The number to compare with"
    does: "Sets the baseline in the tile's unit; the arrow and change show the value minus this."
    group: statTileConfig
  - name: referencePath
    title: Live reference path
    tab: data
    type: string
    description: Dot path in the same payload as the value to a live reference; overrides reference once it arrives
    summary: "Where a live comparison number comes from"
    does: "Reads the baseline from this dot path in the same data as the value and replaces Compare against once it arrives."
    group: statTileConfig
  - name: deltaMode
    title: Change shown as
    type: enum
    values: [percent, absolute]
    default: percent
    description: Percent change, or the absolute difference in the value's unit
    summary: "How the change is written"
    does: "Shows the change as a percent of the baseline or as the plain difference in the tile's unit."
    valueHelp: {"percent": "change as a percent of the baseline", "absolute": "change as the plain difference in the value's unit"}
    group: statTileConfig
  - name: invertDelta
    title: Up is bad
    type: bool
    default: false
    description: Colour a rise red and a fall green (latency, error rate)
    summary: "Swap good and bad colors"
    does: "When on a rise is drawn red and a fall green instead of the reverse."
    group: statTileConfig
  - name: thresholds
    title: Color zones
    type: array
    description: "Background bands [{limit, color}], gauge segment semantics"
    summary: "Background colors for different ranges of values"
    does: "Tints the card with the color of the zone the value sits in, e.g. green to 250 then amber to 600 then red."
    group: statTileConfig
  - name: criticalAbove
    bounds: none
    title: Critical at or above
    type: number
    description: At or above this value the tile fills solid with its band colour
    summary: "The value where the tile turns solid"
    does: "At or above this value the whole tile fills solid with its zone color and white text."
    group: statTileConfig
  - name: criticalBelow
    bounds: none
    title: Critical at or below
    type: number
    description: At or below this value the tile fills solid with its band colour
    summary: "The low value where the tile turns solid"
    does: "At or below this value the whole tile fills solid with its zone color and white text."
    group: statTileConfig
  - name: showSparkline
    edit: part
    depth: hold
    under: tint
    title: Show trend
    tab: style
    type: bool
    default: true
    description: Draw the faint history sparkline under the number
    summary: "The faint trend under the number"
    does: "Draws the recent-history line under the number when on and hides it when off."
    group: statTileConfig
themeFields:
  - use: cornerRadius
    does: "Rounds the tile's corners from square (0) to 30 points."
  - use: controlPadding
    does: "Adds 0 to 24 points between the tile's edge and its content."
  - use: surfacePrimary
    summary: "The fill behind the tile"
    does: "Paints the tile's background in this color including transparency."
  - use: accentColor
    does: "Tints the trend line wherever no color is set directly."
  - use: foregroundColor
    does: "Colors the big number and the title."
  - use: secondaryColor
    summary: "The quieter text color"
    does: "Colors the unit and the flat change text."
  - use: borderColor
    does: "Draws the tile's outline in this color."
  - use: borderWidth
  - use: labelFontSize
    does: "Sets the title's text size from 8 to 24 points."
---

# Stat Tile

One number, told whole: the value large with its unit, a change arrow and percent against a reference, a background tinted by the threshold band the value sits in, and a faint sparkline of recent values under it. The one-control replacement for a label + sparkline + status light stacked by hand. Read-only.

## Type
`"statTile"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|---|---|---|---|
| `label` | string | — | Title above the number |
| `unit` | string | — | Measurement unit of the value ([[values#Units]]). Drawn small beside the number and converted to the device locale — `"celsius"` reads °F in the US. Thresholds, reference and delta stay in this unit. Unknown strings are a literal suffix (`"today"`, `"users"`) |
| `formatValue` | string | — | Number format for the big number (`decimal:1`, `decimal:0`, …) |
| `sparklinePoints` | number | `50` | How many recent values the faint history keeps |
| `valueSize` | number | `34` | Point size of the big number, 14–80 |
| `lineWidth` | number | `2` | Stroke width of the faint trend line, 0.5–12 pt |
| `tint` | color | accent | Sparkline colour when no `thresholds` are set |
| `glowRadius` | number | `0` | Soft glow behind the history curve in its own colour, 0–30 pt (the same attribute on every control that has it) |
| `lineCap` | enum | `round` | End shape of the history curve: `round`, `butt` or `square` (the same attribute on every control that has it) |
| `statTileConfig.reference` | number | — | The value the change is measured against |
| `statTileConfig.referencePath` | string | — | Dot path, in the same payload as the value, to a live reference (e.g. `"previous"`). Overrides `reference` once it arrives |
| `statTileConfig.deltaMode` | string | `"percent"` | `percent` or `absolute` (the difference, in the value's unit) |
| `statTileConfig.invertDelta` | bool | `false` | Up is bad: a rise reads red, a fall green |
| `statTileConfig.thresholds` | GaugeSegment[] | — | Background bands `[{limit, color}]` — same semantics as gauge [[gauge#Gauge Segments]] |
| `statTileConfig.criticalAbove` | number | — | At or above: the tile fills SOLID with its band colour (white text) |
| `statTileConfig.criticalBelow` | number | — | At or below: the tile fills SOLID with its band colour |
| `statTileConfig.showSparkline` | bool | `true` | Draw the faint history under the number |

Every `statTileConfig` field is optional — `{ "type": "statTile", "id": "x" }` is a complete control (the number alone on a plain card).

> **Sizing:** the default `[3, 2]` span (three 56pt rows, half a 4-column phone grid) fits the title, the number, the delta and a strip of history. A `[2, 2]` tile still shows the number and delta; the sparkline takes whatever height is left under the delta line, never more than the lower ~45% of the tile, so it never crosses the number or the percent. Go wide (`[3, 4]`) for a longer trend. See [[grid-dimensions]].

## Data Flow

The tile listens like a gauge: its `sync` delivers a number. Each number also appends to the tile's rolling history (the same buffer a [[sparkline]] uses, capped at `sparklinePoints`); a numeric **array** replaces the history and the number shows its last point.

- **Delta** = value − reference. Percent mode divides by |reference|; a missing reference — or a zero one in percent mode — hides the delta rather than showing ∞ or NaN. A change that rounds to 0.0% shows a flat arrow in the muted colour.
- **Colour:** up is good (green) and down is bad (red) unless `invertDelta` flips them.
- **Thresholds:** sorted by `limit`, the value takes the first band whose limit it does not exceed; below the first → the first band, above the last → the last. The tint is soft by default; `criticalAbove`/`criticalBelow` switch it to a solid fill.

## Examples

### Daily downloads against yesterday
Demonstrates `reference` with `thresholds`: the percent change against 1142 shows under the number and the card tints amber below 500 and green above.
```json
{
  "type": "statTile",
  "id": "downloads",
  "position": [0, 0],
  "span": [3, 2],
  "label": "Downloads",
  "unit": "today",
  "formatValue": "decimal:0",
  "statTileConfig": {
    "reference": 1142,
    "thresholds": [
      { "limit": 500, "color": "#FF9F0A" },
      { "limit": 100000, "color": "#34C759" }
    ]
  },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "stats" }, "valuePath": "downloads" }]
}
```

### Latency where up is bad, with a live reference
Demonstrates `referencePath`, `invertDelta` and `criticalAbove`: the baseline arrives with the value, a rise reads red, and at 600 ms or more the whole tile fills solid red.
```json
{
  "type": "statTile",
  "id": "p95",
  "position": [0, 2],
  "span": [3, 2],
  "label": "p95 latency",
  "unit": "ms",
  "formatValue": "decimal:0",
  "statTileConfig": {
    "referencePath": "p95_prev",
    "invertDelta": true,
    "thresholds": [
      { "limit": 250, "color": "#34C759" },
      { "limit": 600, "color": "#FF9F0A" },
      { "limit": 100000, "color": "#FF453A" }
    ],
    "criticalAbove": 600
  },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "stats" }, "valuePath": "p95" }]
}
```

### Absolute change, no trend
Demonstrates `deltaMode: "absolute"` and `showSparkline: false`: the change reads as a plain difference of users and no history line is drawn.
```json
{
  "type": "statTile",
  "id": "sessions",
  "position": [3, 0],
  "span": [2, 2],
  "label": "Active sessions",
  "unit": "users",
  "statTileConfig": { "reference": 300, "deltaMode": "absolute", "showSparkline": false }
}
```

### Critical when low
Demonstrates `criticalBelow`: at 15 or less the tile fills solid with its band colour, useful for a battery or a stock level.
```json
{ "type": "statTile", "id": "stock", "position": [3, 2], "span": [2, 2], "label": "Stock", "unit": "units",
  "statTileConfig": { "reference": 100, "criticalBelow": 15,
    "thresholds": [ { "limit": 15, "color": "#FF453A" }, { "limit": 40, "color": "#FF9F0A" }, { "limit": 100000, "color": "#34C759" } ] } }
```

### Number alone
Demonstrates the minimal control: with no `statTileConfig` the tile is just a title and a number on a plain card.
```json
{ "type": "statTile", "id": "plain", "position": [0, 0], "span": [2, 2], "label": "Visitors" }
```

### Number size, decimals and no title
Demonstrates `valueSize: 56`, `step: 2` and `hideLabel: true`: a large number with two decimals and the title line removed.
```json
{ "type": "statTile", "id": "big", "position": [0, 0], "span": [3, 2], "label": "Balance", "hideLabel": true, "valueSize": 56, "step": 2, "unit": "usd" }
```

### Converted unit
Demonstrates `unit: "celsius"`: the value arrives in °C but reads °F in the US, while thresholds and reference stay in °C.
```json
{ "type": "statTile", "id": "outside", "position": [0, 0], "span": [3, 2], "label": "Outside", "unit": "celsius", "formatValue": "decimal:1",
  "statTileConfig": { "reference": 18 } }
```

### Trend line style
Demonstrates `sparklinePoints: 120`, `lineWidth: 4`, `tint`, `glowRadius: 10` and `lineCap: "butt"`: a longer, thicker, glowing trend with flat ends.
```json
{ "type": "statTile", "id": "trend", "position": [0, 0], "span": [3, 4], "label": "Power", "unit": "W", "sparklinePoints": 120, "lineWidth": 4, "tint": "#00D4FF", "glowRadius": 10, "lineCap": "butt",
  "statTileConfig": { "reference": 400 } }
```

### Motion and bare card
Demonstrates `animation: "bouncy"` (the number overshoots as it rolls) and `hideBackground: true` (no card or zone tint, so the number floats).
```json
{ "type": "statTile", "id": "floaty", "position": [0, 0], "span": [3, 2], "label": "Score", "animation": "bouncy", "hideBackground": true }
```

### Tile with long-press detail
Demonstrates `longPressGroup`: the tile itself is display-only, so holding it opens a popup with a longer history.
```json
{
  "type": "statTile",
  "id": "cpu-load",
  "position": [0, 0],
  "span": [3, 2],
  "label": "CPU load",
  "unit": "percent",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "device": "server" }, "valuePath": "cpu" }],
  "longPressGroup": {
    "position": [0, 0],
    "span": [2, 2],
    "id": "cpu-detail",
    "label": "CPU history",
    "grid": { "columns": 2, "rows": 2 },
    "children": [
      { "type": "sparkline", "id": "cpu-history", "position": [0, 0], "span": [2, 2], "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "device": "server" }, "valuePath": "cpu" }] }
    ]
  }
}
```

### Themed tile
Demonstrates the theme fields: rounder corners, more inner spacing, custom fill, border and larger title text.
```json
{ "type": "statTile", "id": "theme-demo", "position": [0, 0], "span": [3, 2], "label": "Revenue",
  "theme": { "cornerRadius": 22, "controlPadding": 14, "surfacePrimary": "#1C1C2E", "accentColor": "#34C759", "foregroundColor": "#FFFFFF", "secondaryColor": "#FFFFFF99", "borderColor": "#34C75966", "borderWidth": 2, "labelFontSize": 16 } }
```

## Behavior
- The number rolls with the native numeric-text transition (via the shared numeric readout); the band tint cross-fades.
- Tapping does nothing — the tile is display-only. Add a `longPressGroup` for detail.
- VoiceOver reads the title, the value with its unit, and "up 12.4%" / "down" / "unchanged".
- Free control (no Pro unlock).

## Related
- [[gauge]] — the same segment semantics on a dial
- [[sparkline]] — the history on its own
- [[label]] — a number without the chrome
