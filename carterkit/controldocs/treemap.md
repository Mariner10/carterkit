---
type: treemap
label: Treemap
icon: rectangle.3.group.fill
category: controls
depth: complete
defaultSpan: [3, 4]
addIntent: show
pickerCategory: Charts
friendlyName: Blocks
oneLiner: Sizes compared as blocks
aliases: [tree map, hierarchy, blocks, size, disk usage, proportion]
starterPreset: {"label": "Blocks"}
fields:
  - name: haptic
    tab: action
    type: enum
    values: [none, light, medium, heavy, soft, rigid, selection, success, warning, error]
    description: Touch feedback on interaction (supported hardware)
    summary: Buzz when you tap
    does: Plays this touch feedback when a cell is tapped; leave it empty for a light tap.
    valueHelp: {"none": "no feedback", "light": "a gentle tap", "medium": "a medium tap", "heavy": "a strong tap", "soft": "a cushioned tap", "rigid": "a sharp tap", "selection": "a tiny tick like scrolling a picker", "success": "a confirming pattern", "warning": "a cautioning pattern", "error": "a sharp error pattern"}
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label above the map
    summary: The title above the blocks
    does: Shows this text as the header, which becomes a back button while you are zoomed into a group.
  - name: treemapConfig
    type: object
    description: Full configuration object (see TreemapConfig section)
    summary: Extra block settings
    does: Holds the optional look and behavior settings for the blocks.
  - name: tint
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: First-item color and palette seed
    summary: The main block color
    does: Colors the first block and seeds the colors of the rest.
  - name: formatValue
    tab: data
    type: string
    description: Formatter for item values
    summary: How numbers are written
    does: Formats the values shown on blocks, for example with a unit after the number.
  - name: cellCornerRadius
    edit: scrub
    depth: hold
    under: cellGap
    title: Cell roundness
    unit: pt
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    default: 5
    description: Cell corner rounding
    summary: How round the blocks are
    does: Rounds each block's corners from square to 30 points.
    group: treemapConfig
  - name: cellGap
    edit: scrub
    depth: surface
    title: Cell spacing
    unit: pt
    tab: style
    min: 0
    max: 40
    step: 1
    type: number
    default: 2
    description: Gap between cells
    summary: The space between blocks
    does: Leaves this many points of gap between neighboring blocks.
    group: treemapConfig
  - name: colors
    edit: list
    depth: surface
    title: Cell colors
    tab: style
    type: string[]
    description: Item color cycle (per-item color wins)
    summary: Colors for the blocks
    does: Gives blocks colors from this list in turn; a color set on an item wins.
    group: treemapConfig
  - name: drillDown
    type: bool
    default: true
    description: Tap a parent to zoom into its children
    summary: Tap a group to open it
    does: When on, tapping a block with items inside zooms into it; when off, every tap acts as a pick.
    group: treemapConfig
  - name: itemAction
    tab: action
    type: object
    description: itemAction
    summary: What happens when you pick a block
    does: Runs this action when you tap a block with nothing inside, passing its label, value and path.
    group: treemapConfig
  - name: scrub
    type: bool
    default: false
    description: Drag highlights the cell under the finger with a live readout (no drilling/actions until a tap)
    summary: Slide a finger across the blocks
    does: When on, dragging highlights the block under your finger with a live readout, and only a tap drills in or acts.
    group: treemapConfig
  - name: showLabels
    edit: part
    depth: hold
    title: Labels
    type: bool
    default: true
    description: Item labels inside cells that have room
    summary: Names on the blocks
    does: Draws each block's name inside it where there is room.
    group: treemapConfig
  - name: showValues
    edit: part
    depth: hold
    title: Value labels
    type: bool
    default: false
    description: Value under the label (taller cells only)
    summary: Numbers on the blocks
    does: Draws each block's value under its name on blocks tall enough to fit.
    group: treemapConfig
themeFields:
  - use: cornerRadius
    summary: How round the corners are
    does: Rounds the control's corners from square to 30 points.
  - name: surfacePrimary
    title: Background color
    type: color
    default: #FFFFFF0F
    description: Background fill
    summary: The fill behind the blocks
    does: Paints the control's background in this color, including transparency.
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Value text color
    summary: The quieter text color
    does: Colors the value text on the blocks.
  - use: accentColor
    does: Tints the blocks wherever no color is set directly.
  - use: borderColor
    does: Draws the control's outline in this color.
  - use: borderWidth
    does: Sets the outline thickness from 0 to 5 points.
  - use: controlPadding
    summary: Space inside the edge
    does: Adds this much padding between the control's edge and the blocks.
  - use: foregroundColor
    does: Colors the block names and header text.
  - use: labelFontSize
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
    "itemAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "pick_category", "item": "{{value}}" } }
  },
  "defaultValue": "[{\"label\":\"Rent\",\"value\":1800},{\"label\":\"Food\",\"value\":600},{\"label\":\"Fun\",\"value\":250},{\"label\":\"Save\",\"value\":900}]"
}
```

### Colored blocks with a scrub readout
Sets your own block colors and lets a drag glide across cells. Intended effect: sliding a finger highlights each block with its value, without zooming in.
```json
{
  "type": "treemap",
  "id": "portfolio",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Portfolio",
  "treemapConfig": { "scrub": true, "showValues": true, "cellGap": 4, "colors": ["#667eea", "#f6ad55", "#48bb78"] },
  "defaultValue": "[{\"label\":\"Stocks\",\"value\":60},{\"label\":\"Bonds\",\"value\":25},{\"label\":\"Cash\",\"value\":15}]"
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
