---
type: treemap
label: Treemap
icon: rectangle.3.group.fill
category: controls
defaultSpan: [3, 4]
fields:
  - name: label
    type: string
    description: Header label above the map
  - name: treemapConfig
    type: object
    description: Full configuration object (see TreemapConfig section)
  - name: tint
    type: color
    default: "#667eea"
    description: First-item color and palette seed
  - name: formatValue
    type: string
    description: Formatter for item values
  - name: cellCornerRadius
    type: number
    default: 5
    description: Cell corner rounding
    group: treemapConfig
  - name: cellGap
    type: number
    default: 2
    description: Gap between cells
    group: treemapConfig
  - name: colors
    type: string[]
    description: Item color cycle (per-item color wins)
    group: treemapConfig
  - name: drillDown
    type: bool
    default: true
    description: Tap a parent to zoom into its children
    group: treemapConfig
  - name: itemAction
    type: object
    description: itemAction
    group: treemapConfig
  - name: scrub
    type: bool
    default: false
    description: Drag highlights the cell under the finger with a live readout (no drilling/actions until a tap)
    group: treemapConfig
  - name: showLabels
    type: bool
    default: true
    description: Item labels inside cells that have room
    group: treemapConfig
  - name: showValues
    type: bool
    default: false
    description: Value under the label (taller cells only)
    group: treemapConfig
themeFields:
  - name: cornerRadius
    type: number
    default: 12
    description: Control corner radius
  - name: surfacePrimary
    type: color
    default: #FFFFFF0F
    description: Background fill
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Value text color
---

# Treemap

Hierarchy as space: squarified rectangles sized by value — disk usage, budget
splits, portfolio weights. The hidden edge is **drill-down**: tap an item with
children and the map zooms into it (a back chip replaces the label, Files-app
style); tap a leaf and `itemAction` fires with the item and its drill path, so
a storage map doubles as a category picker.

## Type
`"treemap"`

## Recommended Size
Wide: `[3, 4]`. In a flow grid it auto-sizes to a ~3:2 landscape cell.

## Relevant Fields
Inherits all [[control-def|shared fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Header label (becomes a back chip while drilled in) |
| `treemapConfig` | [[#TreemapConfig]] | — | Full configuration object (all optional) |
| `tint` | string | `"#667eea"` | First-item color / palette seed |
| `formatValue` | string | — | Formatter for value readouts |
| `action` | [[actions\|ActionDefinition]] | — | Fallback for `itemAction` |

## TreemapConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `showLabels` | bool | `true` | Item labels inside cells that have room |
| `showValues` | bool | `false` | Value under the label (taller cells only) |
| `drillDown` | bool | `true` | Tap a parent to zoom into its children |
| `cellGap` | number | `2` | Gap between cells |
| `cellCornerRadius` | number | `5` | Cell corner rounding |
| `colors` | string[] | built-in palette | Item color cycle (per-item `color` wins) |
| `itemAction` | [[actions\|ActionDefinition]] | — | Fired on leaf tap; `{{value}}` = `{"label", "value", "path"}` |
| `scrub` | bool | `false` | Drag highlights the cell under the finger with a live readout (no drilling/actions until a tap) |

## Sync Payload Structure

A tree of weighted items — natural JSON or an encoded string. A bare array is
shorthand for `{"items": …}`. A parent's value defaults to the sum of its
children:

```json
{
  "items": [
    { "label": "Media", "color": "#667eea", "children": [
      { "label": "Video", "value": 41.5 },
      { "label": "Photos", "value": 12.2 }
    ]},
    { "label": "Apps", "value": 23.0 },
    { "label": "System", "value": 14.8 }
  ]
}
```

### Item Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | yes | Cell label |
| `value` | number | no* | Weight (*optional when `children` supply it) |
| `color` | string | no | Cell color (hex) |
| `children` | item[] | no | Nested items (drill-down target) |

## Examples

### Storage map with drill-down
```json
{
  "type": "treemap",
  "id": "storage",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Storage",
  "formatValue": "suffix: GB",
  "treemapConfig": { "showValues": true },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "disk_usage" }, "valuePath": "tree" }]
}
```

### Flat category picker (no drill)
```json
{
  "type": "treemap",
  "id": "budget",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Budget",
  "treemapConfig": {
    "drillDown": false,
    "itemAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast", "payload": { "msg_type": "pick_category", "item": "{{value}}" } }
  },
  "defaultValue": "[{\"label\":\"Rent\",\"value\":1800},{\"label\":\"Food\",\"value\":600},{\"label\":\"Fun\",\"value\":250},{\"label\":\"Save\",\"value\":900}]"
}
```

## Behavior
- Layout is the squarified algorithm (Bruls et al.) — rectangles stay as close to square as the weights allow
- Parents show a `›` hint; drilling cross-fades levels; the back chip walks one level up
- A fresh dataset push resets the drill path (the old path may not exist anymore)
- Labels only render where they fit — small slivers stay clean
- `scrub: true` lets a drag glide the highlight across cells — drilling and actions stay on deliberate taps

## Notes
- The control's value **is the dataset JSON** — selection/drill state never overwrites it
- Zero/negative values collapse to invisible slivers by design
- For part-of-whole with few slices, [[pie-chart]] reads faster; treemap earns its space at ~6+ items or with hierarchy

## Related
- [[pie-chart]] — radial part-of-whole
- [[sankey]] — flows between stages
- [[list]] — the same data as rows
- [[sync]] — how trees arrive
- [[actions]] — how `itemAction` fires
