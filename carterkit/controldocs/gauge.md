---
type: gauge
depth: complete
label: Gauge
icon: gauge.medium
category: controls
defaultSpan: [2, 2]
addIntent: show
pickerCategory: Readouts
friendlyName: Dial
oneLiner: A number on a dial, from low to high
aliases: [dial, meter, speedometer, level, needle, progress]
addRank: 3
starterPreset: {"label": "Dial","min": 0,"max": 100}
lookFormats: [{"id": "dial","name": "Dial","symbol": "gauge.medium","set": {"type": "gauge","gaugeStyle": "half","arcAngle": null}},{"id": "ring","name": "Ring","symbol": "circle.circle","set": {"type": "gauge","gaugeStyle": "full","arcAngle": null}},{"id": "bar","name": "Bar","symbol": "chart.bar.fill","set": {"type": "progressRing","progressStyle": "bar"}}]
lookPresets: [{"id": "standard","name": "Standard","symbol": "gauge.medium","set": {"arcThickness": null,"hideValue": null}},{"id": "bold","name": "Bold","symbol": "circle.lefthalf.filled","set": {"arcThickness": 16,"hideValue": null}},{"id": "quiet","name": "Quiet","symbol": "eye.slash","set": {"hideValue": true}}]
io:
  - emits: none
  - receives: value
    role: show
    type: number
    from: [hub, mqtt, http, sensor, store, derive, default]
    says: a number to point the dial at
    reacts: the arc and number glide to it; a value past either end sits at that end, and anything that is not a number shows the lowest value
    example: 40
    since: next
  - sample: 40
    next: 75
