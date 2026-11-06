---
depth: complete
type: button
label: Button
icon: hand.tap.fill
category: controls
defaultSpan: [1, 1]
addIntent: change
pickerCategory: Buttons
friendlyName: Button
oneLiner: Tap it to make something happen
aliases: [tap, press, click, trigger, action, send]
addRank: 1
starterPreset: {"label": "Button"}
lookPresets: [{"id": "filled","name": "Filled","symbol": "capsule.fill","set": {"style": "filled"}},{"id": "outlined","name": "Outlined","symbol": "capsule","set": {"style": "outlined"}},{"id": "tinted","name": "Tinted","symbol": "capsule.lefthalf.filled","set": {"style": "tinted"}},{"id": "iconOnly","name": "Icon only","symbol": "circle.fill","set": {"style": "icon-only"}}]
io:
  - emits: press
    when: tap
    title: When you tap it
    type: string
    says: the button's current value if it follows one, else false
    example: "true"
    also: Holding it with Repeat while held on sends again on each repeat
    since: next
  - receives: value
    role: show
    type: string
    from: [hub, mqtt, http, store, default]
    says: a state to show, matched against the button's value, icon and color maps
    reacts: the text, symbol and color switch to the matching entry, or to the default entry when none match; a new value never presses the button
    example: "true"
    since: next
  - sample: "true"
    next: "false"
fields:
  - name: label
    summary: "The words on the button"
    does: "Sets the text shown on the button; empty shows the control id."
    edit: inline
    depth: surface
    title: Title
    type: string
    default: "Button"
    description: Button text
  - name: icon
    summary: "A small picture beside the words"
    does: "Draws the chosen SF Symbol before the label, or alone with Symbol only."
    edit: symbol
    depth: surface
    title: Symbol
    type: string
    description: SF Symbol shown before label
  - name: style
    summary: "How the button is dressed"
    does: "Switches the button between a solid fill, an outline, a faint tint, or just the symbol."
    valueHelp: {"filled": "solid colored block with light text", "outlined": "clear inside with a colored border", "outline": "same as outlined", "ghost": "no fill or border, just the colored text", "tinted": "soft wash of the color with colored text", "icon-only": "only the symbol, no text or block"}
    edit: look
    depth: surface
    title: Look
    tab: style
    type: enum
    values: [filled, outlined, outline, ghost, tinted, icon-only]
    default: filled
    description: Visual style variant ("outline" and "outlined" are both accepted)
  - name: size
    summary: "How big the button is"
    does: "Scales the button's height and text between compact, normal and large."
    valueHelp: {"compact": "small and tight, for crowded grids", "default": "the normal size", "large": "tall and roomy, easy to hit"}
    edit: look
    depth: hold
    under: style
    title: Size
    tab: style
    type: enum
    values: [compact, default, large]
    default: default
    description: Size variant
  - name: tint
    summary: "The button's main color"
    does: "Recolors the fill, border or text (per Look) to the chosen color."
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: Accent color
  - name: hideLabel
    summary: "Hide the words, keep the picture"
    does: "When on, the label text disappears and only the symbol remains."
    edit: part
    depth: hold
    title: Symbol only
    type: bool
    default: false
    description: Show icon only
  - name: haptic
    summary: "How the tap feels"
    does: "Plays the chosen buzz on the phone each time the button is pressed."
    valueHelp: {"light": "a faint tick", "medium": "a normal tap", "heavy": "a firm thump", "success": "a short double-tap for done", "warning": "a sharper alert buzz", "error": "a harsh triple buzz for failure", "selection": "a tiny click like scrolling a picker"}
    title: Vibration on tap
    tab: action
    type: enum
    values: [light, medium, heavy, success, warning, error, selection]
    default: medium
    description: Haptic feedback on press
  - name: repeatOnHold
    summary: "Keep going while held"
    does: "Holding the button refires its action repeatedly, speeding up the longer you hold."
    title: Repeat while held
    tab: action
    type: bool
    default: false
    description: Keep firing the action while held, using the system repeat behavior (ignored when longPressAction/longPressGroup is set)
  - name: valueMap
    summary: "Different words for different states"
    does: "Replaces the label with the text matching the synced value, e.g. true shows Pause."
    title: Words for values
    tab: data
    type: object
    description: Synced value → button text ("default" catches the rest)
  - name: iconMap
    summary: "Different pictures for different states"
    does: "Swaps the symbol to the one matching the synced value, with a replace animation."
    title: Symbols for values
    tab: data
    type: object
    description: Synced value → SF Symbol name (swaps with the native replace effect)
  - name: colorMap
    summary: "Different colors for different states"
    does: "Recolors the button to the hex matching the synced value."
    title: Colors for values
    tab: data
    type: object
    description: Synced value → hex tint
  - use: confirm
    does: "A pill naming the change appears for 3 seconds with an Undo button after each tap."
