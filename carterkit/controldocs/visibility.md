---
type: visibility
label: Visibility
icon: eye.fill
category: system
fields:
  - name: when
    type: string
    description: Control ID to watch
  - name: operator
    type: string
    description: Comparison operator (eq, neq, gt, lt, gte, lte)
  - name: value
    type: any
    description: Value to compare against
---

Show/hide controls based on other values.

## Definition

```json
"visible": {
  "when": "power-toggle",
  "operator": "eq",
  "value": true
}
```

## Operators

`eq`, `neq`, `gt`, `lt`, `gte`, `lte`

## Behavior

- Hidden controls **keep their grid slot** (no reflow)
- Fade [[animations]] (`gentle` profile)
- Hit testing disabled when hidden

## Related

- [[control-def]] — any control supports this
- [[group-def]] — groups can also be conditional
