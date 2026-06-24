---
type: gauge
label: Gauge
icon: gauge.medium
category: controls
defaultSpan: [2, 2]
fields:
  - name: min
    type: number
    description: Minimum value
  - name: max
    type: number
    description: Maximum value
  - name: gaugeStyle
    type: enum
    values: [half, full]
    default: half
    description: "Shorthand: half = 180° arc, full = 360° circle"
  - name: segments
    type: array
    description: Color zone breakpoints [{limit, color}]
  - name: tint
    type: color
    default: "#667eea"
    description: Primary arc fill color (when no segments)
  - name: label
    type: string
    description: Text below the gauge
  - name: icon
    type: string
    description: SF Symbol in the center
  - name: step
    type: number
    default: 1
    description: Determines decimal formatting of center value
  - name: arcAngle
    type: number
    default: 180
    description: Arc sweep in degrees (1-360)
  - name: arcRotation
    type: number
    default: 0
    description: Rotates the arc start position in degrees
  - name: arcThickness
    type: number
    default: auto
    description: Arc stroke width in points. Omit to auto-scale with the gauge's size.
  - name: hideValue
    type: bool
    default: false
    description: Show just the arc — hide the center value
themeFields:
  - name: cornerRadius
    type: number
    default: 12
    description: Control corner radius
  - name: controlPadding
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
  - name: foregroundColor
    type: color
    default: #FFFFFF
    description: Primary text color
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Secondary text color
  - name: borderColor
    type: color
    default: #FFFFFF1A
    description: Border color
  - name: borderWidth
    type: number
    default: 1
    description: Border width
  - name: labelFontSize
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
