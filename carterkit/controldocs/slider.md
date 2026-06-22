---
type: slider
label: Slider
icon: slider.horizontal.3
category: controls
defaultSpan: [1, 2]
fields:
  - name: min
    type: number
    default: 0
    description: Minimum value
  - name: max
    type: number
    default: 100
    description: Maximum value
  - name: step
    type: number
    default: 1
    description: Step increment
  - name: label
    type: string
    description: Header label
  - name: defaultValue
    type: number
    description: Initial value
  - name: tint
    type: color
    default: "#667eea"
    description: Track fill color
  - name: style
    type: enum
    values: [default, scrubber, radial]
    default: default
    description: Display style
  - name: formatValue
    type: enum
    values: [decimal, time, percent, none]
    default: decimal
    description: Value display format
  - name: minIcon
    type: string
    description: SF Symbol at minimum end
  - name: maxIcon
    type: string
    description: SF Symbol at maximum end
  - name: hideLabel
    type: bool
    default: false
    description: Hide the header
  - name: hideBackground
    type: bool
    default: false
    description: Remove glass background
  - name: arcAngle
    type: number
    default: 270
    description: Arc sweep in degrees (radial style only)
  - name: arcRotation
    type: number
    default: 0
    description: Arc start rotation (radial style only)
  - name: arcThickness
    type: number
    default: 6
    description: Track stroke width (radial style only)
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
  - name: borderColor
    type: color
    default: #FFFFFF1A
    description: Border color
  - name: labelFontSize
    type: number
    default: 12
    description: Label text size
  - name: trackColor
    type: color
    default: #39393D
    description: Track background color
  - name: trackHeight
    type: number
    default: 31
    description: Track height
  - name: thumbColor
    type: color
    default: #FFFFFF
    description: Thumb fill color
  - name: thumbRadius
    type: number
    default: 14
    description: Thumb corner radius
  - name: thumbSize
    type: number
    default: 28
    description: Thumb diameter
  - name: thumbShadow
    type: bool
    default: true
    description: Show thumb shadow
---

# Slider

A numeric range input. Stores a `.number` value.

## Type
`"slider"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `min` | number | `0` | Minimum value |
| `max` | number | `100` | Maximum value |
| `step` | number | `1` | Step increment |
| `label` | string | — | Header label |
| `tint` | string | `"#667eea"` | Track fill color |
| `style` | string | `"default"` | `"default"`, `"scrubber"`, or `"radial"` |
| `formatValue` | string | `"decimal"` | Value display format |
| `minIcon` | string | — | SF Symbol at minimum end |
| `maxIcon` | string | — | SF Symbol at maximum end |
| `hideLabel` | bool | `false` | Hide the header with label and value |
| `hideBackground` | bool | `false` | Remove glass background |
| `arcAngle` | number | `270` | Arc sweep in degrees (radial style only) |
| `arcRotation` | number | `0` | Arc start rotation (radial style only) |
| `arcThickness` | number | `6` | Track stroke width (radial style only) |

## Styles

### `"default"`
System `Slider` with optional min/max icons.

### `"scrubber"`
Custom thin progress bar with draggable dot. Used for seek bars, compact volume controls.

### `"radial"`
Circular arc slider. The user drags around an arc to set the value. Configure the arc geometry with `arcAngle`, `arcRotation`, and `arcThickness`.

## Format Values

| Value | Output | Example |
|-------|--------|---------|
| `"decimal"` | `"72"` or `"3.5"` | Respects `step` for decimal places |
| `"time"` | `"3:45"` | Minutes:seconds from total seconds |
| `"percent"` | `"80%"` | Integer percentage |
| `"none"` | (hidden) | No value display |

## Examples

### Basic brightness slider
```json
{
  "type": "slider",
  "id": "lr-brightness",
  "position": [1, 0],
  "span": [1, 3],
  "min": 0,
  "max": 100,
  "step": 1,
  "defaultValue": 80,
  "label": "Brightness",
  "action": { "method": "meshsocket", "mode": "broadcast", "event": "route_msg", "payload": { "target_id": "hue-bridge", "type": "brightness", "payload": { "room": "living", "level": "{{value}}" } } }
}
```

### Volume slider with icons
```json
{
  "type": "slider",
  "id": "volume",
  "position": [0, 0],
  "span": [1, 4],
  "min": 0,
  "max": 1,
  "step": 0.01,
  "defaultValue": 0.5,
  "hideLabel": true,
  "minIcon": "speaker.fill",
  "maxIcon": "speaker.wave.3.fill",
  "formatValue": "percent",
  "tint": "#667eea"
}
```

### Seek scrubber with sync
```json
{
  "type": "slider",
  "id": "seek-slider",
  "position": [0, 0],
  "span": [1, 4],
  "min": 0,
  "max": 300,
  "step": 1,
  "defaultValue": 0,
  "label": "Position",
  "style": "scrubber",
  "tint": "#FF2D55",
  "formatValue": "time",
  "hideBackground": true,
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "player", "type": "command", "payload": { "command": "seek", "position": "{{value}}" } } },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "player_state" }, "valuePath": "elapsed" }]
}
```

## Behavior
- Action fires on drag end (default style) or continuously while dragging (scrubber style)
- Network-synced value updates animate smoothly unless the user is actively dragging
- No default haptic (system provides its own slider feedback)

## Related
- [[shared-properties]] — Base fields
- [[style-properties#Slider Fields]] — Full field reference
- [[actions]] — `{{value}}` substitution
- [[sync]] — Value sync from network