themeFields:
  - name: cornerRadius
    summary: "How round the corners are"
    does: "Rounds the button's corners from 0 (square) to 30 points (pill-like)."
    edit: scrub
    depth: hold
    under: style
    unit: pt
    title: Corner roundness
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
  - use: controlPadding
    summary: "Breathing room inside the button"
    does: "Adds 0 to 24 points of space between the edge and the content."
  - use: accentColor
    does: "Sets the default button fill or tint for every button without its own color."
  - use: foregroundColor
    summary: "Color of the words and symbol"
    does: "Sets the label and symbol color on filled buttons."
  - use: borderColor
    does: "Colors the border drawn around the button."
  - name: borderWidth
    summary: "How thick the outline is"
    does: "Draws the border 0 to 5 points thick; 0 hides it."
    edit: scrub
    depth: hold
    under: style
    unit: pt
    title: Border thickness
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
colorSlots:
  - slot: fill
    default: primary
    alias: tint
    since: next
    summary: The color of the key
    does: Fills a filled or tinted key, and draws the label and outline of an outline or ghost key; a color map entry for the current value wins.
---

# Button

A tappable action trigger. Fires its [[actions|action]] on press. It stores no value of its own, but a
button with a `sync` can show server state through `valueMap` / `iconMap` / `colorMap` (a stateful key).

