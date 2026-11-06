---
type: toggle
label: Toggle
icon: switch.2
category: controls
defaultSpan: [1, 1]
addIntent: change
pickerCategory: Inputs
friendlyName: Switch
oneLiner: Turns something on or off
aliases: [switch, on off, checkbox, enable, flip, boolean]
addRank: 2
depth: complete
starterPreset: {"label": "Switch"}
fields:
  - name: animation
    title: Motion
    tab: style
    type: enum
    values: [smooth, snappy, bouncy, gentle, instant]
    description: Motion profile for value changes
    summary: How the switch moves when it flips
    does: Sets the speed and feel of the knob's travel between off and on, from instant to a slow ease.
    valueHelp: {"smooth": "an even natural glide", "snappy": "quick with a crisp stop", "bouncy": "overshoots slightly and settles", "gentle": "slow and soft", "instant": "no travel, it jumps straight to the new state"}
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Toggle label text
    summary: The name shown with the switch
    does: Shows this text above the switch in the label font size (8-24 pt, default 12).
  - name: icon
    title: Symbol
    type: string
    description: SF Symbol
    summary: A small picture beside the name
    does: Draws this SF Symbol beside the label; leave it empty for no icon.
  - name: style
    edit: look
    depth: surface
    title: Look
    tab: style
    type: enum
    values: [switch, button, icon-toggle]
    default: switch
    description: Display style
    summary: What the control looks like
    does: Switches the whole control between an iOS-style sliding switch, a tappable button and a single icon that swaps.
    valueHelp: {"switch": "a sliding track with a round knob", "button": "a tappable tile that glows in the on color when on", "icon-toggle": "one symbol that swaps between the on and off icons"}
  - name: defaultValue
    title: Initial on/off state
    type: bool
    default: false
    description: Initial on/off state
    summary: Whether it starts on or off
    does: Starts the control on (true) or off (false) until the first tap or live update.
  - name: onIcon
    title: Symbol when on
    styles: [button, icon-toggle]
    type: string
    description: SF Symbol when on (button and icon-toggle styles)
    summary: The picture shown when it is on
    does: Shows this SF Symbol while the control is on, replacing the main icon in button and icon-toggle looks.
  - name: offIcon
    title: Symbol when off
    styles: [button, icon-toggle]
    type: string
    description: SF Symbol when off (button and icon-toggle styles)
    summary: The picture shown when it is off
    does: Shows this SF Symbol while the control is off, replacing the main icon in button and icon-toggle looks.
  - name: tint
    edit: color
    depth: surface
    title: Color when on
    tab: style
    type: color
    default: "#667eea"
    description: Accent color when on
    summary: The color it lights up with
    does: Colors the track, glow or icon in this color whenever the control is on.
  - name: hideBackground
    edit: part
    depth: hold
    title: No background card
    tab: style
    type: bool
    default: false
    description: Remove glass background
    summary: Whether the card behind it is drawn
    does: Removes the frosted card behind the control so only the switch and label sit on the page.
  - name: haptic
    edit: look
    depth: hold
    under: style
    title: Vibration on tap
    tab: action
    type: enum
    values: [light, medium, heavy, rigid, success, warning, error, selection]
    default: rigid
    description: Default haptic on toggle
    summary: The buzz you feel on a tap
    does: Plays this haptic on the phone each time the control flips.
    valueHelp: {"light": "a small soft tap", "medium": "a medium tap", "heavy": "a strong thud", "rigid": "a firm sharp click", "success": "the double tap of a success", "warning": "a two-pulse warning", "error": "a sharp triple buzz of an error", "selection": "the faint tick of picking an item"}
  - name: trackLength
    edit: scrub
    depth: surface
    title: Track length
    tab: style
    styles: [switch]
    type: number
    min: 31
    max: 400
    step: 1
    default: 51
    description: Track extent tip-to-tip along its path (pt)
    summary: How long the switch track is
    does: Stretches the track tip to tip along its path from 31 to 400 pt (default 51).
  - name: trackCurvature
    edit: scrub
    depth: hold
    under: trackLength
    title: Track curve
    tab: style
    styles: [switch]
    type: number
    min: -180
    max: 180
    step: 5
    default: 0
    description: Degrees of bend; 0 straight, positive bows up. Clamped to what the length can bend (lengthen the track to curve it more)
    summary: How much the switch bends
    does: Bends the track from -180 to 180 degrees; 0 is straight, positive bows up and negative bows down.
  - name: trackRadius
    title: Track roundness
    tab: style
    styles: [switch]
    type: number
    min: 0
    max: 20
    step: 0.5
    default: 15.5
    description: Track corner radius; on a curved track resolves to round caps (within 0.5 pt of half thickness) or sharp square ends (below)
    summary: How round the switch ends are
    does: Rounds the track corners from 0 (square) to 20 pt (fully round at default thickness).
  - name: knobRadius
    title: Knob roundness
    tab: style
    styles: [switch]
    type: number
    min: 0
    max: 13.5
    step: 0.5
    default: 13.5
    description: Knob corner radius; 0 is a square knob, which rotates to the track's direction on curved tracks. Knob SIZE is derived from the track (fixed ratio, D45a) and is not a dial
    summary: How round the sliding knob is
    does: Rounds the knob corners from 0 (square) to 13.5 pt (a circle).
  - use: confirm
