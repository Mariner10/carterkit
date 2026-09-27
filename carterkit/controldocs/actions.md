---
type: actions
label: Actions
icon: bolt.fill
category: system
fields:
  - name: method
    type: string
    description: Transport method (meshsocket, mqtt, http, local)
  - name: mode
    type: string
    description: Send mode (request, broadcast) — meshsocket only
  - name: event
    type: string
    description: Event name to fire (meshsocket)
  - name: payload
    type: object
    description: Data to send (supports {{value}} substitution)
  - name: source
    type: string
    description: Named entry in the layout's sources (mqtt/http/local)
  - name: topic
    type: string
    description: MQTT topic to publish to
  - name: retain
    type: bool
    default: false
    description: Publish with the MQTT retained flag
  - name: url
    type: string
    description: Absolute request URL (http)
  - name: path
    type: string
    description: Path against the source's baseURL (http)
  - name: httpMethod
    type: string
    description: HTTP verb (default POST with a payload, GET without)
  - name: headers
    type: object
    description: Extra HTTP headers for this action
  - name: op
    type: enum
    values: [insert, update, upsert, delete, select, set, increment, decrement, toggle]
    description: Local-store operation; set/increment/decrement/toggle write a singleton collection (local)
  - name: collection
    type: string
    description: Collection the op targets (local)
  - name: id
    type: string
    description: Record id for update/upsert/delete/select; tokens such as {{selected}} allowed (local)
  - name: set
    type: object
    description: Declared field → value for insert/update/upsert and the singleton set op; supports {{value}} and the store tokens (local)
  - name: field
    type: string
    description: Singleton field an increment/decrement (number or integer) or toggle (bool) changes (local)
  - name: by
    type: number
    default: 1
    description: Step for increment/decrement; a number or an exact token such as {{value}} (local)
---

How controls send commands — the outbound half of the **standardized connection
block**. The payload vocabulary (`{{value}}` and friends) is identical across
transports; `method` picks the wire.

## Definition

```json
"action": {
  "method": "meshsocket",
  "mode": "request",
  "event": "set_power",
  "payload": { "state": "{{value}}" }
}
```

The same command over other transports (see [[sources]]):

```json
{ "method": "mqtt", "topic": "power/set", "payload": "{{value}}" }
{ "method": "http", "path": "/api/power", "httpMethod": "POST",
  "payload": { "state": "{{value}}" } }
{ "method": "local", "op": "insert", "collection": "events",
  "set": { "kind": "power", "state": "{{value}}", "at": "{{now}}" } }
```

## Modes (meshsocket)

| Mode | Behavior |
|------|----------|
| `request` | Send + await response |
| `broadcast` | Fire and forget |

MQTT publishes and HTTP requests are fire-and-forget; failures surface in the
connection console. Ack'd commands (layout `state.acks`) are a MeshSocket
contract and don't apply to mqtt/http actions.

## Substitution

`{{value}}` in any string becomes the current control value:
- [[toggle]]: `true` / `false`
- [[slider]]: `75.0`
- [[picker]]: `"Ocean"`

A string that is *exactly* `"{{value}}"` keeps the value's native type (numbers
stay numbers, bools stay bools). Over MQTT, a string payload publishes as raw
bytes (`ON`, not `"ON"`); objects publish as JSON.

## Local store

With `method: "local"` an action writes the layout's on-device [[local-store]]
instead of sending anything. `op` is one of `insert`, `update`, `upsert`,
`delete` or `select`; `collection` names the target; `id` picks the row for
update/upsert/delete/select (`"{{selected}}"` uses the collection's selection
cursor) and `set` maps declared fields to values for insert/update/upsert.
`payload` is not used. Tokens are substituted into `set` and `id` first —
`{{value}}` and the control's own tokens plus `{{now}}`, `{{today}}`,
`{{startOfWeek}}`, `{{startOfMonth}}`, `{{startOfYear}}` and `{{selected}}` —
and an exact-token string keeps its native type, so `"pages": "{{value}}"` from a
[[stepper]] stores a number. Values are validated against the declared types
(reject, never coerce); a failure is a console line and a red `Local` pipe, never
an alert. Delete is by `id` only.

A collection declared `singleton: true` holds exactly one row, and four more ops
write it without an `id`: `set` patches the named fields, `increment` /
`decrement` add or subtract `by` (default 1) from a number or integer `field`,
and `toggle` flips a bool `field`. Each creates the row from the collection's
`defaults` on its first write.

```json
{ "method": "local", "op": "update", "collection": "books", "id": "{{selected}}",
  "set": { "rating": "{{value}}" } }
{ "method": "local", "op": "increment", "collection": "counter", "field": "count" }
{ "method": "local", "op": "toggle", "collection": "settings", "field": "muted" }
```

## Related

- [[control-def]] — every control can have an action
- [[sources]] — MQTT/HTTP source declaration
- [[local-store]] — the on-device store `local` actions write
- [[long-press]] — alternate action on long press
