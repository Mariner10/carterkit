---
type: keyValue
depth: complete
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
io:
  - emits: row
    when: tap
    title: When you tap a row
    type: json
    says: the tapped row's raw value
    tokens: {"key": "the row's key, dot path included", "value": "the row's raw value"}
    example: 1
    also: Only when an action is set; with no action the table is read-only
    since: next
  - receives: items
    role: show
    type: json
    shape: {"any key": "any value"}
    from: [hub, mqtt, http, store]
    says: one object whose keys become labeled rows (or a list of key and value pairs to fix the order)
    reacts: every push replaces the whole table, so send the full object each time
    example: {"Item 1": 1, "Item 2": 2}
    since: next
  - sample: {"Item 1": 1, "Item 2": 2, "Item 3": 3}
    next: {"Item 1": 3, "Item 2": 2, "Item 3": 1}
fields:
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label
    summary: The heading above the table
    does: Shows this text as the header line on the card; empty leaves the header blank.
  - name: rows
    chip: Rows
    category: content
    title: Rows
    type: array
    description: "Row whitelist and order: [{ key, label, format, icon, unit }]"
    summary: Which readings to show, in what order, and how each is labeled
    does: Limits the table to the listed keys in that order with their own names, icons and units; leave it out to show every key.
  - name: keyValueStyle
    edit: look
    depth: surface
    title: Layout
    type: enum
    values: [rows, chips, grid]
    default: rows
    description: "rows = label left / value right; chips = wrapping pills; grid = cards"
    summary: Whether readings are lines, pills or cards
    does: Redraws the same readings as a list of lines, wrapping pills or small cards.
    valueHelp: {"rows": "one line per reading with the name on the left and the value on the right", "chips": "short wrapping pills that are good for scanning many values", "grid": "small cards that suit a handful of headline numbers"}
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
    summary: How many readings sit side by side
    does: Sets 1 to 4 columns of rows or cards across the control; the grid layout starts at 2.
  - name: sortKeys
    edit: part
    depth: hold
    title: Sorted
    type: bool
    default: false
    description: Sort keys alphabetically instead of keeping the feed's own order
    summary: Put the readings in A to Z order
    does: When on the readings are listed alphabetically by key; off keeps the order the feed sent.
  - name: hideEmpty
    edit: part
    depth: hold
    title: Hide empty
    type: bool
    default: true
    description: Skip rows whose value is null or an empty string
    summary: Drop readings that have nothing to show
    does: When on rows with no value disappear; off keeps them in place with a dash.
  - name: maxRows
    title: Row limit
    min: 0
    max: 200
    step: 1
    type: number
    default: 0
    description: Cap on rendered rows (0 = all of them)
    summary: The most readings the table will show
    does: Stops drawing after this many rows (0 to 200); 0 shows them all.
  - name: format
    title: Number format
    type: string
    description: "Default number format for rows without their own (percent, duration, bytes, suffix:°C, …)"
    summary: How plain numbers are written
    does: Prints every number in rows without their own format as a percent, duration, size or with a unit suffix such as °C.
  - name: colorMap
    title: Status colors
    type: object
    description: Value → hex tint, so a value can carry its own status color
    summary: Colors that follow what a value says
    does: Tints a value with the color listed for it (for example true green and false red); unlisted values use the normal value color.
  - name: tint
    edit: color
    depth: surface
    title: Color
    type: color
    description: Value color when no colorMap entry matches
    summary: The accent for the readings
    does: Colors the values that have no status color; the key names follow it unless they have their own.
  - name: keyTint
    edit: color
    depth: hold
    under: tint
    title: Key color
    type: color
    description: "Color of the key names (default: the theme's secondary color)"
    summary: The shade of the names on the left
    does: Colors the names of the readings; unset uses the softer theme text color.
  - name: valueTint
    edit: color
    depth: hold
    under: tint
    title: Value color
    type: color
    description: "Color of the values when no colorMap entry matches (default: tint)"
    summary: The shade of the readings themselves
    does: Colors the values that have no status color; unset follows the accent color.
  - name: hideLabel
    edit: part
    depth: hold
    title: Title shown
    type: bool
    default: false
    description: Hide the header label
    summary: Whether the heading is shown
    does: When on the header line is removed and the table moves up to fill the space.
  - name: hideBackground
    edit: part
    depth: hold
    title: Background
    type: bool
    default: false
    description: Draw without the card surface
    summary: The card behind the table
    does: When on the fill and border are removed so the readings sit straight on the page.