themeFields:
  - name: cornerRadius
    title: Corner roundness
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
    summary: How round the card corners are
    does: Rounds the control's card corners from 0 to 30 pt (default 12).
  - use: controlPadding
    summary: The gap between card edge and contents
    does: Sets the space inside the card around the label and switch from 0 to 24 pt (default 8).
  - use: surfacePrimary
    does: Fills the card behind the control with this color, default a faint white wash.
  - use: accentColor
    summary: The main highlight color
    does: Sets the highlight color the control uses where no color is set for it.
  - use: borderColor
    does: Draws the card outline in this color, default a faint white line.
  - use: labelFontSize
    summary: How big the name text is
    does: Sets the label text size from 8 to 24 pt (default 12).
  - name: trackColor
    title: Track color
    styles: [switch]
    type: color
    default: #39393D
    description: Track background color
    summary: The switch color when off
    does: Fills the empty switch track with this color while off, default dark grey.
  - name: trackActiveColor
    title: Track color when on
    type: color
    default: #667eea
    description: Track active/on color
    summary: The switch color when on
    does: Fills the switch track with this color while on, default the accent purple.
  - name: trackRadius
    title: Track roundness
    styles: [switch]
    min: 0
    max: 30
    step: 0.5
    type: number
    default: 15.5
    description: Track corner radius
    summary: How round the track ends are in the theme
    does: Rounds the track corners from 0 to 30 pt as a theme default (15.5 is a full pill).
  - name: trackHeight
    title: Track height
    styles: [switch]
    min: 16
    max: 60
    step: 1
    type: number
    default: 31
    description: Track height
    summary: How tall the switch is
    does: Sets the track thickness from 16 to 60 pt (default 31); the knob scales with it.
  - name: trackWidth
    title: Track width
    styles: [switch]
    min: 30
    max: 100
    step: 1
    type: number
    default: 51
    description: Track width
    summary: How wide the switch is
    does: Sets the track width from 30 to 100 pt (default 51).
  - name: knobColor
    edit: color
    depth: hold
    under: tint
    title: Knob color
    styles: [switch]
    type: color
    default: #FFFFFF
    description: Knob fill color
    summary: The color of the sliding knob
    does: Fills the knob with this color, default white.
  - name: knobRadius
    title: Knob roundness
    styles: [switch]
    min: 0
    max: 30
    step: 0.5
    type: number
    default: 13.5
    description: Knob corner radius
    summary: How round the knob is in the theme
    does: Rounds the knob corners from 0 to 30 pt as a theme default (13.5 is a circle).
  - name: knobShadow
    title: Knob shadow
    styles: [switch]
    type: bool
    default: true
    description: Show knob shadow
    summary: Whether the knob casts a shadow
    does: Draws a soft shadow under the knob when on, flat when off.
  - use: borderWidth
    does: Sets the card outline thickness from 0 (none) to 5 pt (default 1).
  - use: secondaryColor
    does: Colors the dimmer supporting text, default a soft translucent white.
---

# Toggle

A boolean on/off control. Stores a `.bool` value.

