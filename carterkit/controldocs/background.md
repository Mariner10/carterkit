---
type: background
depth: complete
since: next
label: Background
icon: moon.stars.fill
category: system
fields:
  - name: type
    since: next
    type: string
    description: "Catalog type to register for, e.g. location.visits, sensors.motion, audio.playback (see the catalog below)"
    summary: What to run in the background
    does: Names the background event type the layout asks for; the user allows each one.
  - name: send
    since: next
    type: object
    description: "Where readings go: { hub: the hub's target_name, event: the msg_type }"
    summary: Where readings are sent
    does: Delivers each reading to a hub with the given message type.
  - name: store
    since: next
    type: string
    description: Local-store collection to write each reading into (alone or with send)
    summary: Where readings are kept
    does: Writes each reading into a collection on this phone.
  - name: interval
    since: next
    type: number
    min: 1
    max: 3600
    step: 1
    description: Seconds between readings, for sensor types (low power and heat can slow it)
    summary: Seconds between readings
    does: Sets how often a sensor reading is taken while it runs.
  - name: keepAlive
    since: next
    type: bool
    description: "Connect+: keep audio.playback or a sensor registration running after the layout is closed"
    summary: Keep going after close
    does: Keeps that channel running after the layout is closed (needs Connect+).
  - name: places
    since: next
    type: object[]
    description: "For location.places: [{ name, latitude, longitude, radius }]; 20 regions app-wide"
    summary: Places to watch
    does: Lists the places to watch for arrivals and departures, within the 20-place limit across the app.
eventTypes:
  - { type: location.visits, since: next }
  - { type: location.travel, since: next }
  - { type: location.places, since: next }
  - { type: location.continuous, since: next }
  - { type: audio.playback, since: next }
  - { type: sensors.motion, since: next }
  - { type: sensors.barometer, since: next }
  - { type: sensors.heading, since: next }
  - { type: sensors.device, since: next }
  - { type: hub.push, since: next }
  - { type: refresh, since: next }
---

A layout asks for background work in a top-level `background` block. It replaces
`sensorSetup`, which still works and is read as the same thing. Nothing runs until the
user allows it: the request appears in the top bar when the layout opens, and each
decision is remembered per layout and destination.

## Definition

```json
"background": [
  { "type": "location.visits", "send": { "hub": "tracker", "event": "visit" } },
  { "type": "audio.playback", "keepAlive": true }
]
```

`send` delivers to a hub (`hub` is the `target_name`, `event` the `msg_type`); `store`
writes to a local-store collection; either or both. Each source runs once, in the
lightest mode that satisfies every registration, and fans readings out to each layout.

## The catalog

| Type | iOS mechanism | Kind | Survives close | Location pill | Needs |
|---|---|---|---|---|---|
| `location.visits` | visit monitoring | wake | yes (relaunch) | no | Always |
| `location.travel` | significant-change monitoring | wake | yes (relaunch) | no | Always |
| `location.places` | region monitoring, 20 regions app-wide | wake | yes (relaunch) | no | Always |
| `location.continuous` | live updates + background activity session | keeper | no | **yes** | While Using or Always |
| `audio.playback` | audio background mode | keeper | no | no | none |
| `sensors.motion`, `.barometer`, `.heading`, `.device` | CoreMotion, altimeter, heading, device | passenger | no | no (heading needs location) | per sensor |
| `hub.push` | silent push | wake | not after force-quit | no | Notifications |
| `refresh` | background app refresh | wake | yes, when iOS chooses | no | Background App Refresh |

- **wake:** iOS wakes or relaunches the app for seconds; it collects, delivers, sleeps.
- **keeper:** keeps the app running while active.
- **passenger:** runs only while a keeper is active, or in the foreground.
- The microphone sensor is excluded while `audio.playback` runs.

## Examples

### Tracker with motion

A tracker that logs visits and trips, and keeps the phone's motion while music plays:

```json
"background": [
  { "type": "location.visits", "send": { "hub": "tracker", "event": "visit" } },
  { "type": "location.travel", "send": { "hub": "tracker", "event": "location" }, "store": "trips" },
  { "type": "sensors.motion", "interval": 30, "send": { "hub": "tracker", "event": "motion" } }
]
```

### Music after close

Music that keeps playing after the layout is closed (Connect+):

```json
"background": [{ "type": "audio.playback", "keepAlive": true }]
```

### Visits stored on the phone

Keep visits in a local-store collection only, with nothing sent to a hub:

```json
"background": [{ "type": "location.visits", "store": "visits" }]
```

## Notes

- The microphone sensor does not run while `audio.playback` runs.
- Low Power Mode slows passengers; a serious thermal state stops them.
- Readings wait on this iPhone until the hub can be reached.
- See [[sensors]] and [[publishers]] for on-screen and streaming sensor use.
