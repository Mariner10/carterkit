---
type: visibility
depth: complete
label: Visibility
icon: eye.fill
category: system
fields:
  - name: when
    type: string
    description: Legacy leaf — the control ID to watch (same as ref.control)
    summary: The control to watch
    does: Names the control whose current value the condition checks; the older short form of ref.control.
  - name: ref
    type: object
    description: "Leaf subject — exactly one of {control: id}, {selected: collection}, {field: formId.cell} or {derive: form.formId.cell}"
    summary: What to look at
    does: Points the condition at a control, a selected record, a form cell or a derived value.
  - name: operator
    type: string
    description: Comparison operator (eq, ne, gt, gte, lt, lte, in, exists; aliases neq, is, isNot). Omitted = eq
    summary: How to compare
    does: Chooses the test, such as equals, greater than, in a list or exists; equals when left out.
  - name: value
    type: any
    description: Value to compare against (required on every leaf)
    summary: What to compare against
    does: Sets the value the watched thing is tested against, e.g. true or 3.
  - name: all
    type: array
    description: Every listed condition must hold
    summary: Every condition must be true
    does: Shows or enables the control only while every listed condition holds.
  - name: any
    type: array
    description: At least one listed condition must hold
    summary: At least one condition must be true
    does: Shows or enables the control while any one of the listed conditions holds.
  - name: not
    type: object
    description: The listed condition must NOT hold
    summary: Flip a condition
    does: Holds only while the listed condition does not hold.
  - name: stale
    type: boolean
    description: With `when` — true shows only while that control's feed is stale (went quiet past its staleAfter); false only while it is not. No `operator` or `value`
    summary: Only when the data went quiet
    does: With when, true holds only while that control's feed has gone stale and false only while it has not.
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
  { "ref": { "selected": "plants" }, "operator": "exists", "value": true },
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
| `{"selected": "<collection>"}` | the selected record id of a local collection or view | set by a `local` action with `op: "select"`; null when nothing is selected (test it with `exists`, below) |
| `{"field": "<formId>.<cell>"}` | a [[form]] cell: `valid`, `dirty`, `<field>`, `<field>.error` | e.g. a Save button `enabled` on `{"field": "plantForm.valid"}` |
| `{"derive": "<id>"}` | a top-level `derive` entry's current value | no value yet (or an unknown id) behaves like a control with no value |
| `{"derive": "form.<formId>.<cell>"}` | the same form cell as `field` | |

Test presence with `exists`: "nothing selected" is `"operator": "exists", "value": false` and "something selected" is `"operator": "exists", "value": true`; `eq` and `ne` against `null` never match (the NULL rule).

## Stale

`{"when": "<id>", "stale": true}` holds only while that control's binding is **stale**:
it had data, then nothing arrived within its `staleAfter`. Use it to show a card
("Sensor offline") only when the feed has gone quiet; `"stale": false` is the
opposite. A control that has never received data is not stale (it shows the "No data
yet" skeleton instead), and a control with no `staleAfter` threshold is never stale.
It takes no `operator` or `value`, and combines with `all`/`any`/`not` like any leaf.

```json
"visible": { "when": "cpu", "stale": true }
```

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
- Fail-closed: if any leaf uses an operator the app can't read, the
  whole condition is false — `visible` hides, `enabled` disables. A `not` can never
  switch something on for an older app.

## Behavior

- Hidden controls **keep their grid slot** (no reflow)
- Fade [[animations]] (`gentle` profile)
- Hit testing disabled when hidden
- Disabled controls (`enabled` false) render dimmed, ignore touches and read as dimmed
  to VoiceOver; a group's `enabled` covers every child inside it

## Examples

### Show a card when a toggle is on
Demonstrates the simplest leaf: `when` watches a control and `value` is what it must equal.
```json
{ "type": "gauge", "id": "fan-speed", "position": [1, 0], "span": [2, 2], "label": "Fan",
  "visible": { "when": "power-toggle", "operator": "eq", "value": true } }
```

### Disable Save until the form is valid
Demonstrates `enabled` with a `ref` to a form cell: the button dims and ignores touches until the form is valid.
```json
{ "type": "button", "id": "save", "position": [4, 0], "label": "Save",
  "enabled": { "ref": { "field": "plantForm.valid" }, "operator": "eq", "value": true } }
```

### Combine conditions
Demonstrates `all`, `any`, `not` and `exists`: shown when a plant is selected and it is either dry for 3 days or healthy plants are not hidden.
```json
{ "type": "statusLight", "id": "water-alert", "position": [0, 0], "label": "Needs water",
  "visible": { "all": [
    { "ref": { "selected": "plants" }, "operator": "exists", "value": true },
    { "any": [
      { "ref": { "control": "daysDry" }, "operator": "gte", "value": 3 },
      { "not": { "when": "hideHealthy", "value": true } }
    ] }
  ] } }
```

### Offline notice
Demonstrates `stale`: the card shows only after the cpu feed went quiet past its staleAfter.
```json
{ "type": "label", "id": "offline", "position": [0, 0], "label": "Sensor offline",
  "visible": { "when": "cpu", "stale": true } }
```

## Related

- [[control-def]] — any control supports `visible` and `enabled`
- [[group-def]] — groups can also be conditional
