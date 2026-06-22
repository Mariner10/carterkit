---
type: pulse
label: Pulse
icon: dot.radiowaves.left.and.right
category: system
fields:
  - name: event
    type: string
    description: Server event that fires the pulse
  - name: color
    type: color
    default: "#34C759"
    description: Ring colour
  - name: direction
    type: enum
    values: ["outward", "inward"]
    default: outward
    description: Ring expands outward or contracts inward
  - name: spread
    type: number
    default: "0.1"
    description: Ring travel as a fraction of the group's size (0.1 = 10%)
  - name: duration
    type: number
    default: "0.9"
    description: Pulse length in seconds
  - name: curve
    type: enum
    values: ["snappy", "smooth", "bouncy", "gentle", "instant"]
    default: gentle
    description: Easing preset — springy presets overshoot
  - name: filter
    type: object
    description: Optional payload match, e.g. { "device": "thunk-app" }
---

A **pulse** is a decorative ring that flashes around a container the moment
live data lands on it — a zero-wiring way to *see* events arriving. The ring
expands **outward** (data collected / leaving) or contracts **inward** (data
arriving / stored), with a brief glow along the resting border, then fades. It
never intercepts touches and is invisible at rest.

Use the preview above to tune the **colour**, **direction**, **ring width**,
**curve**, **spread**, and **duration**, then tap **Fire Pulse** — or flip
**Auto Pulse** to watch it repeat as though readings were streaming in. The
`curve` reuses the app's [[animations|animation presets]]: `gentle` is a calm
ease, while `bouncy`/`smooth`/`snappy` give the ring a springy overshoot.

## On a group

Attach a `pulse` to any [[group-def|group]] and it flashes whenever its `event`
arrives over the socket. An optional `filter` narrows which payloads count,
matching keys the same way a [[sync]] filter does.

```json
{
  "type": "group",
  "id": "gps-collector",
  "label": "Live GPS",
  "grid": { "columns": 2, "rows": 2 },
  "children": [],
  "pulse": {
    "event": "iCloudListen",
    "direction": "outward",
    "color": "34C759",
    "spread": 0.12,
    "duration": 0.8,
    "curve": "bouncy"
  }
}
```

## In the app

The **Location Metrics** screen uses the same effect directly: the live-payload
card pulses green outward each time a reading is collected, and the buffer card
pulses inward each time the queue is flushed to the server.

## Related
- [[group-def]] — attach a pulse to a container
- [[sync]] — the event/filter mechanism pulses share
- [[animations]] — other motion in the system