## Type
`"button"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | falls back to `id` | Button text |
| `icon` | string | — | SF Symbol shown before label |
| `style` | string | `"filled"` | `"filled"`, `"outlined"`, `"ghost"`, `"tinted"`, `"icon-only"` (`"outline"` also accepted) |
| `size` | string | `"default"` | `"compact"`, `"default"`, `"large"` |
| `tint` | string | `"#667eea"` | Accent color |
| `hideLabel` | bool | `false` | Show icon only |
| `action` | [[actions\|ActionDefinition]] | — | Command fired on tap |
| `haptic` | string | `"medium"` | Default haptic on press |
| `confirm` | bool | `false` | "Show confirmation": after each local write, a 3-second pill naming the change, with Undo. See [[actions#Confirmation and Undo]] |
| `repeatOnHold` | bool | `false` | Hold to keep firing `action`, with the system's accelerating repeat (like [[stepper]]) |
| `valueMap` | object | — | Synced value → button text (`"default"` catches the rest) |
| `iconMap` | object | — | Synced value → SF Symbol name |
| `colorMap` | object | — | Synced value → hex tint |

### Repeat while held
`repeatOnHold: true` makes a held button refire its action at the system's native repeat
cadence (Apple's `buttonRepeatBehavior`, the same one [[stepper]] uses), like holding an
arrow key. Without the field a button fires once per tap. **`repeatOnHold` is ignored when
`longPressAction` or `longPressGroup` is set**: the long-press wrapper owns the touch, so a
hold opens the long-press instead.

### Stateful keys
Give a button a `sync` and the maps, and it shows the server's current state, like a Stream
Deck key. The synced value is matched against map keys the same way as on [[label]]
(`true`/`"Yes"`/`1` all hit `"true"`; `3`/`"3.00"` hit `"3"`; strings match case-insensitively).

- A hit shows the mapped text / symbol / tint. A changed symbol swaps with the native
  `.symbolEffect(.replace)` transition.
- No match, or no value received yet ⇒ the map's `"default"` entry, else the button's own
  `label` / `icon` / `tint`. A button that has never received a value never shows a `"false"`
  entry.
- Tapping still fires `action`; `{{value}}` in the payload is the current synced value.

## Examples

### Simple button

A plain filled button that sends a scene command to a hub; tapping it fires the action once with the default medium buzz.

```json
{
  "type": "button",
  "id": "all-off",
  "position": [0, 3],
  "label": "All Off",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "hue-bridge", "type": "scene", "payload": { "name": "all_off" } } }
}
```

### Icon-only ghost button (large, for transport controls)

Shows only a large pink play symbol with no block or text, the way a media transport key looks.

```json
{
  "type": "button",
  "id": "btn-play",
  "position": [0, 2],
  "label": "Play",
  "icon": "playpause.fill",
  "style": "ghost",
  "size": "large",
  "hideLabel": true,
  "tint": "#FF2D55",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "player", "type": "command", "payload": { "command": "playpause" } } }
}
```

### Hold-to-repeat arrow key

Holding this compact outlined key keeps sending Up, like holding an arrow key on a keyboard.

```json
{
  "type": "button",
  "id": "t-up",
  "position": [8, 2],
  "label": "Up",
  "icon": "arrow.up",
  "style": "outlined",
  "size": "compact",
  "repeatOnHold": true,
  "action": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "command", "key": "Up" } }
}
```

### Stateful play/pause key

The key's symbol swaps between play and pause to match the player's state, and tapping still sends the toggle.

```json
{
  "type": "button",
  "id": "btn-playpause",
  "position": [0, 2],
  "label": "Play/Pause",
  "icon": "playpause.fill",
  "size": "large",
  "hideLabel": true,
  "tint": "#FF2D55",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "cider_state" }, "valuePath": "playing" }],
  "valueMap": { "true": "Pause", "false": "Play" },
  "iconMap": { "true": "pause.fill", "false": "play.fill" },
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "player", "type": "command", "payload": { "command": "playpause" } } }
}
```

### Button with long-press detail popup

Tapping fires the Movie scene; holding opens a detail panel with brightness and two switches.

```json
{
  "type": "button",
  "id": "scene-movie",
  "position": [0, 0],
  "label": "Movie",
  "icon": "film",
  "style": "tinted",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "home-hub", "type": "macro", "payload": { "name": "movie_mode" } } },
  "longPressGroup": {
    "position": [0, 0],
    "span": [2, 2],
    "id": "movie-detail",
    "label": "Movie Mode Settings",
    "grid": { "columns": 2, "rows": 2 },
    "children": [
      { "type": "slider", "id": "movie-brightness", "position": [0, 0], "span": [1, 2], "min": 0, "max": 100, "label": "Brightness" },
      { "type": "toggle", "id": "movie-auto-screen", "position": [1, 0], "label": "Auto Screen" },
      { "type": "toggle", "id": "movie-auto-audio", "position": [1, 1], "label": "Auto Audio" }
    ]
  }
}
```

### Filled look (the default)

A solid colored block with light text; the strongest look, for the main action.

```json
{
  "type": "button",
  "id": "b-filled",
  "position": [0, 0],
  "label": "Lights On",
  "style": "filled",
  "tint": "#34C759",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "hue-bridge", "type": "scene", "payload": { "name": "lights_on" } } }
}
```

### Outlined look

A clear button with a colored border, for a quieter secondary action.

```json
{
  "type": "button",
  "id": "b-outlined",
  "position": [1, 0],
  "label": "Dim",
  "style": "outlined",
  "tint": "#FF9500",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "hue-bridge", "type": "scene", "payload": { "name": "dim" } } }
}
```

### Ghost look

Only colored text with no block or border, for a low-key action in a busy panel.

```json
{
  "type": "button",
  "id": "b-ghost",
  "position": [2, 0],
  "label": "More",
  "style": "ghost",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "hue-bridge", "type": "scene", "payload": { "name": "more" } } }
}
```

### Tinted look

A soft wash of the color behind colored text, a calm middle ground between filled and outlined.

```json
{
  "type": "button",
  "id": "b-tinted",
  "position": [3, 0],
  "label": "Night",
  "icon": "moon.fill",
  "style": "tinted",
  "tint": "#5856D6",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "hue-bridge", "type": "scene", "payload": { "name": "night" } } }
}
```

### Icon-only look

The symbol alone with no text or block, for tight spaces; the label is still used for accessibility.

```json
{
  "type": "button",
  "id": "b-icon",
  "position": [4, 0],
  "label": "Lamp",
  "icon": "lightbulb.fill",
  "style": "icon-only",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "hue-bridge", "type": "scene", "payload": { "name": "lamp" } } }
}
```

### Compact and large sizes

Size changes the button's height and text: a compact key fits dense grids while a large one is easy to hit with a thumb.

```json
{
  "type": "button",
  "id": "b-large",
  "position": [0, 1],
  "span": [2, 1],
  "label": "Big Red",
  "size": "large",
  "tint": "#FF3B30",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "hue-bridge", "type": "scene", "payload": { "name": "big_red" } } }
}
```

### Strong haptic on tap

Plays a firm thump when pressed, so a risky action feels deliberate.

```json
{
  "type": "button",
  "id": "b-haptic",
  "position": [2, 1],
  "label": "Lock Down",
  "haptic": "heavy",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "hue-bridge", "type": "scene", "payload": { "name": "lock_down" } } }
}
```

### Tap with Undo confirmation

After each tap a pill names the change and offers Undo for 3 seconds, so an accidental press can be reversed.

```json
{
  "type": "button",
  "id": "b-confirm",
  "position": [3, 1],
  "label": "Arm",
  "confirm": true,
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "hue-bridge", "type": "scene", "payload": { "name": "arm" } } }
}
```

### Symbol only toggle (hideLabel)

Keeps the label in the data but shows just the symbol, turning a labeled button into an icon key.

```json
{
  "type": "button",
  "id": "b-hide",
  "position": [4, 1],
  "label": "Fan",
  "icon": "fan.fill",
  "hideLabel": true,
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "hue-bridge", "type": "scene", "payload": { "name": "fan" } } }
}
```

### Stateful key with colors for values

The button's words, symbol and color all follow a synced value: it reads Armed in red when true and Disarmed in green when false.

```json
{
  "type": "button",
  "id": "b-alarm",
  "position": [0, 2],
  "label": "Alarm",
  "icon": "shield",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "alarm_state" }, "valuePath": "armed" }],
  "valueMap": { "true": "Armed", "false": "Disarmed", "default": "Alarm" },
  "iconMap": { "true": "shield.fill", "false": "shield" },
  "colorMap": { "true": "#FF3B30", "false": "#34C759" },
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "alarm", "type": "command", "payload": { "command": "toggle" } } }
}
```

### Long-press action

Tapping sends the normal action; holding runs a different one, here a full reset, without opening a panel.

```json
{
  "type": "button",
  "id": "b-longaction",
  "position": [1, 2],
  "label": "Heat",
  "icon": "flame",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "thermostat", "type": "command", "payload": { "command": "boost" } } },
  "longPressAction": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "thermostat", "type": "command", "payload": { "command": "off" } } }
}
```

## Related
- [[shared-properties]] — Base fields
- [[style-properties#Button Styles]] — Style variants
- [[actions]] — Action definition
- [[long-press]] — Long-press behavior
- [[haptics]] — Haptic feedback
- [[label]] — Value maps in depth
- [[stepper]] — The other `repeatOnHold` control
