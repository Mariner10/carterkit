---
type: progressRing
label: Progress Ring
icon: circle.dashed
category: controls
defaultSpan: [2, 2]
addIntent: show
pickerCategory: Readouts
friendlyName: Ring
oneLiner: How far along something is
aliases: [ring, progress, circle, completion, percent, activity ring]
addRank: 4
starterPreset: {"label": "Progress","min": 0,"max": 100,"progressStyle": "ring"}
lookFormats: [{"id": "dial","name": "Dial","symbol": "gauge.medium","set": {"type": "gauge","gaugeStyle": "half"}},{"id": "ring","name": "Ring","symbol": "circle.circle","set": {"type": "progressRing","progressStyle": "ring"}},{"id": "bar","name": "Bar","symbol": "chart.bar.fill","set": {"type": "progressRing","progressStyle": "bar"}}]
lookPresets: [{"id": "standard","name": "Standard","symbol": "circle.circle","set": {"hideValue": null}},{"id": "quiet","name": "Quiet","symbol": "eye.slash","set": {"hideValue": true}}]
fields:
  - name: animation
    title: Motion
    tab: style
    type: enum
    values: [smooth, snappy, bouncy, gentle, instant]
    description: Motion profile for value changes
  - name: min
    title: Lowest value
    bounds: none
    type: number
    default: 0
    description: Minimum value (0%)
    summary: The value that shows an empty ring
  - name: max
    title: Highest value
    bounds: none
    type: number
    default: 100
    description: Maximum value (100%)
    summary: The value that shows a full ring
  - name: progressStyle
    edit: look
    title: Shape
    tab: style
    type: enum
    values: [ring, bar]
    default: ring
    description: Circular ring or linear bar
  - name: glowRadius
    edit: scrub
    depth: hold
    under: progressStyle
    title: Glow
    unit: pt
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    default: 0
    description: Soft glow behind the ring or bar fill in its own colour, in points (0 = none). Cross-control, same on every control
  - name: lineCap
    edit: look
    depth: hold
    under: glowRadius
    title: Line ends
    tab: style
    type: enum
    values: [round, butt, square]
    default: round
    description: End shape of the ring (the linear bar rounds its corners for round, squares them for butt and square). Cross-control, same on every control
  - name: tint
    edit: color
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: Fill color
  - name: colorByValue
    edit: stops
    axis: value
    depth: surface
    title: Color zones
    tab: style
    type: array
    description: Color zones [{limit, color}] in the min–max unit — the fill takes the zone colour of the current value (gauge semantics). Overrides tint.
    summary: Colour the ring by how far along it is
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Center text (ring) or header text (bar)
  - name: icon
    edit: symbol
    depth: hold
    under: label
    title: Symbol
    type: string
    description: SF Symbol in center (ring only)
  - name: arcThickness
    edit: scrub
    depth: hold
    under: progressStyle
    title: Thickness
    unit: pt
    tab: style
    min: 2
    max: 40
    step: 1
    type: number
    description: Ring stroke width, or bar height, in points. Absent scales with the control size.
  - name: barCornerRadius
    edit: scrub
    depth: hold
    under: progressStyle
    title: Bar roundness
    unit: pt
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    default: 4
    description: Corner rounding of the linear bar (progressStyle bar)
  - name: hideValue
    edit: part
    depth: hold
    under: label
    title: Hide the number
    type: bool
    default: false
    description: Show just the arc — hide the center value
  - name: forecast
    title: Look ahead
    tab: data
    type: enum
    values: [countdown, reach]
    description: "Look ahead beside the real reading: countdown = the value is a time and the widget counts down to it; reach = the value is expected to arrive at forecastTarget (at the time forecastTimeFrom holds) or to keep moving by forecastRate per second. A newer real value always replaces the guess; past its end the value reads stale."
    summary: Show as a countdown, or show where the value is expected to reach
  - name: forecastTarget
    title: Expected to reach
    tab: data
    type: number
    min: -1000000
    max: 1000000
    step: 1
    description: The value this one is expected to arrive at (with forecast "reach")
    summary: The number it should reach
  - name: forecastTimeFrom
    title: Arrival time from
    tab: data
    simple: hide
    type: string
    description: Id of the control whose value is the arrival time (epoch seconds or ISO-8601), for forecast "reach"
  - name: forecastRate
    title: Change per second
    tab: data
    simple: hide
    type: number
    min: -1000
    max: 1000
    step: 0.01
    description: Keep moving by this much per second from the last real reading (forecast "reach", no time needed)
  - name: unit
    title: Unit
    type: string
    description: "Measurement unit the value arrives in ([[values#Units]] name or symbol, e.g. celsius, km/h). With a unit the readout shows the value itself (converted to the device locale) instead of the fill percentage; min and max stay in this unit. Unknown strings show literally."
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

