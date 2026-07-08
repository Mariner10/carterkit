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

## Consent — always

Layouts are untrusted JSON, so a `publishers` block never starts silently. The
first time a layout wants to broadcast, CAR-TER shows a consent sheet naming
each sensor and the exact destination; every decision is remembered per layout
and revocable in Settings → Sensor Broadcasting. While streaming, a radiating
pill in the header opens the live activity view — see what's flowing, pause a
stream, stop everything. Layouts pushed by a live-edit session (an AI editor)
get session-only consent: they ask again next session.

## Notes

- Streams run while the layout is open and connected; backgrounding pauses them.
- Frames ride the layout's E2EE cipher when a key is set, like all traffic.
- The identity should keep `can_broadcast: true` (role defaults usually do).
- `interval` is clamped to a per-sensor floor so a typo can't flood the relay.
- See [[privacy]] — readings go to your server, never to the developer.
