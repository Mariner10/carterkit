---
type: datePicker
label: Date Picker
icon: calendar
category: controls
defaultSpan: [1, 2]
fields:
  - name: datePickerStyle
    type: enum
    values: [compact, wheel, graphical]
    default: compact
    description: Display style
  - name: datePickerMode
    type: enum
    values: [date, time, dateAndTime]
    default: dateAndTime
    description: Date/time components
  - name: dateMin
    type: string
    description: Minimum date (ISO 8601)
  - name: dateMax
    type: string
    description: Maximum date (ISO 8601)
  - name: label
    type: string
    description: Display label
  - name: tint
    type: color
    default: "#667eea"
    description: Accent color
  - name: defaultValue
    type: string
    description: Initial ISO 8601 date string
  - name: haptic
    type: enum
    values: [light, medium, heavy, success, warning, error, selection]
    default: selection
    description: Default haptic on change
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
  - name: accentColor
    type: color
    default: #667eea
    description: Accent/tint color
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
```json
{
  "type": "datePicker",
  "id": "alarm-time",
  "position": [0, 0],
  "span": [1, 2],
  "datePickerMode": "time",
  "datePickerStyle": "compact",
  "label": "Wake Up",
  "action": { "method": "meshsocket", "mode": "request", "event": "set_alarm", "payload": { "time": "{{value}}" } }
}
```

### Date range picker with bounds
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

## Notes
- Value is always transmitted as ISO 8601 string (e.g., `"2026-06-04T15:30:00Z"`)
- The `{{value}}` substitution in actions outputs the ISO string

## Related
- [[shared-properties]] — Base fields
- [[actions]] — `{{value}}` substitution
