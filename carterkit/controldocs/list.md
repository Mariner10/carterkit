---
type: list
label: List
icon: list.bullet
category: controls
defaultSpan: [2, 4]
fields:
  - name: label
    type: string
    description: Header label
  - name: listColumns
    type: array
    description: "Column definitions: [{key, label, format}]"
  - name: tint
    type: color
    default: "#FFFFFF"
    description: Header text color
  - name: hideLabel
    type: bool
    default: false
    description: Hide header label
  - name: hideBackground
    type: bool
    default: false
    description: Remove glass card background
themeFields:
  - name: cornerRadius
    type: number
    default: 12
    description: Control corner radius
  - name: controlPadding
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
    description: Primary text color
  - name: borderColor
    type: color
    default: #FFFFFF1A
    description: Border color
  - name: borderWidth
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
| `tint` | color | `"#FFFFFF"` | Header text color |
| `hideLabel` | bool | `false` | Hide header label |
| `hideBackground` | bool | `false` | Remove glass card background |

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
  "sync": { "method": "meshsocket", "event": "device_list" }
}
```

## Related
- [[shared-properties]] — Base fields
- [[sync]] — Real-time data sync
