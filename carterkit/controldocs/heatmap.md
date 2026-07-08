---
type: heatmap
label: Heatmap
icon: square.grid.3x3.fill
category: controls
defaultSpan: [2, 4]
fields:
  - name: label
    type: string
    description: Header label above the grid
  - name: heatmapConfig
    type: object
    description: Full configuration object (see HeatmapConfig section)
  - name: tint
    type: color
    default: "#667eea"
    description: Ramp/palette seed color
  - name: formatValue
    type: string
    description: Formatter for scale/cell values
  - name: cellAction
    type: object
    description: cellAction
    group: heatmapConfig
  - name: cellCorner
    type: number
    default: 3
    description: Cell corner rounding
    group: heatmapConfig
  - name: cellGap
    type: number
    default: 2
    description: Gap between cells
    group: heatmapConfig
  - name: cellShape
    type: string
    description: square or circle (circle reads as dot-matrix/LED)
    group: heatmapConfig
  - name: colors
    type: string[]
    description: Continuous: 2+ gradient stops. Discrete: the palette (value = index)
    group: heatmapConfig
  - name: discrete
    type: bool
    default: false
    description: Treat values as palette indices instead of a continuous range
    group: heatmapConfig
  - name: drag
    type: bool
    default: true
    description: Drag paints the first-touched cell's new value across cells
    group: heatmapConfig
  - name: editable
    type: bool
    default: false
    description: Tap cycles a cell (discrete: next palette index; continuous: 0 ↔ vMax toggle)
    group: heatmapConfig
  - name: sendMode
    type: string
    description: cell fires per change; matrix fires the whole dataset once an edit burst settles (~0.4s)
    group: heatmapConfig
  - name: showColLabels
    type: bool
    default: true
    description: Column labels along the top (when cols present; auto-thinned)
    group: heatmapConfig
  - name: showRowLabels
    type: bool
    default: true
    description: Row labels down the leading edge (when rows present)
    group: heatmapConfig
  - name: showScale
    type: bool
    default: false
    description: Gradient scale legend under the grid (continuous only)
    group: heatmapConfig
  - name: showValues
    type: bool
    default: false
    description: Numeric value inside each cell (when cells are large enough)
    group: heatmapConfig
  - name: vMax
    type: number
    description: Continuous color-scale bounds
    group: heatmapConfig
  - name: vMin
    type: number
    description: Continuous color-scale bounds
    group: heatmapConfig
themeFields:
  - name: cornerRadius
    type: number
    default: 12
    description: Control corner radius
  - name: surfacePrimary
    type: color
    default: #FFFFFF0F
    description: Background fill
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Label text color
---

# Heatmap

A color-mapped matrix. In **continuous** mode values interpolate across a gradient
ramp — server-room temperatures, signal strength, an activity calendar. In
**discrete** mode each value is an index into a palette. Flip on `editable` and the
same grid becomes an input surface: tap cycles a cell, drag paints — a weekly
schedule programmer, an LED-matrix pixel editor, or a step sequencer, straight from
one flag.

## Type
`"heatmap"`

## Recommended Size
Wide: `[2, 4]` for a dashboard strip; taller for schedule grids (one row per day).

