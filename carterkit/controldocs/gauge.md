---
type: gauge
label: Gauge
icon: gauge.medium
category: controls
defaultSpan: [2, 2]
addIntent: show
friendlyName: Dial
oneLiner: A number on a dial, from low to high
addRank: 3
starterPreset: {"label": "Dial","min": 0,"max": 100}
lookFormats: [{"id": "dial","name": "Dial","symbol": "gauge.medium","set": {"type": "gauge","gaugeStyle": "half","arcAngle": null}},{"id": "ring","name": "Ring","symbol": "circle.circle","set": {"type": "gauge","gaugeStyle": "full","arcAngle": null}},{"id": "bar","name": "Bar","symbol": "chart.bar.fill","set": {"type": "progressRing","progressStyle": "bar"}}]
lookPresets: [{"id": "standard","name": "Standard","symbol": "gauge.medium","set": {"arcThickness": null,"hideValue": null}},{"id": "bold","name": "Bold","symbol": "circle.lefthalf.filled","set": {"arcThickness": 16,"hideValue": null}},{"id": "quiet","name": "Quiet","symbol": "eye.slash","set": {"hideValue": true}}]
fields:
  - name: animation
    title: Motion
    tab: style
    type: enum
    values: [smooth, snappy, bouncy, gentle, instant]
    description: Motion profile for value changes
  - name: min
    title: Lowest value
    default: 0
    bounds: none
    type: number
    description: Minimum value
    summary: Where the dial starts
  - name: max
    title: Highest value
    default: 100
    bounds: none
    type: number
    description: Maximum value
    summary: Where the dial fills up
  - name: gaugeStyle
    title: Shape
    tab: style
    type: enum
    values: [half, full]
    default: half
    description: "Shorthand: half = 180° arc, full = 360° circle"
  - name: segments
    title: Color zones
    type: array
    description: Color zone breakpoints [{limit, color}]
    summary: Colors for different ranges of values
  - name: colorBlend
    title: Zone blending
    tab: style
    min: 0
    max: 1
    step: 0.05
    type: number
    default: 0
    description: "How much the segment colors blend, 0–1. 0 = hard boundaries, 1 = one smooth gradient, between = feathered edges. Needs segments."
  - name: tint
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: Primary arc fill color (when no segments)
  - name: label
    title: Title
    type: string
    description: Text below the gauge
  - name: icon
    title: Symbol
    type: string
    description: SF Symbol in the center
  - name: step
    title: Decimal places
    bounds: none
    type: number
    default: 1
    description: Determines decimal formatting of center value
  - name: arcAngle
    title: Arc length
    tab: style
    min: 1
    max: 360
    step: 1
    type: number
    default: 180
    description: Arc sweep in degrees (1-360)
  - name: arcRotation
    title: Arc turn
    tab: style
    min: -180
    max: 180
    step: 1
    type: number
    default: 0
    description: Rotates the arc start position in degrees
  - name: arcThickness
    title: Arc thickness
    tab: style
    min: 1
    max: 40
    step: 1
    type: number
    default: auto
    description: Arc stroke width in points. Omit to auto-scale with the gauge's size.
  - name: hideValue
    title: Hide the number
    type: bool
    default: false
    description: Show just the arc — hide the center value
  - name: unit
    title: Unit
    type: string
    description: "Measurement unit the value arrives in ([[values#Units]] name or symbol, e.g. celsius, km/h). The readout converts to the device locale (°C → °F in the US); min, max and segments stay in this unit, so the arc is the same everywhere. Unknown strings show literally."
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

# Gauge

A circular arc dial showing a synced numeric value within a range. Read-only.

