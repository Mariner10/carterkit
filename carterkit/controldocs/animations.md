---
type: animations
label: Animations
icon: sparkles
category: system
fields:
  - name: profile
    type: string
    description: Named animation preset
  - name: duration
    min: 0
    max: 10
    step: 0.1
    type: number
    description: Custom duration override
---

Transition and interaction animations.

## Profiles

| Name | SwiftUI |
|------|---------|
| `snappy` | Spring: 0.25 seconds, bounce 0.1 |
| `smooth` | Spring: 0.35 seconds, bounce 0.15 |
| `bouncy` | Spring: 0.5 seconds, bounce 0.3 |
| `gentle` | `.easeInOut(duration: 0.6)` |
| `instant` | `.linear(duration: 0)` |

## Usage

```json
"animation": "bouncy"
```

Or custom:
```json
"animation": { "profile": "smooth", "duration": 0.5 }
```

A custom duration of zero (or a negative duration) is immediate. The `instant` profile stays immediate even with a duration override. Non-finite durations fall back to the profile default.

Toggle switches honor animation overrides for taps, remote state changes, and drag release or cancellation. Their default is a spring with response 0.32 and damping 0.64. Curved toggle knobs and radial slider thumbs follow their tracks during animation. Dragging follows the finger immediately; Reduce Motion disables these travel animations.

## Related

- [[visibility]] — uses `gentle` for show/hide
- [[control-def]] — any control can override its animation
