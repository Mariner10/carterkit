---
type: sankey
depth: complete
label: Sankey
icon: arrow.triangle.branch
category: controls
defaultSpan: [3, 4]
addIntent: show
pickerCategory: Charts
friendlyName: Flows
oneLiner: Where amounts flow from and to
aliases: [flow, funnel, diagram, sources, links, breakdown]
starterPreset: {"label": "Flows"}
io:
  - emits: node
    when: tap
    title: When you tap a node
    field: sankeyConfig.nodeAction
    fallback: action
    type: json
    says: the tapped node's name with its total flow in and out
    example: {"name": "Item 1", "in": 3, "out": 2}
    also: Sends only when the tap selects a node, not when it clears the selection
    since: next
  - receives: nodes
    role: show
    type: json
    shape: {"nodes": [{"name": "text", "color": "hex?"}], "links": [{"source": "node name or index", "target": "node name or index", "value": "number"}]}
    from: [hub, mqtt, http, store]
    says: nodes, and links between them each with an amount
    reacts: nodes are re-stacked into columns and the ribbons resize to their new amounts
    example: {"nodes": [{"name": "Item 1"}, {"name": "Item 2"}], "links": [{"source": "Item 1", "target": "Item 2", "value": 3}]}
    since: next
  - sample: {"nodes": [{"name": "Item 1"}, {"name": "Item 2"}, {"name": "Item 3"}, {"name": "Item 4"}], "links": [{"source": "Item 1", "target": "Item 3", "value": 3}, {"source": "Item 1", "target": "Item 4", "value": 1}, {"source": "Item 2", "target": "Item 4", "value": 2}]}
    next: {"nodes": [{"name": "Item 1"}, {"name": "Item 2"}, {"name": "Item 3"}, {"name": "Item 4"}], "links": [{"source": "Item 1", "target": "Item 3", "value": 1}, {"source": "Item 1", "target": "Item 4", "value": 3}, {"source": "Item 2", "target": "Item 4", "value": 2}]}
fields:
  - name: haptic
    tab: action
    type: enum
    values: [none, light, medium, heavy, soft, rigid, selection, success, warning, error]
    description: Touch feedback on interaction (supported hardware)
    summary: Buzz when you touch it
    does: Gives a small physical tap when you interact, on phones that support it.
    valueHelp: {"none": "no vibration", "light": "a faint tap", "medium": "a normal tap", "heavy": "a strong thump", "soft": "a gentle cushioned tap", "rigid": "a crisp hard tap", "selection": "a tiny tick like scrolling a picker", "success": "a pattern that feels like done", "warning": "a pattern that feels like careful", "error": "a sharp pattern that feels like failed"}
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label above the diagram
    summary: The heading above the chart
    does: Shows this text as the header above the diagram.
  - name: sankeyConfig
    type: object
    description: Full configuration object (see SankeyConfig section)
    summary: All the chart settings in one place
    does: Holds the optional look and tap settings for the diagram.
  - name: tint
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: First-node color and palette seed
    summary: The main colour
    does: Colours the first node and seeds the colours of the others.
  - name: formatValue
    tab: data
    type: string
    description: Formatter for node throughput values
    summary: How numbers are written
    does: Formats the throughput numbers shown next to node labels and the selection readout.
  - name: colors
    edit: list
    depth: surface
    title: Node colors
    tab: style
    type: string[]
    description: Node color cycle (per-node color wins)
    summary: The colours nodes cycle through
    does: Gives each node a colour in turn; a colour set on a node itself wins.
    group: sankeyConfig
  - name: linkOpacity
    edit: scrub
    depth: surface
    title: Flow strength
    tab: style
    min: 0
    max: 1
    step: 0.05
    type: number
    default: 0.32
    description: Ribbon opacity (selection brightens involved ribbons)
    summary: How solid the flow bands are
    does: Sets how see-through the ribbons are, from 0 invisible to 1 solid; selected ones brighten.
    group: sankeyConfig
  - name: nodeAction
    tab: action
    type: object
    description: nodeAction
    summary: What happens when you tap a node
    does: Runs this action when a node is tapped, passing its name and in and out totals.
    group: sankeyConfig
  - name: nodeSpacing
    edit: scrub
    depth: hold
    under: linkOpacity
    title: Node spacing
    unit: pt
    tab: style
    min: 0
    max: 40
    step: 1
    type: number
    default: 10
    description: Minimum vertical gap between nodes in a column
    summary: Gap between boxes
    does: Sets the smallest vertical gap between nodes in a column, 0 to 40 points.
    group: sankeyConfig
  - name: cellCornerRadius
    edit: scrub
    depth: hold
    under: linkOpacity
    title: Cell roundness
    unit: pt
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    description: "Node corner rounding (default: a third of the node width)"
    summary: How round the boxes are
    does: Rounds the node bars, 0 to 30 points; unset it is a third of the node width.
    group: sankeyConfig
  - name: nodeWidth
    edit: scrub
    depth: hold
    under: linkOpacity
    title: Node width
    unit: pt
    tab: style
    min: 1
    max: 40
    step: 1
    type: number
    default: 10
    description: Node bar width in points
    summary: How thick the boxes are
    does: Sets the width of each node bar, 1 to 40 points.
    group: sankeyConfig
  - name: scrub
    chip: Touch
    type: bool
    default: false
    description: Drag sweeps the spotlight from node to node with haptic ticks (the action still fires on tap)
    summary: Slide your finger across nodes
    does: Lets a drag move the spotlight from node to node with a tick each step; a tap still fires the action.
    group: sankeyConfig
  - name: showLabels
    edit: part
    depth: hold
    title: Labels
    type: bool
    default: true
    description: Node names beside the bars
    summary: Show node names
    does: Shows or hides the node names beside the bars.
    group: sankeyConfig
  - name: showValues
    edit: part
    depth: hold
    title: Value labels
    type: bool
    default: false
    description: Throughput value alongside each label
    summary: Show the numbers
    does: Shows or hides each node's throughput value next to its name.
    group: sankeyConfig