## Type
`"gauge"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `min` | number | required | Minimum value |
| `max` | number | required | Maximum value |
| `gaugeStyle` | string | `"half"` | `"half"` (180° arc) or `"full"` (360° circle) |
| `segments` | GaugeSegment[] | — | Color zone breakpoints |
| `tint` | string | `"#667eea"` | Primary arc fill color (when no segments) |
| `label` | string | — | Text below the gauge |
| `icon` | string | — | SF Symbol in the center |
| `step` | number | `1` | Used to determine decimal formatting of center value |
| `arcAngle` | number | `180` | Arc sweep in degrees (1-360) |
| `arcRotation` | number | `0` | Rotates the arc start position in degrees |
| `arcThickness` | number | auto | Arc stroke width in points. Omit to auto-scale with the gauge's size; set for an absolute width |
| `hideValue` | bool | `false` | Show just the arc — hide the center value (pairs with `hideBackground` for a compact glyph) |
| `unit` | string | — | Measurement unit of the value ([[values#Units]]). The center readout converts to the device locale — `"celsius"` reads 70.7°F in the US, 21,5 °C in Germany. `min`, `max` and `segments` stay in this unit, so the arc never moves. Unknown strings are a literal suffix |

> **Note:** `gaugeStyle` is a shorthand alias. `"half"` sets `arcAngle: 180` and `"full"` sets `arcAngle: 360`. When `arcAngle` is set explicitly, it takes precedence over `gaugeStyle`.

> **Sizing:** the arc, stroke, and center value all scale to the gauge's size. A `half` gauge is wide (2:1); a `full` gauge is square (1:1) — give it ~3 `rowSpan` in a 2-D grid so it reads square. See [[grid-dimensions]].

## Gauge Segments

Color zones that change based on the current value:

```json
"segments": [
  { "limit": 60, "color": "#00FF00" },
  { "limit": 80, "color": "#FFAA00" },
  { "limit": 100, "color": "#FF0000" }
]
```

Each segment fills from the previous segment's limit (or min) up to its own limit. The arc is colored according to which segment the value falls within.

## Examples

### Temperature gauge with color zones
```json
{
  "type": "gauge",
  "id": "cpu-temp",
  "position": [0, 0],
  "min": 30,
  "max": 100,
  "gaugeStyle": "half",
  "label": "CPU Temp",
  "icon": "thermometer.medium",
  "segments": [
    { "limit": 60, "color": "#34C759" },
    { "limit": 80, "color": "#FF9500" },
    { "limit": 100, "color": "#FF3B30" }
  ],
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "device": "server" }, "valuePath": "cpu_temp" }]
}
```

### Full circle gauge (battery level)
```json
{
  "type": "gauge",
  "id": "battery",
  "position": [0, 2],
  "min": 0,
  "max": 100,
  "gaugeStyle": "full",
  "tint": "#34C759",
  "icon": "battery.100",
  "label": "Battery",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "device": "rover" }, "valuePath": "battery_pct" }]
}
```

### Gauge with long-press detail
```json
{
  "type": "gauge",
  "id": "room-temp",
  "position": [0, 0],
  "min": 50,
  "max": 100,
  "gaugeStyle": "half",
  "label": "Living Room",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "room": "living" }, "valuePath": "temperature" }],
  "longPressGroup": {
    "position": [0, 0],
    "span": [2, 2],
    "id": "temp-detail",
    "label": "Temperature History",
    "grid": { "columns": 2, "rows": 2 },
    "children": [
      { "type": "sparkline", "id": "temp-history", "position": [0, 0], "span": [1, 2], "tint": "#FF6B6B", "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "room": "living" }, "valuePath": "temperature" }] },
      { "type": "label", "id": "temp-min", "position": [1, 0], "text": "Min: --" },
      { "type": "label", "id": "temp-max", "position": [1, 1], "text": "Max: --" }
    ]
  }
}
```

## Behavior
- Value animates smoothly between updates (smooth profile)
- Center displays the numeric value with animated content transition
- No action — display only (use [[long-press]] for interaction)

## Related
- [[shared-properties]] — Base fields
- [[sync]] — Receiving values
- [[long-press]] — Detail popup on hold
- [[sparkline]] — Often paired in long-press detail views
- [[pie-chart]] — Radial part-of-whole (and spin wheel / radial menu)
- [[radar]] — Multi-axis profiles when one dial isn't enough
