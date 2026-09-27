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
keys:
  - { sensor: heading, name: Heading, valueType: measurement, unit: degrees }
  - { sensor: heading.magnetic, name: Magnetic heading, valueType: measurement, unit: degrees }
  - { sensor: heading.trueHeading, name: True heading, valueType: measurement, unit: degrees }
  - { sensor: heading.accuracy, name: Heading accuracy, valueType: measurement, unit: degrees }
  - { sensor: heading.cardinal, name: Compass direction, valueType: string }
  - { sensor: motion, name: Tilt, valueType: measurement, unit: degrees }
  - { sensor: motion.pitch, name: Pitch, valueType: measurement, unit: degrees }
  - { sensor: motion.roll, name: Roll, valueType: measurement, unit: degrees }
  - { sensor: motion.yaw, name: Yaw, valueType: measurement, unit: degrees }
  - { sensor: motion.accel, name: Acceleration, valueType: measurement, unit: gravity }
  - { sensor: motion.rotation, name: Rotation rate, valueType: measurement, unit: "°/s" }
  - { sensor: barometer, name: Air pressure, valueType: measurement, unit: kilopascals }
  - { sensor: barometer.pressure, name: Air pressure (explicit), valueType: measurement, unit: kilopascals }
  - { sensor: barometer.altitude, name: Relative altitude, valueType: measurement, unit: meters }
  - { sensor: device, name: Battery, valueType: measurement, unit: percent }
  - { sensor: device.battery, name: Battery level, valueType: measurement, unit: percent }
  - { sensor: device.state, name: Charging state, valueType: string }
  - { sensor: device.thermal, name: Thermal state, valueType: string }
  - { sensor: device.lowPower, name: Low Power Mode, valueType: bool }
  - { sensor: device.brightness, name: Screen brightness, valueType: measurement, unit: percent }
  - { sensor: audio, name: Sound level, valueType: number }
  - { sensor: audio.level, name: Sound level (explicit), valueType: number }
  - { sensor: audio.dbfs, name: Loudness, valueType: measurement, unit: dBFS }
  - { sensor: audio.peak, name: Peak loudness, valueType: measurement, unit: dBFS }
  - { sensor: location, name: Speed, valueType: measurement, unit: kilometersPerHour }
  - { sensor: location.speedKmh, name: Speed (km/h), valueType: measurement, unit: kilometersPerHour }
  - { sensor: location.speedMph, name: Speed (mph), valueType: measurement, unit: milesPerHour }
  - { sensor: location.speed, name: Speed (m/s), valueType: measurement, unit: metersPerSecond }
  - { sensor: location.latitude, name: Latitude, valueType: measurement, unit: degrees }
  - { sensor: location.longitude, name: Longitude, valueType: measurement, unit: degrees }
  - { sensor: location.course, name: Course, valueType: measurement, unit: degrees }
  - { sensor: location.altitude, name: Altitude, valueType: measurement, unit: meters }
  - { sensor: location.accuracy, name: Location accuracy, valueType: measurement, unit: meters }
  - { sensor: location.timestamp_ms, name: Location time, valueType: date }
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
| `location` | Speed, km/h | `latitude`, `longitude`, `speed` (m/s), `speedKmh`, `speedMph`, `course`, `altitude`, `accuracy`, `timestamp_ms` |

Every key's friendly name, value type and unit is the `keys` table in this
page's front matter (see [[values]]); the app's capability catalog is checked
against it, so a key added in code without a row here fails the tests.

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
