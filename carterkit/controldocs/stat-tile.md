---
type: statTile
label: Stat Tile
icon: number.square
category: controls
defaultSpan: [3, 2]
addIntent: show
friendlyName: Stat tile
oneLiner: A big number, its change, and a faint trend
starterPreset: {"label": "Downloads","unit": "today","statTileConfig": {"reference": 1000}}
fields:
  - name: label
    title: Title
    type: string
    description: Title above the number
  - name: hideLabel
    type: bool
    default: false
    description: Hide the title
  - name: unit
    title: Unit
    type: string
    description: "Measurement unit the value arrives in ([[values#Units]] name or symbol, e.g. milliseconds, celsius). Shown small beside the number and converted to the device locale; thresholds, reference and delta stay in this unit. Unknown strings show literally."
  - name: formatValue
    title: Number format
    simple: hide
    tab: data
    type: string
    description: Number format for the big number (see the formatValue table, e.g. decimal:1)
  - name: step
    title: Decimal places
    bounds: none
    type: number
    description: Determines decimal formatting of the number when formatValue is unset
  - name: sparklinePoints
    title: History length
    min: 5
    max: 500
    step: 5
    type: number
    default: 50
    description: Max values kept in the faint history sparkline
  - name: tint
    title: Color
    tab: style
    type: color
    description: Sparkline colour when no thresholds are set
  - name: hideBackground
    tab: style
    type: bool
    default: false
    description: Remove the card (and its threshold tint)
  - name: animation
    title: Motion
    tab: style
    type: enum
    values: [smooth, snappy, bouncy, gentle, instant]
    description: Motion profile for the number roll
  - name: reference
    bounds: none
    title: Compare against
    tab: data
    type: number
    description: The value the change is measured against (yesterday, target…)
    group: statTileConfig
  - name: referencePath
    title: Live reference path
    tab: data
    type: string
    description: Dot path in the same payload as the value to a live reference; overrides reference once it arrives
    group: statTileConfig
  - name: deltaMode
    title: Change shown as
    type: enum
    values: [percent, absolute]
    default: percent
    description: Percent change, or the absolute difference in the value's unit
    group: statTileConfig
  - name: invertDelta
    title: Up is bad
    type: bool
    default: false
    description: Colour a rise red and a fall green (latency, error rate)
    group: statTileConfig
  - name: thresholds
    title: Color zones
    type: array
    description: "Background bands [{limit, color}], gauge segment semantics"
    summary: Background colors for different ranges of values
    group: statTileConfig
  - name: criticalAbove
    bounds: none
    title: Critical at or above
    type: number
    description: At or above this value the tile fills solid with its band colour
    group: statTileConfig
  - name: criticalBelow
    bounds: none
    title: Critical at or below
    type: number
    description: At or below this value the tile fills solid with its band colour
    group: statTileConfig
  - name: showSparkline
    title: Show trend
    tab: style
    type: bool
    default: true
    description: Draw the faint history sparkline under the number
    group: statTileConfig
themeFields:
  - name: cornerRadius
    title: Corner roundness
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
  - name: controlPadding
    title: Inner spacing
    min: 0
    max: 24
    step: 1
    type: number
    default: 8
    description: Internal padding
  - name: surfacePrimary
    title: Background color
    type: color
    default: #FFFFFF0F
    description: Background fill
  - name: accentColor
    title: Accent color
    type: color
    default: #667eea
    description: Accent/tint color
  - name: foregroundColor
    title: Text color
    type: color
    default: #FFFFFF
    description: Primary text color
  - name: secondaryColor
    title: Second text color
    type: color
    default: #FFFFFF99
    description: Secondary text color
  - name: borderColor
    title: Border color
    type: color
    default: #FFFFFF1A
    description: Border color
    summary: The outline around the control
  - name: borderWidth
    title: Border thickness
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
  - name: labelFontSize
    title: Title text size
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
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
| `tint` | color | accent | Sparkline colour when no `thresholds` are set |
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

## Behavior
- The number rolls with the native numeric-text transition (via the shared numeric readout); the band tint cross-fades.
- Tapping does nothing — the tile is display-only. Add a `longPressGroup` for detail.
- VoiceOver reads the title, the value with its unit, and "up 12.4%" / "down" / "unchanged".
- Free control (no Pro unlock).

## Related
- [[gauge]] — the same segment semantics on a dial
- [[sparkline]] — the history on its own
- [[label]] — a number without the chrome
