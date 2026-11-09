---
type: stepper
label: Stepper
icon: plus.forwardslash.minus
category: controls
defaultSpan: [1, 2]
addIntent: change
pickerCategory: Inputs
depth: complete
friendlyName: Plus / minus
oneLiner: Count up or down one step at a time
aliases: [plus minus, increment, counter, quantity, spinner, number input]
addRank: 4
starterPreset: {"label": "Count","min": 0,"max": 100,"step": 1}
io:
  - emits: value
    when: change
    title: When you tap plus or minus
    type: number
    says: the number it now shows
    example: 5
    also: Each step sends once; a step that changes nothing, such as plus at the highest value, sends nothing
    since: next
  - receives: value
    role: follow
    type: number
    from: [hub, mqtt, http, store, default]
    says: a number to show; text that reads as a number works too
    reacts: the number rolls to it, held between the lowest and highest value; your next step starts from there
    example: 5
    since: next
  - sample: 5
    next: 6
fields:
  - name: animation
    title: Motion
    tab: style
    type: enum
    values: [smooth, snappy, bouncy, gentle, instant]
    description: Motion profile for value changes
    summary: How the number changes when it steps
    does: "Sets how the readout animates between values, from an instant swap to a soft glide."
    valueHelp: {"smooth": "an even natural transition", "snappy": "a quick firm change", "bouncy": "overshoots slightly then settles", "gentle": "a slow soft transition", "instant": "changes with no animation"}
    valueTitles: {"smooth": "Smooth", "snappy": "Snappy", "bouncy": "Bouncy", "gentle": "Gentle", "instant": "Instant"}
    valueSymbols: {"smooth": "water.waves", "snappy": "bolt.fill", "bouncy": "arrow.up.and.down.circle", "gentle": "wind", "instant": "forward.end.fill"}
  - name: min
    chip: Range
    edit: range
    depth: surface
    title: Lowest value
    bounds: none
    type: number
    default: 0
    description: Minimum value
    summary: The count never goes below this
    does: "Sets the lowest number reachable; the minus button dims there."
  - name: max
    edit: range
    depth: hold
    under: min
    axis: max
    title: Highest value
    bounds: none
    type: number
    default: 100
    description: Maximum value
    summary: The count never goes above this
    does: "Sets the highest number reachable; the plus button dims there."
  - name: step
    edit: range
    depth: hold
    under: min
    axis: step
    title: Step size
    bounds: none
    type: number
    default: 1
    description: Positive increment/decrement amount; zero or negative falls back to 1
    summary: How much each tap adds or removes
    does: "Changes the number by this amount per tap, in the control's own units; 0 or less acts as 1."
  - name: repeatOnHold
    effect: behavior
    edit: switch
    depth: hold
    title: Repeat while held
    tab: action
    type: bool
    default: false
    description: Hold plus or minus to repeat steps using the system repeat behavior
    summary: Keeps stepping while you hold a button
    does: "On, holding plus or minus repeats the step until you let go; off, each tap is one step."
  - name: wraps
    edit: part
    depth: hold
    title: Wrap around at the ends
    type: bool
    default: false
    description: Step past an endpoint to cycle to the opposite endpoint
    summary: Loops around instead of stopping
    does: "On, plus at the highest value jumps to the lowest and minus at the lowest jumps to the highest; off, the buttons dim at the ends."
  - name: hideValue
    edit: part
    depth: hold
    title: Hide the number
    type: bool
    default: false
    description: Hide the numeric readout; keep the buttons, label, and spoken value
    summary: Takes the number off the control
    does: "Removes the visible number between the buttons; the title and buttons stay and VoiceOver still reads the value."
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Display label
    summary: The name shown on the control
    does: "Writes this text as the title of the stepper."
  - name: icon
    edit: symbol
    depth: surface
    title: Symbol
    type: string
    description: SF Symbol before value
    summary: A small picture beside the number
    does: "Shows this SF Symbol before the value."
  - name: formatValue
    title: Number format
    tab: data
    type: enum
    values: [{ value: decimal, since: next }, { value: percent, since: next }, { value: time, since: next }, { value: duration, since: next }, { value: bytes, since: next }, { value: bytesKB, since: next }, { value: bps, since: next }, { value: relative, since: next }, { value: none, since: next }]
    default: decimal
    valueHelp: {"decimal": "a plain number like 72 or 3.5", "percent": "a whole percentage like 80%", "time": "minutes and seconds like 3:45, from a total in seconds", "duration": "a length of time like 1h 5m, from seconds", "bytes": "a size like 1.2 MB, from bytes", "bytesKB": "a size like 1.2 MB, from kilobytes", "bps": "a speed like 4 Mbps, from bits per second", "relative": "how long ago, like 5 min ago, from a date", "none": "no number shown"}
    valueTitles: {"decimal": "Decimal", "percent": "Percent", "time": "Time", "duration": "Duration", "bytes": "Bytes", "bytesKB": "Kilobytes", "bps": "Bits per second", "relative": "Relative", "none": "None"}
    valueSymbols: {"decimal": "number", "percent": "percent", "time": "clock", "duration": "timer", "bytes": "internaldrive", "bytesKB": "externaldrive", "bps": "speedometer", "relative": "clock.arrow.circlepath", "none": "nosign"}
    description: "Value format: decimal, percent, time, duration, bytes, bytesKB, bps, relative or none; decimal:N, prefix:X and suffix:X also work in JSON"
    summary: How the number is written
    does: "Changes the readout from a plain number such as 72 to a time like 3:45 or a percentage like 80%; suffix:text adds a unit."
  - name: defaultValue
    edit: scrub
    depth: hold
    under: min
    title: Starting value
    bounds: none
    type: number
    description: Initial value
    summary: Where the count starts
    does: "Shows this number (within lowest to highest) until something else sets it."
  - name: haptic
    edit: look
    depth: hold
    under: label
    title: Vibration on tap
    tab: action
    type: enum
    values: [light, medium, heavy, success, warning, error, selection]
    default: light
    description: Default haptic on step
    summary: The buzz you feel on each tap
    does: "Plays this vibration on every step: light to heavy taps or a success warning error or selection pattern."
    valueHelp: {"light": "a soft tap", "medium": "a firmer tap", "heavy": "a strong thump", "success": "a pleasant double tap", "warning": "a cautionary buzz", "error": "a sharp failure buzz", "selection": "a tiny tick like a picker"}
    valueTitles: {"light": "Light", "medium": "Medium", "heavy": "Heavy", "success": "Success", "warning": "Warning", "error": "Error", "selection": "Selection"}
    valueSymbols: {"light": "circle", "medium": "circle.fill", "heavy": "circle.inset.filled", "success": "checkmark.circle", "warning": "exclamationmark.triangle", "error": "xmark.octagon", "selection": "hand.tap"}
  - use: confirm
    does: "Shows a pill naming the change with an Undo button for 3 seconds after you step."
