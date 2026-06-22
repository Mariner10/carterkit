---
type: haptics
label: Haptics
icon: waveform
category: system
fields:
  - name: haptic
    type: string
    description: Haptic profile name
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