## Relevant Fields
Inherits all [[control-def|shared fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Header label |
| `heatmapConfig` | [[#HeatmapConfig]] | — | Full configuration object (all optional) |
| `tint` | string | `"#667eea"` | Default ramp top / palette accent |
| `formatValue` | string | — | Formatter for the scale legend and cell values |

## HeatmapConfig

### Color Mapping

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `colors` | string[] | tint ramp | Continuous: 2+ gradient stops. Discrete: the palette (value = index) |
| `discrete` | bool | `false` | Treat values as palette indices instead of a continuous range |
| `vMin` / `vMax` | number | data range | Continuous color-scale bounds |

### Cells

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `cellCorner` | number | `3` | Cell corner rounding |
| `cellGap` | number | `2` | Gap between cells |
| `cellShape` | string | `"square"` | `square` or `circle` (circle reads as dot-matrix/LED) |

### Labels & Legend

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `showRowLabels` | bool | `true` | Row labels down the leading edge (when `rows` present) |
| `showColLabels` | bool | `true` | Column labels along the top (when `cols` present; auto-thinned) |
| `showScale` | bool | `false` | Gradient scale legend under the grid (continuous only) |
| `showValues` | bool | `false` | Numeric value inside each cell (when cells are large enough) |

### Editing

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `editable` | bool | `false` | Tap cycles a cell (discrete: next palette index; continuous: 0 ↔ vMax toggle) |
| `drag` | bool | `true` | Drag paints the first-touched cell's new value across cells |
| `cellAction` | [[actions\|ActionDefinition]] | — | Fired per edit; `{{value}}` = `{"row", "col", "value"}` JSON |
| `sendMode` | string | `"cell"` | `cell` fires per change; `matrix` fires the whole dataset once an edit burst settles (~0.4s) |

If `cellAction` is omitted, edits fall back to the control's own `action`.

## Sync Payload Structure

A dense matrix plus optional axis labels — natural JSON or an encoded string.
`{"values": [[…]]}` with labels, or a bare `[[…]]` array of rows:

```json
{
  "rows": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
  "cols": ["00", "03", "06", "09", "12", "15", "18", "21"],
  "values": [
    [0, 0, 1, 3, 3, 2, 1, 0],
    [0, 0, 1, 3, 3, 2, 1, 0],
    [0, 0, 2, 3, 3, 3, 2, 1],
    [0, 0, 1, 3, 3, 2, 1, 0],
    [0, 0, 1, 2, 3, 3, 3, 2],
    [1, 0, 0, 1, 2, 3, 3, 2],
    [1, 0, 0, 1, 2, 2, 1, 0]
  ]
}
```

## Examples

### Continuous telemetry heatmap
```json
{
  "type": "heatmap",
  "id": "rack-temps",
  "defaultValue": "{\"rows\":[\"Mon\",\"Tue\",\"Wed\"],\"cols\":[\"00\",\"06\",\"12\",\"18\"],\"values\":[[24,31,62,45],[28,55,81,49],[22,38,74,68]]}",
  "position": [0, 0],
  "span": [2, 4],
  "label": "Rack temperatures",
  "formatValue": "suffix:°C",
  "heatmapConfig": { "colors": ["#1B2845", "#667eea", "#FF9500", "#FF6B6B"], "showScale": true, "vMin": 20, "vMax": 90 },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "rack_temps" }, "valuePath": "grid" }]
}
```

### Weekly schedule programmer (editable, discrete)
```json
{
  "type": "heatmap",
  "id": "thermostat-schedule",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Heating schedule",
  "heatmapConfig": {
    "discrete": true,
    "colors": ["#FFFFFF14", "#667eea", "#FF9500"],
    "editable": true,
    "sendMode": "matrix",
    "cellAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast", "payload": { "msg_type": "schedule_set", "schedule": "{{value}}" } }
  },
  "defaultValue": "{\"rows\":[\"Mon\",\"Tue\",\"Wed\",\"Thu\",\"Fri\",\"Sat\",\"Sun\"],\"cols\":[\"6\",\"9\",\"12\",\"15\",\"18\",\"21\"],\"values\":[[0,1,0,0,1,1],[0,1,0,0,1,1],[0,1,0,0,1,1],[0,1,0,0,1,1],[0,1,0,0,1,2],[1,1,1,1,1,2],[1,1,1,1,1,0]]}"
}
```

### LED matrix pixel editor
```json
{
  "type": "heatmap",
  "id": "led-editor",
  "position": [0, 0],
  "span": [4, 4],
  "label": "LED panel",
  "heatmapConfig": {
    "discrete": true,
    "colors": ["#1A1A1A", "#FF3B30", "#34C759", "#007AFF", "#FFCC00"],
    "cellShape": "circle",
    "cellGap": 3,
    "editable": true,
    "cellAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast", "payload": { "msg_type": "led_set", "pixel": "{{value}}" } }
  },
  "defaultValue": "[[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]]"
}
```

## Behavior
- Dataset pushes animate cell colors; edits render instantly (a local draft holds until the next push)
- Tap cycles: discrete `(value + 1) % palette.count`, continuous `0 ↔ vMax`
- Dragging paints the brush value chosen by the first cell touched — fill a row in one stroke
- Every cell change ticks a selection haptic and updates the control's stored dataset, so state [[sync|readback]] returns the edited grid
- `sendMode: "matrix"` batches an edit burst into a single dataset-sized action — ideal for schedule saves

## Notes
- Ragged rows render (short rows read as 0) and are padded rectangular on first edit
- A GitHub-style activity calendar is a 7-row continuous heatmap with week columns
- A step sequencer is an editable discrete grid where the server plays column-by-column

## Related
- [[chart]] — cartesian series
- [[list]] — tabular rows
- [[color-picker]] — free-form color input
- [[actions]] — how `cellAction` fires
- [[sync]] — how the matrix arrives
