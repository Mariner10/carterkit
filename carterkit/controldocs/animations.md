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
    type: number
    description: Custom duration override
---

Transition and interaction animations.

## Profiles

| Name | SwiftUI |
|------|---------|
| `snappy` | `.snappy` |
| `smooth` | `.smooth(duration: 0.35)` |
| `bouncy` | `.bouncy(duration: 0.5)` |
| `gentle` | `.easeInOut(duration: 0.25)` |
| `instant` | `.linear(duration: 0)` |

## Usage

```json
"animation": "bouncy"
```

Or custom:
```json
"animation": { "profile": "smooth", "duration": 0.5 }
```

## Related

- [[visibility]] — uses `gentle` for show/hide
- [[control-def]] — any control can override its animation
