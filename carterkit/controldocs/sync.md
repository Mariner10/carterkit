---
type: sync
label: Sync
icon: arrow.triangle.2.circlepath
category: system
fields:
  - name: method
    type: string
    description: Transport method (meshsocket, mqtt, http, sensor)
  - name: type
    type: string
    description: Sync direction (listen)
  - name: event
    type: string
    description: Event name to subscribe to (meshsocket)
  - name: filter
    type: object
    description: Key-value pairs to match incoming messages
  - name: valuePath
    type: string
    description: Dot-notation path to extract value
  - name: source
    type: string
    description: Named entry in the layout's sources (mqtt/http)
  - name: topic
    type: string
    description: MQTT topic filter to subscribe (mqtt; supports +/#)
  - name: url
    type: string
    description: Absolute URL to poll (http)
  - name: path
    type: string
    description: Path against the source's baseURL (http)
  - name: interval
    type: number
    description: Poll interval in seconds (http)
---

How controls receive live state — the **standardized connection block**. The
same vocabulary (`filter`, `valuePath`, value semantics) applies no matter the
transport; `method` picks the wire: `meshsocket` (a CAR-TER server),
`mqtt`/`http` (see [[sources]]), or `sensor` (this device's own hardware).

## Definition

```json
"sync": [{
  "method": "meshsocket",
  "type": "listen",
  "event": "broadcast",
  "filter": { "msg_type": "telemetry" },
  "valuePath": "cpu"
}]
```

Equivalent bindings on other transports:

```json
{ "method": "mqtt", "topic": "server/telemetry", "valuePath": "cpu" }
{ "method": "http", "path": "/api/status", "interval": 5, "valuePath": "cpu" }
```

## Flow

1. A payload arrives (server broadcast, MQTT publish, or HTTP poll response)
2. App filters by matching all `filter` keys against the payload
3. Extracts value at `valuePath` (dot-notation)
4. Updates control binding — identically for every transport

## External sources (MQTT / HTTP)

With `method: "mqtt"` or `"http"` a sync entry binds an external source directly
— an MQTT broker topic or a polled JSON endpoint — with no MeshSocket server in
the loop. Same `filter`/`valuePath` semantics, same special receivers. See
[[sources]] for source declaration, payload rules, and full examples.

## Local hardware

With `method: "sensor"` a sync entry binds this device's own hardware instead of
the mesh — `{ "method": "sensor", "sensor": "heading" }` feeds the control the
compass with no server at all. See [[sensors]] for the catalog and
[[publishers]] to stream readings to other devices.

## The layout `state` block (join, snapshots, ack'd commands)

A top-level layout key, not a per-control sync — the app↔server session contract:

```json
"state": { "sync": true, "authority": "MyHub", "acks": true, "ackTimeoutMs": 2000 }
```

- With `sync` on (or any dynamic content in the layout), the app broadcasts
  `control_sync_request {from, dynamic:[slot events]}` on layout load AND every
  reconnect. Servers treat it as the join signal (carterkit
  `on_sync_request`) and the `authority` answers with a `control_snapshot`
  of current values, so a rejoining device renders truth immediately.
- `acks: true` opts every control action into **ack'd commands**: fired payloads
  are stamped `_cmd` (uuid) + `_from` (sender name); the serving hub answers
  `command_ack {cmd_id, to, ok}` for commands it actually handled (carterkit
  `enable_command_acks`). The control stays optimistically set but *pending* —
  sync updates are held off it — until the ack; on `ok:false` or `ackTimeoutMs`
  (default 2000) expiry it reverts to the last synced value with an error haptic.
- `control_sync_request` / `control_snapshot` / `command_ack` and the
  `_cmd`/`_from` stamps are **wire API** — never rename them.

## Notes

- Multiple syncs per [[control-def]] allowed — and they may mix transports
  (e.g. a meshsocket binding plus an [[sources]] fallback)
- Filter matches exact key-value pairs
- [[sparkline]] accumulates values in a ring buffer
- Used by [[gauge]], [[label]], [[map]], [[graph]], and more
- Dynamic-content injections are diffed **by control id**: an identical re-push
  is a no-op, and ids that persist keep their live values — keep injected ids
  stable across pushes (see [[group-def]] `dynamic`)
