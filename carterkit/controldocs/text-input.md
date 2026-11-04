---
type: textInput
label: Text Input
icon: character.cursor.ibeam
category: controls
defaultSpan: [1, 2]
addIntent: change
pickerCategory: Inputs
depth: complete
friendlyName: Text box
oneLiner: Type something in
aliases: [text field, input, textbox, entry, type, search box]
addRank: 5
starterPreset: {"label": "Text box","placeholder": "Type here"}
fields:
  - name: placeholder
    edit: inline
    depth: surface
    type: string
    description: Placeholder text when empty
    summary: The faint hint inside an empty box
    does: "Shows this text in grey inside the field until something is typed."
  - name: label
    edit: inline
    depth: surface
    type: string
    description: Display label
    summary: The name shown above the box
    does: "Writes this text in the header above the field."
  - name: icon
    edit: symbol
    depth: hold
    under: label
    type: string
    description: SF Symbol shown in the field
    summary: A small picture at the start of the box
    does: "Shows this SF Symbol at the left inside the field."
  - name: defaultValue
    type: string
    description: Initial text
    summary: What is already typed when it first appears
    does: "Pre-fills the field with this text when the layout first appears."
  - name: style
    edit: look
    depth: surface
    tab: style
    type: enum
    values: [default, search, multiline]
    default: default
    description: Display style variant
    summary: Which kind of box it is
    does: "Switches between a plain field, a search field, or a tall multi-line field."
    valueHelp: {"default": "a plain single-line field with a rounded background", "search": "a field with a magnifying glass and a clear button", "multiline": "a tall field that grows for several lines of text"}
  - name: sendButton
    type: bool
    default: false
    description: Growing composer with a Send button (Return inserts a newline)
    summary: A chat-style box with a Send button
    does: "On, adds a Send button and makes Return start a new line; off, Return submits."
  - name: minLines
    min: 1
    max: 20
    step: 1
    type: number
    default: 1
    description: Composer starting line count
    summary: How tall the box starts
    does: "Sets how many text lines tall the composer is when empty, from 1 to 20."
  - name: maxLines
    min: 1
    max: 50
    step: 1
    type: number
    default: 6
    description: Composer max lines before it scrolls internally
    summary: How tall the box can grow
    does: "Lets the composer grow up to this many lines (1 to 50) before it scrolls inside."
  - name: autocorrect
    type: bool
    default: false
    description: Default autocorrect/caps (off = ASCII keyboard, terminal-friendly)
    summary: Whether the keyboard fixes your typing
    does: "On, the keyboard corrects and capitalizes words; off, it uses a plain ASCII keyboard."
  - name: autocorrectToggle
    type: bool
    default: false
    description: Inline Aa button that flips autocorrect on the live keyboard
    summary: A tiny button to switch typing help on the fly
    does: "Shows an Aa button that turns autocorrect on or off while the keyboard is open."
  - name: keyboard
    type: enum
    values: [ascii, default, url, email, numbers]
    description: Keyboard type
    summary: Which keys appear when you tap the box
    does: "Chooses the on-screen keyboard layout, such as email or number keys."
    valueHelp: {"ascii": "plain letters and symbols with no suggestions", "default": "the standard iPhone keyboard", "url": "keys for web addresses with a slash and dot", "email": "keys for email with an at sign", "numbers": "a number pad"}
  - name: clearOnSubmit
    tab: action
    type: bool
    default: false
    description: Clear the field after the return-key submit
    summary: Whether the box empties after sending
    does: "Empties the field right after you press return to submit."
  - name: tint
    edit: color
    depth: surface
    tab: style
    type: color
    default: "#667eea"
    description: Accent color
    summary: The accent color of the box
    does: "Colors the cursor, search icon and Send button with this color."
  - name: hideBackground
    edit: part
    depth: hold
    tab: style
    type: bool
    default: false
    description: Remove glass background
    summary: Lets the box sit directly on the page
    does: "Removes the frosted card behind the field so it floats on the page."
  - name: hideLabel
    edit: part
    depth: hold
    type: bool
    default: false
    description: Hide the header label
    summary: Takes the name off the top
    does: "Removes the header row so only the field itself shows."
  - name: confirm
    title: Show confirmation
    tab: action
    type: bool
    default: false
    summary: A short note with Undo after each tap
    description: After this control's local write lands, show a pill naming the change with an Undo button for 3 seconds (default off)
    does: "Shows a pill naming the change with an Undo button for 3 seconds after you submit."
