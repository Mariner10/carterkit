---
type: slider
label: Slider
icon: slider.horizontal.3
category: controls
defaultSpan: [1, 2]
fields:
  - name: animation
    type: enum
    values: [smooth, snappy, bouncy, gentle, instant]
    description: Motion profile for value changes
  - name: min
    bounds: none
    type: number
    default: 0
    description: Minimum value
  - name: max
    bounds: none
    type: number
    default: 100
    description: Maximum value
  - name: step
    bounds: none
    type: number
    default: 1
    description: Detent spacing measured from min; zero or negative allows continuous values
  - name: continuous
    type: bool
    default: true
    description: Send actions while dragging; false previews locally and sends once on release
  - name: hideValue
    type: bool
    default: false
    description: Hide numeric readouts in every slider style; keep the label and interaction
  - name: label
    type: string
    description: Header label
  - name: defaultValue
    bounds: none
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
    styles: [default]
    type: string
    description: SF Symbol at minimum end
  - name: maxIcon
    styles: [default]
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
    styles: [radial]
    min: 1
    max: 360
    step: 1
    type: number
    default: 270
    description: Arc sweep in degrees (radial style only)
  - name: arcRotation
    styles: [radial]
    min: -180
    max: 180
    step: 1
    type: number
    default: 0
    description: Arc start rotation (radial style only)
  - name: arcThickness
    styles: [radial]
    min: 1
    max: 40
    step: 1
    type: number
    default: 8
    description: Track stroke width (radial style only)
themeFields:
  - name: cornerRadius
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
  - name: controlPadding
    min: 0
    max: 24
    step: 1
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
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
  - name: trackColor
    type: color
    default: #39393D
    description: Track background color
  - name: trackHeight
    styles: [default]
    min: 4
    max: 60
    step: 1
    type: number
    default: 31
    description: Track height
  - name: thumbColor
    styles: [default]
    type: color
    default: #FFFFFF
    description: Thumb fill color
  - name: thumbRadius
    styles: [default]
    min: 0
    max: 30
    step: 1
    type: number
    default: 14
    description: Thumb corner radius
  - name: thumbSize
    styles: [default]
    min: 12
    max: 50
    step: 1
    type: number
    default: 28
    description: Thumb diameter
  - name: thumbShadow
    styles: [default]
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

### Send a seek command only on release

```json
{
  "type": "slider", "id": "seek", "position": [0, 0],
  "label": "Playback", "min": 0, "max": 300, "step": 1,
  "style": "scrubber", "formatValue": "time", "continuous": false
}
```


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
- With `continuous: true` (default), all styles send actions as the dragged value changes, plus one final action on release. Repeated movement within the same detent does not send extra change actions.
- With `continuous: false`, the thumb and local value preview throughout the drag, but only release sends an action. Cancellation or removal restores the starting value without sending an action, unless a newer remote value has replaced the preview. VoiceOver adjustments remain immediate.
- `hideValue: true` hides header and radial readouts while retaining the label and spoken value.
- Positive `step` snaps relative to `min`; `step <= 0` is continuous. Values always stay within the range, and both endpoints are reachable even when the span is not a multiple of `step`.
- Reversed bounds are sorted; equal bounds produce a fixed value. Incoming values outside the range are clamped for display without writing back during rendering.
- All styles animate remote changes. Radial fill and thumb move together along the arc; dragging follows the finger immediately. Reduce Motion disables travel animation. Arc sweep clamps to 1–360° and thickness to 1–40 pt.
- Drag cancellation and removal end the editing session, allowing the attribute editor to close its undo group.
- Network-synced value updates animate smoothly unless the user is actively dragging
- No default haptic (system provides its own slider feedback)

## Related
- [[shared-properties]] — Base fields
- [[style-properties#Slider Fields]] — Full field reference
- [[actions]] — `{{value}}` substitution
- [[sync]] — Value sync from network
