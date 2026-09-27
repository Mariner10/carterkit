---
type: sync
label: Sync
icon: arrow.triangle.2.circlepath
category: system
fields:
  - name: method
    type: string
    description: Transport method (meshsocket, mqtt, http, sensor, local)
  - name: type
    type: string
    description: Sync direction (listen)
  - name: event
    type: string
    description: Event name to subscribe to (meshsocket)
  - name: filter
    type: object
    description: Key-value pairs to match incoming messages
  - name: staleAfter
    min: 0
    max: 86400
    step: 1
    type: number
    description: Seconds after the last source arrival before the value counts as stale (opt-in; 0 opts out; overrides the layout's liveness.staleAfter)
  - name: timestampPath
    type: string
    description: Dot path to epoch seconds or ISO-8601 in the frame; age runs from that timestamp instead of receipt time
  - name: valuePath
    type: string
    description: Dot-notation path to extract value
  - name: source
    type: string
    description: Named entry in the layout's sources (mqtt/http/local)
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
    min: 1
    max: 3600
    step: 1
    type: number
    description: Poll interval in seconds (http)
  - name: collection
    type: string
    description: Collection or view name in the local source (local, required)
  - name: where
    type: object
    description: Row filter — field → operator object, or and/or combinators (local)
  - name: groupBy
    type: object
    description: Bucket rows — a field name, {field, bucket} for dates or {field, width} for numbers (local)
  - name: aggregate
    type: object
    description: Collapse rows to one value — "count" or {op, field} with sum/avg/min/max/distinct/first/last (local)
  - name: orderBy
    type: string
    description: Sort key(s); "-field" for descending (local)
  - name: limit
    min: 1
    max: 1000
    step: 1
    type: number
    description: Maximum rows or groups delivered, 1–1000 (local)
---

How controls receive live state — the **standardized connection block**. The
same vocabulary (`filter`, `valuePath`, value semantics) applies no matter the
transport; `method` picks the wire: `meshsocket` (a CAR-TER server),
`mqtt`/`http` (see [[sources]]), `sensor` (this device's own hardware), or
`local` (the on-device [[local-store]]).

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
{ "method": "local", "collection": "readings", "aggregate": { "op": "avg", "field": "cpu" } }
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

## Liveness (staleAfter)

Staleness is **opt-in**. By default a synced value looks live forever, even if
its server went quiet hours ago. Give a binding `staleAfter` (seconds) and the
app treats the value as stale once that long has passed without a new arrival:

```json
{ "method": "meshsocket", "event": "broadcast",
  "filter": { "msg_type": "telemetry" }, "valuePath": "cpu", "staleAfter": 30 }
{ "method": "mqtt", "topic": "garage/freezer", "valuePath": "temp",
  "timestampPath": "ts", "staleAfter": 900 }
{ "method": "meshsocket", "event": "broadcast", "valuePath": "mode", "staleAfter": 0 }
```

**Resolution order** for each binding:

1. The sync entry's own `staleAfter`.
2. Otherwise the layout's `liveness.staleAfter` (see [[layout-config]]).
3. Otherwise off.

`0` at whichever level applies turns staleness **off** for that binding, which
suits settings-style controls (pickers, toggles) that change rarely. Values
above 86400 (one day) are clamped to 86400; negative or non-numeric values are
ignored, as if the key were absent. A control
with several sync entries is stale only when **all** of its bindings are stale:
one live transport is enough.

**What counts as an arrival.** A frame that matches the binding's `event` and
`filter` and whose `valuePath` extracts, even if the value did not change. The
same holds for MQTT messages, HTTP poll responses, sensor readings, and the
authority's control-state snapshot (a mesh arrival).

**Values with no source.** Some writes to a control come from the app itself,
not from a source: a user gesture, an optimistic or held value released or
reverted by a command ack (see [ack'd commands](#the-layout-state-block-join-snapshots-ackd-commands)),
a `defaultValue`, a widget or Shortcuts press, a Studio write, a guide, or the
demo. These carry no source kind (`sourceKind` is nil). They **neither refresh
nor reset** the staleness clock: age always runs from the binding's last source
arrival. So tapping a toggle on a dead hub does not make it look live, and a
held value awaiting its ack keeps the age of the last real frame. A control that
has never had a source arrival is *never received*, not stale; it keeps the
usual no-data look.

**`timestampPath`** is a dot path (not an expression) to epoch seconds or an
ISO-8601 string inside the frame. When present and parseable, age runs from that
timestamp instead of from when the phone received the frame; future timestamps
are clamped to now. Retained MQTT messages need it: the broker replays the last
value on every subscribe, so receipt time says nothing about freshness.

**Sensor idle heartbeat.** Batched sensor publishers hold back unchanged readings
for up to 120 s. A `staleAfter` of 120 or less on a `msg_type: "sensor"` binding
will flicker stale whenever the publishing phone sits still; use more than 120.

Invalid values (negative, or not a number / string) are ignored, and the binding
behaves as if the key were absent. Older apps ignore both keys.

## Local hardware

With `method: "sensor"` a sync entry binds this device's own hardware instead of
the mesh — `{ "method": "sensor", "sensor": "heading" }` feeds the control the
compass with no server at all. See [[sensors]] for the catalog and
[[publishers]] to stream readings to other devices.

## Local store

With `method: "local"` a sync entry reads the layout's on-device [[local-store]]
instead of a wire. `collection` names a collection or view; the optional stage
fields `where`, `groupBy`, `aggregate`, `orderBy` and `limit` are plain JSON (no
SQL, no code) and decide the payload shape: an `aggregate` alone delivers
`{"value": n}`, a `groupBy` delivers `categories` + `series` for a [[chart]], and
a bare row query delivers `{"rows": [...], "count", "total", "first"}` for a
[[list]]. The store sets a matching default `valuePath`, so the minimal form
works everywhere. `event`, `topic`, `url`, `path`, `interval` and `sensor` are
ignored for `local`.

```json
{ "method": "local", "collection": "books", "where": { "finished": { "gte": "{{startOfYear}}" } },
  "aggregate": "count" }
```

The control re-delivers whenever a write touches the collection, when the day or
time zone changes (if the query used a token), and when the collection's
selection cursor moves (if it used `{{selected}}`).

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
