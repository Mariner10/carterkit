---
type: sparkline
label: Sparkline
icon: chart.xyaxis.line
category: controls
defaultSpan: [2, 2]
addIntent: show
pickerCategory: Charts
friendlyName: Trend line
oneLiner: A little line that shows how a number changes
aliases: [trend, mini chart, tiny chart, spark, history, line]
addRank: 5
starterPreset: {"label": "Trend","sparklinePoints": 60}
lookPresets: [{"id": "line","name": "Line","symbol": "chart.xyaxis.line","set": {"sparklineFill": null}},{"id": "filled","name": "Filled","symbol": "chart.line.uptrend.xyaxis","set": {"sparklineFill": true}}]
fields:
  - name: sparklinePoints
    edit: scrub
    depth: hold
    under: sparklineFill
    title: Time window
    min: 5
    max: 500
    step: 5
    type: number
    default: 50
    description: Max data points retained in the buffer
  - name: lineWidth
    edit: scrub
    depth: hold
    under: sparklineFill
    unit: pt
    title: Line width
    tab: style
    min: 0.5
    max: 12
    step: 0.5
    type: number
    description: Line stroke width in points. Omit to scale with the control's height.
  - name: sparklineFill
    edit: look
    tab: style
    type: bool
    default: false
    description: Fill the area under the line with a gradient
  - name: glowRadius
    edit: scrub
    depth: hold
    under: sparklineFill
    title: Glow
    unit: pt
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    default: 0
    description: Soft glow behind the line in its own colour, in points (0 = none). Cross-control, same on every control
  - name: lineCap
    edit: look
    depth: hold
    under: glowRadius
    title: Line ends
    tab: style
    type: enum
    values: [round, butt, square]
    default: round
    description: End shape of the line. Cross-control, same on every control
  - name: colorByValue
    edit: stops
    axis: value
    facet: colorByValue
    tab: style
    type: array
    description: Color zones [{limit, color}] — the line and fill take the zone colour of the value at each height. Overrides tint.
    summary: Colour the line by how high it is
  - name: colorBlend
    facet: colorByValue
    tab: style
    min: 0
    max: 1
    step: 0.05
    type: number
    default: 0
    description: "How much the zone colors blend, 0–1. 0 = hard boundaries, 1 = one smooth gradient. Needs colorByValue."
  - name: tint
    edit: color
    tab: style
    type: color
    default: "#667eea"
    description: Line and fill color
  - name: label
    depth: surface
    title: Title
    edit: inline
    type: string
    description: Header label (also shows latest value)
  - name: defaultValue
    type: array
    description: Seed series drawn before the first sync (an array of numbers), trimmed to sparklinePoints
    summary: Starting readings shown until new ones arrive
themeFields:
  - name: cornerRadius
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
  - name: controlPadding
    min: 0
    max: 24
    step: 1
    type: number
    default: 8
    description: Internal padding
  - name: surfacePrimary
    type: color
    default: #FFFFFF0F
    description: Background fill
  - name: accentColor
    type: color
    default: #667eea
    description: Accent/tint color
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Secondary text color
  - name: borderColor
    type: color
    default: #FFFFFF1A
    description: Border color
  - name: borderWidth
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
  - name: labelFontSize
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
---

# Sparkline

A tiny inline line chart that accumulates synced values over time. Read-only.

## Type
`"sparkline"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `sparklinePoints` | int | `50` | Max data points retained in the buffer |
| `lineWidth` | number | auto | Line stroke width in points, 0.5–12. Omit to scale with the control's height |
| `sparklineFill` | bool | `false` | Fill the area under the line with a gradient |
| `colorByValue` | `[{limit, color}]` | — | Color zones like gauge `segments`: the line and fill take the zone colour of the value at each height (a zone runs up to its `limit`; the last extends upward). Overrides `tint` |
| `colorBlend` | number | `0` | 0 hard zone edges … 1 one smooth gradient. Needs `colorByValue` |
| `tint` | string | `"#667eea"` | Line and fill color |
| `glowRadius` | number | `0` | Soft glow behind the line in its own colour, 0–30 pt (the same attribute on every control that has it) |
| `lineCap` | enum | `round` | End shape of the line: `round`, `butt` or `square` (the same attribute on every control that has it) |
| `label` | string | — | Header label (also shows latest value) |
| `defaultValue` | number or number[] | — | Seed series drawn before the first sync (`[41, 40, 39]`); trimmed to `sparklinePoints`. See [[control-def#defaultValue per type]] |

## Data Flow

Unlike other controls that store a single value, sparklines maintain a **ring buffer** of numeric values in `AppState.sparklineBuffers`. When the buffer exceeds `sparklinePoints`, the oldest value is dropped.

A sync payload feeds that buffer one of two ways, decided by what the `valuePath` resolves to:

| Payload at `valuePath` | Effect |
|---|---|
| a number | Appended as one new point — the live-telemetry case |
| an **array of numbers** | Taken as the whole series, **replacing** the buffer (trimmed to the last `sparklinePoints`) |

The array form is what a forecast or history endpoint returns, and is the same
shape [[chart]] accepts — so `hourly.temperature_2m` works in both. `null`s inside
the array are skipped (feeds pad trailing hours with them). When an array arrives,
the sparkline's header value shows its last element.

The sparkline renders all points in the buffer as a line path, auto-scaling Y to the min/max of the current buffer.

## Examples

### Temperature history
```json
{
  "type": "sparkline",
  "id": "temp-history",
  "position": [0, 0],
  "span": [1, 3],
  "sparklinePoints": 100,
  "sparklineFill": true,
  "tint": "#FF6B6B",
  "label": "Temperature",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "room": "living" }, "valuePath": "temperature" }]
}
```

### Compact sparkline (no label, no fill)
```json
{
  "type": "sparkline",
  "id": "cpu-load",
  "position": [0, 2],
  "sparklinePoints": 30,
  "tint": "#34C759",
  "hideLabel": true,
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "device": "server" }, "valuePath": "cpu_load" }]
}
```

### Forecast series from an HTTP feed
```json
{
  "type": "sparkline",
  "id": "temp-forecast",
  "position": [1, 0],
  "span": [1, 4],
  "sparklinePoints": 48,
  "sparklineFill": true,
  "tint": "#0A84FF",
  "label": "Next 48h",
  "sync": [{ "method": "http", "url": "https://api.open-meteo.com/v1/forecast?latitude=42.36&longitude=-71.06&hourly=temperature_2m", "interval": 900, "valuePath": "hourly.temperature_2m" }]
}
```

The endpoint returns a plain numeric array at that path; each poll replaces the
whole series rather than appending a point.

## Behavior
- A numeric payload appends a point; a numeric array replaces the series
- New data points animate in smoothly
- The Y axis auto-scales to the min/max of current buffer data
- When fewer than 2 points exist, shows a `"--"` placeholder
- The latest value is shown in the header (right side) with animated numeric transition

## On-control editing (C6)

The chart publishes its y range as a value axis and part `label`; `colorByValue` level dots in edit mode ride the line's right edge, bottom = lowest sample, top = highest, and snap to other levels. See `SharedEditorContract.swift`.

## Related
- [[shared-properties]] — Base fields
- [[sync]] — How values are received
- [[gauge]] — Often paired with sparklines in long-press detail views
- [[chart]] — Multi-series bars/lines/areas/scatter when one trend isn't enough
