---
type: form
label: Form
icon: list.bullet.rectangle.portrait
category: system
fields:
  - name: mode
    type: enum
    values: [create, edit]
    default: create
    description: "edit prefills the draft from the collection's selected record ({{selected}}) and refills it when the selection moves"
  - name: collection
    type: string
    description: Local collection the form edits; the prefill source in edit mode and the default collection of a local submit
  - name: fields
    type: object
    description: "Field name → validators, a closed set: required, min, max, minLength, maxLength, oneOf, kind (integer|number|date|email|url). No regex"
  - name: submit
    type: object
    description: "The one action the form writes with (local, http, mqtt or meshsocket); {{form}} is the whole draft, {{form.<field>}} one field"
  - name: afterSubmit
    type: enum
    values: [clear, keep]
    default: clear
    description: After a submit, clear the draft back to its starting values, or keep what was submitted
---

# Form

A **form** is a [[group-def|group]] with a `form` block. Its input children write to a
**draft** instead of firing their own actions, a closed set of validators checks the
draft, and one `submit` writes the whole draft at once. Typing never writes anything
until the user submits.

## How it works

- **Fields.** Every input inside the group (`textInput`, `stepper`, `slider`, `toggle`,
  `picker`, `segmentedControl`, `datePicker`, `colorPicker`, including those in nested
  groups but not in a nested form) is a draft field. The field name is the input's
  `field` key, else its `id`. Use `field` when two forms write the same column (an
  add form and an edit form both writing `name`), because control ids are unique in a layout.
- **No writes before submit.** While an input belongs to a form, its own `action` never
  fires, its value never reaches the control store, the mesh, or glance surfaces. The
  draft is the only place the value lives.
- **Submit.** A [[button]] with `"role": "submit"` inside the form submits it. If any
  field fails validation the submit is refused, every error shows, and nothing is
  written. Otherwise `submit` runs once with `{{form}}` = the draft object (every field;
  an empty field is `null`; `kind: integer`/`number` turns a typed `"12"` into `12`).
- **Starting values.** A field starts at the input's `defaultValue`, else what the input
  shows with no value: a stepper or slider's `min`, a picker's first option, a toggle off,
  a date picker's current time, an empty text field.
- **Edit mode.** With `"mode": "edit"` the draft is filled from the record whose id is the
  collection's selection cursor (`{{selected}}`, moved by a `local` action with
  `op: "select"`), and refilled when the selection changes. Pair it with
  `"op": "update", "id": "{{selected}}"`.

## Validators

A closed set. Anything else (including `pattern`/regex) makes the layout fail to load.

| Validator | Value | Fails when |
|-----------|-------|------------|
| `required` | bool | the field is empty (no value, blank text) |
| `min` / `max` | number | the value (or a numeric string) is below / above it |
| `minLength` / `maxLength` | integer ≥ 0 | the text is shorter / longer |
| `oneOf` | array | the value is not one of the listed values |
| `kind` | `integer` \| `number` \| `date` \| `email` \| `url` | the value is not that kind (`date` = `yyyy-MM-dd` or ISO-8601; `url` = http/https with a host; `email` is a structural check) |

An empty optional field is valid; only `required` checks emptiness. An input with an
error shows a red outline and the message once it has been edited or a submit was refused.

## Cells for conditions

A form exposes readable cells, addressed with a `field` ref in any [[visibility]]
condition (`visible` / `enabled`):

| Ref | Value |
|-----|-------|
| `{"field": "<formId>.valid"}` | `true` when every field passes |
| `{"field": "<formId>.dirty"}` | `true` when the draft differs from its starting values |
| `{"field": "<formId>.<field>"}` | the field's draft value |
| `{"field": "<formId>.<field>.error"}` | the shown error message, `null` when none |

`{"derive": "form.<formId>.valid"}` is the same cell spelled as a derive.

## Example

```json
{ "type": "group", "id": "plantForm", "label": "New plant",
  "position": [0, 0], "span": [4, 4], "grid": { "columns": 2, "rows": 3 },
  "form": {
    "collection": "plants",
    "fields": {
      "name":      { "required": true, "maxLength": 40 },
      "everyDays": { "required": true, "min": 1, "max": 60, "kind": "integer" },
      "room":      { "oneOf": ["Kitchen", "Office", "Porch"] }
    },
    "submit": { "method": "local", "op": "insert", "set": "{{form}}" }
  },
  "children": [
    { "type": "textInput", "id": "name", "position": [0, 0], "span": [1, 2], "placeholder": "Name" },
    { "type": "stepper", "id": "everyDays", "position": [1, 0], "min": 1, "max": 60, "label": "Every (days)" },
    { "type": "picker", "id": "room", "position": [1, 1], "options": ["Kitchen", "Office", "Porch"] },
    { "type": "button", "id": "save", "position": [2, 0], "span": [1, 2], "label": "Save", "role": "submit",
      "enabled": { "ref": { "field": "plantForm.valid" }, "operator": "eq", "value": true } }
  ] }
```

A form can submit anywhere an action can go: `{"method": "http", "path": "/plants", "payload": "{{form}}"}`
or `{"method": "meshsocket", "event": "broadcast_request", "payload": {"msg_type": "plant_add", "plant": "{{form}}"}}`.

## Related
- [[group-def]] — the group that carries `form`
- [[actions]] — the submit action and its tokens
- [[local-store]] — collections, `{{selected}}`
- [[visibility]] — `visible` / `enabled` conditions
