---
type: toggle
label: Toggle
icon: switch.2
category: controls
defaultSpan: [1, 1]
fields:
  - name: label
    type: string
    description: Toggle label text
  - name: icon
    type: string
    description: SF Symbol
  - name: style
    type: enum
    values: [switch, button, icon-toggle]
    default: switch
    description: Display style
  - name: defaultValue
    type: bool
    default: false
    description: Initial on/off state
  - name: onIcon
    type: string
    description: SF Symbol when on (icon-toggle style)
  - name: offIcon
    type: string
    description: SF Symbol when off (icon-toggle style)
  - name: tint
    type: color
    default: "#667eea"
    description: Accent color when on
  - name: hideBackground
    type: bool
    default: false
    description: Remove glass background
  - name: haptic
    type: enum
    values: [light, medium, heavy, rigid, success, warning, error, selection]
    default: rigid
    description: Default haptic on toggle
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
  - name: trackActiveColor
    type: color
    default: #667eea
    description: Track active/on color
  - name: trackRadius
    type: number
    default: 15.5
    description: Track corner radius
  - name: trackHeight
    type: number
    default: 31
    description: Track height
  - name: trackWidth
    type: number
    default: 51
    description: Track width
  - name: knobColor
    type: color
    default: #FFFFFF
    description: Knob fill color
  - name: knobRadius
    type: number
    default: 13.5
    description: Knob corner radius
  - name: knobSize
    type: number
    default: 27
    description: Knob diameter
  - name: knobShadow
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
| `onIcon` | string | — | SF Symbol when on (icon-toggle style) |
| `offIcon` | string | — | SF Symbol when off (icon-toggle style) |
| `tint` | string | `"#667eea"` | Accent color when on |
| `defaultValue` | bool | — | Initial state |
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
  "action": { "method": "meshsocket", "mode": "request", "event": "route_msg", "payload": { "target_id": "hue-bridge", "type": "light", "payload": { "room": "living", "fixture": "main", "command": "{{value}}" } } },
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

## Related
- [[shared-properties]] — Base fields
- [[style-properties#Toggle Styles]] — Style details
- [[actions]] — `{{value}}` substitution
- [[sync]] — Live state sync
- [[conditional-visibility]] — The `visible` field
