---
type: actions
label: Actions
icon: bolt.fill
category: system
fields:
  - name: method
    type: string
    description: Transport method (meshsocket)
  - name: mode
    type: string
    description: Send mode (request, broadcast)
  - name: event
    type: string
    description: Event name to fire
  - name: payload
    type: object
    description: Data to send (supports {{value}} substitution)
---

How controls send commands to the server.

## Definition

```json
"action": {
  "method": "meshsocket",
  "mode": "request",
  "event": "set_power",
  "payload": { "state": "{{value}}" }
}
```

## Modes

| Mode | Behavior |
|------|----------|
| `request` | Send + await response |
| `broadcast` | Fire and forget |

## Substitution

`{{value}}` in any string becomes the current control value:
- [[toggle]]: `"true"` / `"false"`
- [[slider]]: `"75.0"`
- [[picker]]: `"Ocean"`

## Related

- [[control-def]] — every control can have an action
- [[long-press]] — alternate action on long press
