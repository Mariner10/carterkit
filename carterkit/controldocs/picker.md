---
type: picker
label: Picker
icon: list.bullet
category: controls
defaultSpan: [1, 2]
addIntent: change
pickerCategory: Inputs
depth: complete
friendlyName: Menu
oneLiner: Pick one from a list
aliases: [dropdown, select, menu, choose, options, combo box]
addRank: 7
starterPreset: {"label": "Menu","options": ["One","Two","Three"]}
io:
  - emits: value
    when: pick
    title: When you pick an option
    type: string
    says: the option you picked, as its stored value
    example: "Item 1"
    also: Picking the option already chosen sends nothing
    since: next
  - receives: value
    role: follow
    type: string
    from: [hub, mqtt, http, store, default]
    says: the stored value of the option to select
    reacts: that option becomes the selected one without sending; your next pick replaces it
    example: "Item 1"
    since: next
  - sample: "Item 1"
fields:
  - name: animation
    title: Motion
    tab: style
    type: enum
    values: [smooth, snappy, bouncy, gentle, instant]
    description: Motion profile for value changes
    summary: How the choice change animates
    does: "Sets how the shown choice transitions when the value changes, from instant swap to a soft glide."
    valueHelp: {"smooth": "an even natural transition", "snappy": "a quick firm change", "bouncy": "overshoots slightly then settles", "gentle": "a slow soft change", "instant": "swaps with no transition"}
    valueTitles: {"smooth": "Smooth", "snappy": "Snappy", "bouncy": "Bouncy", "gentle": "Gentle", "instant": "Instant"}
    valueSymbols: {"smooth": "water.waves", "snappy": "bolt.fill", "bouncy": "arrow.up.and.down.circle", "gentle": "wind", "instant": "forward.end.fill"}
  - name: optionIcons
    title: Choice symbols
    type: array
    description: Optional SF Symbols parallel to options, supported in every picker style
    summary: A small picture beside each choice
    does: "Shows the SF Symbol at the same position next to each choice, in every look; a blank or missing entry shows no icon."
  - name: optionLabels
    title: Choice names
    type: array
    description: Display labels parallel to options; actions and sync use the original option values
    summary: Display names for the choices, in the same order
    does: "Shows these names instead of the stored values; the original value is still what is saved and sent."
  - name: placeholder
    title: Empty text
    type: string
    description: Text shown when no options are available or a picker has no selection
    summary: What shows when nothing is chosen
    does: "Writes this text when the list is empty (default No options) or nothing is selected (default Choose…)."
  - name: options
    chip: Options
    edit: rows
    columns: [{"name": "value", "title": "Choice", "type": "string", "edit": "inline", "self": true, "default": "Option {n}"}, {"name": "label", "title": "Shown as", "type": "string", "edit": "inline", "in": "optionLabels"}, {"name": "icon", "title": "Symbol", "type": "string", "edit": "symbol", "in": "optionIcons"}]
    depth: surface
    title: Choices
    type: array
    description: Available choices (string array)
    summary: The list of things you can pick
    does: "Fills the menu, wheel or list with one row per entry; the picked entry is the value stored and sent."
  - name: pickerStyle
    edit: look
    depth: surface
    title: Look
    tab: style
    type: enum
    values: [menu, wheel, inline]
    default: menu
    description: Display style
    summary: How the list is shown
    does: "Switches between a compact dropdown, a spinning wheel, or a list shown in full."
    valueHelp: {"menu": "a compact button that opens a dropdown", "wheel": "a spinning drum you scroll to a choice", "inline": "every choice shown as a tappable list"}
    valueTitles: {"menu": "Menu", "wheel": "Wheel", "inline": "Inline"}
    valueSymbols: {"menu": "list.bullet.rectangle", "wheel": "dial.medium", "inline": "list.bullet"}
  - name: label
    edit: inline
    depth: surface
    title: Label
    type: string
    description: Display label
    summary: The name shown with the picker
    does: "Writes this text as the picker title."
  - name: tint
    title: Color
    edit: color
    depth: surface
    tab: style
    type: color
    default: "#667eea"
    description: Accent color
    summary: The highlight color
    does: "Colors the selected choice and the picker accent with this color."
  - name: defaultValue
    title: Starting choice
    type: string
    description: Initially selected option
    summary: Which choice is picked at first
    does: "Selects this choice when the layout first appears; it should match one of the stored values."
  - name: haptic
    title: Tap feel
    tab: action
    type: enum
    values: [light, medium, heavy, { value: rigid, since: next }, { value: soft, since: next }, success, warning, error, selection]
    default: selection
    description: Default haptic on change
    summary: The buzz felt when you change the choice
    does: "Plays this haptic on the phone each time a new choice is picked (default selection)."
    valueHelp: {"rigid": "a firm sharp click", "soft": "a gentle cushioned tap", "light": "a faint tap", "medium": "a firm tap", "heavy": "a strong thud", "success": "a happy double tap", "warning": "a cautionary buzz", "error": "a sharp triple buzz", "selection": "a tiny tick like scrolling a wheel"}
    valueTitles: {"rigid": "Rigid", "soft": "Soft", "light": "Light", "medium": "Medium", "heavy": "Heavy", "success": "Success", "warning": "Warning", "error": "Error", "selection": "Selection"}
    valueSymbols: {"rigid": "square.fill", "soft": "cloud.fill", "light": "circle", "medium": "circle.fill", "heavy": "circle.inset.filled", "success": "checkmark.circle", "warning": "exclamationmark.triangle", "error": "xmark.octagon", "selection": "hand.tap"}
  - name: hideLabel
    since: next
    edit: part
    depth: hold
    title: Title shown
    type: bool
    default: false
    description: Hide the label
    summary: Hide the title
    does: Hides the label text above the control.
  - name: hideBackground
    since: next
    edit: part
    depth: hold
    title: No background card
    type: bool
    default: false
    description: Remove glass background
    summary: Whether the card behind it is drawn
    does: Removes the frosted card behind the control so it sits on the page.
  - use: confirm
    does: "Shows a pill naming the change with an Undo button for 3 seconds after you pick a choice."
