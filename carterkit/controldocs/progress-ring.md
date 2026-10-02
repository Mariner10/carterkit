---
type: progressRing
label: Progress Ring
icon: circle.dashed
category: controls
defaultSpan: [2, 2]
addIntent: show
friendlyName: Ring
oneLiner: How far along something is
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
    title: Shape
    tab: style
    type: enum
    values: [ring, bar]
    default: ring
    description: Circular ring or linear bar
  - name: tint
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: Fill color
  - name: label
    title: Title
    type: string
    description: Center text (ring) or header text (bar)
  - name: icon
    title: Symbol
    type: string
    description: SF Symbol in center (ring only)
  - name: hideValue
    title: Hide the number
    type: bool
    default: false
    description: Show just the arc — hide the center value
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
| `label` | string | — | Center text (ring) or header text (bar) |
| `icon` | string | — | SF Symbol in center (ring only) |
| `hideValue` | bool | `false` | Show just the arc — hide the center value (pairs with `hideBackground` for a compact glyph) |
| `unit` | string | — | Measurement unit of the value ([[values#Units]]). With a unit the readout is the value itself, converted to the device locale (`180` `"celsius"` reads 356°F in the US), not the fill percentage. `min`/`max` stay in this unit |

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
