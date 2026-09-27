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

`eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `exists` — the app-wide Match grammar
(also used by alert rules and support-guide conditions). `neq` is an alias of `ne`,
`is`/`isNot` of `eq`/`ne`. Omitting `operator` means `eq`.

- No coercion: `3` never equals `"3"`; `gt`/`lt` order numbers numerically and strings
  by Unicode order, never mixed types.
- `in` takes an array (`"value": ["a", "b"]`); `exists` takes a bool.
- A control with no value yet satisfies only `exists: false` — every other operator,
  `ne` included, is false, so the control stays hidden.
- An unknown operator is refused on the wire and reset to `eq` (with a repair note)
  when loading from disk; it never silently compares.

## Behavior

- Hidden controls **keep their grid slot** (no reflow)
- Fade [[animations]] (`gentle` profile)
- Hit testing disabled when hidden

## Related

- [[control-def]] — any control supports this
- [[group-def]] — groups can also be conditional