themeFields:
  - use: cornerRadius
    does: Rounds the card's corners from square (0) to 30 points.
  - use: controlPadding
    does: Adds 0 to 24 points between the card's edge and the table.
  - use: surfacePrimary
    summary: The color of the card behind the table
    does: Fills the card with this color; a low-opacity white by default.
  - name: foregroundColor
    title: Text color
    type: color
    default: #FFFFFF
    description: Value text color
    summary: The main text shade
    does: Colors the values and header when no tint is set.
  - name: secondaryColor
    title: Soft text color
    type: color
    default: #FFFFFF99
    description: Key/label text color
    summary: The quieter text shade
    does: Colors the key names when no key color is set.
  - use: borderColor
    summary: The outline around the card
    does: Colors the card's edge line.
  - use: borderWidth
    summary: How heavy the outline is
    does: Draws the card's edge line 0 to 5 points thick; 0 removes it.
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
Shows a Pi's live stats as labeled rows with icons, and tints the link value green or red by its state.
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
Shows current weather as a two-column grid of cards, each with a unit, read straight from a polled web source.
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
Shows every key as an A to Z wrapping pill (at most 12); tapping a pill sends that key and its value to an agent.
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

### Plain details with a default number format
Shows an object with no `rows` list, so every key appears, with all numbers written as percentages and a custom accent color for values.
```json
{
  "type": "keyValue",
  "id": "disk",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Disk",
  "format": "percent",
  "tint": "#5AC8FA",
  "sync": [
    { "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "disk" }, "valuePath": "usage" }
  ]
}
```

### Two-column rows with their own key and value colors
Shows rows in two columns with the names in grey and the values in orange, keeping empty readings visible as dashes.
```json
{
  "type": "keyValue",
  "id": "pairs",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Pairs",
  "keyValueStyle": "rows",
  "columns": 2,
  "hideEmpty": false,
  "keyTint": "#8E8E93",
  "valueTint": "#FF9F0A"
}
```

### Bare table without a title or card
Shows the readings straight on the page with no header and no card surface, for a quiet inline look.
```json
{
  "type": "keyValue",
  "id": "bare",
  "position": [0, 0],
  "span": [3, 4],
  "hideLabel": true,
  "hideBackground": true
}
```

### Feed that pins its own order
Shows how an array of key and value pairs keeps the feed's order; the value `[{ "key": "b", "value": 2 }, { "key": "a", "value": 1 }]` prints b before a.
```json
{
  "type": "keyValue",
  "id": "ordered",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Ordered",
  "sortKeys": false
}
```

### Theme override
Shows a squarer card with a thicker orange border using the control's theme fields.
```json
{
  "type": "keyValue",
  "id": "themed",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Themed",
  "theme": { "cornerRadius": 4, "borderWidth": 2, "borderColor": "#FF9F0A" }
}
```

## Behavior
- Each push replaces the whole table; rows animate in and out
- `colorMap` matches the stringified value (`true`, `41`, `"idle"`), with a `default` entry as the catch-all — the same matcher [[label]] and [[image]] use
- Long values scale down before they truncate; structured values print as compact JSON
- Rows scroll internally, so the control always fits its cell

## Related
[[list]] · [[label]] · [[sync]] · [[sources]] · [[actions]] · [[grid-dimensions]]
