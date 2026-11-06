---
type: chord
label: Chord
icon: circle.hexagonpath.fill
category: controls
defaultSpan: [3, 3]
addIntent: show
pickerCategory: Charts
depth: complete
friendlyName: Connections
oneLiner: How things connect to each other
aliases: [relationships, connections, circular, flow, matrix]
starterPreset: {"label": "Connections"}
fields:
  - name: haptic
    tab: action
    type: enum
    values: [none, light, medium, heavy, soft, rigid, selection, success, warning, error]
    description: Touch feedback on interaction (supported hardware)
    summary: Buzz when you tap
    does: Plays this vibration when you tap an arc, on supported phones.
    valueHelp: {"none": "no vibration", "light": "a gentle tap", "medium": "a firm tap", "heavy": "a strong thump", "soft": "a muted, cushioned tap", "rigid": "a sharp, hard tap", "selection": "a tiny tick like scrolling a picker", "success": "a double tap for done", "warning": "a sharp double tap for caution", "error": "a buzzy triple tap for failure"}
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label above the diagram
    summary: The title above the chart
    does: Shows this text as the header above the diagram, with the selected group's readout beside it.
  - name: chordConfig
    type: object
    description: Full configuration object (see ChordConfig section)
    summary: All the chart settings in one place
    does: Groups the arc, ribbon, color and action settings for the diagram; every part is optional.
  - name: tint
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: First-group color and palette seed
    summary: The main color
    does: Colors the first group and seeds the palette for the rest when no colors list is given.
  - name: formatValue
    tab: data
    type: string
    description: Formatter for group totals
    summary: How totals are written
    does: Formats the group total shown in the selection readout, for example as a number or percent.
  - name: arcAction
    tab: action
    type: object
    description: arcAction
    summary: What happens when you tap a group
    does: Runs this action when you tap an arc; the value sent is the group's label and total.
    group: chordConfig
  - name: colors
    edit: list
    depth: surface
    title: Arc colors
    tab: style
    type: string[]
    description: Group color cycle (payload colors wins)
    summary: The colors for each group
    does: Colors the arcs in order and repeats the list if there are more groups; colors in the data take priority.
    group: chordConfig
  - name: pad
    edit: scrub
    depth: hold
    under: ribbonOpacity
    title: Arc gap
    unit: deg
    min: 0
    max: 20
    step: 0.5
    type: number
    default: 2.5
    description: Degrees of breathing room between arcs
    summary: Gap between arcs
    does: Leaves this many degrees of empty space between neighbouring arcs, from 0 to 20 (default 2.5).
    group: chordConfig
  - name: ribbonOpacity
    edit: scrub
    depth: surface
    title: Ribbon strength
    tab: style
    min: 0
    max: 1
    step: 0.05
    type: number
    default: 0.4
    description: Ribbon opacity (selection brightens involved ribbons)
    summary: How solid the ribbons look
    does: Sets how opaque the ribbons are from 0 to 1 (default 0.4); ribbons of the selected group brighten.
    group: chordConfig
  - name: scrub
    type: bool
    default: false
    description: Drag around the ring sweeps the spotlight arc-to-arc like a dial, with haptic ticks (the action still fires on tap)
    summary: Drag around the ring to focus
    does: When on, dragging around the ring moves the spotlight from group to group with a tick at each one; tapping still runs the action.
    group: chordConfig
  - name: showLabels
    edit: part
    depth: hold
    title: Labels
    type: bool
    default: true
    description: Group names around the rim
    summary: Show group names
    does: Writes each group's name around the outside of the ring; turn off to hide them.
    group: chordConfig
themeFields:
  - use: cornerRadius
    summary: How round the corners are
    does: Rounds the control's corners from 0 to 30 pt (default 12).
  - name: surfacePrimary
    title: Background color
    type: color
    default: #FFFFFF0F
    description: Background fill
    summary: The colour behind the control
    does: Fills the control's background with this color.
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Group label color
    summary: Group name color
    does: Colors the group names around the rim.
  - use: accentColor
    summary: Highlight color
    does: Sets the accent color used for tinting when no tint is set.
  - use: borderColor
    summary: Outline color
    does: Colors the outline drawn around the control.
  - use: borderWidth
    summary: Outline thickness
    does: Sets the outline width from 0 to 5 pt (default 1).
  - use: controlPadding
    summary: Space inside the edges
    does: Adds this much padding between the control's edge and the diagram, from 0 to 24 pt (default 8).
  - use: foregroundColor
    summary: Main text color
    does: Colors the primary text such as the title and readout.
  - use: labelFontSize
    summary: Label text size
    does: Sets the label text size from 8 to 24 pt (default 12).
  - use: tertiaryColor
    summary: Dimmed text color
    does: Colors the group names that are dimmed while another group is spotlighted.
