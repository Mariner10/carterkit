---
type: sensors
label: Sensors
icon: gyroscope
category: system
fields:
  - name: method
    type: string
    description: Set to "sensor" on a sync entry to bind local hardware
  - name: sensor
    type: string
    description: Pipeline and key, e.g. "heading", "motion.roll", "device.battery"
---

Bind controls to this device's own hardware — compass, motion, barometer, vitals,
sound level, location — with no server and no network. A `sync` entry with
`method: "sensor"` feeds the control live readings the moment the layout opens.

## Definition

```json
{
  "type": "gauge",
  "id": "compass",
  "min": 0, "max": 360,
  "sync": [{ "method": "sensor", "sensor": "heading" }]
}
```

The `sensor` string names a pipeline, optionally dotted with one of its reading
keys: `"heading"` is shorthand for `"heading.value"`, and `"motion.roll"` picks
the roll angle. Any control that can listen — [[gauge]], [[label]],
[[sparkline]], [[progress-ring]], [[status-light]], [[graph]] — can bind.

## Pipelines & keys

| Pipeline | `value` means | Other keys |
|---|---|---|
| `heading` | Magnetic heading, 0–360° | `magnetic`, `trueHeading`, `accuracy`, `cardinal` ("WNW") |
| `motion` | Pitch, degrees | `pitch`, `roll`, `yaw`, `accel` (g), `rotation` (°/s) |
| `barometer` | Pressure, kPa | `pressure`, `altitude` (relative m) |
| `device` | Battery, 0–100 | `battery`, `state`, `thermal`, `lowPower`, `brightness` |
| `audio` | Loudness, 0–100 rel. dB | `level`, `dbfs`, `peak` |
| `location` | Speed, km/h | `latitude`, `longitude`, `speed` (m/s), `speedMph`, `course`, `altitude`, `accuracy` |

## Permissions & battery

- `heading`, `motion`, and `device` need no permission.
- `barometer` asks for Motion & Fitness; `audio` for the microphone; `location`
  for While-Using access. iOS prompts once, on first use.
- Hardware runs only while a bound layout is on screen — switching layouts or
  backgrounding the app stops every pipeline immediately.
- `audio` measures loudness only. Samples never leave the audio tap.

## Notes

- On-screen bindings stay on the device. To stream readings to your server or
  another CAR-TER device, add a [[publishers]] block — that path is consent-gated.
- The simulator has no compass/barometer and reports battery as unknown; test
  sensors on hardware.
- Multiple controls can bind the same pipeline; it runs once.
