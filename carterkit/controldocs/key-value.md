---
type: keyValue
label: Key–Value
icon: tablecells
category: display
defaultSpan: [3, 4]
addIntent: show
pickerCategory: Readouts
friendlyName: Details
oneLiner: Labeled readings from one object
aliases: [details, key value, properties, fields, info, readings]
starterPreset: {"label": "Details"}
fields:
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label
  - name: rows
    type: array
    description: "Row whitelist and order: [{ key, label, format, icon, unit }]"
    summary: Which readings to show, in what order, and how each is labeled
  - name: keyValueStyle
    edit: look
    depth: surface
    title: Layout
    type: enum
    values: [rows, chips, grid]
    default: rows
    description: "rows = label left / value right; chips = wrapping pills; grid = cards"
  - name: columns
    edit: scrub
    depth: surface
    under: keyValueStyle
    title: Columns
    min: 1
    max: 4
    step: 1
    type: number
    default: 1
    description: How many columns of rows or cards to lay out (grid defaults to 2)
  - name: sortKeys
    edit: part
    depth: hold
    title: Sorted
    type: bool
    default: false
    description: Sort keys alphabetically instead of keeping the feed's own order
  - name: hideEmpty
    edit: part
    depth: hold
    title: Hide empty
    type: bool
    default: true
    description: Skip rows whose value is null or an empty string
  - name: maxRows
    min: 0
    max: 200
    step: 1
    type: number
    default: 0
    description: Cap on rendered rows (0 = all of them)
  - name: format
    type: string
    description: "Default number format for rows without their own (percent, duration, bytes, suffix:°C, …)"
  - name: colorMap
    type: object
    description: Value → hex tint, so a value can carry its own status color
  - name: tint
    edit: color
    depth: surface
    title: Color
    type: color
    description: Value color when no colorMap entry matches
  - name: keyTint
    edit: color
    depth: hold
    under: tint
    title: Key color
    type: color
    description: Color of the key names (default: the theme's secondary color)
  - name: valueTint
    edit: color
    depth: hold
    under: tint
    title: Value color
    type: color
    description: Color of the values when no colorMap entry matches (default: tint)
  - name: hideLabel
    edit: part
    depth: hold
    title: Title shown
    type: bool
    default: false
    description: Hide the header label
  - name: hideBackground
    edit: part
    depth: hold
    title: Background
    type: bool
    default: false
    description: Draw without the card surface
themeFields:
  - name: cornerRadius
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
  - name: controlPadding
    min: 0
    max: 24
    step: 1
    type: number
    default: 8
    description: Internal padding
  - name: surfacePrimary
    type: color
    default: #FFFFFF0F
    description: Background fill
  - name: foregroundColor
    type: color
    default: #FFFFFF
    description: Value text color
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Key/label text color
  - name: borderColor
    type: color
    default: #FFFFFF1A
    description: Border color
  - name: borderWidth
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
---

# Key–Value

Renders a JSON **object** as labeled rows. It is the sibling of [[list]], which needs an *array* — and objects are what REST endpoints, MQTT retained topics and status broadcasts actually return, so this is the control most telemetry lands in.

## Type
`"keyValue"`

## Data shape

The control's value is a JSON **document**, exactly like [[chart]] or [[heatmap]]: point `sync` at the feed and let `valuePath` pick the sub-object.

```json
{ "cpu": 41, "temp": 52.5, "uptime": 86400, "ip": "10.0.0.7", "online": true }
```

Two inbound shapes are accepted:

| Shape | When to use it |
|---|---|
| An **object** | The normal case. Key order is the order the feed wrote it |
| An **array of pairs** — `[{ "key": "cpu", "value": 41 }, …]` | A feed that wants to pin the order itself, or one with duplicate-ish names |

Each push **replaces** the table (unlike [[sparkline]] or [[log-console]], which append). A server that wants a partial update should send the whole object back.

Values print by type: strings verbatim, numbers through the [[label]] `formatValue` vocabulary, booleans as `✓ Yes` / `✗ No`, and nested objects or arrays as compact JSON in a mono face — so a table never silently hides part of its own document. `hideEmpty` (on by default) drops nulls and empty strings, which is what keeps a sparse feed from drawing a column of dashes.

## Rows

Without `rows` the table shows every key. With it, `rows` is both the **whitelist** and the **order**:

| Key | Type | Description |
|-----|------|-------------|
| `key` | string | The key to read. Dot paths work (`properties.mag`, `geometry.coordinates.0`), same as a [[list]] column |
| `label` | string | Display name; defaults to a prettified key (`cpu_temp` → "Cpu Temp") |
| `format` | string | Number format for this row; overrides the control-level `format` |
| `icon` | string | Leading SF Symbol |
| `unit` | string | Appended after the value, space-separated. For a tight unit use `format: "suffix:°C"` |

A key the document doesn't contain renders as `—`, or disappears entirely when `hideEmpty` is on.

## Styles

`keyTint` and `valueTint` colour the key names and the values (a `colorMap` hit still wins for a value).

- **`rows`** (default) — label left, value right. `columns: 2` prints two pairs per line in a wide cell.
- **`chips`** — wrapping pills. Best for a dozen short values you want to scan, not read in order.
- **`grid`** — small cards, two across by default. Best for a handful of headline numbers.

## Sizing

Rows scroll **inside** the control, so the cell never overflows — but a table crushed to one row is unreadable. In a 2-D grid give it a real `rowSpan`: `[3, 4]` fits about six pairs, `[5, 4]` about a dozen. See [[grid-dimensions]].

## Tapping a row

Give the control an `action` and every row becomes a button, substituting `{{key}}` (the row's key, dot path and all) and `{{value}}` (its raw value). That turns a health table into a drill-down. With no `action` the table is read-only and VoiceOver reads it as text rather than as controls.

## Examples

### Device health over MeshSocket
```json
{
  "type": "keyValue",
  "id": "health",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Pi Health",
  "rows": [
    { "key": "cpu", "label": "CPU", "format": "percent", "icon": "cpu" },
    { "key": "temp", "label": "Temp", "format": "suffix:°C", "icon": "thermometer.medium" },
    { "key": "uptime", "label": "Uptime", "format": "duration", "icon": "clock" },
    { "key": "ip", "label": "IP", "icon": "network" },
    { "key": "online", "label": "Link", "icon": "antenna.radiowaves.left.and.right" }
  ],
  "colorMap": { "true": "#34C759", "false": "#FF3B30" },
  "sync": [
    {
      "method": "meshsocket",
      "type": "listen",
      "event": "broadcast",
      "filter": { "msg_type": "health" },
      "valuePath": "stats"
    }
  ]
}
```

### Open-Meteo "current" — a zero-server dashboard
```json
{
  "type": "keyValue",
  "id": "weather-now",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Right Now",
  "keyValueStyle": "grid",
  "columns": 2,
  "rows": [
    { "key": "temperature_2m", "label": "Air", "unit": "°C" },
    { "key": "relative_humidity_2m", "label": "Humidity", "unit": "%" },
    { "key": "wind_speed_10m", "label": "Wind", "unit": "km/h" },
    { "key": "is_day", "label": "Daylight" }
  ],
  "sync": [
    {
      "method": "http",
      "source": "open-meteo",
      "valuePath": "current"
    }
  ]
}
```
See [[sources]] for the polled-HTTP source block this reads from.

### Drill-down chips
```json
{
  "type": "keyValue",
  "id": "env",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Environment",
  "keyValueStyle": "chips",
  "sortKeys": true,
  "maxRows": 12,
  "action": {
    "method": "meshsocket",
    "mode": "broadcast",
    "event": "route_msg",
    "payload": {
      "target_id": "agent",
      "type": "inspect",
      "payload": { "field": "{{key}}", "was": "{{value}}" }
    }
  }
}
```

## Behavior
- Each push replaces the whole table; rows animate in and out
- `colorMap` matches the stringified value (`true`, `41`, `"idle"`), with a `default` entry as the catch-all — the same matcher [[label]] and [[image]] use
- Long values scale down before they truncate; structured values print as compact JSON
- Rows scroll internally, so the control always fits its cell

## Related
[[list]] · [[label]] · [[sync]] · [[sources]] · [[actions]] · [[grid-dimensions]]
