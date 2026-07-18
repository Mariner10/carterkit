---
type: sync
label: Sync
icon: arrow.triangle.2.circlepath
category: system
fields:
  - name: method
    type: string
    description: Transport method (meshsocket, sensor)
  - name: type
    type: string
    description: Sync direction (listen)
  - name: event
    type: string
    description: Event name to subscribe to
  - name: filter
    type: object
    description: Key-value pairs to match incoming messages
  - name: valuePath
    type: string
    description: Dot-notation path to extract value
---

How controls receive live state from the network.

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

## Flow

1. Server broadcasts on event
2. App filters by matching all keys
3. Extracts value at `valuePath` (dot-notation)
4. Updates control binding

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

- Multiple syncs per [[control-def]] allowed
- Filter matches exact key-value pairs
- [[sparkline]] accumulates values in a ring buffer
- Used by [[gauge]], [[label]], [[map]], [[graph]], and more
- Dynamic-content injections are diffed **by control id**: an identical re-push
  is a no-op, and ids that persist keep their live values — keep injected ids
  stable across pushes (see [[group-def]] `dynamic`)
