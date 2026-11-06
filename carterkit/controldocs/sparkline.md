---
type: sparkline
depth: complete
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
io:
  - emits: none
  - receives: value
    role: show
    type: number
    from: [hub, mqtt, http, sensor, store, derive, default]
    says: a number to add to the line as its newest point, or a list of numbers that becomes the whole line
    reacts: a single number joins the right end and the oldest point drops off once the line is full; a list replaces the line, skipping empty entries
    example: 40
    since: next
  - sample: [41, 40, 44, 43, 47, 45]
    next: 48
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
    summary: How many readings the line keeps
    does: Keeps only the newest this-many readings on the line; older ones drop off the left.
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
    summary: How thick the line is
    does: Draws the line this many points thick; when not set it grows with the control's height.
  - name: sparklineFill
    edit: look
    tab: style
    type: bool
    default: false
    description: Fill the area under the line with a gradient
    summary: Shade under the line
    does: Fills the area under the line with a fading tint when on; off leaves just the line.
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
    summary: A soft halo around the line
    does: Adds a soft glow in the line's own color behind it; 0 turns it off.
  - name: lineCap
    edit: look
    depth: hold
    under: sparklineFill
    title: Line ends
    tab: style
    type: enum
    values: [round, butt, square]
    default: round
    description: End shape of the line. Cross-control, same on every control
    summary: Shape of the line's ends
    does: Shapes the two ends of the line as rounded, flat or squared off.
    valueHelp: {"round": "rounded ends and the default", "butt": "flat ends that stop exactly at the last point", "square": "flat ends that extend a little past the last point"}
  - name: colorByValue
    edit: stops
    axis: value
    facet: colorByValue
    tab: style
    type: array
    description: Color zones [{limit, color}] — the line and fill take the zone colour of the value at each height. Overrides tint.
    does: "Colors the line and fill by height: each part takes the color of the zone its value falls in."
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
    summary: Hard or soft color edges
    does: Softens the edges between the color zones, from sharp bands at 0 to one smooth gradient at 1.
  - name: tint
    edit: color
    tab: style
    type: color
    default: "#667eea"
    description: Line and fill color
    summary: Color of the line
    does: Colors the line and its fill; color zones replace it when set.
  - name: label
    depth: surface
    title: Title
    edit: inline
    type: string
    description: Header label (also shows latest value)
    summary: The title and latest number
    does: Shows this text at the top left, with the newest reading at the top right.
  - name: defaultValue
    type: array
    description: Seed series drawn before the first sync (an array of numbers), trimmed to sparklinePoints
    does: Draws these numbers as the line until real readings arrive.
    summary: Starting readings shown until new ones arrive
themeFields:
  - use: cornerRadius
  - use: controlPadding
  - use: surfacePrimary
    summary: The fill behind the control
    does: Paints the control's background in this color, including transparency.
  - use: accentColor
    summary: The main highlight color
    does: Sets the accent color used for the control's tint when it has none of its own.
  - use: secondaryColor
    summary: Color of the quieter text
    does: Colors the label and other secondary text.
  - use: borderColor
    summary: Color of the outline
    does: Colors the control's border line.
  - use: borderWidth
    does: Sets the border line thickness from none (0) to 5 points.
  - use: labelFontSize
    summary: Size of the label text
    does: Sets the label's text size from 8 to 24 points.
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
A filled trend of the last 100 room temperatures, arriving live from another device.

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
A bare green line of the last 30 CPU readings with no title.

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
A 48-hour forecast curve that is replaced whole on every poll.

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

### Colored zones with a glow
Color the line green, amber or red by how high it is, softly blended, with a glowing edge and a seed series so it shows before data arrives.
```json
{
  "type": "sparkline",
  "id": "load-zones",
  "position": [0, 0],
  "span": [2, 2],
  "label": "Load",
  "sparklinePoints": 60,
  "sparklineFill": true,
  "lineWidth": 3,
  "glowRadius": 8,
  "lineCap": "round",
  "colorByValue": [{ "limit": 50, "color": "#34C759" }, { "limit": 80, "color": "#FF9F0A" }, { "limit": 100, "color": "#FF3B30" }],
  "colorBlend": 0.5,
  "defaultValue": [20, 35, 30, 55, 70, 62, 85]
}
```

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
