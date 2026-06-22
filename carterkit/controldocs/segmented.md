---
type: segmentedControl
label: Segmented Control
icon: rectangle.split.3x1
category: controls
defaultSpan: [1, 2]
fields:
  - name: options
    type: array
    description: Segment labels (string array)
  - name: optionIcons
    type: array
    description: SF Symbols parallel to options
  - name: style
    type: enum
    values: [default, pills]
    default: default
    description: System segmented or capsule pills
  - name: tint
    type: color
    default: "#667eea"
    description: Accent for pills style
  - name: defaultValue
    type: string
    description: Initially selected option
  - name: haptic
    type: enum
    values: [light, medium, heavy, success, warning, error, selection]
    default: selection
    description: Default haptic on change
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
  - name: selectedColor
    type: color
    default: #636366
    description: Selected segment fill
  - name: selectedRadius
    type: number
    default: 6
    description: Selected segment radius
  - name: selectedShadow
    type: bool
    default: true
    description: Selected segment shadow
  - name: textColor
    type: color
    default: #FFFFFF99
    description: Unselected text color
  - name: selectedTextColor
    type: color
    default: #FFFFFF
    description: Selected text color
---

# Segmented Control

A short option list displayed as inline segments. Stores a `.string` value.

## Type
`"segmentedControl"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `options` | string[] | required | Segment labels |
| `optionIcons` | string[] | — | SF Symbols parallel to options |
| `style` | string | `"default"` | `"default"` (system) or `"pills"` (capsule buttons) |
| `tint` | string | `"#667eea"` | Accent for pills style |
| `defaultValue` | string | — | Initially selected option |
| `haptic` | string | `"selection"` | Default haptic on change |

## Styles

### `"default"`
Standard iOS segmented picker. System-styled.

### `"pills"`
Horizontal row of capsule-shaped buttons. Selected pill gets tinted background.

## Examples

### HVAC mode selector
```json
{
  "type": "segmentedControl",
  "id": "hvac-mode",
  "position": [1, 2],
  "span": [1, 2],
  "options": ["Heat", "Cool", "Auto", "Off"],
  "defaultValue": "Auto",
  "action": { "method": "meshsocket", "mode": "request", "event": "route_msg", "payload": { "target_id": "ecobee", "type": "set_mode", "payload": { "mode": "{{value}}" } } }
}
```

### Fan speed with icons
```json
{
  "type": "segmentedControl",
  "id": "fan-speed",
  "position": [0, 1],
  "span": [1, 3],
  "options": ["Low", "Med", "High"],
  "optionIcons": ["wind", "wind", "wind"],
  "style": "pills",
  "defaultValue": "Med"
}
```

## Notes
- Best for 2-5 options. For longer lists, use [[picker]] instead.
- Value is the string text of the selected option.

## Related
- [[shared-properties]] — Base fields
- [[picker]] — For longer option lists
- [[actions]] — `{{value}}` substitution
