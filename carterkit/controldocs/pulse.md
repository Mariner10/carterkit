---
type: pulse
label: Pulse
icon: dot.radiowaves.left.and.right
category: system
depth: complete
fields:
  - name: event
    tab: advanced
    type: string
    description: Server event that fires the pulse
    summary: Which server event triggers it
    does: Makes the ring flash each time this socket event arrives, such as broadcast.
  - name: color
    tab: style
    type: color
    default: "#34C759"
    description: Ring colour
    summary: Ring color
    does: Colors the flashing ring and the glow along the border (default green).
  - name: direction
    type: enum
    values: ["outward", "inward"]
    default: outward
    description: Ring expands outward or contracts inward
    summary: Which way the ring moves
    does: Makes the ring either grow away from the group or shrink toward it.
    valueHelp: {"outward": "the ring expands away from the group, as if data is leaving or collected", "inward": "the ring contracts toward the group, as if data is arriving or stored"}
  - name: spread
    min: 0
    max: 1
    step: 0.05
    type: number
    default: "0.1"
    description: Ring travel as a fraction of the group's size (0.1 = 10%)
    summary: How far the ring travels
    does: Sets how far the ring moves as a fraction of the group's size, 0 to 1 (default 0.1 is 10%).
  - name: duration
    min: 0.1
    max: 10
    step: 0.1
    type: number
    default: "0.9"
    description: Pulse length in seconds
    summary: How long one pulse lasts
    does: Sets the pulse length in seconds, from 0.1 to 10 (default 0.9).
  - name: curve
    type: enum
    values: ["snappy", "smooth", "bouncy", "gentle", "instant"]
    default: gentle
    description: Easing preset — springy presets overshoot
    summary: How the ring eases
    does: Picks the easing of the ring's motion; the springy presets make it overshoot slightly.
    valueHelp: {"snappy": "quick with a crisp stop", "smooth": "an even natural glide", "bouncy": "overshoots and settles", "gentle": "a calm slow ease (the default)", "instant": "no easing, it jumps straight through"}
  - name: filter
    tab: advanced
    type: object
    description: "Optional payload match, e.g. { 'device': 'thunk-app' }"
    summary: Only pulse for matching data
    does: Limits the pulse to events whose payload contains these key/value pairs, so other events are ignored.
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

## Examples

### Live GPS collector
A green ring flashes outward whenever an iCloud reading arrives.

```json
{
  "type": "group",
  "id": "gps-collector",
  "label": "Live GPS",
  "grid": { "columns": 2, "rows": 2 },
  "children": [],
  "pulse": {
    "event": "broadcast",
    "filter": { "msg_type": "iCloudListen" },
    "direction": "outward",
    "color": "34C759",
    "spread": 0.12,
    "duration": 0.8,
    "curve": "bouncy"
  }
}
```

### Queue flush
An inward blue ring marks data being stored, with a calm ease.

```json
{
  "type": "group",
  "id": "buffer",
  "label": "Buffer",
  "grid": { "columns": 2, "rows": 2 },
  "children": [],
  "pulse": { "event": "flush", "direction": "inward", "color": "5AC8FA", "duration": 1.2, "curve": "gentle" }
}
```

### Any broadcast, big and snappy
No filter, so every broadcast flashes a wide, quick ring.

```json
{
  "type": "group",
  "id": "inbox",
  "label": "Inbox",
  "grid": { "columns": 2, "rows": 2 },
  "children": [],
  "pulse": { "event": "broadcast", "color": "FF9500", "spread": 0.3, "duration": 0.5, "curve": "snappy" }
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