## Type
`"toggle"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Display label |
| `icon` | string | — | SF Symbol |
| `style` | string | `"switch"` | `"switch"`, `"button"`, `"icon-toggle"` |
| `onIcon` | string | — | SF Symbol when on (button and icon-toggle styles) |
| `offIcon` | string | — | SF Symbol when off (button and icon-toggle styles) |
| `tint` | string | `"#667eea"` | Accent color when on |
| `defaultValue` | bool | `false` | Initial state |
| `hideBackground` | bool | `false` | Remove glass background |
| `haptic` | string | `"rigid"` | Default haptic on toggle |
| `confirm` | bool | `false` | "Show confirmation": after each local write, a 3-second pill naming the change, with Undo. See [[actions#Confirmation and Undo]] |

## Styles

### `"switch"` (default)
Standard iOS toggle switch with label above and optional icon beside.

### `"button"`
Tap-to-toggle button. Background highlights when on with a tinted glow.

### `"icon-toggle"`
Icon that swaps between `onIcon` and `offIcon` with a symbol transition animation.

## Examples

### Standard switch
Shows the default look wired both ways: flipping it sends the new on/off value to a light, and the switch follows the light's live state. Intended effect: the living-room light turns on or off with a tap, and the switch stays correct when someone else changes it.
```json
{
  "type": "toggle",
  "id": "lr-main",
  "position": [0, 0],
  "label": "Main Light",
  "defaultValue": true,
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "hue-bridge", "type": "light", "payload": { "room": "living", "fixture": "main", "command": "{{value}}" } } },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "room": "living", "fixture": "main" }, "valuePath": "state" }]
}
```

### Button look
Shows the button look, a tile that glows in the tint color while on. Intended effect: a bold, thumb-sized tile for a setting you flip often, starting off.
```json
{
  "type": "toggle",
  "id": "porch-light",
  "position": [0, 0],
  "label": "Porch",
  "style": "button",
  "icon": "lightbulb.fill",
  "tint": "#FFCC00",
  "defaultValue": false
}
```

### Icon-toggle with custom icons
Shows the icon-toggle look, where the symbol swaps between the on and off icons. Intended effect: a red microphone that shows a slashed mic when muted.
```json
{
  "type": "toggle",
  "id": "mic-mute",
  "position": [0, 0],
  "label": "Mic",
  "style": "icon-toggle",
  "onIcon": "mic.fill",
  "offIcon": "mic.slash.fill",
  "tint": "#FF3B30",
  "defaultValue": true
}
```

### Curved, restyled switch track
Shows the track fields: a longer track bent upward with a squarer knob. Intended effect: a 120 pt switch that bows 90 degrees, with its knob following the curve.
```json
{
  "type": "toggle",
  "id": "arc-switch",
  "position": [0, 0],
  "label": "Arc",
  "style": "switch",
  "trackLength": 120,
  "trackCurvature": 90,
  "trackRadius": 15.5,
  "knobRadius": 4,
  "animation": "bouncy"
}
```

### Confirmation with Undo and custom haptic
Shows the confirm option and a chosen haptic, with no background card. Intended effect: each flip gives a heavy buzz and a 3-second pill with Undo, so a risky switch can be reversed.
```json
{
  "type": "toggle",
  "id": "garage-lock",
  "position": [0, 0],
  "label": "Garage Lock",
  "haptic": "heavy",
  "confirm": true,
  "hideBackground": true,
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "garage", "type": "lock", "payload": { "command": "{{value}}" } } }
}
```

### Conditionally visible toggle
Shows the visible rule: the control appears only while another control has a given value. Intended effect: the Oscillate switch is hidden until the fan power switch is on.
```json
{
  "type": "toggle",
  "id": "fan-oscillate",
  "position": [1, 1],
  "label": "Oscillate",
  "defaultValue": false,
  "visible": { "when": "fan-power", "operator": "eq", "value": true }
}
```

### Toggle with long-press detail
Shows a long-press group opening a detail panel from the toggle. Intended effect: tap flips the heater, holding it opens a small panel of extra readouts.
```json
{
  "type": "toggle",
  "id": "heater",
  "position": [0, 0],
  "label": "Heater",
  "longPressGroup": {
    "position": [0, 0],
    "span": [2, 1],
    "id": "heater-detail",
    "label": "Heater Detail",
    "grid": { "columns": 2, "rows": 1 },
    "children": [
      { "type": "label", "id": "heater-note", "position": [0, 0], "text": "Runs until switched off" }
    ]
  }
}
```

## Track geometry and interaction

Switch styles support `trackLength` (31–400 pt at the default theme), `trackCurvature` (−180° to 180°), `trackRadius`, and `knobRadius`. Length is measured along the path. Positive curvature bows up; negative bows down. Tight curves are limited to keep the inner track edge from collapsing. Lengthen the track to allow a larger bend.

The knob follows the curved centerline throughout taps, remote changes, and drag release; square knobs rotate with the tangent. `animation` applies to all toggle styles, including custom durations and `instant`. Reduce Motion disables travel animation.

Tap to flip, or drag and release toward an endpoint. A flick uses its projected destination; a drag released on the original side emits no action. Cancellation returns to the current state. Zero-travel tracks still respond to taps.

Knob size is always 27/31 of the themed track height. Radii clamp to half their respective sizes. Curved track caps are round when `trackRadius` is within 0.5 pt of half the track thickness, otherwise they have sharp radial ends; intermediate curved fillets are not supported. Straight tracks honor intermediate radii. Give long or deeply curved tracks enough grid space to avoid clipping.

## Related
- [[shared-properties]] — Base fields
- [[style-properties#Toggle Styles]] — Style details
- [[actions]] — `{{value}}` substitution
- [[sync]] — Live state sync
- [[conditional-visibility]] — The `visible` field