themeFields:
  - use: cornerRadius
  - use: surfacePrimary
    summary: Background colour
    does: Fills the control's background with this colour.
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Node label color
    summary: Node name colour
    does: Colours the node labels.
  - use: accentColor
    summary: Highlight colour
    does: Sets the accent colour used to tint the control.
  - use: borderColor
    summary: Outline colour
    does: Colours the control's outline.
  - use: borderWidth
    summary: Outline thickness
    does: Sets the outline width, 0 to 5 points.
  - use: controlPadding
    summary: Space inside the edge
    does: Adds padding between the control's edge and its content, 0 to 24 points.
  - use: foregroundColor
    summary: Main text colour
    does: Colours the primary text.
  - use: labelFontSize
    summary: Label text size
    does: Sets the title text size, 8 to 24 points.
  - use: tertiaryColor
    summary: Faint text colour
    does: Colours the faintest text and ink.
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
| `cellCornerRadius` | number | a third of `nodeWidth` | Node corner rounding in points, 0–30 |
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
A power-flow diagram fed live from a mesh socket, with values shown.
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
Tapping a service broadcasts its in and out totals so something else can react.
```json
{
  "type": "sankey",
  "id": "traffic",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Requests/min",
  "sankeyConfig": {
    "nodeAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "inspect_service", "node": "{{value}}" } }
  },
  "defaultValue": "{\"nodes\":[{\"name\":\"Edge\"},{\"name\":\"API\"},{\"name\":\"DB\"},{\"name\":\"Cache\"}],\"links\":[{\"source\":0,\"target\":1,\"value\":120},{\"source\":1,\"target\":2,\"value\":80},{\"source\":1,\"target\":3,\"value\":40}]}"
}
```

### Budget flow with scrubbing and custom colors
Where monthly income goes, with values shown and a drag that sweeps the spotlight across nodes.
```json
{
  "type": "sankey",
  "id": "budget",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Monthly budget",
  "tint": "#34C759",
  "sankeyConfig": {
    "showValues": true,
    "scrub": true,
    "nodeWidth": 14,
    "linkOpacity": 0.45,
    "colors": ["#34C759", "#FF9F0A", "#0A84FF"]
  },
  "defaultValue": "{\"nodes\":[{\"name\":\"Income\"},{\"name\":\"Rent\"},{\"name\":\"Food\"},{\"name\":\"Savings\"}],\"links\":[{\"source\":0,\"target\":1,\"value\":1200},{\"source\":0,\"target\":2,\"value\":500},{\"source\":0,\"target\":3,\"value\":300}]}"
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
