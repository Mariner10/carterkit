---
type: radar
depth: complete
label: Radar
icon: hexagon.fill
category: controls
defaultSpan: [3, 3]
addIntent: show
pickerCategory: Charts
friendlyName: Radar
oneLiner: Several scores on one shape
aliases: [spider, web, polar, compare, skills, star chart]
starterPreset: {"label": "Radar", "defaultValue": "{\"axes\":[\"Speed\",\"Range\",\"Torque\",\"Grip\"],\"series\":[{\"values\":[8,5,7,6]}]}"}
io:
  - receives: series
    role: show
    type: json
    shape: {"axes": ["text"], "series": [{"name": "text?", "color": "hex?", "values": ["number"]}], "max": "number?"}
    from: [hub, mqtt, http, store, default]
    says: "axes (the spokes) and series: a list of numbers, one per axis, each"
    reacts: the shape grows or shrinks to the new numbers along each axis
    example: {"axes": ["Item 1", "Item 2", "Item 3"], "series": [{"name": "Series 1", "values": [3, 2, 1]}]}
    since: next
  - emits: value
    when: release
    title: When you let go of the shape
    type: json
    says: the axis names and the first series' numbers, as JSON
    example: {"axes": ["Item 1", "Item 2", "Item 3"], "values": [3, 2, 1]}
    also: Only when editing is on; dragging a corner redraws the shape live and sends once on release
    since: next
  - sample: {"axes": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"], "series": [{"name": "Series 1", "values": [3, 2, 4, 1, 3]}]}
    next: {"axes": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"], "series": [{"name": "Series 1", "values": [4, 1, 2, 3, 4]}]}
fields:
  - name: haptic
    tab: action
    type: enum
    values: [none, light, medium, heavy, soft, rigid, selection, success, warning, error]
    description: Touch feedback on interaction (supported hardware)
    summary: The buzz you feel after an edit
    does: Plays this haptic on the phone when you let go of a dragged vertex; light if unset.
    valueHelp: {"none": "no vibration", "light": "a small soft tap", "medium": "a medium tap", "heavy": "a strong thud", "soft": "a gentle cushioned bump", "rigid": "a firm sharp click", "selection": "the faint tick of picking an item", "success": "the double tap of a success", "warning": "a two-pulse warning", "error": "a sharp triple buzz of an error"}
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Label under the chart
    summary: The caption under the chart
    does: Shows this text beneath the radar chart.
  - name: radarConfig
    type: object
    description: Full configuration object (see RadarConfig section)
    summary: All the chart's look and edit settings in one box
    does: Groups the chart options (rings, fill, labels, editing) that shape how the radar draws and behaves.
  - name: tint
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: First-series color and palette seed
    summary: The main color of the chart
    does: Colors the first series and seeds the palette the other series cycle through.
  - name: formatValue
    tab: data
    type: string
    description: Formatter for vertex values
    summary: How the numbers are written
    does: Formats the numeric value beside each vertex, e.g. as a whole number or a percent.
  - name: colors
    edit: list
    depth: hold
    under: tint
    title: Series colors
    tab: style
    type: string[]
    description: Series color cycle (per-series color wins)
    summary: The colors for each series
    does: Gives each series its own outline and fill color in turn; a series with its own color keeps it.
    group: radarConfig
  - name: curved
    edit: part
    depth: hold
    title: Curved edges
    type: bool
    default: false
    description: Rounded polygon instead of straight edges
    summary: Smooth or pointed shape
    does: Draws each series as a rounded shape instead of a polygon with straight edges.
    group: radarConfig
  - name: editable
    edit: switch
    title: Drag to edit
    depth: hold
    type: bool
    default: false
    description: Drag the **first** series' vertices along their axes
    summary: Drag the shape to change values
    does: Lets you drag the first series' vertices along their axes; releasing fires the action with every axis value.
    group: radarConfig
  - name: fillOpacity
    edit: scrub
    depth: surface
    title: Fill strength
    tab: style
    min: 0
    max: 1
    step: 0.05
    type: number
    default: 0.25
    description: Polygon fill opacity 0–1
    summary: How solid the filled shape is
    does: Sets how opaque the filled area inside each series outline is, from 0 (clear) to 1 (solid).
    group: radarConfig
  - name: glowRadius
    edit: scrub
    depth: hold
    under: fillOpacity
    title: Glow
    unit: pt
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    default: 0
    description: Soft glow behind each series outline in its own colour, in points (0 = none). Cross-control, same on every control
    summary: A soft halo around the outline
    does: Adds a glow behind each series outline in its own color, 0 (off) to 30 points wide.
  - name: lineCap
    edit: look
    depth: hold
    under: fillOpacity
    title: Line ends
    tab: style
    type: enum
    values: [round, butt, square]
    default: round
    description: "End shape of each series outline: it is a closed shape, so the cap sets its corners (round = round, square = sharp, butt = cut). Cross-control, same on every control"
    summary: The shape of the outline corners
    does: Rounds, cuts or sharpens the corners of each series outline.
    valueHelp: {"round": "soft rounded corners", "butt": "corners cut flat", "square": "sharp pointed corners"}
    valueTitles: {"round": "Round", "butt": "Flat", "square": "Pointed"}
    valueSymbols: {"round": "capsule.fill", "butt": "rectangle.fill", "square": "square.fill"}
  - name: maxValue
    chip: Radar
    bounds: none
    type: number
    description: Per-axis maximum (payload max wins)
    summary: The value at the outer edge
    does: Sets the value that reaches the rim on every axis; a max in the data overrides it.
    group: radarConfig
  - name: rings
    edit: scrub
    depth: surface
    title: Grid rings
    min: 1
    max: 12
    step: 1
    type: number
    default: 4
    description: Concentric grid rings
    summary: How many grid circles
    does: Draws this many concentric grid rings (1 to 12) to read values against.
    group: radarConfig
  - name: showAxisLabels
    edit: part
    depth: hold
    title: Axis labels
    type: bool
    default: true
    description: Axis names around the rim
    summary: Show the axis names
    does: Prints each axis name around the outside of the chart.
    group: radarConfig
  - name: showLegend
    edit: part
    depth: hold
    title: Legend
    type: bool
    default: false
    description: Series legend under the chart
    summary: Show a key for the series
    does: Adds a legend under the chart naming each series in its color.
    group: radarConfig
  - name: showPoints
    edit: part
    depth: hold
    title: Points
    type: bool
    default: true
    description: Vertex dots (always on while editing)
    summary: Show dots at the corners
    does: Draws a dot at each vertex of every series; dots always show while editing.
    group: radarConfig
  - name: showValues
    edit: part
    depth: hold
    title: Value labels
    type: bool
    default: false
    description: Numeric value beside each vertex (the dragged vertex always shows)
    summary: Show the numbers
    does: Prints each vertex's number beside it; the vertex you are dragging always shows its number.
    group: radarConfig
  - name: step
    bounds: none
    type: number
    description: Snap dragged values to this step (e.g. 1, 5, 0.1)
    summary: Jump size when dragging
    does: Snaps dragged values to multiples of this step, e.g. 5 or 0.1.
    group: radarConfig
themeFields:
  - use: cornerRadius
  - use: surfacePrimary
    summary: The colour behind the control
    does: Fills the radar chart background with this color.
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Heading and axis label color
    summary: Heading and axis label color
    does: Colors the heading and the axis labels on the radar chart.
  - use: accentColor
    summary: Highlight color
    does: Sets the accent color used to tint the radar chart when no tint is set.
  - use: borderColor
    summary: Outline color
    does: Colors the outline drawn around the radar chart.
  - use: borderWidth
    summary: Outline thickness
    does: Sets the outline width from 0 to 5 points.
  - use: controlPadding
    summary: Space inside the edges
    does: Adds padding between the radar chart edge and its content, 0 to 24 points.
  - use: foregroundColor
    summary: Main text color
    does: Colors the primary text on the radar chart.
  - use: labelFontSize
    summary: Label text size
    does: Sets the label text size from 8 to 24 points.
colorSlots:
  - slot: main
    default: primary
    alias: tint
    since: next
    summary: The radar's own primary color
    does: Colors the first series, and every primary entry of the series colors; until the layout picks a color it follows the primary role.
  - slot: series
    default: [primary, secondary, tertiary, "#FF6B6B", "#34C759", "#FF9500", "#4D96FF", "#BF5AF2"]
    since: next
    summary: The colors the series take in turn
    does: Gives series one, two, three and so on these colors in order unless the radar colors list is set, and a color on a series itself wins; secondary and tertiary join once a palette sets them.
---

# Radar

A spider/polygon profile chart: N axes radiate from center, each series draws one
filled polygon — device health across dimensions, fleet comparisons, character
stats. With `editable`, the first series' vertices **drag along their axes**,
turning the chart into a multi-parameter tuner (EQ bands, PID gains, mixer sends)
that fires one action carrying every axis value on release.

## Type
`"radar"`

## Recommended Size
Square cells — `[2, 2]` minimum, `[3, 3]` when axis labels are long. The control
keeps itself round.

## Relevant Fields
Inherits all [[control-def|shared fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Label under the chart |
| `radarConfig` | [[#RadarConfig]] | — | Full configuration object (all optional) |
| `tint` | string | `"#667eea"` | First-series color / palette seed |
| `glowRadius` | number | `0` | Soft glow behind each series outline in its own colour, 0–30 pt (the same attribute on every control that has it) |
| `lineCap` | enum | `round` | End shape of each series outline: it is a closed shape, so the cap sets its corners (round = round, square = sharp, butt = cut): `round`, `butt` or `square` (the same attribute on every control that has it) |
| `formatValue` | string | — | Formatter for vertex values |
| `action` | [[actions\|ActionDefinition]] | — | Fired on edit release; `{{value}}` = `{"axes": […], "values": […]}` JSON |

## RadarConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rings` | number | `4` | Concentric grid rings |
| `maxValue` | number | data max | Per-axis maximum (payload `max` wins) |
| `fillOpacity` | number | `0.25` | Polygon fill opacity 0–1 |
| `curved` | bool | `false` | Rounded polygon instead of straight edges |
| `showPoints` | bool | `true` | Vertex dots (always on while editing) |
| `showAxisLabels` | bool | `true` | Axis names around the rim |
| `showValues` | bool | `false` | Numeric value beside each vertex (the dragged vertex always shows) |
| `showLegend` | bool | `false` | Series legend under the chart |
| `colors` | string[] | built-in palette | Series color cycle (per-series `color` wins) |
| `editable` | bool | `false` | Drag the **first** series' vertices along their axes |
| `step` | number | — | Snap dragged values to this step (e.g. `1`, `5`, `0.1`) |

## Sync Payload Structure

Axes + one or more series — natural JSON or an encoded string:

```json
{
  "axes": ["Speed", "Range", "Torque", "Battery", "Thermals"],
  "max": 100,
  "series": [
    { "name": "Rover A", "color": "#667eea", "values": [80, 55, 70, 90, 62] },
    { "name": "Rover B", "color": "#FF9500", "values": [65, 82, 58, 74, 88] }
  ]
}
```

Shorthand: `{"axes": […], "values": […]}` renders one anonymous series.

### Series Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | no | Legend name |
| `color` | string | no | Series color (hex) |
| `values` | number[] | yes | One value per axis, in axis order |

## Examples

### Fleet comparison (two overlaid profiles)
```json
{
  "type": "radar",
  "id": "rover-compare",
  "position": [0, 0],
  "span": [3, 3],
  "label": "Rover profiles",
  "radarConfig": { "showLegend": true, "curved": true },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "fleet_stats" }, "valuePath": "radar" }]
}
```

### Multi-parameter tuner (editable EQ)
```json
{
  "type": "radar",
  "id": "eq-tuner",
  "position": [0, 0],
  "span": [3, 3],
  "label": "EQ bands",
  "radarConfig": { "editable": true, "step": 1, "showValues": true, "rings": 5 },
  "action": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "eq_set", "bands": "{{value}}" } },
  "defaultValue": "{\"axes\":[\"60Hz\",\"250Hz\",\"1kHz\",\"4kHz\",\"12kHz\"],\"max\":10,\"series\":[{\"values\":[5,6,5,4,6]}]}"
}
```

### Skill chart with glow
Demonstrates `curved`, `fillOpacity`, `glowRadius`, `lineCap`, `colors` and `showAxisLabels`: a smooth glowing shape with a custom series color.
```json
{
  "type": "radar",
  "id": "skills",
  "position": [0, 0],
  "span": [3, 3],
  "label": "Skills",
  "tint": "#00D4FF",
  "glowRadius": 10,
  "lineCap": "round",
  "haptic": "light",
  "radarConfig": { "curved": true, "fillOpacity": 0.4, "rings": 5, "maxValue": 10, "showAxisLabels": true, "showPoints": false, "colors": ["#00D4FF", "#FF9500"] },
  "defaultValue": "{\"axes\":[\"Speed\",\"Range\",\"Torque\",\"Grip\"],\"series\":[{\"values\":[8,5,7,6]}]}"
}
```

## Behavior
- Dataset pushes animate the polygons; series after the first draw underneath the editable one
- Editing: touch near an axis to grab its vertex, drag along the axis (values clamp to 0…max, snap to `step`), release fires the action with all values
- Edits update the control's stored dataset live, so state [[sync|readback]] returns the tuned values
- Needs at least 3 axes to render (it's a polygon)

## Notes
- For one value on one scale use [[gauge]]; radar earns its footprint at 3+ dimensions
- Keep axis counts ≤ 8 and labels short — the rim gets crowded fast
- Scale is shared across axes v1 (per-axis scales would make shapes lie)

## Related
- [[chart]] — cartesian series
- [[pie-chart]] — radial part-of-whole
- [[gauge]] — single-value radial
- [[joystick]] — 2-axis continuous input
- [[actions]] — how the edit action fires
- [[sync]] — how profiles arrive