---

# Chord

Who talks to whom: groups as arcs around a circle, relationships as ribbons
through the middle, ribbon width ∝ flow. Feed it a matrix — service-to-service
traffic, team hand-offs, trade between regions. Tapping an arc **spotlights
that group's ribbons** (the rest fade to a whisper) and fires `arcAction` with
the group's total, so the diagram doubles as a focus picker.

## Type
`"chord"`

## Recommended Size
Square — `[3, 3]`. The control keeps itself round and leaves a rim gutter for
labels.

## Relevant Fields
Inherits all [[control-def|shared fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Header label (selection readout appears beside it) |
| `chordConfig` | [[#ChordConfig]] | — | Full configuration object (all optional) |
| `tint` | string | `"#667eea"` | First-group color / palette seed |
| `formatValue` | string | — | Formatter for total readouts |
| `action` | [[actions\|ActionDefinition]] | — | Fallback for `arcAction` |

## ChordConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `showLabels` | bool | `true` | Group names around the rim |
| `pad` | number | `2.5` | Degrees of breathing room between arcs |
| `ribbonOpacity` | number | `0.4` | Ribbon opacity (selection brightens involved ribbons) |
| `colors` | string[] | built-in palette | Group color cycle (payload `colors` wins) |
| `arcAction` | [[actions\|ActionDefinition]] | — | Fired on arc tap; `{{value}}` = `{"label", "total"}` |
| `scrub` | bool | `false` | Drag around the ring sweeps the spotlight arc-to-arc like a dial, with haptic ticks (the action still fires on tap) |

## Sync Payload Structure

Labels plus a square matrix — `matrix[i][j]` is the flow from group `i` to
group `j`. A symmetric matrix reads as undirected relationship strength:

```json
{
  "labels": ["API", "Web", "DB", "Cache"],
  "colors": ["#667eea", "#34C759", "#FF9500", "#BF5AF2"],
  "matrix": [
    [0, 5, 3, 2],
    [5, 0, 1, 0],
    [3, 1, 0, 4],
    [2, 0, 4, 0]
  ]
}
```

Arc size ∝ the group's row sum (pure receivers use their incoming total so
they still show). Each ribbon end is sized by that direction's flow, so an
asymmetric matrix tapers honestly.

## Examples

### Service mesh traffic
A live matrix of service calls arrives over the socket and fills the ring.

```json
{
  "type": "chord",
  "id": "mesh-traffic",
  "position": [0, 0],
  "span": [3, 3],
  "label": "Calls/min",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "mesh_matrix" }, "valuePath": "chord" }]
}
```

### Tap-to-focus hand-off board
Tapping a team's arc broadcasts which team to focus on.

```json
{
  "type": "chord",
  "id": "handoffs",
  "position": [0, 0],
  "span": [3, 3],
  "label": "Hand-offs",
  "chordConfig": {
    "arcAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "focus_team", "team": "{{value}}" } }
  },
  "defaultValue": "{\"labels\":[\"Design\",\"Build\",\"QA\"],\"matrix\":[[0,6,1],[2,0,5],[1,3,0]]}"
}
```

### Dial-style relationship map
A fixed matrix with wider gaps, softer ribbons and a drag-to-scrub spotlight.

```json
{
  "type": "chord",
  "id": "regions",
  "position": [0, 0],
  "span": [3, 3],
  "label": "Trade",
  "tint": "#34C759",
  "haptic": "selection",
  "chordConfig": { "scrub": true, "pad": 6, "ribbonOpacity": 0.3, "showLabels": true },
  "defaultValue": "{\"labels\":[\"EU\",\"US\",\"Asia\"],\"matrix\":[[0,4,2],[4,0,3],[2,3,0]]}"
}
```

## Behavior
- Arcs start at 12 o'clock and run clockwise; labels stay horizontal, anchored away from the rim
- Tap an arc to spotlight its ribbons + fire `arcAction`; tap again or tap outside the ring to clear
- `scrub: true` turns the ring into a dial — dragging sweeps the spotlight with a tick at every arc boundary
- Ribbons blend a gradient between their two group colors
- Dataset pushes animate via the control's `animation` profile

## Notes
- 3–8 groups read best; the rim gets crowded past that
- Self-flows (`matrix[i][i]`) are ignored
- For staged/directional flow use [[sankey]]; for arbitrary topology use [[graph]]

## Related
- [[sankey]] — staged flow volumes
- [[graph]] — force-directed node-link
- [[pie-chart]] — one group's share of a whole
- [[sync]] — how matrices arrive
- [[actions]] — how `arcAction` fires