themeFields:
  - name: cornerRadius
    title: Corner roundness
    unit: pt
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
    summary: How round the card corners are
    does: "Rounds the card corners from 0 (square) to 30 points."
  - use: controlPadding
    summary: Space between the card edge and the content
    does: "Sets the padding inside the card from 0 to 24 points."
  - use: surfacePrimary
    does: "Fills the card behind the picker with this color."
  - use: accentColor
    summary: The highlight color
    does: "Sets the accent used for the picker highlights."
  - use: secondaryColor
    does: "Colors the quieter text such as the placeholder and value."
  - use: borderColor
  - name: borderWidth
    title: Border thickness
    unit: pt
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
    summary: How heavy the outline is
    does: "Sets the outline thickness from 0 to 5 points."
  - use: labelFontSize
    summary: How big the label is
    does: "Sets the label text size from 8 to 24 points."
colorSlots:
  - slot: fill
    default: primary
    alias: tint
    since: next
    summary: The highlight color
    does: Tints the menu, wheel and inline choices; until set it follows the primary role.
---

# Picker

A scrollable selection for long option lists. Stores a `.string` value.

## Type
`"picker"`

## Relevant Fields
Inherits all [[shared-fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `options` | string[] | required | Available choices |
| `pickerStyle` | string | `"menu"` | `"menu"`, `"wheel"`, `"inline"` |
| `label` | string | — | Display label |
| `tint` | string | `"#667eea"` | Accent color |
| `defaultValue` | string | — | Initially selected option |
| `haptic` | string | `"selection"` | Default haptic on change |
| `confirm` | bool | `false` | "Show confirmation": after each local write, a 3-second pill naming the change, with Undo. See [[actions#Confirmation and Undo]] |

## Styles

| Value | Description |
|-------|-------------|
| `"menu"` | Dropdown menu (compact, default) |
| `"wheel"` | Spinning wheel picker |
| `"inline"` | Inline scrollable list |

## Examples

### Friendly labels with stable server values
Shows `optionLabels` and `optionIcons`: the menu reads Economy, Comfort and Sport with a symbol each, while `eco`, `comfort` or `sport` is what is stored and sent.

```json
{
  "type": "picker", "id": "drive-mode", "position": [0, 0],
  "options": ["eco", "comfort", "sport"],
  "optionLabels": ["Economy", "Comfort", "Sport"],
  "optionIcons": ["leaf", "car", "bolt"], "defaultValue": "eco"
}
```

### Room selector (menu)
Shows the default menu look with an action: picking a room broadcasts a `switch_room` message carrying the chosen name.

```json
{
  "type": "picker",
  "id": "room-select",
  "position": [0, 0],
  "span": [1, 2],
  "options": ["Living Room", "Bedroom", "Kitchen", "Bathroom", "Office", "Garage", "Patio"],
  "defaultValue": "Living Room",
  "label": "Room",
  "action": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "switch_room", "room": "{{value}}" } }
}
```

### Playlist picker (wheel)
Shows the wheel look: a spinning drum you scroll to a playlist, starting on Chill.

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

### Inline list
Shows the inline look: every choice is visible as a tappable list, with a custom tint and a success haptic on change.

```json
{
  "type": "picker", "id": "fan-mode", "position": [0, 0], "span": [2, 3],
  "options": ["Auto", "Low", "Medium", "High"], "pickerStyle": "inline",
  "label": "Fan", "tint": "#34C759", "haptic": "success", "defaultValue": "Auto"
}
```

### Placeholder with undo
Shows `placeholder` and `confirm`: with no starting choice the picker reads "Pick a scene", and each pick shows an Undo pill for 3 seconds.

```json
{
  "type": "picker", "id": "scene", "position": [0, 0],
  "options": ["Movie", "Dinner", "Reading"], "placeholder": "Pick a scene",
  "label": "Scene", "confirm": true, "animation": "snappy"
}
```

### Themed picker
Shows `theme` overrides: rounder corners, more padding and a thicker border in a custom accent for a bolder card.

```json
{
  "type": "picker", "id": "themed-pick", "position": [0, 0],
  "options": ["Day", "Night"], "label": "Mode",
  "theme": { "cornerRadius": 24, "controlPadding": 14, "borderWidth": 2, "borderColor": "#667eea", "accentColor": "#FF9500", "labelFontSize": 16 }
}
```

## Notes
- `haptic` and `animation` have no visible effect in the wheel look beyond the system wheel feel; the picker has no long-press or detail view
- For 2-5 options, prefer [[segmented-control]] for better space efficiency
- Value is the string text of the selected option

## Display labels and live options

`options` contains the stored/server values. `optionLabels` supplies optional user-facing labels at the same indexes, and `optionIcons` supplies SF Symbols. Missing or empty labels fall back to the original value; missing icons are omitted. Duplicate option values use the first occurrence, preserving its label and icon. Labels themselves may repeat.

For example, `"options": ["eco", "comfort", "sport"]` with `"optionLabels": ["Economy", "Comfort", "Sport"]` displays “Economy” while storing and sending `"eco"`. VoiceOver uses the friendly label too. Selecting the already-selected value sends no extra action.

Empty options show `placeholder` (default “No options”). A picker with an empty selection shows `placeholder` (default “Choose…”); an unknown nonempty selection remains visible until the user picks an available option. Live option changes never silently select or send a replacement value.

## Related
- [[shared-fields]] — Base fields
- [[segmented-control]] — For shorter option lists
- [[actions]] — `{{value}}` substitution
