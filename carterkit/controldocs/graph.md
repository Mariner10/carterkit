---
type: graph
label: Graph
icon: circle.grid.cross.fill
category: controls
defaultSpan: [3, 4]
fields:
  - name: label
    type: string
    description: Header label above the graph
  - name: graphConfig
    type: object
    description: Full configuration object (see GraphConfig section)
  - name: tint
    type: color
    default: "#667eea"
    description: Fallback node color
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
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Secondary text color
  - name: borderColor
    type: color
    default: #FFFFFF1A
    description: Border color
  - name: borderWidth
    type: number
    default: 1
    description: Border width
  - name: labelFontSize
    type: number
    default: 12
    description: Label text size
---

# Graph

An Obsidian-style force-directed graph visualization. Displays nodes and edges with physics simulation, glow effects, and interactive pan/zoom/drag. Read-only (display), optionally interactive.

## Type
`"graph"`

## Recommended Size
This control is visually large. Use a span of at least `[3, 4]` (full width, 3 rows) for readability.

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Header label above the graph |
| `graphConfig` | [[#GraphConfig]] | — | Full configuration object (all optional) |
| `tint` | string | `"#667eea"` | Fallback node color if graphConfig omitted |

## GraphConfig

All fields are optional with sensible defaults.

### Node Tap Behavior

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `nodeAction` | [[actions\|ActionDefinition]] | — | Default action fired when any node is tapped (node ID as `{{value}}`) |
| `contentEvent` | string | — | (Reserved) Event for content-push model |

### Node Appearance

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `nodeColor` | string | `"#667eea"` | Default node fill color (hex) |
| `nodeSize` | number | `8.0` | Base node radius in points |
| `nodeHighlightColor` | string | — | Color when node is active/selected |
| `nodeBorderWidth` | number | `0` | Border stroke width around nodes |
| `nodeBorderColor` | string | `"#FFFFFF"` | Border stroke color |

### Edge Appearance

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `edgeColor` | string | `"#FFFFFF"` | Default edge line color |
| `edgeWidth` | number | `1.0` | Edge line width |
| `edgeOpacity` | number | `0.4` | Edge line opacity (0-1) |
| `edgeCurved` | bool | `false` | Use curved (quadratic) edges instead of straight |

### Labels

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `showLabels` | bool | `true` | Show text labels under nodes |
| `labelColor` | string | `"#CCCCCC"` | Label text color |
| `labelSize` | number | `10.0` | Label font size |
| `labelOffset` | number | `12.0` | Distance from node center to label |

### Physics Simulation

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `repulsionForce` | number | `100` | How strongly nodes push apart |
| `attractionForce` | number | `0.01` | How strongly connected nodes pull together |
| `centerForce` | number | `0.02` | How strongly nodes are pulled toward center |
| `damping` | number | `0.9` | Velocity dampening per tick (0-1, lower = more friction) |
| `velocityDecay` | number | `0.6` | Velocity decay rate (0-1, lower = faster settling) |

### Interaction

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `interactive` | bool | `true` | Allow pan and zoom |
| `draggable` | bool | `true` | Allow dragging individual nodes |
| `zoomRange` | [min, max] | `[0.3, 3.0]` | Pinch zoom limits |

### Visual Effects

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `backgroundColor` | string | `"#0D0D1A"` | Graph canvas background |
| `showParticles` | bool | `false` | (Reserved) Animated particles along edges |
| `particleColor` | string | — | (Reserved) Particle color |
| `particleSpeed` | number | — | (Reserved) Particle animation speed |
| `glowEnabled` | bool | `true` | Node glow effect |
| `glowRadius` | number | `6.0` | Glow blur radius |
| `glowColor` | string | `"#667eea"` | Glow color |

### Group Colors

Map group names to colors. Nodes with a matching `group` field use this color:

```json
"groupColors": {
  "controls": "#667eea",
  "models": "#FF6B6B",
  "views": "#34C759",
  "services": "#FF9500"
}
```

## Sync Payload Structure

The graph receives its data as a JSON string via [[sync]]:

```json
{
  "nodes": [
    { "id": "button", "label": "Button", "group": "controls", "size": 1.2 },
    { "id": "toggle", "label": "Toggle", "group": "controls" },
    { "id": "grid-renderer", "label": "GridRenderer", "group": "views", "size": 1.5 },
    { "id": "app-state", "label": "AppState", "group": "models", "color": "#FFD700", "size": 2.0 }
  ],
  "edges": [
    { "from": "grid-renderer", "to": "button" },
    { "from": "grid-renderer", "to": "toggle" },
    { "from": "app-state", "to": "grid-renderer", "width": 2.0, "color": "#FFD700" },
    { "from": "button", "to": "app-state", "label": "action" }
  ]
}
```

### Node Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique node identifier |
| `label` | string | no | Display text under the node |
| `color` | string | no | Override color for this node (hex) |
| `size` | number | no | Size multiplier (1.0 = base size) |
| `group` | string | no | Group name for color coding via `groupColors` |
| `icon` | string | no | (Reserved) SF Symbol rendered in the node |
| `onTap` | [[#NodeTapBehavior]] | no | Per-node tap behavior (overrides graphConfig.nodeAction) |

### NodeTapBehavior

Each node can define what happens when tapped. Two types:

**Action** — fires a MeshSocket action with the node's ID:
```json
"onTap": {
  "type": "action",
  "method": "meshsocket",
  "mode": "request",
  "event": "route_msg",
  "payload": { "target_id": "home-hub", "type": "select_device", "payload": { "device": "{{value}}" } }
}
```

**Content** — requests markdown content from the server, opens a [[markdown-sheet]]:
```json
"onTap": {
  "type": "content",
  "event": "get_doc",
  "payload": { "path": "controls/button.md" }
}
```

The server should respond with:
```json
{
  "title": "Button",
  "content": "# Button\n\nA tappable action trigger..."
}
```

Or simply a string (the raw markdown), in which case the node's `label` is used as the title.

### Edge Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from` | string | yes | Source node ID |
| `to` | string | yes | Target node ID |
| `color` | string | no | Override color for this edge |
| `width` | number | no | Override width for this edge |
| `label` | string | no | (Reserved) Text along the edge |

## Examples

### Full configuration
```json
{
  "type": "graph",
  "id": "network-topology",
  "position": [0, 0],
  "span": [4, 4],
  "label": "Network Topology",
  "graphConfig": {
    "nodeColor": "#667eea",
    "nodeSize": 10,
    "nodeBorderWidth": 1.5,
    "nodeBorderColor": "#FFFFFF",
    "edgeColor": "#FFFFFF",
    "edgeWidth": 1.0,
    "edgeOpacity": 0.3,
    "edgeCurved": true,
    "showLabels": true,
    "labelColor": "#AAAAAA",
    "labelSize": 9,
    "repulsionForce": 120,
    "attractionForce": 0.015,
    "centerForce": 0.03,
    "damping": 0.85,
    "velocityDecay": 0.5,
    "interactive": true,
    "draggable": true,
    "zoomRange": [0.5, 2.5],
    "backgroundColor": "#0A0A1A",
    "glowEnabled": true,
    "glowRadius": 8,
    "glowColor": "#667eea",
    "groupColors": {
      "hub": "#FF6B6B",
      "bridge": "#FFD93D",
      "device": "#6BCB77",
      "mobile": "#4D96FF"
    }
  },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "network_graph" }, "valuePath": "graph_data" }]
}
```

### Minimal (all defaults)
```json
{
  "type": "graph",
  "id": "simple-graph",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Connections",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "graph_update" }, "valuePath": "data" }]
}
```

### Static graph (no sync, default value)
```json
{
  "type": "graph",
  "id": "static-graph",
  "position": [0, 0],
  "span": [4, 4],
  "defaultValue": "{\"nodes\":[{\"id\":\"a\",\"label\":\"Hub\"},{\"id\":\"b\",\"label\":\"Light\"},{\"id\":\"c\",\"label\":\"Sensor\"}],\"edges\":[{\"from\":\"a\",\"to\":\"b\"},{\"from\":\"a\",\"to\":\"c\"}]}",
  "graphConfig": {
    "interactive": false,
    "glowEnabled": true,
    "glowColor": "#FF6B6B"
  }
}
```

## Behavior
- Physics simulation runs at 60fps via `TimelineView`
- Nodes settle into a stable arrangement based on force parameters
- Dragging a node pins it temporarily; releasing lets it rejoin the simulation
- Pinch to zoom, drag canvas to pan
- New nodes animate in from random positions; removed nodes disappear
- Graph data can update via sync — the simulation adapts incrementally (no full reset)

## Notes
- The `size` field on nodes is a multiplier, not an absolute value. `size: 2.0` = twice the base `nodeSize`
- For dense graphs (50+ nodes), consider reducing `repulsionForce` and increasing `damping` for faster settling
- The canvas uses `Canvas` (immediate mode drawing) for performance — handles hundreds of nodes smoothly
- Fields marked (Reserved) are defined in the schema but not yet rendered

## Related
- [[shared-properties]] — Base fields
- [[sync]] — How graph data is received
- [[long-press]] — Can have a long-press detail popup
- [[conditional-visibility]] — Can be conditionally shown/hidden
