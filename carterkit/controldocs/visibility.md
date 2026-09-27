---
type: visibility
label: Visibility
icon: eye.fill
category: system
fields:
  - name: when
    type: string
    description: Legacy leaf — the control ID to watch (same as ref.control)
  - name: ref
    type: object
    description: 'Leaf subject — exactly one of {"control": id} or {"selected": collection}; "field" and "derive" are reserved'
  - name: operator
    type: string
    description: Comparison operator (eq, ne, gt, gte, lt, lte, in, exists; aliases neq, is, isNot). Omitted = eq
  - name: value
    type: any
    description: Value to compare against (required on every leaf)
  - name: all
    type: array
    description: Every listed condition must hold
  - name: any
    type: array
    description: At least one listed condition must hold
  - name: not
    type: object
    description: The listed condition must NOT hold
---

Show/hide or enable/disable controls and groups based on other values. The same
condition shape drives two fields on any control or group:

- `visible` — false hides the child (it keeps its grid slot).
- `enabled` — false dims the child and turns off touches; it stays on screen.

## Definition

The simplest condition is one comparison (a **leaf**):

```json
"visible": {
  "when": "power-toggle",
  "operator": "eq",
  "value": true
}
```

`when` is shorthand for a control ref. The general leaf names what it reads with `ref`:

```json
"enabled": { "ref": { "control": "name" }, "operator": "ne", "value": "" }
```

Combine leaves with `all`, `any` and `not` (nest them freely, up to 16 levels):

```json
"visible": { "all": [
  { "ref": { "selected": "plants" }, "operator": "ne", "value": null },
  { "any": [
    { "ref": { "control": "daysDry" }, "operator": "gte", "value": 3 },
    { "not": { "when": "hideHealthy", "value": true } }
  ] }
] }
```

## Refs

| Ref | Reads | Notes |
|-----|-------|-------|
| `{"control": "<id>"}` | that control's current value | same as `"when": "<id>"` |
| `{"selected": "<collection>"}` | the selected record id of a local collection or view | set by a `local` action with `op: "select"`; null when nothing is selected |
| `{"field": "…"}`, `{"derive": "…"}` | reserved | forms and derive are not in this app version: a condition that uses them is always false |

## Operators

`eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `exists` — the app-wide Match grammar
(also used by alert rules and support-guide conditions). `neq` is an alias of `ne`,
`is`/`isNot` of `eq`/`ne`. Omitting `operator` means `eq`.

- No coercion: `3` never equals `"3"`; `gt`/`lt` order numbers numerically and strings
  by Unicode order, never mixed types.
- `in` takes an array (`"value": ["a", "b"]`); `exists` takes a bool. Arrays and `null`
  need the `ref` form — a `when` leaf's `value` must be a bool, number or string.
- A control with no value yet satisfies only `exists: false` — every other operator,
  `ne` included, is false, so the control stays hidden.
- An unknown operator is refused on the wire and reset to `eq` (with a repair note)
  when loading from disk; it never silently compares.

## Rules

- A node carries exactly one of `all`, `any`, `not`, `ref`, `when`; `all`/`any` need at
  least one condition. Anything else, or nesting past 16 levels, is refused.
- Fail-closed: if any leaf uses a reserved ref (or an operator the app can't read), the
  whole condition is false — `visible` hides, `enabled` disables. A `not` can never
  switch something on for an older app.

## Behavior

- Hidden controls **keep their grid slot** (no reflow)
- Fade [[animations]] (`gentle` profile)
- Hit testing disabled when hidden
- Disabled controls (`enabled` false) render dimmed, ignore touches and read as dimmed
  to VoiceOver; a group's `enabled` covers every child inside it

## Related

- [[control-def]] — any control supports `visible` and `enabled`
- [[group-def]] — groups can also be conditional
