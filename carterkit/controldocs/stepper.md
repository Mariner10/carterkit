---
type: stepper
label: Stepper
icon: plus.forwardslash.minus
category: controls
defaultSpan: [1, 2]
fields:
  - name: min
    type: number
    default: 0
    description: Minimum value
  - name: max
    type: number
    default: 100
    description: Maximum value
  - name: step
    type: number
    default: 1
    description: Increment/decrement amount
  - name: label
    type: string
    description: Display label
  - name: icon
    type: string
    description: SF Symbol before value
  - name: formatValue
    type: string
    default: decimal
    description: "Value format: decimal, time, percent"
  - name: defaultValue
    type: number
    description: Initial value
  - name: haptic
    type: enum
    values: [light, medium, heavy, success, warning, error, selection]
    default: light
    description: Default haptic on step
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
  - name: borderColor
    type: color
    default: #FFFFFF1A
    description: Border color
  - name: labelFontSize
    type: number
    default: 12
    description: Label text size
  - name: valueFontSize
    type: number
    default: 14
    description: Value text size
  - name: buttonColor
    type: color
    default: #667eea
    description: Button fill color
  - name: buttonRadius
    type: number
    default: 8
    description: Button corner radius
  - name: buttonSize
    type: number
    default: 32
    description: Button diameter
  - name: iconColor
    type: color
    default: #FFFFFF
    description: Button icon color
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

## Examples

### Thermostat target

```json
{
  "type": "stepper",
  "id": "target-temp",
  "position": [1, 0],
  "span": [1, 2],
  "min": 60,
  "max": 85,
  "step": 1,
  "defaultValue": 72,
  "label": "Target °F",
  "action": { "method": "meshsocket", "mode": "request", "event": "route_msg", "payload": { "target_id": "ecobee", "type": "set_temp", "payload": { "target": "{{value}}" } } }
}
```

## Behavior
- Displays current value with animated numeric transition
- +/- buttons respect min/max bounds
- Fires action on each increment/decrement

## Related
- [[shared-properties]] — Base fields
- [[actions]] — `{{value}}` substitution
- [[haptics]] — Feedback on step
