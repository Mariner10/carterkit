---
type: graph
label: Graph
icon: circle.grid.cross.fill
category: controls
defaultSpan: [4, 4]
addIntent: show
pickerCategory: Charts
friendlyName: Network
oneLiner: Dots joined by lines
aliases: [network, nodes, edges, diagram, relationships, links]
depth: complete
starterPreset: {"label": "Network"}
fields:
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label above the graph
    summary: The name shown above the graph
    does: "Shows this text as the header above the graph in the label font size (8-24 pt)."
  - name: graphConfig
    type: object
    description: Full configuration object (see GraphConfig section)
    summary: All the graph's look and behavior in one bundle
    does: "Holds every graph setting below; any setting left out uses its default."
  - name: tint
    edit: color
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: Fallback node color
    summary: The standby color for the dots
    does: "Colors the nodes with this hex color when graphConfig sets no node color."
  - name: attractionForce
    bounds: none
    type: number
    default: 0.01
    description: How strongly connected nodes pull together
    summary: How tightly linked dots hug each other
    does: "Pulls connected nodes closer together; 0.01 is gentle and larger values draw linked dots into tight clusters."
    group: graphConfig
  - name: backgroundColor
    edit: color
    depth: hold
    under: tint
    title: Background
    tab: style
    type: color
    description: Graph canvas background
    summary: The backdrop behind the network
    does: "Fills the graph canvas with this hex color; the default is a near-black navy."
    group: graphConfig
  - name: centerForce
    bounds: none
    type: number
    default: 0.02
    description: How strongly nodes are pulled toward center
    summary: How strongly the network gathers in the middle
    does: "Pulls every node toward the canvas center; 0.02 keeps it loose and larger values squeeze the cloud into the middle."
    group: graphConfig
  - name: contentEvent
    type: string
    description: (Reserved) Event for content-push model
    summary: Not used yet
    does: "Reserved for a future content-push feature, so setting it changes nothing on screen."
    group: graphConfig
  - name: damping
    min: 0
    max: 1
    step: 0.05
    type: number
    default: 0.9
    description: Velocity dampening per tick (0-1, lower = more friction)
    summary: How quickly the dots stop moving
    does: "Scales motion each tick from 0 to 1; lower values add friction so the dots stop sooner."
    group: graphConfig
  - name: draggable
    type: bool
    default: true
    description: Allow dragging individual nodes
    summary: Whether a dot can be pulled around
    does: "On lets a finger drag a single node and the rest follow; off keeps every dot where physics puts it."
    group: graphConfig
  - name: edgeColor
    edit: color
    depth: hold
    under: edgeWidth
    title: Line color
    tab: style
    type: color
    description: Default edge line color
    summary: The color of the connecting lines
    does: "Colors every line between nodes with this hex color unless an edge sets its own."
    group: graphConfig
  - name: edgeCurved
    edit: part
    depth: hold
    title: Curved lines
    type: bool
    default: false
    description: Use curved (quadratic) edges instead of straight
    summary: Straight or bowed connections
    does: "On bends each line into a gentle curve; off draws straight lines."
    group: graphConfig
  - name: edgeOpacity
    edit: scrub
    depth: hold
    under: edgeWidth
    title: Line fade
    tab: style
    min: 0
    max: 1
    step: 0.05
    type: number
    default: 0.4
    description: Edge line opacity (0-1)
    summary: How faint the lines are
    does: "Sets line opacity from 0 (invisible) to 1 (solid); the default 0.4 keeps lines soft."
    group: graphConfig
  - name: edgeWidth
    edit: scrub
    unit: pt
    title: Line width
    tab: style
    min: 0.5
    max: 12
    step: 0.5
    type: number
    default: 1.0
    description: Edge line width
    summary: How thick the lines are
    does: "Sets the line thickness in points, 0.5 to 12; an edge can override it."
    group: graphConfig
  - name: glowColor
    tab: style
    type: color
    description: Glow color
    summary: The color of the halo around dots
    does: "Tints the glow behind nodes with this hex color; it only shows while glow is on."
    group: graphConfig
  - name: glowEnabled
    edit: part
    depth: hold
    title: Glow
    tab: style
    type: bool
    default: true
    description: Node glow effect
    summary: A soft halo behind each dot
    does: "On draws a blurred glow behind every node; off leaves flat dots."
    group: graphConfig
  - name: glowRadius
    edit: scrub
    depth: hold
    under: nodeSize
    title: Glow
    unit: pt
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    default: 6.0
    description: Glow blur radius
    summary: How wide the halo spreads
    does: "Sets the glow blur in points, 0 to 30; larger values spread a softer, wider halo."
    group: graphConfig
  - name: groupColors
    tab: style
    type: object
    description: groupColors
    summary: A color for each kind of dot
    does: "Maps group names to hex colors so nodes whose group matches are filled with that color."
    group: graphConfig
  - name: interactive
    type: bool
    default: true
    description: Allow pan and zoom
    summary: Whether you can pan and zoom
    does: "On lets a drag move the canvas and a pinch zoom it; off freezes the view."
    group: graphConfig
  - name: labelColor
    tab: style
    type: color
    description: Label text color
    summary: The color of the dot names
    does: "Colors the text under each node with this hex color."
    group: graphConfig
  - name: labelOffset
    tab: style
    min: 0
    max: 40
    step: 1
    type: number
    default: 12.0
    description: Distance from node center to label
    summary: How far the name sits from its dot
    does: "Moves each label this many points away from its node center, 0 to 40."
    group: graphConfig
  - name: labelSize
    edit: scrub
    depth: hold
    under: nodeSize
    title: Label size
    tab: style
    min: 8
    max: 24
    step: 1
    type: number
    default: 10.0
    description: Label font size
    summary: How big the dot names are
    does: "Sets the node label font size in points, 8 to 24."
    group: graphConfig
  - name: nodeAction
    tab: action
    type: object
    description: nodeAction
    summary: What happens when you tap a dot
    does: "Runs this action when any node is tapped, with the node id available as {{value}}; a node's own onTap wins."
    group: graphConfig
  - name: nodeBorderColor
    tab: style
    type: color
    description: Border stroke color
    summary: The color of the ring around each dot
    does: "Colors the outline drawn around nodes; it only shows when the outline width is above 0."
    group: graphConfig
  - name: nodeBorderWidth
    edit: scrub
    depth: hold
    under: nodeSize
    title: Node outline
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 0
    description: Border stroke width around nodes
    summary: A ring around each dot
    does: "Draws an outline of this thickness in points, 0 to 5; 0 means no outline."
    group: graphConfig
  - name: nodeColor
    edit: color
    depth: hold
    under: nodeSize
    title: Node color
    tab: style
    type: color
    description: Default node fill color (hex)
    summary: The default fill of the dots
    does: "Fills every node with this hex color unless its group or its own color overrides it."
    group: graphConfig
  - name: nodeHighlightColor
    tab: style
    type: color
    description: Color when node is active/selected
    summary: The color of the dot you touch
    does: "Switches a node to this hex color while it is active or selected."
    group: graphConfig
  - name: nodeSize
    edit: scrub
    unit: pt
    title: Node size
    tab: style
    min: 2
    max: 40
    step: 1
    type: number
    default: 8.0
    description: Base node radius in points
    summary: How big the dots are
    does: "Sets the base node radius in points, 2 to 40; a node's size multiplier scales it."
    group: graphConfig
  - name: particleColor
    tab: style
    type: color
    description: (Reserved) Particle color
    summary: Not used yet
    does: "Reserved for the particle color, so setting it changes nothing on screen."
    group: graphConfig
  - name: particleSpeed
    bounds: none
    type: number
    description: (Reserved) Particle animation speed
    summary: Not used yet
    does: "Reserved for the particle speed, so setting it changes nothing on screen."
    group: graphConfig
  - name: repulsionForce
    bounds: none
    type: number
    default: 100
    description: How strongly nodes push apart
    summary: How hard the dots push each other away
    does: "Pushes every pair of nodes apart; larger values spread the network out and smaller ones pack it tight."
    group: graphConfig
  - name: showLabels
    edit: part
    depth: hold
    title: Labels
    type: bool
    default: true
    description: Show text labels under nodes
    summary: Names under the dots
    does: "On writes each node's label under it; off shows bare dots."
    group: graphConfig
  - name: showParticles
    edit: part
    depth: hold
    title: Particles
    type: bool
    default: false
    description: Animated particles travelling along edges
    summary: Little lights traveling along the lines
    does: "On animates small particles running along the edges; off leaves the lines still."
    group: graphConfig
  - name: velocityDecay
    min: 0
    max: 1
    step: 0.05
    type: number
    default: 0.6
    description: Velocity decay rate (0-1, lower = faster settling)
    summary: How fast the network settles
    does: "Sets how quickly dot speed fades, 0 to 1; lower values let the layout come to rest sooner."
    group: graphConfig
  - name: zoomRange
    type: object
    description: Pinch zoom limits
    summary: How far you can zoom out and in
    does: "Sets the smallest and largest pinch zoom as [min, max], default [0.3, 3.0]."
    group: graphConfig
