---
type: progressRing
label: Progress Ring
icon: circle.dashed
category: controls
defaultSpan: [2, 2]
fields:
  - name: min
    type: number
    default: 0
    description: Minimum value (0%)
  - name: max
    type: number
    default: 100
    description: Maximum value (100%)
  - name: progressStyle
    type: enum
    values: [ring, bar]
    default: ring
    description: Circular ring or linear bar
  - name: tint
    type: color
    default: "#667eea"
    description: Fill color
  - name: label
    type: string
    description: Center text (ring) or header text (bar)
  - name: icon
    type: string
    description: SF Symbol in center (ring only)
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

## Styles

### `"ring"` (default)
Circular progress ring with percentage and optional label/icon in the center. Square aspect ratio.

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
