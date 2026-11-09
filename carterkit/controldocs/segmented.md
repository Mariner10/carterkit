---
type: segmentedControl
depth: complete
label: Segmented Control
icon: rectangle.split.3x1
category: controls
defaultSpan: [1, 2]
addIntent: change
pickerCategory: Inputs
friendlyName: Choice
oneLiner: Pick one of a few options
aliases: [tabs, tab bar, choice, options, radio, switcher]
addRank: 6
starterPreset: {"options": ["One","Two","Three"]}
io:
  - emits: value
    when: pick
    title: When you pick a choice
    type: string
    says: the stored value of the choice you tapped (not its friendly label)
    example: "One"
    also: Tapping the choice that is already selected sends nothing
    since: next
  - receives: value
    role: follow
    type: string
    from: [hub, mqtt, http, store, default]
    says: the stored value of the choice to select
    reacts: that segment lights up without sending anything; a value that matches no choice stays shown until you pick one
    example: "One"
    since: next
  - sample: One
    next: Two
fields:
  - name: animation
    tab: style
    type: enum
    values: [smooth, snappy, bouncy, gentle, instant]
    description: Motion profile for value changes
    summary: How the highlight slides between choices
    does: The selected highlight eases to a new choice; instant makes it jump with no travel.
    valueHelp: {"smooth": "an even ease", "snappy": "a quick move that settles fast", "bouncy": "overshoots slightly then springs back", "gentle": "a slow and soft glide", "instant": "jumps straight to the new choice with no travel"}
    valueTitles: {"smooth": "Smooth", "snappy": "Snappy", "bouncy": "Bouncy", "gentle": "Gentle", "instant": "Instant"}
    valueSymbols: {"smooth": "water.waves", "snappy": "bolt.fill", "bouncy": "arrow.up.and.down.circle", "gentle": "wind", "instant": "forward.end.fill"}
  - name: optionLabels
    type: array
    description: Display labels parallel to options; actions and sync use the original option values
    does: Each segment shows this text in place of its stored value; a blank entry falls back to the value.
    summary: Display names for the choices, in the same order
  - name: placeholder
    type: string
    description: Text shown when no options are available or a picker has no selection
    summary: Words shown when there is nothing to pick
    does: Shows this text, e.g. No options, where the segments would be when the list is empty.
  - name: options
    chip: Options
    edit: rows
    columns: [{"name": "value", "title": "Choice", "type": "string", "edit": "inline", "self": true, "default": "Option {n}"}, {"name": "label", "title": "Shown as", "type": "string", "edit": "inline", "in": "optionLabels"}, {"name": "icon", "title": "Symbol", "type": "string", "edit": "symbol", "in": "optionIcons"}]
    depth: surface
    title: Choices
    type: array
    description: Segment labels (string array)
    summary: The choices you can tap
    does: Creates one segment per entry, in order; two to five fit best.
  - name: optionIcons
    type: array
    description: SF Symbols parallel to options
    summary: Small pictures on the choices
    does: Draws an SF Symbol on each segment at the same position as its option; missing entries show none.
  - name: style
    edit: look
    depth: surface
    tab: style
    type: enum
    values: [default, pills, stars]
    default: default
    description: System segmented, capsule pills, or tap-a-star rating (options "1"…"N"; sends the number)
    summary: Plain bar, round pills or stars
    does: Switches between the system segmented bar, separate capsule buttons and a row of tappable stars.
    valueHelp: {"default": "the standard iOS segmented bar", "pills": "separate capsule buttons with the chosen one tinted", "stars": "a row of stars where tapping one fills up to it and sends its number"}
    valueTitles: {"default": "Default", "pills": "Pills", "stars": "Stars"}
    valueSymbols: {"default": "textformat", "pills": "capsule", "stars": "star.fill"}
  - name: tint
    edit: color
    depth: surface
    tab: style
    type: color
    default: "#667eea"
    description: Accent for pills style
    summary: The highlight colour on pills
    does: Colours the selected pill background and the filled stars; the default bar ignores it.
  - name: defaultValue
    type: string
    description: Initially selected option
    summary: Which choice starts selected
    does: The segment matching this option is highlighted when the control first appears; with no starting choice and nothing stored, the first option starts selected.
  - name: haptic
    tab: action
    type: enum
    values: [light, medium, heavy, { value: rigid, since: next }, { value: soft, since: next }, success, warning, error, selection]
    default: selection
    description: Default haptic on change
    summary: The tap feel when you change choice
    does: Plays this haptic on the phone each time a different segment is selected.
    valueHelp: {"rigid": "a firm sharp click", "soft": "a gentle cushioned tap", "light": "a small soft tap", "medium": "a medium tap", "heavy": "a strong thump", "success": "a confirming double pulse", "warning": "an alert pulse", "error": "a sharp failure buzz", "selection": "a tiny tick like scrolling a picker"}
    valueTitles: {"rigid": "Rigid", "soft": "Soft", "light": "Light", "medium": "Medium", "heavy": "Heavy", "success": "Success", "warning": "Warning", "error": "Error", "selection": "Selection"}
    valueSymbols: {"rigid": "square.fill", "soft": "cloud.fill", "light": "circle", "medium": "circle.fill", "heavy": "circle.inset.filled", "success": "checkmark.circle", "warning": "exclamationmark.triangle", "error": "xmark.octagon", "selection": "hand.tap"}
  - use: confirm
    does: After each change a pill naming it with an Undo button shows for 3 seconds.
