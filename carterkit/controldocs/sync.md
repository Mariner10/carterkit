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

## Notes

- Multiple syncs per [[control-def]] allowed
- Filter matches exact key-value pairs
- [[sparkline]] accumulates values in a ring buffer
- Used by [[gauge]], [[label]], [[map]], [[graph]], and more
