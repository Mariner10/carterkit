---
type: picker
label: Picker
icon: list.bullet
category: controls
defaultSpan: [1, 2]
fields:
  - name: options
    type: array
    description: Available choices (string array)
  - name: pickerStyle
    type: enum
    values: [menu, wheel, inline]
    default: menu
    description: Display style
  - name: label
    type: string
    description: Display label
  - name: tint
    type: color
    default: "#667eea"
    description: Accent color
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

# Picker

A scrollable selection for long option lists. Stores a `.string` value.

## Type
`"picker"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `options` | string[] | required | Available choices |
| `pickerStyle` | string | `"menu"` | `"menu"`, `"wheel"`, `"inline"` |
| `label` | string | — | Display label |
| `tint` | string | `"#667eea"` | Accent color |
| `defaultValue` | string | — | Initially selected option |
| `haptic` | string | `"selection"` | Default haptic on change |

## Styles

| Value | Description |
|-------|-------------|
| `"menu"` | Dropdown menu (compact, default) |
| `"wheel"` | Spinning wheel picker |
| `"inline"` | Inline scrollable list |

## Examples

### Room selector (menu)
```json
{
  "type": "picker",
  "id": "room-select",
  "position": [0, 0],
  "span": [1, 2],
  "options": ["Living Room", "Bedroom", "Kitchen", "Bathroom", "Office", "Garage", "Patio"],
  "defaultValue": "Living Room",
  "label": "Room",
  "action": { "method": "meshsocket", "mode": "request", "event": "switch_room", "payload": { "room": "{{value}}" } }
}
```

### Playlist picker (wheel)
```json
{
  "type": "picker",
  "id": "playlist",
  "position": [0, 0],
  "span": [2, 4],
  "options": ["Chill", "Focus", "Workout", "Party", "Sleep", "Jazz", "Classical"],
  "pickerStyle": "wheel",
  "defaultValue": "Chill",
  "label": "Playlist"
}
```

## Notes
- For 2-5 options, prefer [[segmented-control]] for better space efficiency
- Value is the string text of the selected option

## Related
- [[shared-properties]] — Base fields
- [[segmented-control]] — For shorter option lists
- [[actions]] — `{{value}}` substitution