themeFields:
  - use: cornerRadius
    summary: How round the outer bar is
    does: Rounds the outer edge of the whole control, 0 to 30 points.
  - use: controlPadding
    summary: Space inside the bar edge
    does: Insets the segments from the bar edge by 0 to 24 points.
  - use: surfacePrimary
    summary: The bar background tint
    does: Fills the area behind the segments with this colour.
  - use: accentColor
    summary: The main highlight colour
    does: Tints accent parts of the control such as the pill highlight when no tint is set.
  - use: borderColor
    summary: The outline colour
    does: Colours the line drawn around the control.
  - use: labelFontSize
    summary: How big the segment words are
    does: Sets the segment label size, 8 to 24 points.
  - name: trackColor
    type: color
    default: #39393D
    description: Track background color
    summary: The colour behind the segments
    does: Fills the strip the segments sit on with this colour.
  - name: selectedColor
    edit: color
    depth: hold
    under: tint
    type: color
    default: #636366
    description: Selected segment fill
    summary: The colour of the chosen segment
    does: Fills the selected segment with this colour.
  - name: selectedRadius
    edit: scrub
    depth: hold
    under: style
    unit: pt
    min: 0
    max: 30
    step: 1
    type: number
    default: 6
    description: Selected segment radius
    summary: How round the chosen segment is
    does: Rounds the corners of the highlighted segment, 0 to 30 points.
  - name: selectedShadow
    type: bool
    default: true
    description: Selected segment shadow
    summary: A shadow under the chosen segment
    does: Turns on a soft drop shadow beneath the highlighted segment; off leaves it flat.
  - name: textColor
    type: color
    default: #FFFFFF99
    description: Unselected text color
    summary: The words of choices not picked
    does: Colours the labels of segments that are not selected.
  - name: selectedTextColor
    type: color
    default: #FFFFFF
    description: Selected text color
    summary: The words of the picked choice
    does: Colours the label of the selected segment.
  - use: borderWidth
    summary: How heavy the outline is
    does: Sets the outline line weight, 0 (none) to 5 points.
  - use: secondaryColor
    summary: The colour of supporting words
    does: Colours the quieter supporting text in the control.
colorSlots:
  - slot: fill
    default: primary
    alias: tint
    since: next
    summary: The highlight color on pills and stars
    does: Tints the chosen pill and the filled stars; until set it follows the primary role.
  - slot: track
    default: "#39393D"
    alias: theme.trackColor
    since: next
    summary: The color behind the segments
    does: Fills the bar behind the segments; until set it keeps the segmented theme's track color, light or dark.
  - slot: selected
    default: "#636366"
    alias: theme.selectedColor
    since: next
    summary: The color of the chosen segment
    does: Fills the chosen segment; until set it keeps the segmented theme's pill color, light or dark.
  - slot: text
    default: "#FFFFFF99"
    alias: theme.textColor
    since: next
    summary: The words of choices not picked
    does: Colors the labels of segments that are not chosen; until set it keeps the segmented theme's text color.
  - slot: selectedText
    default: "#FFFFFF"
    alias: theme.selectedTextColor
    since: next
    summary: The words of the picked choice
    does: Colors the chosen segment's label; until set it takes black or white, whichever reads on the chosen segment.
---

# Segmented Control

A short option list displayed as inline segments. Stores a `.string` value.

## Type
`"segmentedControl"`

