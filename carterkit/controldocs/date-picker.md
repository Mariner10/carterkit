---
type: datePicker
label: Date Picker
icon: calendar
category: controls
defaultSpan: [1, 2]
addIntent: change
pickerCategory: Inputs
depth: complete
friendlyName: Date & time
oneLiner: Pick a day or a time
aliases: [calendar, time, date, schedule, clock, day]
addRank: 8
starterPreset: {"label": "When","datePickerMode": "date"}
fields:
  - name: datePickerStyle
    edit: look
    depth: surface
    title: Look
    tab: style
    type: enum
    values: [compact, wheel, graphical]
    default: compact
    description: Display style
    summary: How the date and time chooser is drawn
    does: "Switches between a small tappable field, a spinning wheel, or a full calendar grid."
    valueHelp: {"compact": "a small field that opens a pop-up when tapped", "wheel": "spinning columns you scroll to pick", "graphical": "a full month calendar shown inline"}
  - name: datePickerMode
    edit: look
    depth: surface
    title: Shows
    type: enum
    values: [date, time, dateAndTime]
    default: dateAndTime
    description: Date/time components
    summary: Whether you choose a day, a time of day, or both
    does: "Chooses which parts can be picked: the day only, the clock time only, or both together."
    valueHelp: {"date": "day month and year only", "time": "hour and minute only", "dateAndTime": "both a day and a clock time"}
  - name: dateMin
    title: Earliest date
    type: string
    description: Minimum date (ISO 8601)
    summary: The earliest day that can be chosen
    does: "Greys out and blocks dates before this ISO 8601 moment, such as 2026-01-01T00:00:00Z."
  - name: dateMax
    title: Latest date
    type: string
    description: Maximum date (ISO 8601)
    summary: The latest day that can be chosen
    does: "Greys out and blocks dates after this ISO 8601 moment, such as 2026-12-31T23:59:59Z."
  - name: label
    edit: inline
    depth: surface
    title: Label
    type: string
    description: Display label
    summary: The name shown beside the picker
    does: "Writes this text next to the date or time field."
  - name: tint
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: Accent color
    summary: The accent color of the picker
    does: "Colors the selected day and highlights in the picker with this color."
  - name: defaultValue
    title: Starting date
    type: string
    description: Initial ISO 8601 date string
    summary: The date or time shown before anyone picks
    does: "Starts the picker on this ISO 8601 moment when the layout first appears."
  - name: haptic
    title: Vibration on change
    edit: look
    depth: hold
    under: datePickerStyle
    tab: action
    type: enum
    values: [light, medium, heavy, success, warning, error, selection]
    default: selection
    description: Default haptic on change
    summary: The buzz you feel when the value changes
    does: "Plays this haptic on the phone each time a new date or time is chosen."
    valueHelp: {"light": "a small soft tap", "medium": "a medium tap", "heavy": "a strong thud", "success": "the double tap of a success", "warning": "a two-pulse warning", "error": "a sharp triple buzz of an error", "selection": "the faint tick of picking an item"}
  - name: confirm
    title: Show confirmation
    tab: action
    type: bool
    default: false
    description: After this control's local write lands, show a pill naming the change with an Undo button for 3 seconds (default off)
    summary: A short note with Undo after each change
    does: "Shows a pill naming the change with an Undo button for 3 seconds after each local write."
themeFields:
  - name: cornerRadius
    title: Corner roundness
    edit: scrub
    depth: hold
    under: datePickerStyle
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
    title: Inner spacing
    min: 0
    max: 24
    step: 1
    type: number
    default: 8
    description: Internal padding
    summary: Space between the card edge and the content
    does: "Sets the padding inside the card from 0 to 24 points."
  - name: surfacePrimary
    title: Background color
    type: color
    default: #FFFFFF0F
    description: Background fill
    summary: The card's fill color
    does: "Fills the card behind the picker with this color."
  - name: accentColor
    title: Accent color
    type: color
    default: #667eea
    description: Accent/tint color
    summary: The main highlight color
    does: "Colors the picker accents, such as the selected day, with this color."
  - name: secondaryColor
    title: Secondary text color
    type: color
    default: #FFFFFF99
    description: Secondary text color
    summary: The color of quieter text
    does: "Colors the label and other secondary text with this color."
  - name: borderColor
    title: Border color
    type: color
    default: #FFFFFF1A
    description: Border color
    summary: The color of the card outline
    does: "Colors the line around the card with this color."
  - name: borderWidth
    title: Border width
    edit: scrub
    depth: hold
    under: datePickerStyle
    unit: pt
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
    summary: How thick the card outline is
    does: "Sets the outline thickness from 0 (none) to 5 points."
  - name: labelFontSize
    title: Label size
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
    summary: How big the label text is
    does: "Sets the label text size from 8 to 24 points."
