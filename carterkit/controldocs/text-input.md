---
type: textInput
label: Text Input
icon: character.cursor.ibeam
category: controls
defaultSpan: [1, 2]
fields:
  - name: placeholder
    type: string
    description: Placeholder text when empty
  - name: label
    type: string
    description: Display label
  - name: icon
    type: string
    description: SF Symbol shown in the field
  - name: defaultValue
    type: string
    description: Initial text
  - name: style
    type: enum
    values: [default, search, multiline]
    default: default
    description: Display style variant
  - name: tint
    type: color
    default: "#667eea"
    description: Accent color
  - name: hideBackground
    type: bool
    default: false
    description: Remove glass background
  - name: hideLabel
    type: bool
    default: false
    description: Hide the header label
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

# Text Input

A free text entry field. Stores a `.string` value. Fires action on submit (return key).

## Type
`"textInput"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `placeholder` | string | — | Placeholder text when empty |
| `label` | string | — | Display label |
| `icon` | string | — | SF Symbol shown in the field |
| `defaultValue` | string | — | Initial text |
| `style` | string | `"default"` | `"default"`, `"search"`, `"multiline"` |
| `tint` | string | `"#667eea"` | Accent color |
| `clearOnSubmit` | bool | `false` | Clear the field after the return-key submit (for entry forms where the typed value shouldn't linger) |
| `hideBackground` | bool | `false` | Remove glass background |
| `hideLabel` | bool | `false` | Hide the header label |

## Styles

### `"default"`
Standard single-line text field with rounded background.

### `"search"`
Search-style field with magnifying glass icon and clear button.

### `"multiline"`
Expands vertically for multi-line text entry.

## Example

```json
{
  "type": "textInput",
  "id": "device-name",
  "position": [1, 0],
  "span": [1, 2],
  "placeholder": "Device name",
  "defaultValue": "my-device",
  "icon": "tag",
  "action": { "method": "meshsocket", "mode": "request", "event": "identify", "payload": { "name": "{{value}}" } }
}
```

## Behavior
- Action fires when the user presses return/submit
- The `{{value}}` placeholder is replaced with the current text content

## Related
- [[shared-properties]] — Base fields
- [[actions]] — `{{value}}` substitution
