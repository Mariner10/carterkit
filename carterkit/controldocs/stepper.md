---
type: stepper
label: Stepper
icon: plus.forwardslash.minus
category: controls
defaultSpan: [1, 2]
fields:
  - name: animation
    type: enum
    values: [smooth, snappy, bouncy, gentle, instant]
    description: Motion profile for value changes
  - name: min
    bounds: none
    type: number
    default: 0
    description: Minimum value
  - name: max
    bounds: none
    type: number
    default: 100
    description: Maximum value
  - name: step
    bounds: none
    type: number
    default: 1
    description: Positive increment/decrement amount; zero or negative falls back to 1
  - name: repeatOnHold
    type: bool
    default: false
    description: Hold plus or minus to repeat steps using the system repeat behavior
  - name: wraps
    type: bool
    default: false
    description: Step past an endpoint to cycle to the opposite endpoint
  - name: hideValue
    type: bool
    default: false
    description: Hide the numeric readout; keep the buttons, label, and spoken value
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
    bounds: none
    type: number
    description: Initial value
  - name: haptic
    type: enum
    values: [light, medium, heavy, success, warning, error, selection]
    default: light
    description: Default haptic on step
themeFields:
  - name: cornerRadius
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
  - name: controlPadding
    min: 0
    max: 24
    step: 1
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
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
  - name: valueFontSize
    min: 8
    max: 28
    step: 1
    type: number
    default: 14
    description: Value text size
  - name: buttonColor
    type: color
    default: #667eea
    description: Button fill color
  - name: buttonRadius
    min: 0
    max: 30
    step: 1
    type: number
    default: 8
    description: Button corner radius
  - name: buttonSize
    min: 12
    max: 50
    step: 1
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

### Cyclic selector with hold-to-repeat

```json
{
  "type": "stepper", "id": "preset", "position": [0, 0],
  "label": "Preset", "min": 1, "max": 8, "step": 1,
  "repeatOnHold": true, "wraps": true
}
```


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
