---
type: actions
label: Actions
icon: bolt.fill
category: system
fields:
  - name: method
    tab: advanced
    type: string
    description: Transport method (meshsocket, mqtt, http, local)
  - name: mode
    type: string
    description: Send mode (broadcast = fire and forget, request = await a reply; only route_msg replies) — meshsocket only
  - name: event
    tab: advanced
    type: string
    description: MeshSocket frame type, sent verbatim — must be a relay verb (broadcast_request, route_msg, route_msg_noreply); the command name goes in payload.msg_type
  - name: payload
    tab: advanced
    type: object
    description: Data to send (supports {{value}} substitution); for broadcast_request include msg_type so servers can demux
  - name: source
    type: string
    description: Named entry in the layout's sources (mqtt/http/local)
  - name: topic
    tab: advanced
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
    tab: advanced
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
    bounds: none
    type: number
    default: 1
    description: Step for increment/decrement; any non-zero number or an exact token such as {{value}}; decrement subtracts it; integer fields take whole steps only (local)
---

How controls send commands — the outbound half of the **standardized connection
block**. The payload vocabulary (`{{value}}` and friends) is identical across
transports; `method` picks the wire.

## Definition

```json
"action": {
  "method": "meshsocket",
  "mode": "broadcast",
  "event": "broadcast_request",
  "payload": { "msg_type": "set_power", "state": "{{value}}" }
}
```

## `event` vs `msg_type` (meshsocket)

The app sends `event` **verbatim as the MeshSocket frame type**, and the relay
only dispatches its own verbs — `broadcast_request` (fan-out to every other
member of the channel), `route_msg` (targeted request/reply) and
`route_msg_noreply` (targeted fire-and-forget). Any other name (`set_power`,
`broadcast`, `arm`, …) is silently dropped: nothing errors, no server handler
ever runs, the control does nothing.

So the *command name* never goes in `event`. Put it in **`payload.msg_type`** —
the relay re-emits a `broadcast_request` to the channel as a `broadcast` frame,
and servers demux on `msg_type` (carterkit's `Hub.on("set_power")` and
`bind.command("set_power")` are the two halves of exactly this shape).

Targeted send, when you hold a live relay-assigned `target_id` (a name is *not*
resolved here — use `route_msg_noreply` with `target_name` for that):

```json
"action": {
  "method": "meshsocket",
  "mode": "request",
  "event": "route_msg",
  "payload": { "target_id": "<relay id>", "type": "set_power",
               "payload": { "state": "{{value}}" } }
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
| `broadcast` | Fire and forget — the mode for `broadcast_request` and `route_msg_noreply` |
| `request` | Send + await response — only meaningful with `route_msg` (the relay routes the target's reply back); on a `broadcast_request` nothing ever replies, so the tap just waits out the timeout |

Need an answer to a broadcast command? Use the round trip instead: fire the
command, and [[sync]] the control to the state broadcast the server sends back.

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

A [[form]]'s `submit` action also gets `{{form}}` (the whole draft object) and
`{{form.<field>}}` (one draft field), on any transport: `"set": "{{form}}"` for a
local insert/update, `"payload": "{{form}}"` for http or meshsocket.

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
