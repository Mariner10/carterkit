---
type: joystick
label: Joystick
icon: dpad.fill
category: controls
defaultSpan: [2, 2]
fields:
  - name: label
    type: string
    description: Header label
  - name: tint
    type: color
    default: "#667eea"
    description: Stick and track color
  - name: style
    type: enum
    values: [analog, dpad]
    default: analog
    description: "analog (free) or dpad (4/8-direction snapping)"
  - name: deadzone
    type: number
    default: 0.1
    description: Center deadzone radius (0-1)
  - name: sticky
    type: bool
    default: false
    description: Stick stays where released instead of snapping to center
  - name: sendRate
    type: number
    default: 0.1
    description: Throttle interval in seconds for action firing
  - name: hideLabel
    type: bool
    default: false
    description: Hide label and coordinate readout
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

# Joystick

A virtual analog stick or directional pad for continuous 2D input. Fires throttled actions with `x` and `y` values ranging from -1 to 1.

## Type
`"joystick"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | falls back to `id` | Header label |
| `tint` | color | `"#667eea"` | Stick and track color |
| `style` | string | `"analog"` | `"analog"` (free) or `"dpad"` (4/8-direction snapping) |
| `deadzone` | number | `0.1` | Center deadzone radius (0-1) |
| `sticky` | bool | `false` | Stick stays where released instead of snapping to center |
| `sendRate` | number | `0.1` | Throttle interval in seconds for action firing |
| `hideLabel` | bool | `false` | Hide label and coordinate readout |

## Examples

### Robot drive controller
```json
{
  "type": "joystick",
  "id": "drive-stick",
  "position": [0, 0],
  "span": [2, 2],
  "label": "Drive",
  "tint": "#FF2D55",
  "style": "analog",
  "deadzone": 0.15,
  "sendRate": 0.05,
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "robot", "type": "drive", "payload": { "x": "$value.x", "y": "$value.y" } } }
}
```

## Related
- [[shared-properties]] — Base fields
- [[actions]] — Action definition