themeFields:
  - use: cornerRadius
    summary: How round the corners are
    does: "Rounds the card behind the graph in points, 0 to 30; 0 is square."
  - name: controlPadding
    title: Inner spacing
    min: 0
    max: 24
    step: 1
    type: number
    default: 8
    description: Internal padding
    summary: Breathing room inside the card
    does: "Insets the graph from the card edge by this many points, 0 to 24."
  - name: surfacePrimary
    title: Background color
    type: color
    default: #FFFFFF0F
    description: Background fill
    summary: The card's own color
    does: "Fills the card behind the graph with this color, usually a faint translucent white."
  - name: secondaryColor
    title: Second text color
    type: color
    default: #FFFFFF99
    description: Secondary text color
    summary: The quieter text color
    does: "Colors the less prominent text such as the header with this color."
  - name: borderColor
    title: Border color
    type: color
    default: #FFFFFF1A
    description: Border color
    summary: The outline of the card
    does: "Colors the card's border line."
  - name: borderWidth
    title: Border thickness
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
    summary: How heavy the card outline is
    does: "Sets the card border thickness in points, 0 to 5; 0 hides it."
  - name: labelFontSize
    title: Title text size
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
    summary: The size of the header text
    does: "Sets the header label size in points, 8 to 24."
  - use: foregroundColor
    does: "Colors the header label and primary text with this color."