## Relevant Fields
Inherits all [[shared-fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `options` | string[] | required | Segment labels |
| `optionIcons` | string[] | — | SF Symbols parallel to options |
| `style` | string | `"default"` | `"default"` (system), `"pills"` (capsule buttons) or `"stars"` (rating) |
| `tint` | string | `"#667eea"` | Accent for pills style |
| `defaultValue` | string | — | Initially selected option |
| `haptic` | string | `"selection"` | Default haptic on change |
| `confirm` | bool | `false` | "Show confirmation": after each local write, a 3-second pill naming the change, with Undo. See [[actions#Confirmation and Undo]] |

## Styles

### `"default"`
Standard iOS segmented picker. System-styled.

### `"pills"`
Horizontal row of capsule-shaped buttons. Selected pill gets tinted background.

### `"stars"`
A tap-a-star rating: options `"1"`…`"N"` show as stars, and tapping one fills up to it and sends its number.

## Examples

### Friendly labels with stable server values
Shows `optionLabels` and `optionIcons`: the segments read Economy, Comfort and Sport with icons, while the stored and sent values stay `eco`, `comfort` and `sport`.

```json
{
  "type": "segmentedControl", "id": "drive-mode", "position": [0, 0],
  "options": ["eco", "comfort", "sport"],
  "optionLabels": ["Economy", "Comfort", "Sport"],
  "optionIcons": ["leaf", "car", "bolt"], "defaultValue": "eco"
}
```

### HVAC mode selector
Shows the default bar with an action: tapping a mode sends that mode's text to the thermostat, starting on Auto.

```json
{
  "type": "segmentedControl",
  "id": "hvac-mode",
  "position": [1, 2],
  "span": [1, 2],
  "options": ["Heat", "Cool", "Auto", "Off"],
  "defaultValue": "Auto",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "ecobee", "type": "set_mode", "payload": { "mode": "{{value}}" } } }
}
```

### Fan speed with pills
Shows the `pills` look: three separate capsule buttons with a wind icon on each, the chosen one tinted.

```json
{
  "type": "segmentedControl",
  "id": "fan-speed",
  "position": [0, 1],
  "span": [1, 3],
  "options": ["Low", "Med", "High"],
  "optionIcons": ["wind", "wind", "wind"],
  "style": "pills",
  "tint": "#34C759",
  "defaultValue": "Med"
}
```

### Star rating
Shows the `stars` look: five tappable stars where tapping the fourth fills four and sends the number 4.

```json
{
  "type": "segmentedControl", "id": "movie-rating", "position": [0, 0],
  "options": ["1", "2", "3", "4", "5"],
  "style": "stars", "tint": "#FFCC00", "defaultValue": "3",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "media", "type": "rate", "payload": { "stars": "{{value}}" } } }
}
```

### Live selection from the network
Shows `sync`: the highlighted choice follows the mode the device reports, and tapping still sends a change.

```json
{
  "type": "segmentedControl", "id": "scene-mode", "position": [0, 0],
  "options": ["Day", "Evening", "Night"],
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "scene_state" }, "valuePath": "mode" }],
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "lights", "type": "set_scene", "payload": { "mode": "{{value}}" } } }
}
```

### Quiet choice with undo and a firm tap
Shows `confirm`, `haptic` and `animation`: each change plays a heavy tap, snaps quickly, and shows a pill with Undo for 3 seconds.

```json
{
  "type": "segmentedControl", "id": "garage-door", "position": [0, 0],
  "options": ["Open", "Closed"], "defaultValue": "Closed",
  "confirm": true, "haptic": "heavy", "animation": "snappy"
}
```

### Empty list placeholder
Shows `placeholder`: with no options yet, the control reads "Nothing to pick" instead of the default "No options".

```json
{
  "type": "segmentedControl", "id": "empty-choice", "position": [0, 0],
  "options": [], "placeholder": "Nothing to pick"
}
```

### Themed segmented control
Shows `theme` overrides: a rounder bar with a bold border, a bright selected segment with no shadow and larger text.

```json
{
  "type": "segmentedControl", "id": "bold-choice", "position": [0, 0],
  "options": ["A", "B", "C"], "defaultValue": "A",
  "theme": { "cornerRadius": 24, "controlPadding": 6, "trackColor": "#2C2C2E", "selectedColor": "#667eea", "selectedRadius": 18, "selectedShadow": false, "selectedTextColor": "#FFFFFF", "textColor": "#FFFFFF99", "labelFontSize": 16, "borderWidth": 2, "borderColor": "#667eea" }
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
- [[shared-fields]] — Base fields
- [[picker]] — For longer option lists
- [[actions]] — `{{value}}` substitution
