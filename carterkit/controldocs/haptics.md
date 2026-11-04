---
type: haptics
depth: complete
label: Haptics
icon: waveform
category: system
fields:
  - name: haptic
    tab: action
    type: string
    description: Haptic profile name
    summary: The buzz you feel on a tap
    does: Plays the named haptic on the phone when you interact with the control; none or an unknown name gives no tactile feedback.
---

Tactile feedback on control interactions.

## Profiles

| Name | Feel |
|------|------|
| `light` | Subtle tap |
| `medium` | Standard ([[button]] default) |
| `heavy` | Strong thud |
| `success` | Positive pattern |
| `warning` | Cautionary |
| `error` | Failure |
| `selection` | Ultra-light tick |

## Usage

```json
"haptic": "heavy"
```

Defaults: [[button]] = medium, [[toggle]] = light, [[stepper]] = light, [[segmented]] = selection

## Examples

### Strong thud on a button
A button that gives a heavy thud when pressed, so a big action feels deliberate.
```json
{
  "type": "button",
  "id": "launch",
  "position": [0, 0],
  "label": "Launch",
  "haptic": "heavy"
}
```

### Success buzz on a toggle
A toggle that plays the positive success pattern each time it flips.
```json
{
  "type": "toggle",
  "id": "lights",
  "position": [0, 1],
  "label": "Lights",
  "haptic": "success"
}
```

### Quiet tick on a stepper
A stepper that ticks very lightly with each step, so counting up stays subtle.
```json
{
  "type": "stepper",
  "id": "count",
  "position": [1, 0],
  "label": "Count",
  "min": 0,
  "max": 10,
  "haptic": "selection"
}
```
