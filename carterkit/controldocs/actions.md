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

`{{secret:name}}` fills in a credential from the phone's Keychain when the
action is sent, never earlier ([[layout-config#Secrets]]). It works in an HTTP
action's `url` path/query, `headers` and `payload`, an MQTT action's `payload`,
and a MeshSocket action's `payload`. Only the text you wrote in the action is
filled in; a `{{secret:…}}` that arrives inside `{{value}}` is sent as plain
text. The secret must be allowed at the destination:

- an HTTP or MQTT action goes to its host, which must be a declared source's
  host or listed in the secret's `hosts`. An absolute `url` on any other host
  needs `"hosts": ["that.host"]` in the declaration;
- a MeshSocket action goes to every peer in the room, so the secret needs
  `"mesh": true`. Without it the action is not sent and the console logs
  `secret <name> not allowed for the mesh`.

## Related

- [[control-def]] — every control can have an action
- [[sources]] — MQTT/HTTP source declaration
- [[layout-config#Secrets]] — `{{secret:name}}` and where a secret may be sent
- [[long-press]] — alternate action on long press
