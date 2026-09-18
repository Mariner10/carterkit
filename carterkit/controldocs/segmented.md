---
type: segmentedControl
label: Segmented Control
icon: rectangle.split.3x1
category: controls
defaultSpan: [1, 2]
fields:
  - name: animation
    type: enum
    values: [smooth, snappy, bouncy, gentle, instant]
    description: Motion profile for value changes
  - name: optionLabels
    type: array
    description: Display labels parallel to options; actions and sync use the original option values
  - name: placeholder
    type: string
    description: Text shown when no options are available or a picker has no selection
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
  - name: selectedColor
    type: color
    default: #636366
    description: Selected segment fill
  - name: selectedRadius
    min: 0
    max: 30
    step: 1
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

### Friendly labels with stable server values

```json
{
  "type": "segmentedControl", "id": "drive-mode", "position": [0, 0],
  "options": ["eco", "comfort", "sport"],
  "optionLabels": ["Economy", "Comfort", "Sport"],
  "optionIcons": ["leaf", "car", "bolt"], "defaultValue": "eco"
}
```


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

## Display labels and live options

`options` contains the stored/server values. `optionLabels` supplies optional user-facing labels at the same indexes, and `optionIcons` supplies SF Symbols. Missing or empty labels fall back to the original value; missing icons are omitted. Duplicate option values use the first occurrence, preserving its label and icon. Labels themselves may repeat.

For example, `"options": ["eco", "comfort", "sport"]` with `"optionLabels": ["Economy", "Comfort", "Sport"]` displays “Economy” while storing and sending `"eco"`. VoiceOver uses the friendly label too. Selecting the already-selected value sends no extra action.

Empty options show `placeholder` (default “No options”). A picker with an empty selection shows `placeholder` (default “Choose…”); an unknown nonempty selection remains visible until the user picks an available option. Live option changes never silently select or send a replacement value.

## Related
- [[shared-properties]] — Base fields
- [[picker]] — For longer option lists
- [[actions]] — `{{value}}` substitution