fields:
  - name: animation
    title: Motion
    tab: style
    type: enum
    values: [smooth, snappy, bouncy, gentle, instant]
    description: Motion profile for value changes
    summary: How the dial moves when the number changes
    does: The needle or arc eases to each new value; instant jumps with no travel.
    valueHelp: {"smooth": "an even ease", "snappy": "a quick move that settles fast", "bouncy": "overshoots slightly then springs back", "gentle": "a slow and soft glide", "instant": "jumps straight to the new value with no travel"}
    valueTitles: {"smooth": "Smooth", "snappy": "Snappy", "bouncy": "Bouncy", "gentle": "Gentle", "instant": "Instant"}
    valueSymbols: {"smooth": "water.waves", "snappy": "bolt.fill", "bouncy": "arrow.up.and.down.circle", "gentle": "wind", "instant": "forward.end.fill"}
  - name: min
    chip: Range
    edit: range
    depth: surface
    title: Lowest value
    default: 0
    bounds: none
    type: number
    description: Minimum value
    summary: Where the dial starts
    does: The value shown at the empty end of the arc, in the gauge's unit (e.g. 0).
  - name: max
    edit: range
    depth: hold
    under: min
    axis: max
    title: Highest value
    default: 100
    bounds: none
    type: number
    description: Maximum value
    summary: Where the dial fills up
    does: The value shown at the full end of the arc; readings at or above it fill the arc completely.
  - name: gaugeStyle
    edit: look
    title: Shape
    tab: style
    type: enum
    values: [half, full]
    default: half
    description: "Shorthand: half = 180° arc, full = 360° circle"
    summary: Half dial or full ring
    does: Switches between a wide 180° half dial and a 360° square ring.
    valueHelp: {"half": "a half-circle dial that is wide and short", "full": "a closed ring that is square"}
    valueTitles: {"half": "Half dial", "full": "Full ring"}
    valueSymbols: {"half": "circle.lefthalf.filled", "full": "circle"}
  - name: glowRadius
    edit: scrub
    depth: hold
    under: gaugeStyle
    title: Glow
    unit: pt
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    default: 0
    description: Soft glow behind the value arc in its own colour, in points (0 = none). Cross-control, same on every control
    summary: A soft halo around the fill
    does: Adds a glow behind the value arc, 0 (off) to 30 points wide.
  - name: lineCap
    edit: look
    depth: hold
    under: gaugeStyle
    title: Line ends
    tab: style
    type: enum
    values: [round, butt, square]
    default: round
    description: End shape of the track, value arc and segment arcs (the blended gradient arc keeps its butt ends until set). Cross-control, same on every control
    summary: The shape of the arc's ends
    does: Rounds, flattens or squares the ends of the track and the filled arc.
    valueHelp: {"round": "soft rounded ends", "butt": "flat ends cut exactly at the value", "square": "flat ends that stick out half a stroke past the value"}
    valueTitles: {"round": "Round", "butt": "Flat", "square": "Square"}
    valueSymbols: {"round": "capsule.fill", "butt": "rectangle.fill", "square": "square.fill"}
  - name: segments
    edit: stops
    axis: value
    depth: surface
    facet: colorByValue
    title: Color zones
    type: array
    description: Color zone breakpoints [{limit, color}]
    summary: Colors for different ranges of values
    does: The arc changes color as the value crosses each limit, e.g. green to 60 then amber to 80 then red.
  - name: colorBlend
    facet: colorByValue
    title: Zone blending
    tab: style
    min: 0
    max: 1
    step: 0.05
    type: number
    default: 0
    description: "How much the segment colors blend, 0–1. 0 = hard boundaries, 1 = one smooth gradient, between = feathered edges. Needs segments."
    summary: Hard bands or a smooth fade between colors
    does: Softens the color changes between zones, from 0 (sharp steps) to 1 (one smooth gradient).
  - name: tint
    edit: color
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: Primary arc fill color (when no segments)
    summary: The color of the filled arc
    does: Paints the filled part of the arc in one color when there are no color zones.
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Text below the gauge
    summary: The caption under the dial
    does: Shows this text beneath the gauge in the title text size.
  - name: icon
    title: Symbol
    type: string
    description: SF Symbol in the center
    summary: A small picture in the middle
    does: Draws the chosen SF Symbol in the center of the dial next to the number.
  - name: step
    edit: range
    depth: hold
    under: min
    axis: step
    title: Decimal places
    bounds: none
    type: number
    default: 1
    description: Determines decimal formatting of center value
    summary: How many digits after the point
    does: Sets the rounding of the center number, e.g. 1 shows 72.5 and 0.1 shows 72.54.
  - name: arcAngle
    edit: scrub
    depth: hold
    under: gaugeStyle
    title: Arc length
    tab: style
    min: 1
    max: 360
    step: 1
    type: number
    default: 180
    description: Arc sweep in degrees (1-360)
    summary: How much of a circle the arc covers
    does: Sets the sweep of the arc from 1° to 360°; 270 gives a three-quarter dial.
  - name: arcRotation
    edit: scrub
    depth: hold
    under: gaugeStyle
    title: Arc turn
    tab: style
    min: -180
    max: 180
    step: 1
    type: number
    default: 0
    description: Rotates the arc start position in degrees
    summary: Where the arc begins around the circle
    does: Rotates the whole arc by -180° to 180° so its gap sits elsewhere.
  - name: arcThickness
    edit: scrub
    depth: hold
    under: gaugeStyle
    unit: pt
    title: Arc thickness
    tab: style
    min: 1
    max: 40
    step: 1
    type: number
    default: auto
    description: Arc stroke width in points. Omit to auto-scale with the gauge's size.
    summary: How fat the arc stroke is
    does: Sets the stroke width from 1 to 40 points; left empty it scales with the gauge size.
  - name: hideValue
    edit: part
    depth: hold
    title: Hide the number
    type: bool
    default: false
    description: Show just the arc — hide the center value
    summary: Dial only, no number
    does: Removes the center number when on, leaving just the arc.
  - name: forecast
    title: Look ahead
    tab: data
    type: enum
    values: [countdown, reach]
    description: "Look ahead beside the real reading: countdown = the value is a time and the widget counts down to it; reach = the value is expected to arrive at forecastTarget (at the time forecastTimeFrom holds) or to keep moving by forecastRate per second. A newer real value always replaces the guess; past its end the value reads stale."
    summary: A guess drawn beside the real reading
    does: Counts the dial down to a time, or moves it toward a predicted value until a real reading arrives.
    valueHelp: {"countdown": "the value is a time; the dial counts down to it", "reach": "the value is expected to arrive at a target number or to keep changing at a set rate"}
    valueTitles: {"countdown": "Countdown", "reach": "Reach"}
    valueSymbols: {"countdown": "timer", "reach": "scope"}
  - use: forecastTarget
    does: Moves the dial toward this value, between -1,000,000 and 1,000,000, until the real reading replaces it.
  - use: forecastTimeFrom
  - use: forecastRate
    does: Keeps moving the dial by this much per second, -1000 to 1000, from the last real reading.
  - name: unit
    title: Unit
    type: string
    description: "Measurement unit the value arrives in ([[values#Units]] name or symbol, e.g. celsius, km/h). The readout converts to the device locale (°C → °F in the US); min, max and segments stay in this unit, so the arc is the same everywhere. Unknown strings show literally."
    summary: What the number is measured in
    does: Shows the number in the viewer's local unit, e.g. celsius reads 70.7°F in the US.
