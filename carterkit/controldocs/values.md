---
type: values
label: Value Types
icon: number.square
category: system
valueTypes:
  - { type: bool, wire: "true / false", example: "true" }
  - { type: integer, wire: "number with no fraction", example: "42" }
  - { type: number, wire: "number", example: "21.5" }
  - { type: string, wire: "string", example: "\"WNW\"" }
  - { type: date, wire: "ISO-8601 string or epoch milliseconds", example: "\"2026-09-27T09:30:00Z\"" }
  - { type: duration, wire: "number of seconds", example: "90" }
  - { type: measurement, wire: "number, in the capability's unit", example: "21.5" }
  - { type: location, wire: "object with latitude and longitude", example: "{\"latitude\": 45.5, \"longitude\": -73.6}" }
  - { type: json, wire: "any JSON", example: "{\"any\": [1, 2]}" }
  - { type: list, wire: "array of row objects (local rows only)", example: "[{\"name\": \"Basil\"}]" }
units:
  - { unit: degrees, dimension: angle, symbol: "°" }
  - { unit: kilopascals, dimension: pressure, symbol: kPa }
  - { unit: hectopascals, dimension: pressure, symbol: hPa }
  - { unit: meters, dimension: length, symbol: m }
  - { unit: kilometers, dimension: length, symbol: km }
  - { unit: miles, dimension: length, symbol: mi }
  - { unit: feet, dimension: length, symbol: ft }
  - { unit: metersPerSecond, dimension: speed, symbol: m/s }
  - { unit: kilometersPerHour, dimension: speed, symbol: km/h }
  - { unit: milesPerHour, dimension: speed, symbol: mph }
  - { unit: gravity, dimension: acceleration, symbol: g }
  - { unit: celsius, dimension: temperature, symbol: °C }
  - { unit: fahrenheit, dimension: temperature, symbol: °F }
  - { unit: kelvin, dimension: temperature, symbol: K }
  - { unit: seconds, dimension: duration, symbol: s }
  - { unit: minutes, dimension: duration, symbol: min }
  - { unit: hours, dimension: duration, symbol: h }
  - { unit: percent, dimension: ratio, symbol: "%" }
---

The kinds of value CAR-TER can show or send, and the units a measurement can
carry. These are **catalog vocabulary, not wire vocabulary**: a binding's JSON
is unchanged — a gauge bound to `heading` still receives a plain number. The
type and unit tell the designer, carterkit and the MCP what that number
*is*, so they can label it ("Heading, degrees") and pick sensible controls.

## Value types

| Type | On the wire | Example |
|---|---|---|
| `bool` | `true` / `false` | `true` |
| `integer` | a number with no fraction | `42` |
| `number` | a number | `21.5` |
| `string` | a string | `"WNW"` |
| `date` | an ISO-8601 string or epoch milliseconds | `"2026-09-27T09:30:00Z"` |
| `duration` | a number of seconds | `90` |
| `measurement` | a number, in the capability's `unit` | `21.5` |
| `location` | an object with `latitude` and `longitude` | `{"latitude": 45.5, "longitude": -73.6}` |
| `json` | any JSON | `{"any": [1, 2]}` |
| `list` | an array of row objects — local rows only | `[{"name": "Basil"}]` |

The list is closed: a new kind of value is a change to this page first.

## Units

A `measurement` names one real unit. Unit names are Foundation's
(`UnitTemperature.celsius` → `celsius`), so the app can convert for display:
a reading in `celsius` shows as °F on a US-locale device. A unit string not in
this table is shown literally, exactly as written (`"°/s"`, `"dBFS"`).

| Unit | Dimension | Symbol |
|---|---|---|
| `degrees` | angle | ° |
| `kilopascals`, `hectopascals` | pressure | kPa, hPa |
| `meters`, `kilometers`, `miles`, `feet` | length | m, km, mi, ft |
| `metersPerSecond`, `kilometersPerHour`, `milesPerHour` | speed | m/s, km/h, mph |
| `gravity` | acceleration | g |
| `celsius`, `fahrenheit`, `kelvin` | temperature | °C, °F, K |
| `seconds`, `minutes`, `hours` | duration | s, min, h |
| `percent` | ratio | % (0–100, never converted) |

### The control `unit` field

`gauge`, `label` and `progressRing` (and `statTile`) take one optional `unit`
naming the unit their value arrives in — a name above, its symbol (`°C`, `km/h`,
`mph`, `kPa`, `%`, …) or the name in any case. The value on the wire and in
storage never changes; only the readout converts, to the device locale:

| Dimension | US | UK | Metric |
|---|---|---|---|
| temperature (`celsius`, `fahrenheit`) | °F | °C | °C |
| speed | mph | mph | km/h |
| length, short (`meters`, `feet`) | ft | m | m |
| length, long (`kilometers`, `miles`) | mi | mi | km |
| pressure | inHg | as written | as written |

`kelvin`, angles, durations, `gravity` and `percent` never convert. `min`, `max`
and gauge `segments` stay in the source unit, so a needle, fill or colour zone sits
in the same place on every device. A binding whose sensor key names its unit
(`location.speedKmh`, `location.speedMph`, `location.speed`) keeps that unit.
Any other string is a literal suffix (`"unit": "dBFS"` → `12.5 dBFS`).

## Where types come from

- Each [[sensors]] key declares its type and unit in the sensors page's front
  matter; the app's capability catalog is checked against that table.
- Server-fed values (`meshsocket`, `mqtt`, `http`) are `json` until the layout
  says otherwise — the catalog can't know what a server sends.

## Setup states

Every capability is in one of these states on a given device:

| State | Meaning |
|---|---|
| `ready` | Works now |
| `allowAccess` | Needs an iOS permission (location, microphone, Motion & Fitness) |
| `configure` | Needs a setting filled in (an MQTT broker, an HTTP URL) |
| `needsYourServer` | Needs a server on the mesh to send or answer |
| `unsupported` | This device or app version can't do it |
| `signIn` | Reserved — no capability uses it yet |
