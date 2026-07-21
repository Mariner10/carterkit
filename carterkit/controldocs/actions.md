---
type: actions
label: Actions
icon: bolt.fill
category: system
fields:
  - name: method
    type: string
    description: Transport method (meshsocket, mqtt, http)
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
    description: Named entry in the layout's sources (mqtt/http)
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

## Related

- [[control-def]] — every control can have an action
- [[sources]] — MQTT/HTTP source declaration
- [[long-press]] — alternate action on long press
