---
type: list
label: List
icon: list.bullet
category: controls
defaultSpan: [3, 4]
addIntent: show
friendlyName: Table
oneLiner: Rows of information
starterPreset: {"label": "Table"}
fields:
  - name: label
    title: Title
    type: string
    description: Header label
  - name: listColumns
    title: Columns
    type: array
    description: "Column definitions: [{key, label, format}]"
    summary: Which columns to show and how to display them
  - name: tint
    title: Header color
    tab: style
    type: color
    default: "#FFFFFF"
    description: Header text color
  - name: hideLabel
    title: Hide the title
    type: bool
    default: false
    description: Hide header label
  - name: hideBackground
    title: No background card
    tab: style
    type: bool
    default: false
    description: Remove glass card background
  - name: defaultValue
    title: Starting rows
    type: object[]
    description: Seed rows shown before the first sync (the same row objects a sync delivers)
    summary: Starting rows shown until new data arrives
themeFields:
  - name: cornerRadius
    title: Corner roundness
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
  - name: controlPadding
    title: Inner spacing
    min: 0
    max: 24
    step: 1
    type: number
    default: 8
    description: Internal padding
  - name: surfacePrimary
    title: Background color
    type: color
    default: #FFFFFF0F
    description: Background fill
  - name: foregroundColor
    title: Text color
    type: color
    default: #FFFFFF
    description: Primary text color
  - name: borderColor
    title: Border color
    type: color
    default: #FFFFFF1A
    description: Border color
    summary: The outline around the control
  - name: borderWidth
    title: Border thickness
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
---

# List

A tabular data display that renders rows of structured data with configurable columns. Rows are populated via sync and can be formatted per column.

## Type
`"list"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | falls back to `id` | Header label |
| `listColumns` | array | — | Column definitions: `[{key, label, format}]` |
| `listColumns[].key` | string | required | Field to read from each row. A **dot path** reaches into nested rows — see [[#Column keys]] |
| `listColumns[].label` | string | required | Column header text |
| `listColumns[].format` | string | — | Number format applied to numeric cells (same formats as [[label]]) |
| `action` | [[actions\|ActionDefinition]] | — | Fired on a row tap with `{{value}}` = the row's `id` — see [[#Row taps]] |
| `tint` | color | `"#FFFFFF"` | Header text color |
| `hideLabel` | bool | `false` | Hide header label |
| `hideBackground` | bool | `false` | Remove glass card background |
| `defaultValue` | object[] | — | Seed rows shown before the first sync, the same row objects a sync delivers. See [[control-def#defaultValue per type]] |

## Column keys

A `key` is looked up flat on the row first, so `"key": "name"` reads `row.name` and a
row whose field name genuinely contains a dot still works.

If there's no flat match and the key contains dots, it's walked as a **dot path**:

- `"properties.title"` → `row.properties.title`
- `"geometry.coordinates.0"` → an integer segment indexes an array

That's what makes a nested public feed usable without a server in between: rows from
a GeoJSON `features[]` keep their data under `properties`, and a path key reads it
directly. A key that resolves to nothing renders as `—`.

## Row taps

With an `action`, each row whose data carries an `id` becomes tappable and fires the
action with `{{value}}` = that row's `id`. Rows from a [[local-store]] binding always
carry one, so a checklist ticks the tapped row with
`{"method": "local", "op": "update", "collection": "items", "id": "{{value}}", "set": {"done": true}}`
or removes it with `op: "delete"`. To edit a row elsewhere on the screen, select it:
`{"method": "local", "op": "select", "collection": "books", "id": "{{value}}"}` moves the
selection cursor, and every control bound with `"where": {"id": "{{selected}}"}` refills
with the tapped row. Rows without an `id` aren't tappable. Without an `action` the list
stays read-only.

## Examples

### Device status list
```json
{
  "type": "list",
  "id": "device-list",
  "position": [0, 0],
  "span": [2, 4],
  "label": "Connected Devices",
  "listColumns": [
    { "key": "name", "label": "Name" },
    { "key": "status", "label": "Status" },
    { "key": "latency", "label": "Ping", "format": "number" }
  ],
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "device_list" }, "valuePath": "devices" }]
}
```

The server broadcasts `{"msg_type": "device_list", "devices": [{"name": "…", "status": "…", "latency": 12}, …]}`; `valuePath` picks the row array out of the frame.

### Nested feed rows (USGS GeoJSON, no server)
```json
{
  "type": "list",
  "id": "quake-list",
  "position": [2, 0],
  "span": [3, 4],
  "label": "Recent quakes",
  "listColumns": [
    { "key": "properties.mag", "label": "M", "format": "number" },
    { "key": "properties.place", "label": "Place" },
    { "key": "geometry.coordinates.2", "label": "Depth", "format": "number" }
  ],
  "sync": [{ "method": "http", "url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson", "interval": 300, "valuePath": "features" }]
}
```

`valuePath` picks the row array out of the document; each column key then reaches
into that row.

## Related
- [[shared-properties]] — Base fields
- [[sync]] — Real-time data sync