---

# Graph

An Obsidian-style force-directed graph visualization. Displays nodes and edges with physics simulation, glow effects, and interactive pan/zoom/drag. Read-only (display), optionally interactive.

## Type
`"graph"`

## Recommended Size
This control is visually large. Use a span of at least `[4, 4]` (full width, 4 rows) for readability.

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
| `showParticles` | bool | `false` | Animated particles travelling along edges |
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
  "mode": "broadcast",
  "event": "route_msg_noreply",
  "payload": { "target_name": "home-hub", "type": "select_device", "payload": { "device": "{{value}}" } }
}
```

`route_msg_noreply` resolves the hub by its registered name and delivers a `select_device`
frame to it. (`route_msg` would need the hub's live relay-assigned `target_id`, not a name.)

**Content** — requests markdown content from the server and opens it in a scrollable markdown sheet.
`event` is sent verbatim as the frame type and the reply is awaited, so it must be `route_msg`
(the only relay verb that carries a reply back) aimed at the server's live relay-assigned
`target_id`; the relay delivers the inner `payload` to that peer as a `get_doc` request.
A name is not resolved here, so this suits layouts a server generates after it connects:
```json
"onTap": {
  "type": "content",
  "event": "route_msg",
  "payload": { "target_id": "<relay id>", "type": "get_doc", "payload": { "path": "controls/button.md" } }
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
Demonstrates every graphConfig group together: styled nodes, curved lines, tuned physics, zoom limits and group colors fed by live data.
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
Demonstrates the defaults: glowing blue dots with labels, straight faint lines, and pan, zoom and drag, filled from live data.
```json
{
  "type": "graph",
  "id": "simple-graph",
  "position": [0, 0],
  "span": [4, 4],
  "label": "Connections",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "graph_update" }, "valuePath": "data" }]
}
```

### Static graph (no sync, default value)
Demonstrates a fixed network from `defaultValue` with `interactive` off, so the view stays put and glows red.
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

### Curved lines, no labels
Demonstrates `edgeCurved` and `showLabels`: connections bow into soft curves and the dots appear bare, for a decorative network.
```json
{
  "type": "graph",
  "id": "curved-graph",
  "position": [0, 0],
  "span": [4, 4],
  "graphConfig": {
    "edgeCurved": true,
    "showLabels": false,
    "edgeWidth": 2,
    "edgeOpacity": 0.6
  },
  "defaultValue": "{\"nodes\":[{\"id\":\"a\"},{\"id\":\"b\"},{\"id\":\"c\"}],\"edges\":[{\"from\":\"a\",\"to\":\"b\"},{\"from\":\"b\",\"to\":\"c\"},{\"from\":\"c\",\"to\":\"a\"}]}"
}
```

### Flat dots, particles and outlines
Demonstrates `glowEnabled`, `showParticles`, `nodeBorderWidth` and `nodeHighlightColor`: dots lose their halo, get a white ring, and small lights travel along the lines.
```json
{
  "type": "graph",
  "id": "particle-graph",
  "position": [0, 0],
  "span": [4, 4],
  "graphConfig": {
    "glowEnabled": false,
    "showParticles": true,
    "nodeBorderWidth": 2,
    "nodeBorderColor": "#FFFFFF",
    "nodeHighlightColor": "#FFD93D"
  },
  "defaultValue": "{\"nodes\":[{\"id\":\"a\",\"label\":\"A\"},{\"id\":\"b\",\"label\":\"B\"}],\"edges\":[{\"from\":\"a\",\"to\":\"b\"}]}"
}
```

### Node tap action
Demonstrates `nodeAction`: tapping any dot sends its id to the hub as a `select_device` message.
```json
{
  "type": "graph",
  "id": "device-graph",
  "position": [0, 0],
  "span": [4, 4],
  "label": "Devices",
  "graphConfig": {
    "nodeAction": {
      "type": "action",
      "method": "meshsocket",
      "mode": "broadcast",
      "event": "route_msg_noreply",
      "payload": { "target_name": "home-hub", "type": "select_device", "payload": { "device": "{{value}}" } }
    }
  },
  "defaultValue": "{\"nodes\":[{\"id\":\"lamp\",\"label\":\"Lamp\"},{\"id\":\"fan\",\"label\":\"Fan\"}],\"edges\":[{\"from\":\"lamp\",\"to\":\"fan\"}]}"
}
```

### Group colors and physics
Demonstrates `groupColors`, `repulsionForce`, `attractionForce` and `centerForce`: nodes take their group's color and the layout spreads wide but stays centered.
```json
{
  "type": "graph",
  "id": "grouped-graph",
  "position": [0, 0],
  "span": [4, 4],
  "graphConfig": {
    "groupColors": { "controls": "#667eea", "models": "#FF6B6B" },
    "repulsionForce": 200,
    "attractionForce": 0.02,
    "centerForce": 0.05
  },
  "defaultValue": "{\"nodes\":[{\"id\":\"b\",\"label\":\"Button\",\"group\":\"controls\"},{\"id\":\"s\",\"label\":\"State\",\"group\":\"models\"}],\"edges\":[{\"from\":\"b\",\"to\":\"s\"}]}"
}
```

### Graph with long-press detail
Demonstrates `longPressGroup`: holding the graph opens a popup with a note about what the network shows.
```json
{
  "type": "graph",
  "id": "detail-graph",
  "position": [0, 0],
  "span": [4, 4],
  "label": "Network",
  "defaultValue": "{\"nodes\":[{\"id\":\"a\",\"label\":\"Hub\"},{\"id\":\"b\",\"label\":\"Light\"}],\"edges\":[{\"from\":\"a\",\"to\":\"b\"}]}",
  "longPressGroup": {
    "position": [0, 0],
    "span": [2, 1],
    "id": "graph-detail",
    "label": "About this network",
    "grid": { "columns": 2, "rows": 1 },
    "children": [
      { "type": "label", "id": "graph-note", "position": [0, 0], "span": [2, 1], "text": "Hub connects every light" }
    ]
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
- [[chart]] — Cartesian series (bars/lines/areas/scatter)
- [[heatmap]] — Dense 2-D matrices where a node graph would tangle
- [[long-press]] — Can have a long-press detail popup
- [[conditional-visibility]] — Can be conditionally shown/hidden