---

# Date Picker

A date and/or time selection control. Stores a `.string` value (ISO 8601 format).

## Type
`"datePicker"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `datePickerStyle` | string | `"compact"` | `"compact"`, `"wheel"`, `"graphical"` |
| `datePickerMode` | string | `"dateAndTime"` | `"date"`, `"time"`, `"dateAndTime"` |
| `dateMin` | string | — | Minimum date (ISO 8601) |
| `dateMax` | string | — | Maximum date (ISO 8601) |
| `label` | string | — | Display label |
| `tint` | string | `"#667eea"` | Accent color |
| `defaultValue` | string | — | Initial ISO 8601 date string |
| `haptic` | string | `"selection"` | Default haptic on change |
| `confirm` | bool | `false` | "Show confirmation": after each local write, a 3-second pill naming the change, with Undo. See [[actions#Confirmation and Undo]] |

## Styles

| Value | Description |
|-------|-------------|
| `"compact"` | Inline date display that expands on tap (default) |
| `"wheel"` | Spinning wheel picker |
| `"graphical"` | Calendar view for date selection |

## Modes

| Value | Components |
|-------|------------|
| `"date"` | Date only |
| `"time"` | Time only |
| `"dateAndTime"` | Both date and time |

## Examples

### Schedule time picker
Shows time-only mode with an action. Intended effect: picking a time sends it as an ISO 8601 string to set an alarm.
```json
{
  "type": "datePicker",
  "id": "alarm-time",
  "position": [0, 0],
  "span": [1, 2],
  "datePickerMode": "time",
  "datePickerStyle": "compact",
  "label": "Wake Up",
  "action": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "set_alarm", "time": "{{value}}" } }
}
```

### Date range picker with bounds
Shows the graphical calendar with `dateMin` and `dateMax`. Intended effect: a full month grid where only days in 2026 can be chosen.
```json
{
  "type": "datePicker",
  "id": "vacation-start",
  "position": [0, 0],
  "span": [2, 4],
  "datePickerMode": "date",
  "datePickerStyle": "graphical",
  "label": "Start Date",
  "dateMin": "2026-01-01T00:00:00Z",
  "dateMax": "2026-12-31T23:59:59Z"
}
```

### Wheel look for date and time
Shows the `wheel` look in `dateAndTime` mode with a starting value. Intended effect: spinning columns for day and clock time that begin on 15 June 2026 at 09:30.
```json
{
  "type": "datePicker",
  "id": "meeting-wheel",
  "position": [0, 0],
  "span": [2, 4],
  "datePickerMode": "dateAndTime",
  "datePickerStyle": "wheel",
  "label": "Meeting",
  "defaultValue": "2026-06-15T09:30:00Z"
}
```

### Date only, compact, with tint
Shows `date` mode in the default compact look with a custom accent. Intended effect: a small field that opens a calendar pop-up in green.
```json
{
  "type": "datePicker",
  "id": "due-date",
  "position": [0, 0],
  "label": "Due",
  "datePickerMode": "date",
  "datePickerStyle": "compact",
  "tint": "#34c759"
}
```

### Haptic and confirmation with Undo
Shows `haptic` and `confirm`. Intended effect: each new time gives a success buzz and a 3-second pill with Undo.
```json
{
  "type": "datePicker",
  "id": "feed-time",
  "position": [0, 0],
  "label": "Feeding",
  "datePickerMode": "time",
  "haptic": "success",
  "confirm": true,
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "feeder", "type": "schedule", "payload": { "at": "{{value}}" } } }
}
```

## Notes
- `confirm` and `haptic` only act when the value changes; with no action the picker still keeps its local value
- Value is always transmitted as ISO 8601 string (e.g., `"2026-06-04T15:30:00Z"`)
- The `{{value}}` substitution in actions outputs the ISO string

## Related
- [[shared-properties]] — Base fields
- [[actions]] — `{{value}}` substitution