themeFields:
  - use: cornerRadius
    summary: How round the card corners are
    does: "Rounds the card corners from 0 (square) to 30 points."
  - use: controlPadding
    summary: Space between the card edge and the content
    does: "Sets the padding inside the card from 0 to 24 points."
  - use: surfacePrimary
    does: "Fills the card behind the stepper with this color."
  - use: accentColor
    summary: The highlight color
    does: "Sets the accent used for highlights on the stepper."
  - use: borderColor
  - use: labelFontSize
  - name: valueFontSize
    title: Number text size
    min: 8
    max: 28
    step: 1
    type: number
    default: 14
    description: Value text size
    summary: How big the number is
    does: "Sets the number text size from 8 to 28 points."
  - name: buttonColor
    edit: color
    depth: surface
    title: Button color
    type: color
    default: #667eea
    description: Button fill color
    summary: The color of the plus and minus buttons
    does: "Fills both round buttons with this color."
  - name: buttonRadius
    edit: scrub
    depth: hold
    under: buttonColor
    unit: pt
    title: Button roundness
    min: 0
    max: 30
    step: 1
    type: number
    default: 8
    description: Button corner radius
    summary: How round the buttons are
    does: "Rounds the button corners from 0 (square) to 30 points."
  - name: buttonSize
    edit: scrub
    depth: hold
    under: buttonColor
    unit: pt
    title: Button size
    min: 12
    max: 50
    step: 1
    type: number
    default: 32
    description: Button diameter
    summary: How big the buttons are
    does: "Sets the button diameter from 12 to 50 points."
  - name: iconColor
    edit: color
    depth: hold
    under: buttonColor
    title: Symbol color
    type: color
    default: #FFFFFF
    description: Button icon color
    summary: The color of the plus and minus signs
    does: "Colors the symbols drawn on the buttons."
  - use: borderWidth
    summary: How heavy the outline is
    does: "Sets the card outline thickness from 0 to 5 points."
  - use: secondaryColor
    summary: The softer text color
    does: "Colors the secondary text such as the title."
