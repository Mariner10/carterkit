---
type: sankey
label: Sankey
icon: arrow.triangle.branch
category: controls
defaultSpan: [3, 4]
fields:
  - name: label
    type: string
    description: Header label above the diagram
  - name: sankeyConfig
    type: object
    description: Full configuration object (see SankeyConfig section)
  - name: tint
    type: color
    default: "#667eea"
    description: First-node color and palette seed
  - name: formatValue
    type: string
    description: Formatter for node throughput values
  - name: colors
    type: string[]
    description: Node color cycle (per-node color wins)
    group: sankeyConfig
  - name: linkOpacity
    type: number
    default: 0.32
    description: Ribbon opacity (selection brightens involved ribbons)
    group: sankeyConfig
  - name: nodeAction
    type: object
    description: nodeAction
    group: sankeyConfig
  - name: nodeSpacing
    type: number
    default: 10
    description: Minimum vertical gap between nodes in a column
    group: sankeyConfig
  - name: nodeWidth
    type: number
    default: 10
    description: Node bar width in points
    group: sankeyConfig
  - name: scrub
    type: bool
    default: false
    description: Drag sweeps the spotlight from node to node with haptic ticks (the action still fires on tap)
    group: sankeyConfig
  - name: showLabels
    type: bool
    default: true
    description: Node names beside the bars
    group: sankeyConfig
  - name: showValues
    type: bool
    default: false
    description: Throughput value alongside each label
    group: sankeyConfig
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
    description: Node label color
---

# Sankey

Flow volumes between nodes: energy from panels to loads, requests through
services, budget through categories. Nodes stack into columns (sources left,
sinks right — computed from the link graph), ribbons run between them with
thickness ∝ value and a color gradient from source to target. Tapping a node
**spotlights its flows** — everything else fades — and fires `nodeAction`
with the node's in/out totals.

## Type
`"sankey"`

## Recommended Size
Wide: `[3, 4]` and up. In a flow grid it auto-sizes to a ~3:2 landscape cell.

## Relevant Fields
Inherits all [[control-def|shared fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Header label (selection readout appears beside it) |
| `sankeyConfig` | [[#SankeyConfig]] | — | Full configuration object (all optional) |
| `tint` | string | `"#667eea"` | First-node color / palette seed |
| `formatValue` | string | — | Formatter for throughput readouts |
| `action` | [[actions\|ActionDefinition]] | — | Fallback for `nodeAction` |

## SankeyConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `nodeWidth` | number | `10` | Node bar width in points |
| `nodeSpacing` | number | `10` | Minimum vertical gap between nodes in a column |
| `showLabels` | bool | `true` | Node names beside the bars |
| `showValues` | bool | `false` | Throughput value alongside each label |
| `linkOpacity` | number | `0.32` | Ribbon opacity (selection brightens involved ribbons) |
| `colors` | string[] | built-in palette | Node color cycle (per-node `color` wins) |
| `nodeAction` | [[actions\|ActionDefinition]] | — | Fired on node tap; `{{value}}` = `{"name", "in", "out"}` |
| `scrub` | bool | `false` | Drag sweeps the spotlight from node to node with haptic ticks (the action still fires on tap) |

## Sync Payload Structure

Nodes plus source→target→value links — natural JSON or an encoded string.
Endpoints may be node names or indices:

```json
{
  "nodes": [
    { "name": "Solar", "color": "#FFD93D" },
    { "name": "Battery" },
    { "name": "House" },
    { "name": "Grid" }
  ],
  "links": [
    { "source": "Solar",   "target": "Battery", "value": 3.2 },
    { "source": "Solar",   "target": "House",   "value": 1.8 },
    { "source": "Battery", "target": "House",   "value": 2.1 },
    { "source": "Solar",   "target": "Grid",    "value": 0.9 }
  ]
}
```

Self-links, unknown endpoints, and zero/negative values are dropped. Cycles
don't hang the layout, but a mostly-acyclic flow reads far better.

## Examples

### Live energy flow
```json
{
  "type": "sankey",
  "id": "energy",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Energy (kW)",
  "sankeyConfig": { "showValues": true },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "power_flow" }, "valuePath": "sankey" }]
}
```

### Tap-to-inspect service traffic
```json
{
  "type": "sankey",
  "id": "traffic",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Requests/min",
  "sankeyConfig": {
    "nodeAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast", "payload": { "msg_type": "inspect_service", "node": "{{value}}" } }
  },
  "defaultValue": "{\"nodes\":[{\"name\":\"Edge\"},{\"name\":\"API\"},{\"name\":\"DB\"},{\"name\":\"Cache\"}],\"links\":[{\"source\":0,\"target\":1,\"value\":120},{\"source\":1,\"target\":2,\"value\":80},{\"source\":1,\"target\":3,\"value\":40}]}"
}
```

## Behavior
- Columns come from the longest path from the sources; pure sinks align to the last column; each column is vertically centered
- Node height ∝ max(inflow, outflow); ribbons attach in far-end order so they fan instead of crossing at the bar
- Tap a node to spotlight it (its ribbons brighten, unrelated ones fade to a whisper) and fire `nodeAction`; tap empty space to clear
- `scrub: true` lets a drag sweep the spotlight fluidly across nodes with a tick per hand-off
- Dataset pushes animate via the control's `animation` profile

## Notes
- ≤ 4 columns and ≤ ~10 nodes stay readable on a phone
- The control's value **is the dataset JSON** — selection never overwrites it
- For pairwise relationships without direction/stages, [[chord]] is the circular sibling

## Related
- [[chord]] — circular inter-relationships
- [[graph]] — force-directed node-link topology
- [[pie-chart]] — single-stage part-of-whole
- [[sync]] — how flows arrive
- [[actions]] — how `nodeAction` fires
