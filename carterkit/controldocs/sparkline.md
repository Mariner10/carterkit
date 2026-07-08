---
type: sparkline
label: Sparkline
icon: chart.xyaxis.line
category: controls
defaultSpan: [1, 2]
fields:
  - name: sparklinePoints
    type: number
    default: 50
    description: Max data points retained in the buffer
  - name: sparklineFill
    type: bool
    default: false
    description: Fill the area under the line with a gradient
  - name: tint
    type: color
    default: "#667eea"
    description: Line and fill color
  - name: label
    type: string
    description: Header label (also shows latest value)
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

# Sparkline

A tiny inline line chart that accumulates synced values over time. Read-only.

## Type
`"sparkline"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `sparklinePoints` | int | `50` | Max data points retained in the buffer |
| `sparklineFill` | bool | `false` | Fill the area under the line with a gradient |
| `tint` | string | `"#667eea"` | Line and fill color |
| `label` | string | — | Header label (also shows latest value) |

## Data Flow

Unlike other controls that store a single value, sparklines maintain a **ring buffer** of numeric values in `AppState.sparklineBuffers`. Each synced value is appended to the buffer. When the buffer exceeds `sparklinePoints`, the oldest value is dropped.

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

## Behavior
- New data points animate in smoothly
- The Y axis auto-scales to the min/max of current buffer data
- When fewer than 2 points exist, shows a `"--"` placeholder
- The latest value is shown in the header (right side) with animated numeric transition

## Related
- [[shared-properties]] — Base fields
- [[sync]] — How values are received
- [[gauge]] — Often paired with sparklines in long-press detail views
- [[chart]] — Multi-series bars/lines/areas/scatter when one trend isn't enough