# Progress Ring

A determinate progress indicator (circular ring or linear bar). Read-only.

## Type
`"progressRing"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `min` | number | `0` | Minimum value (0%) |
| `max` | number | `100` | Maximum value (100%) |
| `progressStyle` | string | `"ring"` | `"ring"` (circular) or `"bar"` (linear) |
| `tint` | string | `"#667eea"` | Fill color |
| `barCornerRadius` | number | `4` | Corner rounding of the linear bar (`progressStyle` `bar`), 0–30 pt |
| `glowRadius` | number | `0` | Soft glow behind the ring or bar fill in its own colour, 0–30 pt (the same attribute on every control that has it) |
| `lineCap` | enum | `round` | End shape of the ring (the linear bar rounds its corners for round, squares them for butt and square): `round`, `butt` or `square` (the same attribute on every control that has it) |
| `colorByValue` | array | — | Color zones `[{limit, color}]` in the `min`–`max` unit; the fill takes the zone colour of the current value (gauge semantics) and overrides `tint` |
| `arcThickness` | number | auto | Ring stroke width or bar height, in points (2–40). Absent scales with the control |
| `label` | string | — | Center text (ring) or header text (bar) |
| `icon` | string | — | SF Symbol in center (ring only) |
| `hideValue` | bool | `false` | Show just the arc — hide the center value (pairs with `hideBackground` for a compact glyph) |
| `unit` | string | — | Measurement unit of the value ([[values#Units]]). With a unit the readout is the value itself, converted to the device locale (`180` `"celsius"` reads 356°F in the US), not the fill percentage. `min`/`max` stay in this unit |
| `forecast` | enum | — | `"countdown"` (the value is a time; count down to it) or `"reach"` (expected to arrive at `forecastTarget`). Shown on widgets and Live Activities, marked "about"; the next real value replaces it, and past its end the value reads stale |
| `forecastTarget` | number | — | With `"reach"`: the value it is expected to arrive at |
| `forecastTimeFrom` | string | — | With `"reach"`: id of the control whose value is the arrival time (epoch seconds or ISO-8601) |
| `forecastRate` | number | — | With `"reach"`: change per second from the last real reading (instead of a target and time) |

## Styles

### `"ring"` (default)
Circular progress ring with percentage and optional label/icon in the center. The
stroke, number, icon, and label all scale to the ring's size, so a small cell stays
tight and a large one reads bold. Square aspect (1:1) — give it ~3 `rowSpan` in a
2-D grid. Set `hideValue` (and `hideBackground`) for a bare ring glyph. See [[grid-dimensions]].

### `"bar"`
Linear progress bar (thin horizontal bar). Header shows label and percentage.

## Examples

### Circular download progress
```json
{
  "type": "progressRing",
  "id": "download-progress",
  "position": [0, 0],
  "min": 0,
  "max": 100,
  "progressStyle": "ring",
  "tint": "#34C759",
  "label": "Download",
  "icon": "arrow.down.circle",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "task": "firmware_update" }, "valuePath": "percent" }]
}
```

### Linear bar (washer cycle)
```json
{
  "type": "progressRing",
  "id": "washer-cycle",
  "position": [2, 0],
  "span": [1, 4],
  "min": 0,
  "max": 90,
  "progressStyle": "bar",
  "tint": "#5AC8FA",
  "label": "Washer Cycle (min)",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "device": "washer" }, "valuePath": "elapsed_minutes" }]
}
```

## Behavior
- Progress animates smoothly between value updates
- Percentage is calculated as `(value - min) / (max - min) * 100`
- No action — display only

## Related
- [[shared-properties]] — Base fields
- [[sync]] — Value updates
- [[gauge]] — For when you want a range indicator rather than progress