colorSlots:
  - slot: button
    default: primary
    alias: theme.buttonColor
    since: next
    summary: The color of the plus and minus buttons
    does: Fills the plus and minus buttons; until set they follow the primary role, or the stepper theme's button color when the layout chose one.
  - slot: symbol
    default: "#FFFFFF"
    alias: theme.iconColor
    since: next
    summary: The color of the plus and minus signs
    does: Draws the plus and minus signs; until set they keep the stepper theme's symbol color, white.
  - slot: value
    default: primary
    alias: tint
    since: next
    summary: The color of the number
    does: Colors the number and the icon; until set they follow the primary role.
---

# Stepper

An increment/decrement numeric control. Stores a `.number` value.

## Type
`"stepper"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `min` | number | `0` | Minimum value |
| `max` | number | `100` | Maximum value |
| `step` | number | `1` | Increment/decrement amount |
| `label` | string | — | Display label |
| `icon` | string | — | SF Symbol before value |
| `formatValue` | string | `"decimal"` | Value format: `"decimal"`, `"time"`, `"percent"` |
| `defaultValue` | number | — | Initial value |
| `haptic` | string | `"light"` | Default haptic on step |
| `confirm` | bool | `false` | "Show confirmation": after each local write, a 3-second pill naming the change, with Undo. See [[actions#Confirmation and Undo]] |

## Examples

### Value shown with a title and symbol

Shows the plain readout: a titled counter with an SF Symbol before the number that starts at 3 and moves one at a time between 0 and 10.

```json
{
  "type": "stepper", "id": "guests", "position": [0, 0],
  "label": "Guests", "icon": "person.2", "min": 0, "max": 10, "step": 1,
  "defaultValue": 3
}
```

### Cyclic selector with hold-to-repeat

Cycles through presets 1 to 8: holding a button keeps stepping, and stepping past either end jumps to the other end.

```json
{
  "type": "stepper", "id": "preset", "position": [0, 1],
  "label": "Preset", "min": 1, "max": 8, "step": 1,
  "repeatOnHold": true, "wraps": true
}
```

### Number formats

Writes the value as a percentage in steps of 5; use `"time"` for minutes and seconds from a total in seconds, or `"suffix:text"` to add a unit.

```json
{
  "type": "stepper", "id": "volume-pct", "position": [0, 2],
  "label": "Volume", "min": 0, "max": 100, "step": 5,
  "formatValue": "percent", "defaultValue": 40
}
```

### Hidden number

Keeps the buttons and title but hides the number, for a stepper whose value is shown elsewhere; VoiceOver still announces it.

```json
{
  "type": "stepper", "id": "silent-count", "position": [1, 0],
  "label": "Adjust", "min": 0, "max": 20, "hideValue": true
}
```

### Haptic and confirmation

Gives a heavy vibration on each tap and shows an Undo pill for 3 seconds after every change.

```json
{
  "type": "stepper", "id": "servings", "position": [1, 1],
  "label": "Servings", "min": 1, "max": 12, "haptic": "heavy", "confirm": true
}
```

### Restyled buttons

Makes large, fully round orange buttons with a dark symbol and bigger numbers, set through the theme.

```json
{
  "type": "stepper", "id": "styled", "position": [1, 2],
  "label": "Laps", "min": 0, "max": 50,
  "theme": { "buttonColor": "#FF9F0A", "buttonRadius": 30, "buttonSize": 44, "iconColor": "#000000", "valueFontSize": 22 }
}
```

### Thermostat target

Sends the new number to a device on every step: the action substitutes `{{value}}` with the current count, so the thermostat follows the stepper.

```json
{
  "type": "stepper",
  "id": "target-temp",
  "position": [2, 0],
  "span": [1, 2],
  "min": 60,
  "max": 85,
  "step": 1,
  "defaultValue": 72,
  "label": "Target °F",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "ecobee", "type": "set_temp", "payload": { "target": "{{value}}" } } }
}
```

## Behavior
- Displays current value with animated numeric transition
- With `wraps: false` (default), +/- buttons disable and dim at their respective limits. An unchanged value emits no action, including VoiceOver adjustments.
- Buttons and VoiceOver use the same bounded increment. Zero, negative, or non-finite `step` falls back to 1.
- Reversed min/max bounds are sorted; equal bounds disable both buttons. Incoming values outside the range are clamped for display and the next adjustment starts from that boundary.

- `repeatOnHold: true` enables press-and-hold repetition for both buttons. Releasing or cancelling the press stops repetition. The normal bounds or wrap behavior applies to each step.
- `wraps: true` cycles from max to min (plus) and min to max (minus), including VoiceOver. A step that overshoots first lands on the boundary; the next step wraps. Equal bounds still disable both buttons.
- `hideValue: true` hides only the visible number; VoiceOver still announces the value.

## Related
- [[shared-properties]] — Base fields
- [[actions]] — `{{value}}` substitution
- [[haptics]] — Feedback on step
