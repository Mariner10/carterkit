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
  - name: sendButton
    type: bool
    default: false
    description: Growing composer with a Send button (Return inserts a newline)
  - name: minLines
    type: number
    default: 1
    description: Composer starting line count
  - name: maxLines
    type: number
    default: 6
    description: Composer max lines before it scrolls internally
  - name: autocorrect
    type: bool
    default: false
    description: Default autocorrect/caps (off = ASCII keyboard, terminal-friendly)
  - name: autocorrectToggle
    type: bool
    default: false
    description: Inline Aa button that flips autocorrect on the live keyboard
  - name: keyboard
    type: enum
    values: [ascii, default, url, email, numbers]
    description: Keyboard type
  - name: clearOnSubmit
    type: bool
    default: false
    description: Clear the field after the return-key submit
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
| `sendButton` | bool | `false` | Turn the field into a growing composer with a Send button (Return = newline) |
| `minLines` | int | `1` | Composer starting line count |
| `maxLines` | int | `6` | Composer max lines before it scrolls internally |
| `autocorrect` | bool | `false` | Default autocorrect/caps; off ⇒ ASCII keyboard (terminal-friendly) |
| `autocorrectToggle` | bool | `false` | Show the inline **Aa** toggle |
| `keyboard` | string | — | `"ascii"`, `"default"`, `"url"`, `"email"`, `"numbers"` |
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

## Composer & keyboard

Set `sendButton: true` to turn the field into a **growing composer**: it grows from `minLines`
up to `maxLines` then scrolls inside, **Return inserts a newline**, and a **Send** button
submits. Ideal for chat or command entry.

Keyboard behaviour, tuned for command entry:

- **`autocorrect`** defaults to `false` — autocorrect/autocapitalization off with an ASCII
  keyboard, so typed commands aren't "corrected." Set `true` for prose. `keyboard` overrides
  the keyboard type explicitly.
- **`autocorrectToggle`** shows an inline **Aa** button that flips autocorrect at runtime and
  reconfigures the **live** keyboard immediately (no refocus needed). It also appears on the
  above-keyboard bar.
- An above-keyboard **Hide** button lets you dismiss the keyboard to reach the
  controls/tabs underneath it.

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

### Command composer
```json
{
  "type": "textInput",
  "id": "pane-input",
  "position": [7, 0],
  "span": [1, 4],
  "placeholder": "type a command…",
  "icon": "chevron.right",
  "sendButton": true,
  "autocorrectToggle": true,
  "autocorrect": false,
  "maxLines": 6,
  "action": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast", "payload": { "msg_type": "command", "text": "{{value}}" } }
}
```

## Behavior
- Default field: the action fires when the user presses return/submit
- Composer (`sendButton: true`): **Send** submits and **Return inserts a newline**
- The `{{value}}` placeholder is replaced with the current text content

## Related
- [[shared-properties]] — Base fields
- [[actions]] — `{{value}}` substitution
