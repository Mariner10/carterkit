---
type: slider
label: Slider
icon: slider.horizontal.3
category: controls
defaultSpan: [1, 2]
addIntent: change
pickerCategory: Inputs
depth: complete
friendlyName: Slider
oneLiner: Slide to pick a number
aliases: [range, dial, volume, brightness, scrub, level]
addRank: 3
starterPreset: {"label": "Slider","min": 0,"max": 100,"step": 1}
io:
  - emits: value
    when: change
    title: When you slide it
    type: number
    says: the number you slid to
    example: 42
    whenBy: {"continuous": {"false": "release"}}
    also: With Send while dragging off, it sends once, when you let go
    since: next
  - receives: value
    role: follow
    type: number
    from: [hub, mqtt, http, store, default]
    says: a number to move the handle to
    reacts: the handle glides to it; your next slide replaces it
    example: 42
    since: next
  - sample: 40
    next: 70
fields:
  - name: animation
    title: Motion
    tab: style
    type: enum
    values: [smooth, snappy, bouncy, gentle, instant]
    description: Motion profile for value changes
    summary: How the handle glides when the value changes
    does: "Sets how the handle and fill travel when the value changes, from instant jump to a soft glide."
    valueHelp: {"smooth": "an even, natural glide", "snappy": "a quick, firm move", "bouncy": "overshoots slightly, then settles", "gentle": "a slow, soft drift", "instant": "jumps with no travel"}
  - name: min
    chip: Range
    title: Lowest value
    bounds: none
    type: number
    default: 0
    description: Minimum value
    summary: Where the slider starts
    does: "Sets the value at the left end (or arc start) of the slider, in the slider's own units."
  - name: max
    title: Highest value
    bounds: none
    type: number
    default: 100
    description: Maximum value
    summary: Where the slider ends
    does: "Sets the value at the right end (or arc end) of the slider, in the slider's own units."
  - name: step
    edit: scrub
    depth: hold
    under: style
    title: Step size
    bounds: none
    type: number
    default: 1
    description: Detent spacing measured from min; zero or negative allows continuous values
    summary: How coarsely the slider snaps
    does: "Makes the handle snap to values spaced this far apart from the lowest value; 0 or less slides smoothly."
  - name: continuous
    title: Send while dragging
    type: bool
    default: true
    description: Send actions while dragging; false previews locally and sends once on release
    summary: Whether the change is sent live or only when you let go
    does: "On, the new value is sent throughout the drag; off, it is sent once when you lift your finger."
  - name: hideValue
    edit: part
    depth: hold
    title: Hide the number
    type: bool
    default: false
    description: Hide numeric readouts in every slider style; keep the label and interaction
    summary: Takes the number off the slider
    does: "Removes the number readout from the header and the radial center; the title and dragging still work."
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label
    summary: The name shown above the slider
    does: "Writes this text in the header above the slider."
  - name: defaultValue
    title: Starting value
    bounds: none
    type: number
    description: Initial value
    summary: Where the handle rests until something else sets it
    does: "Places the handle at this value (within lowest to highest) when the layout first appears."
  - name: tint
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: Track fill color
    summary: The color of the filled part
    does: "Colors the filled portion of the track or arc with this color."
  - name: style
    edit: look
    depth: surface
    title: Look
    tab: style
    type: enum
    values: [default, scrubber, radial]
    default: default
    description: Display style
    summary: Which kind of slider it is
    does: "Switches between a bar with a big handle, a thin seek bar, or a circular arc."
    valueHelp: {"default": "a bar with a round handle and optional end symbols", "scrubber": "a thin progress line with a small draggable dot", "radial": "a circular arc you drag around"}
  - name: formatValue
    title: Number format
    simple: hide
    tab: data
    type: enum
    values: [decimal, time, percent, none]
    default: decimal
    description: Value display format
    summary: How the number is written
    does: "Changes how the readout is written, such as 72, 3:45 or 80%, or hides it."
    valueHelp: {"decimal": "a plain number like 72 or 3.5", "time": "minutes and seconds like 3:45, from a total in seconds", "percent": "a whole percentage like 80%", "none": "no number shown"}
  - name: minIcon
    title: Symbol at low end
    styles: [default]
    type: string
    description: SF Symbol at minimum end
    summary: A small picture at the left end
    does: "Shows this SF Symbol at the left end of the bar (default look only)."
  - name: maxIcon
    title: Symbol at high end
    styles: [default]
    type: string
    description: SF Symbol at maximum end
    summary: A small picture at the right end
    does: "Shows this SF Symbol at the right end of the bar (default look only)."
  - name: hideLabel
    edit: part
    depth: hold
    title: Hide the title
    type: bool
    default: false
    description: Hide the header
    summary: Takes the name off the top
    does: "Removes the header row so only the slider itself shows."
  - name: hideBackground
    edit: part
    depth: hold
    title: No background card
    tab: style
    type: bool
    default: false
    description: Remove glass background
    summary: Lets the slider sit directly on the page
    does: "Removes the frosted card behind the slider so it floats on the page."
  - name: arcAngle
    title: Arc length
    tab: style
    styles: [radial]
    min: 1
    max: 360
    step: 1
    type: number
    default: 270
    description: Arc sweep in degrees (radial style only)
    summary: How much of a circle the arc covers
    does: "Sets how far the arc sweeps, from 1 to 360 degrees (270 leaves a gap at the bottom)."
  - name: arcRotation
    title: Arc turn
    tab: style
    styles: [radial]
    min: -180
    max: 180
    step: 1
    type: number
    default: 0
    description: Arc start rotation (radial style only)
    summary: Where the arc begins
    does: "Turns the whole arc around its center by -180 to 180 degrees."
  - name: arcThickness
    edit: scrub
    depth: hold
    under: style
    unit: pt
    title: Arc thickness
    tab: style
    styles: [radial]
    min: 1
    max: 40
    step: 1
    type: number
    default: 8
    description: Track stroke width (radial style only)
    summary: How thick the arc line is
    does: "Sets the arc line width from 1 to 40 points."
  - use: confirm
    does: "Shows a pill naming the change with an Undo button for 3 seconds after you set a value."
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
    does: "Rounds the card corners from 0 (square) to 30 points."
  - use: controlPadding
    summary: Space between the card edge and the content
    does: "Sets the padding inside the card from 0 to 24 points."
  - use: surfacePrimary
    does: "Fills the card behind the slider with this color."
  - use: accentColor
    summary: The highlight color
    does: "Sets the accent used for highlights on the slider."
  - use: foregroundColor
    does: "Colors the title and value text."
  - use: borderColor
  - use: labelFontSize
  - name: trackColor
    edit: color
    depth: hold
    under: tint
    title: Track color
    type: color
    default: #39393D
    description: Track background color
    summary: The color of the empty part of the bar
    does: "Colors the unfilled part of the track."
  - name: trackHeight
    edit: scrub
    depth: hold
    under: style
    unit: pt
    title: Track height
    styles: [default]
    min: 4
    max: 60
    step: 1
    type: number
    default: 31
    description: Track height
    summary: How thick the bar is
    does: "Sets how tall the bar is, from 4 to 60 points."
  - name: thumbColor
    edit: color
    depth: hold
    under: tint
    title: Handle color
    styles: [default]
    type: color
    default: #FFFFFF
    description: Thumb fill color
    summary: The color of the grab handle
    does: "Fills the draggable handle with this color."
  - name: thumbRadius
    title: Handle roundness
    styles: [default]
    min: 0
    max: 30
    step: 1
    type: number
    default: 14
    description: Thumb corner radius
    summary: How round the handle is
    does: "Rounds the handle corners from 0 (square) to 30 points."
  - name: thumbSize
    edit: scrub
    depth: hold
    under: style
    unit: pt
    title: Handle size
    styles: [default]
    min: 12
    max: 50
    step: 1
    type: number
    default: 28
    description: Thumb diameter
    summary: How big the grab handle is
    does: "Sets the handle diameter from 12 to 50 points."
  - name: thumbShadow
    title: Handle shadow
    styles: [default]
    type: bool
    default: true
    description: Show thumb shadow
    summary: A soft shadow under the handle
    does: "Turns the shadow under the handle on or off."
  - use: borderWidth
    summary: How heavy the outline is
    does: "Sets the outline thickness from 0 to 5 points."
  - use: secondaryColor
    does: "Colors the quieter text such as the value readout."
  - name: trackRadius
    title: Track roundness
    min: 0
    max: 20
    step: 1
    type: number
    default: 2
    description: Track corner radius
    summary: How round the bar ends are
    does: "Rounds the track corners from 0 to 20 points."