themeFields:
  - name: cornerRadius
    edit: scrub
    depth: hold
    under: style
    unit: pt
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
    summary: How round the card corners are
    does: "Rounds the card corners from 0 (square) to 30 points."
  - name: controlPadding
    min: 0
    max: 24
    step: 1
    type: number
    default: 8
    description: Internal padding
    summary: Breathing room inside the card
    does: "Adds 0 to 24 points of space between the card edge and the field."
  - name: surfacePrimary
    type: color
    default: #FFFFFF0F
    description: Background fill
    summary: The fill behind the box
    does: "Paints the card behind the field with this color."
  - name: foregroundColor
    type: color
    default: #FFFFFF
    description: Primary text color
    summary: The color of typed text
    does: "Colors the typed text and label with this color."
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Secondary text color
    summary: The color of the hint text
    does: "Colors the placeholder and secondary icons with this color."
  - name: borderColor
    type: color
    default: #FFFFFF1A
    description: Border color
    summary: The outline color
    does: "Draws the card outline in this color."
  - name: borderWidth
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
    summary: How thick the outline is
    does: "Sets the outline thickness from 0 (none) to 5 points."
  - name: labelFontSize
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
    summary: How big the name above the box is
    does: "Sets the header label text size from 8 to 24 points."
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

## Examples

### Device name field

Shows a pre-filled value (`defaultValue`), an icon and a placeholder; pressing return broadcasts the typed text through `{{value}}`.

```json
{
  "type": "textInput",
  "id": "device-name",
  "position": [1, 0],
  "span": [1, 2],
  "placeholder": "Device name",
  "defaultValue": "my-device",
  "icon": "tag",
  "action": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "device_name", "name": "{{value}}" } }
}
```

### Command composer

A growing chat-style box: Send submits, Return adds a newline, and the **Aa** button flips autocorrect on the live keyboard.

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
  "action": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "command", "text": "{{value}}" } }
}
```

### Search box

The `search` look adds a magnifying glass and a clear button, and the field empties itself after each submit (`clearOnSubmit`).

```json
{
  "type": "textInput",
  "id": "search-box",
  "position": [2, 0],
  "span": [1, 2],
  "label": "Search",
  "placeholder": "Search…",
  "style": "search",
  "clearOnSubmit": true,
  "action": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "search", "q": "{{value}}" } }
}
```

### Notes area

The `multiline` look gives a tall field for several lines of prose, with autocorrect on and the header label hidden.

```json
{
  "type": "textInput",
  "id": "notes",
  "position": [3, 0],
  "span": [2, 2],
  "placeholder": "Jot a note",
  "style": "multiline",
  "autocorrect": true,
  "hideLabel": true,
  "hideBackground": true
}
```

### Email field with confirmation

The `email` keyboard shows the @ key, and `confirm` pops an Undo pill for 3 seconds after submit; `tint` colors the accent.

```json
{
  "type": "textInput",
  "id": "email-entry",
  "position": [4, 0],
  "span": [1, 2],
  "label": "Email",
  "placeholder": "you@example.com",
  "keyboard": "email",
  "tint": "#34c759",
  "confirm": true,
  "action": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "email", "address": "{{value}}" } }
}
```

### Other keyboards

`keyboard` can also be `url` (web address keys) or `numbers` (number pad); `ascii` and `default` pick plain or standard keys. Use the email example above as the pattern and change only `keyboard`.

### Notes on hidden-looking fields

`minLines` and `maxLines` only matter when `sendButton` is on; `icon` shows in the default and search looks.

## Behavior
- Default field: the action fires when the user presses return/submit
- Composer (`sendButton: true`): **Send** submits and **Return inserts a newline**
- The `{{value}}` placeholder is replaced with the current text content

## Related
- [[shared-properties]] — Base fields
- [[actions]] — `{{value}}` substitution
