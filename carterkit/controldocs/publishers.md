---
type: publishers
label: Publishers
icon: dot.radiowaves.left.and.right
category: system
fields:
  - name: sensor
    type: string
    description: Pipeline to stream (heading, motion, barometer, device, audio, location)
  - name: interval
    min: 1
    max: 3600
    step: 1
    type: number
    description: Seconds between frames (defaults per sensor; clamped to a safe floor)
---

Turn this device into a telemetry source: a layout-level `publishers` array
streams [[sensors]] readings over the layout's connection, so a hub device — or
your server — can watch this phone's compass, speed, or sound level live.

## Definition

```json
"publishers": [
  { "sensor": "heading", "interval": 0.25 },
  { "sensor": "device" }
]
```

## The wire frame

Each reading is broadcast with the pipeline's keys flattened alongside the
routing fields:

```json
{ "msg_type": "sensor", "sensor": "heading", "device": "carters-iphone",
  "ts_ms": 1782000000000, "value": 274.5, "cardinal": "W", "accuracy": 12.0 }
```

A hub layout subscribes with ordinary [[sync]] — no server code required:

```json
"sync": [{
  "method": "meshsocket", "type": "listen", "event": "broadcast",
  "filter": { "msg_type": "sensor", "sensor": "heading", "device": "carters-iphone" },
  "valuePath": "value"
}]
```

`device` is the publishing layout's identity name (suffixed per device in a
`room`), so several phones can stream side by side and the hub tells them apart
by filter.

## Batched publishing

```json
"batchPublishers": true,
"publishers": [
  { "sensor": "motion",   "interval": 0.1 },
  { "sensor": "location", "interval": 3 }
]
```

One frame per reading keeps the radio awake at the sum of every cadence. With the
top-level `batchPublishers: true`, the phone instead sends **one `sensor_batch`
frame per tick of the fastest declared interval**, carrying every sensor whose own
interval is due on that tick: 29 ticks of motion alone, then one of motion +
location when location's 3 s comes round. Each kind's cadence is exactly what it
declared; only the number of frames changes.

```json
{ "msg_type": "sensor_batch", "device": "carters-iphone", "ts_ms": 1782000003000,
  "count": 2,
  "readings": [
    { "msg_type": "sensor", "sensor": "motion",   "device": "carters-iphone", "ts_ms": 1782000002990, "value": 12.4, "pitch": 12.4, "roll": -3.1, "yaw": 88.0, "accel": 0.02, "rotation": 1.1 },
    { "msg_type": "sensor", "sensor": "location", "device": "carters-iphone", "ts_ms": 1782000002400, "value": 41.2, "latitude": 44.98, "longitude": -93.27, "speed": 11.4 }
  ]
}
```

Every element of `readings` is a complete single-reading frame, so a receiver
unbatches by handing each one to whatever already handles `msg_type: "sensor"`.
CAR-TER itself does this (a hub layout's `filter: {"msg_type": "sensor", …}`
bindings work unchanged) and so does `carterkit`'s client; a hand-written server
must loop over `readings`. A tick with nothing new sends no frame at all.

Batched mode also idles on its own: a reading that hasn't moved past its kind's
noise floor (1° heading, 0.5° motion, 2 levels audio, 0.02 kPa, 1 % battery,
0.5 km/h) rides an ×8 heartbeat instead of its full cadence, so a phone at rest
in a mount sends a fraction of the traffic and cools down.

## Consent — always

Layouts are untrusted JSON, so a `publishers` block never starts silently. The
first time a layout wants to broadcast, CAR-TER shows a consent sheet naming
each sensor and the exact destination; every decision is remembered per layout
and revocable in Settings → Sensor Broadcasting. While streaming, a radiating
pill in the header opens the live activity view — see what's flowing, pause a
stream, stop everything. Layouts pushed by a live-edit session (an AI editor)
get session-only consent: they ask again next session.

## Keeping the screen on

Streaming stops when iOS locks the screen. The user can hold the screen awake
while publishers run (Permissions → Data Pipe), and a layout that *is* the
display can ask for it itself with the top-level `keepAwake: true` field — see
[[layout-config]].

## Notes

- Streams run while the layout is open and connected; backgrounding pauses them.
- Frames ride the layout's E2EE cipher when a key is set, like all traffic.
- The identity should keep `can_broadcast: true` (role defaults usually do).
- `interval` is clamped to a per-sensor floor so a typo can't flood the relay.
- See [[privacy]] — readings go to your server, never to the developer.
