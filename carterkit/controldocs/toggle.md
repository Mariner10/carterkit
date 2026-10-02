---
type: toggle
label: Toggle
icon: switch.2
category: controls
defaultSpan: [1, 1]
addIntent: change
friendlyName: Switch
oneLiner: Turns something on or off
addRank: 2
starterPreset: {"label": "Switch"}
fields:
  - name: animation
    title: Motion
    tab: style
    type: enum
    values: [smooth, snappy, bouncy, gentle, instant]
    description: Motion profile for value changes
  - name: label
    title: Title
    type: string
    description: Toggle label text
  - name: icon
    title: Symbol
    type: string
    description: SF Symbol
  - name: style
    title: Look
    tab: style
    type: enum
    values: [switch, button, icon-toggle]
    default: switch
    description: Display style
  - name: defaultValue
    title: Initial on/off state
    type: bool
    default: false
    description: Initial on/off state
    summary: Whether it starts on or off
  - name: onIcon
    title: Symbol when on
    styles: [button, icon-toggle]
    type: string
    description: SF Symbol when on (button and icon-toggle styles)
  - name: offIcon
    title: Symbol when off
    styles: [button, icon-toggle]
    type: string
    description: SF Symbol when off (button and icon-toggle styles)
  - name: tint
    title: Color when on
    tab: style
    type: color
    default: "#667eea"
    description: Accent color when on
  - name: hideBackground
    title: No background card
    tab: style
    type: bool
    default: false
    description: Remove glass background
  - name: haptic
    title: Vibration on tap
    tab: action
    type: enum
    values: [light, medium, heavy, rigid, success, warning, error, selection]
    default: rigid
    description: Default haptic on toggle
  - name: trackLength
    title: Track length
    tab: style
    styles: [switch]
    type: number
    min: 31
    max: 400
    step: 1
    default: 51
    description: Track extent tip-to-tip along its path (pt)
  - name: trackCurvature
    title: Track curve
    tab: style
    styles: [switch]
    type: number
    min: -180
    max: 180
    step: 5
    default: 0
    description: Degrees of bend; 0 straight, positive bows up. Clamped to what the length can bend (lengthen the track to curve it more)
  - name: trackRadius
    title: Track roundness
    tab: style
    styles: [switch]
    type: number
    min: 0
    max: 20
    step: 0.5
    default: 15.5
    description: Track corner radius; on a curved track resolves to round caps (within 0.5 pt of half thickness) or sharp square ends (below)
  - name: knobRadius
    title: Knob roundness
    tab: style
    styles: [switch]
    type: number
    min: 0
    max: 13.5
    step: 0.5
    default: 13.5
    description: Knob corner radius; 0 is a square knob, which rotates to the track's direction on curved tracks. Knob SIZE is derived from the track (fixed ratio, D45a) and is not a dial
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
  - name: borderColor
    title: Border color
    type: color
    default: #FFFFFF1A
    description: Border color
    summary: The outline around the control
  - name: labelFontSize
    title: Title text size
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
  - name: trackColor
    title: Track color
    styles: [switch]
    type: color
    default: #39393D
    description: Track background color
  - name: trackActiveColor
    title: Track color when on
    type: color
    default: #667eea
    description: Track active/on color
  - name: trackRadius
    title: Track roundness
    styles: [switch]
    min: 0
    max: 30
    step: 0.5
    type: number
    default: 15.5
    description: Track corner radius
  - name: trackHeight
    title: Track height
    styles: [switch]
    min: 16
    max: 60
    step: 1
    type: number
    default: 31
    description: Track height
    summary: How tall the switch is
  - name: trackWidth
    title: Track width
    styles: [switch]
    min: 30
    max: 100
    step: 1
    type: number
    default: 51
    description: Track width
    summary: How wide the switch is
  - name: knobColor
    title: Knob color
    styles: [switch]
    type: color
    default: #FFFFFF
    description: Knob fill color
  - name: knobRadius
    title: Knob roundness
    styles: [switch]
    min: 0
    max: 30
    step: 0.5
    type: number
    default: 13.5
    description: Knob corner radius
  - name: knobShadow
    title: Knob shadow
    styles: [switch]
    type: bool
    default: true
    description: Show knob shadow
---

# Toggle

A boolean on/off control. Stores a `.bool` value.

## Type
`"toggle"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Display label |
| `icon` | string | — | SF Symbol |
| `style` | string | `"switch"` | `"switch"`, `"button"`, `"icon-toggle"` |
| `onIcon` | string | — | SF Symbol when on (button and icon-toggle styles) |
| `offIcon` | string | — | SF Symbol when off (button and icon-toggle styles) |
| `tint` | string | `"#667eea"` | Accent color when on |
| `defaultValue` | bool | `false` | Initial state |
| `hideBackground` | bool | `false` | Remove glass background |
| `haptic` | string | `"rigid"` | Default haptic on toggle |

## Styles

### `"switch"` (default)
Standard iOS toggle switch with label above and optional icon beside.

### `"button"`
Tap-to-toggle button. Background highlights when on with a tinted glow.

### `"icon-toggle"`
Icon that swaps between `onIcon` and `offIcon` with a symbol transition animation.

## Examples

### Standard switch
```json
{
  "type": "toggle",
  "id": "lr-main",
  "position": [0, 0],
  "label": "Main Light",
  "defaultValue": true,
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "hue-bridge", "type": "light", "payload": { "room": "living", "fixture": "main", "command": "{{value}}" } } },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "room": "living", "fixture": "main" }, "valuePath": "state" }]
}
```

### Icon-toggle with custom icons
```json
{
  "type": "toggle",
  "id": "mic-mute",
  "position": [0, 0],
  "label": "Mic",
  "style": "icon-toggle",
  "onIcon": "mic.fill",
  "offIcon": "mic.slash.fill",
  "tint": "#FF3B30",
  "defaultValue": true
}
```

### Conditionally visible toggle
```json
{
  "type": "toggle",
  "id": "fan-oscillate",
  "position": [1, 1],
  "label": "Oscillate",
  "defaultValue": false,
  "visible": { "when": "fan-power", "operator": "eq", "value": true }
}
```

## Track geometry and interaction

Switch styles support `trackLength` (31–400 pt at the default theme), `trackCurvature` (−180° to 180°), `trackRadius`, and `knobRadius`. Length is measured along the path. Positive curvature bows up; negative bows down. Tight curves are limited to keep the inner track edge from collapsing. Lengthen the track to allow a larger bend.

The knob follows the curved centerline throughout taps, remote changes, and drag release; square knobs rotate with the tangent. `animation` applies to all toggle styles, including custom durations and `instant`. Reduce Motion disables travel animation.

Tap to flip, or drag and release toward an endpoint. A flick uses its projected destination; a drag released on the original side emits no action. Cancellation returns to the current state. Zero-travel tracks still respond to taps.

Knob size is always 27/31 of the themed track height. Radii clamp to half their respective sizes. Curved track caps are round when `trackRadius` is within 0.5 pt of half the track thickness, otherwise they have sharp radial ends; intermediate curved fillets are not supported. Straight tracks honor intermediate radii. Give long or deeply curved tracks enough grid space to avoid clipping.

## Related
- [[shared-properties]] — Base fields
- [[style-properties#Toggle Styles]] — Style details
- [[actions]] — `{{value}}` substitution
- [[sync]] — Live state sync
- [[conditional-visibility]] — The `visible` field
