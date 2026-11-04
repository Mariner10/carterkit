---
type: sync
label: Sync
icon: arrow.triangle.2.circlepath
category: system
fields:
  - name: method
    tab: advanced
    type: string
    description: Transport method (meshsocket, mqtt, http, sensor, local, derive)
  - name: type
    type: string
    description: Sync direction (listen)
  - name: event
    tab: advanced
    type: string
    description: MeshSocket frame type to match (meshsocket). Server broadcasts arrive as "broadcast" (demux with filter.msg_type); any other name only matches frames routed to this device by route_msg_noreply
  - name: filter
    tab: advanced
    type: object
    description: Key-value pairs to match incoming messages
  - name: staleAfter
    min: 0
    max: 86400
    step: 1
    type: number
    description: Seconds after the last source arrival before the value counts as stale (opt-in, except HTTP polls default to max(layout liveness.staleAfter, 3x interval); 0 opts out; overrides the layout's liveness.staleAfter)
  - name: timestampPath
    tab: advanced
    type: string
    description: Dot path to epoch seconds or ISO-8601 in the frame; age runs from that timestamp instead of receipt time
  - name: endsAtPath
    tab: advanced
    type: string
    description: Dot path to an end time (epoch seconds or ISO-8601, e.g. an ETA) beside the value; widgets, Lock Screen and Live Activity count down / fill toward it with no push, and the next real value replaces it
  - name: valuePath
    tab: advanced
    type: string
    description: Dot-notation path to extract value
  - name: source
    type: string
    description: Named entry in the layout's sources (mqtt/http/local)
  - name: topic
    tab: advanced
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
  - name: from
    type: string
    description: The id of a layout derive entry this control shows (derive)
  - name: group
    type: string
    description: Event group the binding belongs to (meshsocket, optional)
  - name: sensor
    type: string
    description: "On-device stream to bind when method is sensor, e.g. heading (see [[sensors]])"
  - name: having
    type: object
    description: "Filter on aggregated groups: {key|value: {op: v}} (local, with groupBy)"
---

How controls receive live state — the **standardized connection block**. The
same vocabulary (`filter`, `valuePath`, value semantics) applies no matter the
transport; `method` picks the wire: `meshsocket` (a CAR-TER server),
`mqtt`/`http` (see [[sources]]), `sensor` (this device's own hardware),
`local` (the on-device [[local-store]]), or `derive` (a value the phone
computes from other values, see [[derive]]).

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

`event` is the MeshSocket frame type. A server's `broadcast_request` reaches every
channel member as a `broadcast` frame, so server pushes bind `"event": "broadcast"` and
tell streams apart with `filter.msg_type`. A custom `event` name (`"telemetry"`) only
matches a frame routed straight to this device (`route_msg_noreply` with that `type`);
a plain broadcast never reaches it.

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

Staleness is **opt-in**, except for HTTP polls (below). By default a synced
value looks live forever, even if its server went quiet hours ago. Give a
binding `staleAfter` (seconds) and the app treats the value as stale once that
long has passed without a new arrival:

```json
{ "method": "meshsocket", "event": "broadcast",
  "filter": { "msg_type": "telemetry" }, "valuePath": "cpu", "staleAfter": 30 }
{ "method": "mqtt", "topic": "garage/freezer", "valuePath": "temp",
  "timestampPath": "ts", "staleAfter": 900 }
{ "method": "meshsocket", "event": "broadcast", "valuePath": "mode", "staleAfter": 0 }
```

**Resolution order** for each binding:

1. The sync entry's own `staleAfter`.
2. Otherwise, for an `http` poll: the larger of the layout's
   `liveness.staleAfter` and 3 x the binding's poll interval, or 3 x the poll
   interval when the layout sets no default. A poll never flaps stale between
   two polls, and is never stricter than the layout default. The interval is
   the one the poller uses: the binding's `interval`, else its source's, else 5 s.
3. Otherwise the layout's `liveness.staleAfter` (see [[layout-config]]).
4. Otherwise off.

So with `"liveness": {"staleAfter": 60}`, an HTTP binding polled every 300 s goes
stale after 900 s; with `"staleAfter": 1200`, one polled every 60 s goes stale
after 1200 s.

`0` at whichever level applies turns staleness **off** for that binding, which
suits settings-style controls (pickers, toggles) that change rarely. A layout
`liveness.staleAfter` of `0` opts HTTP polls out too. Values
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
are clamped to now. A number is epoch seconds (a value above 1e11 is read as
milliseconds); a string is ISO-8601, with or without fractional seconds. A missing
or unparseable value falls back to receipt time. Retained MQTT messages need it: the broker replays the last
value on every subscribe, so receipt time says nothing about freshness.

**`endsAtPath`** is a dot path to an end time (same formats as `timestampPath`,
future-dated). A control carrying it shows a system countdown timer on every
surface; widget timelines get an entry per minute along a projection. A time
already past, missing or unparseable clears the forecast. Each real arrival
replaces the previous forecast, and a forecast that runs out with no newer value
reads stale.

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

## Derived values (derive / from)

With `method: "derive"` a sync entry shows a value the phone computes from the
layout's top-level `derive` block instead of a wire. `from` names the derive
entry; nothing else is needed (no `event`, `filter` or `valuePath`):

```json
"derive": { "watts": { "mul": [ {"control": "volts"}, {"control": "amps"} ] } }
...
{ "type": "gauge", "id": "wattsGauge", "min": 0, "max": 1800,
  "sync": [ { "method": "derive", "from": "watts" } ] }
```

The value is recomputed whenever an input control's displayed value moves, on
this device only: derived values never go on the wire, and relay alerts cannot
see them. `from` must name a declared derive id. See [[derive]] for the ops,
argument forms and nil rules.

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
- **Epochs.** `control_snapshot {to, v, epoch, controls}` carries an optional
  `epoch`: an opaque string the authority mints once per process (a restart = a
  new epoch). Replicas order `v` per epoch only, so a restarted hub whose counter
  starts over at 1 is adopted at once, and two hubs on one channel never drop each
  other's lower counter. A snapshot with no `epoch` is ordered as before (one
  legacy counter). Every reconnect/`control_sync_request` also resets the ordering.
- **Ages.** `control_snapshot` may carry `ages {id: seconds}`: how long ago the
  authority last received data for each control that has had an arrival. The
  replica dates each applied value at now minus its age, so a day-old reading does
  not look fresh after a rejoin. With no `ages` (older authority), a non-finite
  age, or an id with no entry, the replica stamps the arrival at now; negative ages
  count as 0.
- **Authority hello.** On start an authority broadcasts
  `control_authority_hello {epoch, from}` (`from` = its own name). A replica only
  honours a hello whose `from` is the layout's configured `state.authority` (exact
  name, or the bare name inside the account's relay-namespaced name). An unseen
  epoch from that authority makes the replica send one `control_sync_request` right
  away, so it gets the restarted hub's real state within a second even if it never
  disconnected. Hellos from any other sender, repeat hellos for a known epoch, and
  hellos received by the authority itself are ignored. Hello-triggered requests are
  rate-limited to one per 3 s; a hello dropped by the limit is not remembered.
- `acks: true` opts every control action into **ack'd commands**: fired payloads
  are stamped `_cmd` (uuid) + `_from` (sender name); the serving hub answers
  `command_ack {cmd_id, to, ok}` for commands it actually handled (carterkit
  `enable_command_acks`). The control stays optimistically set but *pending* —
  sync updates are held off it — until the ack; on `ok:false` or `ackTimeoutMs`
  (default 2000) expiry it reverts to the last synced value with an error haptic.
- `control_sync_request` / `control_snapshot` (incl. its `epoch`) /
  `control_authority_hello {epoch, from}` / `command_ack` and the `_cmd`/`_from` stamps
  are **wire API** — never rename them.

## Across launches (what the app remembers)

A layout with a `connection` block keeps what it last showed, on this device only:
its control values and the selected tab. They are saved
about a second after values settle (at least every 10 s while they stream), and again
when the app leaves the foreground or switches layouts. On the next launch the layout opens with them at once, even while
the hub is away, each value dated at its real arrival so `staleAfter` marks old ones
stale; a toggle a sync drives does not send until live data confirms it. Then live
data wins: the first frame or `control_snapshot` overwrites any remembered value.

- Never saved: a control with a `secure`, `secret` or `password` style, and a text
  input whose id, label or placeholder names a credential (password, passcode,
  secret, token, API key...).
- Limits: a value over 512 KB is skipped, a layout keeps at most 4 MB (the largest
  values go first), values older than 30 days are ignored, and a control whose type
  changed since starts from its default.
- Deleting the layout deletes them. A glance snapshot (`glance.warmOpen`) is
  applied over them, as before.

## Notes

- Multiple syncs per [[control-def]] allowed — and they may mix transports
  (e.g. a meshsocket binding plus an [[sources]] fallback)
- Filter matches exact key-value pairs
- [[sparkline]] accumulates values in a ring buffer
- Used by [[gauge]], [[label]], [[map]], [[graph]], and more
- Dynamic-content injections are diffed **by control id**: an identical re-push
  is a no-op, and ids that persist keep their live values — keep injected ids
  stable across pushes (see [[group-def]] `dynamic`)
