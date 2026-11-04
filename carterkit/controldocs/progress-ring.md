---
depth: complete
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
    summary: How the ring moves when the number changes
    does: The fill eases to each new value; instant jumps with no travel.
    valueHelp: {"smooth": "an even ease and the default", "snappy": "a quick move that settles fast", "bouncy": "overshoots slightly then springs back", "gentle": "a slow and soft glide", "instant": "jumps straight to the new value with no travel"}
  - name: min
    title: Lowest value
    bounds: none
    type: number
    default: 0
    description: Minimum value (0%)
    summary: The value that shows an empty ring
    does: Sets the value at 0% fill, in the control's unit (e.g. 0).
  - name: max
    title: Highest value
    bounds: none
    type: number
    default: 100
    description: Maximum value (100%)
    summary: The value that shows a full ring
    does: Sets the value at 100% fill, in the control's unit (e.g. 100).
  - name: progressStyle
    edit: look
    title: Shape
    tab: style
    type: enum
    values: [ring, bar]
    default: ring
    description: Circular ring or linear bar
    summary: Round ring or flat bar
    does: Switches the display between a circular ring and a horizontal bar.
    valueHelp: {"ring": "a circular ring with the number in the middle", "bar": "a thin horizontal bar with the title and number above"}
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
    summary: A soft halo around the fill
    does: Adds a glow of this many points (0 to 30) behind the fill in its own colour; 0 is none.
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
    summary: The shape of the fill's ends
    does: Rounds, flattens or squares the ends of the ring or the bar corners.
    valueHelp: {"round": "soft rounded ends", "butt": "flat ends cut exactly at the value", "square": "flat ends that stick out half a stroke past the value"}
  - name: tint
    edit: color
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: Fill color
    summary: The colour of the filled part
    does: Paints the fill in this colour (e.g. green #34C759).
  - name: colorByValue
    edit: stops
    axis: value
    depth: surface
    title: Color zones
    tab: style
    type: array
    description: Color zones [{limit, color}] in the min–max unit — the fill takes the zone colour of the current value (gauge semantics). Overrides tint.
    summary: Colour the ring by how far along it is
    does: The fill changes colour as the value crosses each limit, e.g. red to 30 then amber to 70 then green.
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Center text (ring) or header text (bar)
    summary: The words on the control
    does: Shows this text in the middle of the ring or above the bar.
  - name: icon
    edit: symbol
    depth: hold
    under: label
    title: Symbol
    type: string
    description: SF Symbol in center (ring only)
    summary: A small picture in the ring
    does: Draws this SF Symbol in the centre of the ring; a bar ignores it.
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
    summary: How heavy the stroke is
    does: Sets ring stroke width or bar height in points, 2 to 40; unset scales with the size.
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
    summary: How round the bar's corners are
    does: Rounds the bar's corners by this many points, 0 to 30 (4 by default).
  - name: hideValue
    edit: part
    depth: hold
    under: label
    title: Hide the number
    type: bool
    default: false
    description: Show just the arc — hide the center value
    summary: Arc only, no number
    does: Removes the centre number when on, leaving just the arc.
  - name: forecast
    title: Look ahead
    tab: data
    type: enum
    values: [countdown, reach]
    description: "Look ahead beside the real reading: countdown = the value is a time and the widget counts down to it; reach = the value is expected to arrive at forecastTarget (at the time forecastTimeFrom holds) or to keep moving by forecastRate per second. A newer real value always replaces the guess; past its end the value reads stale."
    summary: Show as a countdown, or show where the value is expected to reach
    does: Counts the fill down to a time, or moves it toward a predicted value until a real reading arrives.
    valueHelp: {"countdown": "the value is a time and the control counts down to it", "reach": "the value is expected to arrive at a target number or to keep changing at a set rate"}
  - name: forecastTarget
    title: Expected to reach
    tab: data
    type: number
    min: -1000000
    max: 1000000
    step: 1
    description: The value this one is expected to arrive at (with forecast "reach")
    summary: The number it should reach
    does: Moves the fill toward this value, between -1,000,000 and 1,000,000, until a real reading replaces it.
  - name: forecastTimeFrom
    title: Arrival time from
    tab: data
    simple: hide
    type: string
    description: Id of the control whose value is the arrival time (epoch seconds or ISO-8601), for forecast "reach"
    summary: Which control says when it arrives
    does: Takes the arrival time from another control's value (epoch seconds or ISO date) so the guess lands on time.
  - name: forecastRate
    title: Change per second
    tab: data
    simple: hide
    type: number
    min: -1000
    max: 1000
    step: 0.01
    description: Keep moving by this much per second from the last real reading (forecast "reach", no time needed)
    summary: How fast it is expected to change
    does: Keeps moving the fill by this much per second, -1000 to 1000, from the last real reading.
  - name: unit
    title: Unit
    type: string
    description: "Measurement unit the value arrives in ([[values#Units]] name or symbol, e.g. celsius, km/h). With a unit the readout shows the value itself (converted to the device locale) instead of the fill percentage; min and max stay in this unit. Unknown strings show literally."
    summary: What the number is measured in
    does: Shows the number in the viewer's local unit, e.g. celsius reads 356°F in the US; min and max stay in that unit.
themeFields:
  - name: cornerRadius
    title: Corner roundness
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
    summary: How round the control's corners are
    does: Rounds the background's corners by this many points, 0 to 30.
  - name: controlPadding
    title: Inner spacing
    min: 0
    max: 24
    step: 1
    type: number
    default: 8
    description: Internal padding
    summary: Breathing room inside the edge
    does: Sets the gap between the control's edge and its content in points, 0 to 24.
  - name: surfacePrimary
    title: Background color
    type: color
    default: #FFFFFF0F
    description: Background fill
    summary: The panel behind the control
    does: Fills the background with this colour (default a faint white).
  - name: accentColor
    title: Accent color
    type: color
    default: #667eea
    description: Accent/tint color
    summary: The theme's highlight colour
    does: Sets the default fill colour when no tint is given (default #667eea).
  - name: foregroundColor
    title: Text color
    type: color
    default: #FFFFFF
    description: Primary text color
    summary: The main text colour
    does: Colours the centre number and title text (default white).
  - name: secondaryColor
    title: Second text color
    type: color
    default: #FFFFFF99
    description: Secondary text color
    summary: The quieter text colour
    does: Colours the less prominent text such as the unit (default translucent white).
  - name: borderColor
    title: Border color
    type: color
    default: #FFFFFF1A
    description: Border color
    summary: The outline around the control
    does: Draws the border in this colour (default a faint white).
  - name: borderWidth
    title: Border thickness
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
    summary: How thick the outline is
    does: Sets the border thickness in points, 0 to 5; 0 hides it.
  - name: labelFontSize
    title: Title text size
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
    summary: How big the title is
    does: Sets the title text size in points, 8 to 24.
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
Demonstrates the default `ring` with a `tint`, a center `icon` and a `label`, filling as a live firmware percentage arrives.
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
Demonstrates `progressStyle: "bar"` (the Bar look): a horizontal bar with the title and number above it, filling over a 90-minute cycle.
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

### Dial look
The Dial look turns this control into a gauge (`type: "gauge"`, `gaugeStyle: "half"`), so it is not a Progress Ring any more; see [[gauge]] for its fields and examples.

### Color zones
Demonstrates `colorByValue`: the ring turns red, amber or green depending on which zone the battery level falls in, overriding `tint`.
```json
{
  "type": "progressRing",
  "id": "battery-ring",
  "position": [0, 0],
  "min": 0,
  "max": 100,
  "label": "Battery",
  "colorByValue": [{ "limit": 20, "color": "#FF3B30" }, { "limit": 50, "color": "#FF9500" }, { "limit": 100, "color": "#34C759" }]
}
```

### Quiet look: arc only
Demonstrates `hideValue: true` (the Quiet look): the center number disappears and only the arc shows, handy as a compact glyph.
```json
{
  "type": "progressRing",
  "id": "quiet-ring",
  "position": [0, 0],
  "label": "Progress",
  "hideValue": true
}
```

### Glow, line ends and thickness
Demonstrates `glowRadius: 12` adding a soft halo, `lineCap: "butt"` cutting the ring ends flat and `arcThickness: 16` making a heavier stroke.
```json
{
  "type": "progressRing",
  "id": "glow-ring",
  "position": [0, 0],
  "label": "Goal",
  "tint": "#5AC8FA",
  "glowRadius": 12,
  "lineCap": "butt",
  "arcThickness": 16
}
```

### Bar roundness and motion
Demonstrates `barCornerRadius: 0` squaring the bar's corners and `animation: "bouncy"` making the fill overshoot and settle on each change.
```json
{
  "type": "progressRing",
  "id": "square-bar",
  "position": [0, 0],
  "progressStyle": "bar",
  "barCornerRadius": 0,
  "animation": "bouncy",
  "label": "Upload"
}
```

### Converted unit
Demonstrates `unit: "celsius"`: the value arrives in °C but the readout shows 356°F in the US for 180; min and max stay in °C so the fill looks the same everywhere.
```json
{
  "type": "progressRing",
  "id": "oven-temp",
  "position": [0, 0],
  "min": 0,
  "max": 250,
  "unit": "celsius",
  "label": "Oven"
}
```

### Forecast: countdown
Demonstrates `forecast: "countdown"`: the value is a time, so the widget counts down to it between real readings.
```json
{
  "type": "progressRing",
  "id": "timer-ring",
  "position": [0, 0],
  "label": "Timer",
  "forecast": "countdown"
}
```

### Forecast: reach a target at a time
Demonstrates `forecast: "reach"` with `forecastTarget` and `forecastTimeFrom`: the ring moves toward 100 so it arrives when the `eta` control says; a real value replaces the guess.
```json
{
  "type": "progressRing",
  "id": "charge-ring",
  "position": [0, 0],
  "label": "Charge",
  "forecast": "reach",
  "forecastTarget": 100,
  "forecastTimeFrom": "eta"
}
```

### Forecast: keep moving at a rate
Demonstrates `forecast: "reach"` with `forecastRate: 0.5`: with no arrival time, the ring keeps climbing half a unit per second from the last real reading.
```json
{
  "type": "progressRing",
  "id": "rate-ring",
  "position": [0, 0],
  "label": "Print",
  "forecast": "reach",
  "forecastRate": 0.5
}
```

> **Note:** this control is read-only: it has no action, long-press or detail view, so there are no examples for them. Its theme fields (corner roundness, spacing, colors, border, title size) restyle it through the layout theme like every control.

## Behavior
- Progress animates smoothly between value updates
- Percentage is calculated as `(value - min) / (max - min) * 100`
- No action — display only

## Related
- [[shared-properties]] — Base fields
- [[sync]] — Value updates
- [[gauge]] — For when you want a range indicator rather than progress
