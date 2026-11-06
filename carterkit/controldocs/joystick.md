---
type: joystick
label: Joystick
icon: dpad.fill
category: controls
defaultSpan: [3, 3]
addIntent: change
pickerCategory: Inputs
friendlyName: Joystick
oneLiner: Steer with your thumb
aliases: [stick, pad, direction, steer, drive, gamepad]
depth: complete
starterPreset: {"label": "Joystick"}
io:
  - emits: value
    when: change
    title: While you move the stick
    type: json
    says: the stick position as x and y, each from -1 to 1 (up is positive y)
    example: {"x": 0.5, "y": -0.25}
    also: Sends at the send rate while the stick is outside the deadzone; on release it sends one last position, which is x 0 and y 0 unless the stick is sticky
    since: next
  - receives: none
fields:
  - name: label
    edit: inline
    depth: surface
    title: Label
    type: string
    description: Header label
    summary: The name shown under the stick
    does: Shows this text under the stick, above the live x/y readout, in the label font size.
  - name: tint
    edit: color
    depth: surface
    tab: style
    type: color
    default: "#667eea"
    description: Stick and track color
    summary: The stick color
    does: Colors the stick, its track ring and the faint center dead-zone disc.
  - name: style
    edit: look
    depth: surface
    tab: style
    type: enum
    values: [analog, dpad]
    default: analog
    description: "analog (free) or dpad (4/8-direction snapping)"
    summary: Free stick or 8-way pad
    does: Chooses whether the stick moves freely or snaps to one of 8 directions, with a diagonal counting as full strength.
    valueHelp: {"analog": "the stick moves freely and sends smooth x and y values", "dpad": "snaps to one of 8 directions, sending x and y of -1, 0 or 1 (diagonals scaled to unit length)"}
  - name: deadzone
    chip: Stick
    edit: scrub
    depth: surface
    title: Dead zone
    min: 0
    max: 1
    step: 0.05
    type: number
    default: 0.1
    description: Center deadzone radius (0-1)
    summary: How far to push before it counts
    does: Draws a faint center disc and sends nothing until the stick is pushed past this fraction of its full travel (0-1, default 0.1).
  - name: sticky
    edit: part
    depth: hold
    title: Sticky
    type: bool
    default: false
    description: Stick stays where released instead of snapping to center
    summary: Stay put when you let go
    does: When on, the stick stays where you released it and sends that position once; when off, it springs back to center and sends x 0, y 0.
  - name: sendRate
    effect: behavior
    edit: scrub
    depth: hold
    under: deadzone
    title: Send rate
    tab: action
    min: 0.1
    max: 10
    step: 0.1
    type: number
    default: 0.1
    description: Throttle interval in seconds for action firing
    summary: How often it sends
    does: Sets the minimum seconds between sends while you hold the stick outside the dead zone (0.1-10, default 0.1).
  - name: hideLabel
    edit: part
    depth: hold
    title: Label shown
    type: bool
    default: false
    description: Hide label and coordinate readout
    summary: Hide the name and readout
    does: When on, hides the label and the x/y readout under the stick.
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
    does: Rounds the control's card corners from 0 to 30 pt (default 12).
  - use: controlPadding
    summary: Space inside the card
    does: Sets the padding between the card edge and the stick, from 0 to 24 pt (default 8).
  - use: surfacePrimary
    summary: Card background
    does: Fills the control's card background with this color.
  - use: accentColor
    summary: Highlight color
    does: Sets the theme accent color for this control.
  - use: secondaryColor
    summary: Quiet text color
    does: Colors the label text under the stick.
  - use: borderColor
    summary: Card outline color
    does: Colors the outline around the card.
  - name: borderWidth
    edit: scrub
    depth: hold
    under: style
    unit: pt
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
    summary: Card outline thickness
    does: Sets the card outline thickness from 0 to 5 pt (default 1).
  - use: labelFontSize
    summary: Label text size
    does: Sets the label text size from 8 to 24 pt (default 12).
---

# Joystick

A virtual analog stick or directional pad for continuous 2D input. Fires throttled actions with `x` and `y` values ranging from -1 to 1.

## Type
`"joystick"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | falls back to `id` | Header label |
| `tint` | color | `"#667eea"` | Stick and track color |
| `style` | string | `"analog"` | `"analog"` (free) or `"dpad"` (4/8-direction snapping) |
| `deadzone` | number | `0.1` | Center deadzone radius (0-1) |
| `sticky` | bool | `false` | Stick stays where released instead of snapping to center |
| `sendRate` | number | `0.1` | Throttle interval in seconds for action firing |
| `hideLabel` | bool | `false` | Hide label and coordinate readout |

## Examples

### Robot drive controller
Drive a robot with a free analog stick.
```json
{
  "type": "joystick",
  "id": "drive-stick",
  "position": [0, 0],
  "span": [3, 3],
  "label": "Drive",
  "tint": "#FF2D55",
  "style": "analog",
  "deadzone": 0.15,
  "sendRate": 0.05,
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "robot", "type": "drive", "payload": { "x": "$value.x", "y": "$value.y" } } }
}
```

### Menu pad
An 8-way pad that snaps to directions and stays where you leave it.
```json
{
  "type": "joystick",
  "id": "menu-pad",
  "position": [0, 0],
  "span": [3, 3],
  "label": "Menu",
  "style": "dpad",
  "sticky": true,
  "deadzone": 0.3,
  "tint": "#667eea"
}
```

### Quiet camera pan
A slow-sending stick with no label for a clean card.
```json
{
  "type": "joystick",
  "id": "pan-stick",
  "position": [0, 3],
  "span": [3, 3],
  "hideLabel": true,
  "sendRate": 0.5,
  "deadzone": 0.2,
  "tint": "#34C759",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "camera", "type": "pan", "payload": { "x": "$value.x", "y": "$value.y" } } }
}
```

## Related
- [[shared-properties]] — Base fields
- [[actions]] — Action definition