themeFields:
  - use: cornerRadius
  - use: controlPadding
  - use: surfacePrimary
    summary: The fill behind the dial
    does: Paints the control's background in this color, including transparency.
  - use: accentColor
    does: Tints the dial's fill and accents wherever no color is set directly.
  - use: foregroundColor
    does: Colors the center number and primary text.
  - use: secondaryColor
    summary: The quieter text color
    does: Colors the caption and other supporting text.
  - use: borderColor
    does: Draws the control's outline in this color.
  - use: borderWidth
  - use: labelFontSize
    summary: How big the caption is
    does: Sets the caption's text size from 8 to 24 points.
colorSlots:
  - slot: arc
    default: primary
    alias: tint
    since: next
    summary: The color of the filled arc
    does: Paints the filled part of the arc when there are no color zones; until the layout picks a color it follows the primary role.
  - slot: track
    default: neutral@0.12
    since: next
    summary: The color of the empty track
    does: Paints the unfilled track behind the arc, by default the neutral role at 12%.
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
| `glowRadius` | number | `0` | Soft glow behind the value arc in its own colour, 0–30 pt (the same attribute on every control that has it) |
| `lineCap` | enum | `round` | End shape of the track, value arc and segment arcs (the blended gradient arc keeps its butt ends until set): `round`, `butt` or `square` (the same attribute on every control that has it) |
| `label` | string | — | Text below the gauge |
| `icon` | string | — | SF Symbol in the center |
| `step` | number | `1` | Used to determine decimal formatting of center value |
| `arcAngle` | number | `180` | Arc sweep in degrees (1-360) |
| `arcRotation` | number | `0` | Rotates the arc start position in degrees |
| `arcThickness` | number | auto | Arc stroke width in points. Omit to auto-scale with the gauge's size; set for an absolute width |
| `hideValue` | bool | `false` | Show just the arc — hide the center value (pairs with `hideBackground` for a compact glyph) |
| `unit` | string | — | Measurement unit of the value ([[values#Units]]). The center readout converts to the device locale — `"celsius"` reads 70.7°F in the US, 21,5 °C in Germany. `min`, `max` and `segments` stay in this unit, so the arc never moves. Unknown strings are a literal suffix |
| `forecast` | enum | — | `"countdown"` (the value is a time; count down to it) or `"reach"` (expected to arrive at `forecastTarget`). Shown on widgets and Live Activities, marked "about"; the next real value replaces it, and past its end the value reads stale |
| `forecastTarget` | number | — | With `"reach"`: the value it is expected to arrive at |
| `forecastTimeFrom` | string | — | With `"reach"`: id of the control whose value is the arrival time (epoch seconds or ISO-8601) |
| `forecastRate` | number | — | With `"reach"`: change per second from the last real reading (instead of a target and time) |

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
Demonstrates `segments`: the arc turns green, amber or red depending on which zone the live CPU temperature falls in.
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
Demonstrates a `full` ring with a single `tint` and a center `icon`, reading a live battery percentage.
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
Demonstrates `longPressGroup`: holding the dial opens a popup with a history sparkline and min/max labels.
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

### Ring look (full circle)
Demonstrates the Ring look: `gaugeStyle: "full"` closes the dial into a square 360° ring, with the title under it.
```json
{ "type": "gauge", "id": "ring-demo", "position": [0, 0], "span": [2, 3], "min": 0, "max": 100, "gaugeStyle": "full", "label": "Disk used", "tint": "#667eea" }
```

### Bar look
The Bar look swaps the control for a progress bar that fills left to right: the editor
changes the control's `type` to `progressRing` with `progressStyle: "bar"`, so the example
lives in [[progress-ring]] (its "Bar" example); a gauge document only carries gauge examples.

### Smooth color blend and bold look
Demonstrates `colorBlend: 1` turning the zones into one gradient, with `arcThickness: 16` (the Bold look) for a heavier stroke.
```json
{ "type": "gauge", "id": "blend-demo", "position": [0, 0], "min": 0, "max": 100, "label": "Load", "arcThickness": 16, "colorBlend": 1,
  "segments": [ { "limit": 50, "color": "#34C759" }, { "limit": 80, "color": "#FF9500" }, { "limit": 100, "color": "#FF3B30" } ] }
```

### Quiet look: arc only
Demonstrates `hideValue: true` (the Quiet look): the center number disappears and only the arc shows, handy as a compact glyph.
```json
{ "type": "gauge", "id": "quiet-demo", "position": [0, 0], "min": 0, "max": 100, "hideValue": true, "tint": "#34C759" }
```

### Glow and line ends
Demonstrates `glowRadius: 12` adding a soft halo and `lineCap: "butt"` cutting the arc ends flat.
```json
{ "type": "gauge", "id": "glow-demo", "position": [0, 0], "min": 0, "max": 100, "glowRadius": 12, "lineCap": "butt", "tint": "#00D4FF", "label": "Signal" }
```

### Custom arc shape
Demonstrates `arcAngle: 270`, `arcRotation: 0` and `animation: "bouncy"`: a three-quarter dial whose needle overshoots and settles on each change.
```json
{ "type": "gauge", "id": "arc-demo", "position": [0, 0], "min": 0, "max": 8000, "arcAngle": 270, "arcRotation": 0, "animation": "bouncy", "step": 0, "label": "RPM" }
```

### Converted unit
Demonstrates `unit: "celsius"`: the value arrives in °C but reads 70.7°F in the US; min and max stay in °C so the arc looks the same everywhere.
```json
{ "type": "gauge", "id": "unit-demo", "position": [0, 0], "min": 0, "max": 40, "unit": "celsius", "step": 0, "label": "Outside" }
```

### Forecast: countdown
Demonstrates `forecast: "countdown"`: the value is a time, so the widget counts down to it between real readings.
```json
{ "type": "gauge", "id": "countdown-demo", "position": [0, 0], "min": 0, "max": 3600, "forecast": "countdown", "label": "Oven ready" }
```

### Forecast: reach a target at a time
Demonstrates `forecast: "reach"` with `forecastTarget` and `forecastTimeFrom`: the dial moves toward 100 so it arrives when the `eta` control says; a real value replaces the guess.
```json
{ "type": "gauge", "id": "charge-demo", "position": [0, 0], "min": 0, "max": 100, "forecast": "reach", "forecastTarget": 100, "forecastTimeFrom": "eta", "label": "Charging" }
```

### Forecast: keep moving at a rate
Demonstrates `forecast: "reach"` with `forecastRate: 0.5`: with no arrival time, the dial keeps climbing 0.5 per second from the last real reading.
```json
{ "type": "gauge", "id": "rate-demo", "position": [0, 0], "min": 0, "max": 100, "forecast": "reach", "forecastRate": 0.5, "label": "Tank fill" }
```

### Themed gauge
Demonstrates the theme fields: rounder corners, more inner spacing, a custom background, border and larger title text.
```json
{ "type": "gauge", "id": "theme-demo", "position": [0, 0], "min": 0, "max": 100, "label": "Humidity",
  "theme": { "cornerRadius": 20, "controlPadding": 12, "surfacePrimary": "#1C1C2E", "accentColor": "#34C759", "foregroundColor": "#FFFFFF", "secondaryColor": "#FFFFFF99", "borderColor": "#34C75966", "borderWidth": 2, "labelFontSize": 16 } }
```

## Behavior
- Value animates smoothly between updates (smooth profile)
- Center displays the numeric value with animated content transition
- No action — display only (use [[long-press]] for interaction)

## On-control editing (C6)

The dial publishes its arc as a value axis (`publishValueAxis`) and parts `label` (title), `hideValue` (number) and `tint` (arc fill) via `publishPart`; zone dots in edit mode ride the arc and snap to other zone limits, the ends and 0. See `SharedEditorContract.swift`.

## Related
- [[shared-properties]] — Base fields
- [[sync]] — Receiving values
- [[long-press]] — Detail popup on hold
- [[sparkline]] — Often paired in long-press detail views
- [[pie-chart]] — Radial part-of-whole (and spin wheel / radial menu)
- [[radar]] — Multi-axis profiles when one dial isn't enough
