---
type: colorPicker
label: Color Picker
icon: paintpalette.fill
category: controls
defaultSpan: [1, 1]
fields:
  - name: label
    type: string
    description: Display label
  - name: defaultValue
    type: string
    description: Initial hex color
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

# Color Picker

A color selection control. Stores a `.string` value (hex color like `"#FF6B6B"`).

## Type
`"colorPicker"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Display label |
| `defaultValue` | string | — | Initial hex color (e.g., `"#F4B860"`) |

## Example

```json
{
  "type": "colorPicker",
  "id": "lr-color",
  "position": [1, 3],
  "defaultValue": "#F4B860",
  "label": "Color",
  "action": { "method": "meshsocket", "mode": "broadcast", "event": "route_msg", "payload": { "target_id": "hue-bridge", "type": "color", "payload": { "room": "living", "hex": "{{value}}" } } }
}
```

## Behavior
- Shows the iOS system color picker on tap
- Value stored and transmitted as `#RRGGBB` hex string
- `{{value}}` in actions is the hex string

## Related
- [[shared-properties]] — Base fields
- [[actions]] — `{{value}}` substitution