---

# Slider

A numeric range input. Stores a `.number` value.

## Type
`"slider"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `min` | number | `0` | Minimum value |
| `max` | number | `100` | Maximum value |
| `step` | number | `1` | Step increment |
| `label` | string | — | Header label |
| `tint` | string | `"#667eea"` | Track fill color |
| `style` | string | `"default"` | `"default"`, `"scrubber"`, or `"radial"` |
| `formatValue` | string | `"decimal"` | Value display format |
| `minIcon` | string | — | SF Symbol at minimum end |
| `maxIcon` | string | — | SF Symbol at maximum end |
| `hideLabel` | bool | `false` | Hide the header with label and value |
| `hideBackground` | bool | `false` | Remove glass background |
| `arcAngle` | number | `270` | Arc sweep in degrees (radial style only) |
| `arcRotation` | number | `0` | Arc start rotation (radial style only) |
| `arcThickness` | number | `6` | Track stroke width (radial style only) |

## What it sends and shows

The `io:` facts above are the machine-readable version: a slider sends its number while you drag (`continuous: false` sends once, on release), and it can follow a number set from outside, so the handle moves when your hub changes the value. The editor previews it at 40.

## Styles

### `"default"`
System `Slider` with optional min/max icons.

### `"scrubber"`
Custom thin progress bar with draggable dot. Used for seek bars, compact volume controls.

### `"radial"`
Circular arc slider. The user drags around an arc to set the value. Configure the arc geometry with `arcAngle`, `arcRotation`, and `arcThickness`.

## Format Values

| Value | Output | Example |
|-------|--------|---------|
| `"decimal"` | `"72"` or `"3.5"` | Respects `step` for decimal places |
| `"time"` | `"3:45"` | Minutes:seconds from total seconds |
| `"percent"` | `"80%"` | Integer percentage |
| `"none"` | (hidden) | No value display |

## Examples

### Send a seek command only on release
Shows `continuous: false`: the thumb previews while you drag, and the value is sent once when you let go.


```json
{
  "type": "slider", "id": "seek", "position": [0, 0],
  "label": "Playback", "min": 0, "max": 300, "step": 1,
  "style": "scrubber", "formatValue": "time", "continuous": false
}
```


### Basic brightness slider
Shows the default look with an action: dragging sets a room's brightness from 0 to 100, sending the number each step.

```json
{
  "type": "slider",
  "id": "lr-brightness",
  "position": [1, 0],
  "span": [1, 3],
  "min": 0,
  "max": 100,
  "step": 1,
  "defaultValue": 80,
  "label": "Brightness",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "hue-bridge", "type": "brightness", "payload": { "room": "living", "level": "{{value}}" } } }
}
```

### Volume slider with icons
Shows end symbols and a percent readout: a speaker icon at each end, with no header title, and the value written as a percentage.

```json
{
  "type": "slider",
  "id": "volume",
  "position": [0, 0],
  "span": [1, 4],
  "min": 0,
  "max": 1,
  "step": 0.01,
  "defaultValue": 0.5,
  "hideLabel": true,
  "minIcon": "speaker.fill",
  "maxIcon": "speaker.wave.3.fill",
  "formatValue": "percent",
  "tint": "#667eea"
}
```

### Seek scrubber with sync
Shows the thin scrubber look with a time readout that follows live elapsed time from the network and sends a seek when you drag.

```json
{
  "type": "slider",
  "id": "seek-slider",
  "position": [0, 0],
  "span": [1, 4],
  "min": 0,
  "max": 300,
  "step": 1,
  "defaultValue": 0,
  "label": "Position",
  "style": "scrubber",
  "tint": "#FF2D55",
  "formatValue": "time",
  "hideBackground": true,
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "player", "type": "command", "payload": { "command": "seek", "position": "{{value}}" } } },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "player_state" }, "valuePath": "elapsed" }]
}
```

### Radial dial
Shows the radial look: a 270-degree arc you drag around, with a thicker line, rotated so the gap sits at the bottom.

```json
{
  "type": "slider", "id": "thermostat", "position": [0, 0], "span": [2, 2],
  "label": "Target", "min": 10, "max": 30, "step": 0.5, "defaultValue": 21,
  "style": "radial", "arcAngle": 270, "arcRotation": 0, "arcThickness": 14,
  "tint": "#FF9500"
}
```

### Quiet slider with undo
Shows `hideValue` and `confirm`: the number is hidden, and after each change a pill with Undo appears for 3 seconds.

```json
{
  "type": "slider", "id": "fan-speed", "position": [0, 0],
  "label": "Fan", "min": 0, "max": 5, "step": 1, "defaultValue": 2,
  "hideValue": true, "confirm": true, "animation": "snappy"
}
```

### Themed slider
Shows `theme` overrides: a tall track, a large square-ish handle with no shadow, and a custom accent, for a bolder bar.

```json
{
  "type": "slider", "id": "bold-level", "position": [0, 0],
  "label": "Level", "min": 0, "max": 10, "step": 1, "formatValue": "decimal",
  "theme": { "trackHeight": 44, "thumbSize": 40, "thumbRadius": 8, "thumbShadow": false, "trackColor": "#2C2C2E", "thumbColor": "#FFFFFF", "cornerRadius": 20 }
}
```

## Behavior
- With `continuous: true` (default), all styles send actions as the dragged value changes, plus one final action on release. Repeated movement within the same detent does not send extra change actions.
- With `continuous: false`, the thumb and local value preview throughout the drag, but only release sends an action. Cancellation or removal restores the starting value without sending an action, unless a newer remote value has replaced the preview. VoiceOver adjustments remain immediate.
- `hideValue: true` hides header and radial readouts while retaining the label and spoken value.
- Positive `step` snaps relative to `min`; `step <= 0` is continuous. Values always stay within the range, and both endpoints are reachable even when the span is not a multiple of `step`.
- Reversed bounds are sorted; equal bounds produce a fixed value. Incoming values outside the range are clamped for display without writing back during rendering.
- All styles animate remote changes. Radial fill and thumb move together along the arc; dragging follows the finger immediately. Reduce Motion disables travel animation. Arc sweep clamps to 1–360° and thickness to 1–40 pt.
- Drag cancellation and removal end the editing session, allowing the attribute editor to close its undo group.
- Network-synced value updates animate smoothly unless the user is actively dragging
- No default haptic (system provides its own slider feedback)

## Related
- [[shared-properties]] — Base fields
- [[style-properties#Slider Fields]] — Full field reference
- [[actions]] — `{{value}}` substitution
- [[sync]] — Value sync from network
