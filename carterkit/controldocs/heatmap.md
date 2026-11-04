---
type: heatmap
depth: complete
label: Heatmap
icon: square.grid.3x3.fill
category: controls
defaultSpan: [3, 4]
addIntent: show
pickerCategory: Charts
friendlyName: Heat grid
oneLiner: Colored squares that show how much
aliases: [heat map, density, grid, intensity, matrix, calendar heatmap]
starterPreset: {"label": "Heat grid"}
fields:
  - name: haptic
    tab: action
    type: enum
    values: [none, light, medium, heavy, soft, rigid, selection, success, warning, error]
    description: Touch feedback on interaction (supported hardware)
    summary: "The buzz you feel on touch"
    does: "A tap on the phone gives a short vibration of the chosen strength; none is silent."
    valueHelp: {"none": "no vibration", "light": "a faint tap", "medium": "a medium tap", "heavy": "a strong thud", "soft": "a muffled cushioned tap", "rigid": "a sharp crisp tap", "selection": "a tiny tick like a picker moving", "success": "a happy double pulse", "warning": "a cautionary pulse", "error": "a harsh triple buzz"}
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label above the grid
    summary: "The caption above the grid"
    does: "Shows this text as the header above the grid in the title text size."
  - name: heatmapConfig
    type: object
    description: Full configuration object (see HeatmapConfig section)
    summary: "The grid's settings bundle"
    does: "Holds the cell look, labels, editing and calendar options below; leave it out for a plain read-only grid."
  - name: tint
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: Ramp/palette seed color
    summary: "The main color of the grid"
    does: "Colors the top of the default ramp or the palette accent when no scale colors are set."
  - name: formatValue
    tab: data
    type: string
    description: Formatter for scale/cell values
    summary: "How numbers are written"
    does: "Formats the scale legend and in-cell numbers, e.g. suffix:°C turns 24 into 24°C."
  - name: calendar
    tab: data
    type: bool
    default: false
    description: "Activity calendar: lay a day-keyed payload out as 7 weekday rows x week columns, zero-filled, month labels; tap a day to read it"
    summary: "A day-by-day activity calendar"
    does: "Lays day-keyed data out as 7 weekday rows by week columns with month labels; tapping a day shows its date and value."
    group: heatmapConfig
  - name: weekStartsOn
    tab: data
    type: enum
    values: [monday, sunday]
    description: "Calendar week start (default: the bound local source's weekStartsOn, else monday)"
    summary: "Which day starts each week"
    does: "Sets the top row of each calendar column to Monday or Sunday."
    valueHelp: {"monday": "weeks run Monday to Sunday", "sunday": "weeks run Sunday to Saturday"}
    group: heatmapConfig
  - name: weeks
    tab: data
    type: number
    min: 1
    max: 106
    step: 1
    description: Calendar shows only the most recent N weeks (default the whole span, up to 106)
    summary: "How many weeks the calendar shows"
    does: "Keeps only the most recent N weeks (1 to 106) and drops older ones."
    group: heatmapConfig
  - name: cellAction
    tab: action
    type: object
    description: cellAction
    summary: "What happens when you edit a cell"
    does: "Fires this action for every edit with {{value}} holding the row, column and new value as JSON."
    group: heatmapConfig
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
    default: 3
    description: Cell corner rounding (square cells only)
    summary: "How rounded each square is"
    does: "Rounds each square cell from sharp (0) to 30 points; circle cells ignore it."
    group: heatmapConfig
  - name: cellCorner
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    default: 3
    description: "Older name of cellCornerRadius; cellCornerRadius wins when both are set"
    summary: "Older name for cell roundness"
    does: "Rounds square cells from 0 to 30 points; cellCornerRadius wins when both are set."
    group: heatmapConfig
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
    summary: "The space between cells"
    does: "Sets the gap between neighbouring cells from 0 to 40 points."
    group: heatmapConfig
  - name: cellShape
    edit: look
    depth: hold
    under: cellGap
    title: Cell shape
    tab: style
    type: enum
    values: [square, circle]
    default: square
    description: square or circle (circle reads as dot-matrix/LED)
    summary: "Squares or dots"
    does: "Draws each cell as a rounded square or as a circle for a dot-matrix look."
    valueHelp: {"square": "rounded squares that tile the grid", "circle": "round dots like an LED matrix"}
    group: heatmapConfig
  - name: colors
    edit: list
    depth: surface
    title: Scale colors
    tab: style
    type: string[]
    description: "Continuous: 2+ gradient stops. Discrete: the palette (value = index)"
    summary: "The colors the cells use"
    does: "Continuous mode blends across these gradient stops (2 or more); stepped mode picks the color at each value's index."
    group: heatmapConfig
  - name: discrete
    edit: part
    depth: hold
    title: Stepped scale
    type: bool
    default: false
    description: Treat values as palette indices instead of a continuous range
    summary: "Fixed steps instead of a blend"
    does: "When on each value is a whole-number index into the colors list so cells show flat palette colors instead of a gradient."
    group: heatmapConfig
  - name: drag
    type: bool
    default: true
    description: Drag paints the first-touched cell's new value across cells
    summary: "Painting by dragging"
    does: "When on a drag copies the first-touched cell's new value across every cell the finger crosses; off limits edits to single taps."
    group: heatmapConfig
  - name: editable
    type: bool
    default: false
    description: "Tap cycles a cell (discrete: next palette index; continuous: 0 ↔ vMax toggle)"
    summary: "Lets you change the cells"
    does: "When on tapping a cell cycles it to the next palette color or toggles between 0 and the top value."
    group: heatmapConfig
  - name: sendMode
    tab: action
    type: string
    description: cell fires per change; matrix fires the whole dataset once an edit burst settles (~0.4s)
    summary: "How often edits are sent"
    does: "cell sends every change on its own while matrix waits about 0.4 seconds then sends the whole grid once."
    group: heatmapConfig
  - name: showColLabels
    edit: part
    depth: hold
    title: Column labels
    type: bool
    default: true
    description: Column labels along the top (when cols present; auto-thinned)
    summary: "Labels along the top"
    does: "Shows the column names above the grid and thins them out when space is tight."
    group: heatmapConfig
  - name: showRowLabels
    edit: part
    depth: hold
    title: Row labels
    type: bool
    default: true
    description: Row labels down the leading edge (when rows present)
    summary: "Labels down the side"
    does: "Shows the row names at the left edge of the grid."
    group: heatmapConfig
  - name: showScale
    edit: part
    depth: hold
    title: Scale legend
    type: bool
    default: false
    description: Gradient scale legend under the grid (continuous only)
    summary: "A key under the grid"
    does: "Adds a gradient legend beneath a continuous grid or a Less to More row in calendar mode."
    group: heatmapConfig
  - name: showValues
    edit: part
    depth: hold
    title: Value labels
    type: bool
    default: false
    description: Numeric value inside each cell (when cells are large enough)
    summary: "Numbers inside the cells"
    does: "Prints each cell's number on it when the cells are big enough to read."
    group: heatmapConfig
  - name: vMax
    bounds: none
    type: number
    description: Continuous color-scale bounds
    summary: "The value at the hottest color"
    does: "Sets the number that maps to the last scale color; larger values stay at that color."
    group: heatmapConfig
  - name: vMin
    bounds: none
    type: number
    description: Continuous color-scale bounds
    summary: "The value at the coolest color"
    does: "Sets the number that maps to the first scale color; smaller values stay at that color."
    group: heatmapConfig
themeFields:
  - name: cornerRadius
    title: Corner roundness
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
    summary: "How rounded the card corners are"
    does: "Rounds the control's outer corners from square (0) to 30 points."
  - name: surfacePrimary
    title: Background color
    type: color
    default: #FFFFFF0F
    description: Background fill
    summary: "The fill behind the grid"
    does: "Paints the control's background card in this color including transparency."
  - name: secondaryColor
    title: Label color
    type: color
    default: #FFFFFF99
    description: Label text color
    summary: "The color of labels"
    does: "Colors the header and axis label text in this color."
  - name: accentColor
    title: Accent color
    type: color
    default: #667eea
    description: Accent/tint color
    summary: "The theme's highlight color"
    does: "Tints the grid ramp wherever no color is set directly."
  - name: borderColor
    title: Border color
    type: color
    default: #FFFFFF1A
    description: Border color
    summary: "The outline color"
    does: "Draws the card's border line in this color."
  - name: borderWidth
    title: Border thickness
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
    summary: "How thick the outline is"
    does: "Sets the border from 0 (none) to 5 points."
  - name: controlPadding
    title: Inner spacing
    min: 0
    max: 24
    step: 1
    type: number
    default: 8
    description: Internal padding
    summary: "Breathing room inside the edge"
    does: "Adds 0 to 24 points between the card's edge and the grid."
  - name: foregroundColor
    title: Text color
    type: color
    default: #FFFFFF
    description: Primary text color
    summary: "The main text color"
    does: "Colors the primary text such as the title and in-cell numbers."
  - name: labelFontSize
    title: Title text size
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
    summary: "How big the title text is"
    does: "Sets the header label size from 8 to 24 points."
  - name: tertiaryColor
    title: Faint text color
    type: color
    default: #FFFFFF4D
    description: Tertiary text and ink color
    summary: "The faintest text color"
    does: "Colors the dimmest text and empty-cell ink in this color."
---

# Heatmap

A color-mapped matrix. In **continuous** mode values interpolate across a gradient
ramp — server-room temperatures, signal strength, an activity calendar. In
**discrete** mode each value is an index into a palette. Flip on `editable` and the
same grid becomes an input surface: tap cycles a cell, drag paints — a weekly
schedule programmer, an LED-matrix pixel editor, or a step sequencer, straight from
one flag.

## Type
`"heatmap"`

## Recommended Size
Wide: `[2, 4]` for a dashboard strip; taller for schedule grids (one row per day).

## Relevant Fields
Inherits all [[control-def|shared fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Header label |
| `heatmapConfig` | [[#HeatmapConfig]] | — | Full configuration object (all optional) |
| `tint` | string | `"#667eea"` | Default ramp top / palette accent |
| `formatValue` | string | — | Formatter for the scale legend and cell values |

## HeatmapConfig

### Color Mapping

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `colors` | string[] | tint ramp | Continuous: 2+ gradient stops. Discrete: the palette (value = index) |
| `discrete` | bool | `false` | Treat values as palette indices instead of a continuous range |
| `vMin` / `vMax` | number | data range | Continuous color-scale bounds |

### Cells

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `cellCornerRadius` | number | `3` | Cell corner rounding in points, 0–30 (square cells only) |
| `cellCorner` | number | `3` | Older name of `cellCornerRadius`; the newer key wins |
| `cellGap` | number | `2` | Gap between cells |
| `cellShape` | string | `"square"` | `square` or `circle` (circle reads as dot-matrix/LED) |

### Labels & Legend

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `showRowLabels` | bool | `true` | Row labels down the leading edge (when `rows` present) |
| `showColLabels` | bool | `true` | Column labels along the top (when `cols` present; auto-thinned) |
| `showScale` | bool | `false` | Gradient scale legend under the grid (continuous only) |
| `showValues` | bool | `false` | Numeric value inside each cell (when cells are large enough) |

### Editing

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `editable` | bool | `false` | Tap cycles a cell (discrete: next palette index; continuous: 0 ↔ vMax toggle) |
| `drag` | bool | `true` | Drag paints the first-touched cell's new value across cells |
| `cellAction` | [[actions\|ActionDefinition]] | — | Fired per edit; `{{value}}` = `{"row", "col", "value"}` JSON |
| `sendMode` | string | `"cell"` | `cell` fires per change; `matrix` fires the whole dataset once an edit burst settles (~0.4s) |

If `cellAction` is omitted, edits fall back to the control's own `action`.

### Calendar

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `calendar` | bool | `false` | Activity calendar (GitHub style): a day-keyed payload laid out as 7 weekday rows × week columns |
| `weekStartsOn` | string | source's, else `"monday"` | `"monday"` or `"sunday"`: the top row of each column |
| `weeks` | number | whole span (max 106) | Show only the most recent N weeks |

Calendar mode reads a **day-keyed** payload instead of a matrix, so a local store
feeds it directly with `groupBy {…, bucket: "day"}` (the groups shape
`{categories, series, rows:[{key, value}]}`). A bare `{"2026-01-03": 2, …}` object
or `[{"date": "2026-01-03", "value": 2}, …]` also works; date-time keys use their
first 10 characters, non-date keys (the `null` bucket) are skipped, duplicates add up.

- Days run from the first key to the last, **zero-filled**; slots before the first
  day and after the last day in their week stay blank.
- Cells are square. When the span does not fit the width (8pt minimum cells), the
  **oldest weeks drop off**; the most recent day is always shown.
- Month labels sit over the week holding the 1st; weekday labels on rows 2, 4, 6.
- Color: a day at or below `vMin` (default 0) gets the empty color (`colors[0]`, else a
  faint neutral); others ramp across `colors[1…]` (default the tint) up to `vMax`
  (default the busiest day). `showScale` adds a "Less … More" swatch row.
- Tap a day to show its date and value beside the label; tap again to clear.
  Calendar mode is read-only (`editable` is ignored). VoiceOver reads a summary
  ("41 active days from … to …, most on …").

Reading days from a book log (every day between `started` and `finished`):

```json
{
  "type": "heatmap", "id": "reading-days", "label": "Reading days",
  "heatmapConfig": { "calendar": true },
  "sync": [{ "method": "local", "collection": "books",
             "groupBy": { "range": ["started", "finished"], "bucket": "day" } }]
}
```

## Sync Payload Structure

A dense matrix plus optional axis labels — natural JSON or an encoded string.
`{"values": [[…]]}` with labels, or a bare `[[…]]` array of rows:

```json
{
  "rows": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
  "cols": ["00", "03", "06", "09", "12", "15", "18", "21"],
  "values": [
    [0, 0, 1, 3, 3, 2, 1, 0],
    [0, 0, 1, 3, 3, 2, 1, 0],
    [0, 0, 2, 3, 3, 3, 2, 1],
    [0, 0, 1, 3, 3, 2, 1, 0],
    [0, 0, 1, 2, 3, 3, 3, 2],
    [1, 0, 0, 1, 2, 3, 3, 2],
    [1, 0, 0, 1, 2, 2, 1, 0]
  ]
}
```

## Examples

### Continuous telemetry heatmap
Demonstrates a read-only continuous ramp with `showScale`, `vMin`/`vMax` and `formatValue`: hot cells glow orange to red and a legend runs under the grid, fed live over MeshSocket.
```json
{
  "type": "heatmap",
  "id": "rack-temps",
  "defaultValue": "{\"rows\":[\"Mon\",\"Tue\",\"Wed\"],\"cols\":[\"00\",\"06\",\"12\",\"18\"],\"values\":[[24,31,62,45],[28,55,81,49],[22,38,74,68]]}",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Rack temperatures",
  "formatValue": "suffix:°C",
  "heatmapConfig": { "colors": ["#1B2845", "#667eea", "#FF9500", "#FF6B6B"], "showScale": true, "vMin": 20, "vMax": 90 },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "rack_temps" }, "valuePath": "grid" }]
}
```

### Weekly schedule programmer (editable, discrete)
Demonstrates `editable` with `discrete` and `sendMode: matrix`: tapping or dragging recolors hours as off, comfort or boost, and the whole week is sent once edits pause.
```json
{
  "type": "heatmap",
  "id": "thermostat-schedule",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Heating schedule",
  "heatmapConfig": {
    "discrete": true,
    "colors": ["#FFFFFF14", "#667eea", "#FF9500"],
    "editable": true,
    "sendMode": "matrix",
    "cellAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "schedule_set", "schedule": "{{value}}" } }
  },
  "defaultValue": "{\"rows\":[\"Mon\",\"Tue\",\"Wed\",\"Thu\",\"Fri\",\"Sat\",\"Sun\"],\"cols\":[\"6\",\"9\",\"12\",\"15\",\"18\",\"21\"],\"values\":[[0,1,0,0,1,1],[0,1,0,0,1,1],[0,1,0,0,1,1],[0,1,0,0,1,1],[0,1,0,0,1,2],[1,1,1,1,1,2],[1,1,1,1,1,0]]}"
}
```

### LED matrix pixel editor
Demonstrates `cellShape: circle` with `cellAction` firing per cell: each tap cycles a dot through five colors and sends that one pixel.
```json
{
  "type": "heatmap",
  "id": "led-editor",
  "position": [0, 0],
  "span": [4, 4],
  "label": "LED panel",
  "heatmapConfig": {
    "discrete": true,
    "colors": ["#1A1A1A", "#FF3B30", "#34C759", "#007AFF", "#FFCC00"],
    "cellShape": "circle",
    "cellGap": 3,
    "editable": true,
    "cellAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "led_set", "pixel": "{{value}}" } }
  },
  "defaultValue": "[[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]]"
}
```

### Activity calendar (day-keyed)
Demonstrates `calendar` mode with `weekStartsOn` and `showScale`: day-keyed counts become a week-by-week grid where tapping a day reads its date and value.
```json
{
  "type": "heatmap",
  "id": "reading-calendar",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Reading days",
  "heatmapConfig": { "calendar": true, "weekStartsOn": "monday", "showScale": true },
  "defaultValue": "{\"2026-01-03\":1,\"2026-01-04\":1,\"2026-01-05\":2,\"2026-01-06\":2,\"2026-02-27\":1,\"2026-02-28\":1,\"2026-03-01\":1,\"2026-03-02\":1,\"2026-03-13\":1,\"2026-03-14\":1,\"2026-03-15\":1}"
}
```

### Recent weeks with values in cells
Demonstrates `weeks`, `showValues` and `formatValue`: the calendar keeps only the latest 8 weeks and cell numbers are written with a unit.
```json
{
  "type": "heatmap",
  "id": "recent-steps",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Recent activity",
  "formatValue": "suffix: km",
  "heatmapConfig": { "calendar": true, "weeks": 8, "showValues": true, "cellCornerRadius": 6, "cellGap": 3 },
  "defaultValue": "{\"2026-10-12\":3,\"2026-10-13\":5,\"2026-10-20\":2,\"2026-11-01\":8,\"2026-11-02\":4}"
}
```

### Tap-only tick board (drag off, per-cell sends)
Demonstrates `drag: false` and `sendMode: cell`: each tap toggles one square between 0 and the top value and sends just that cell.
```json
{
  "type": "heatmap",
  "id": "habit-board",
  "position": [0, 0],
  "span": [3, 3],
  "label": "Habits",
  "heatmapConfig": {
    "editable": true,
    "drag": false,
    "sendMode": "cell",
    "vMin": 0,
    "vMax": 1,
    "colors": ["#1B2845", "#34C759"],
    "showRowLabels": true,
    "showColLabels": true,
    "cellAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "habit_set", "cell": "{{value}}" } }
  },
  "defaultValue": "{\"rows\":[\"Read\",\"Walk\",\"Stretch\"],\"cols\":[\"Mon\",\"Tue\",\"Wed\",\"Thu\"],\"values\":[[1,0,1,1],[0,0,1,0],[1,1,0,0]]}"
}
```

## Behavior
- Dataset pushes animate cell colors; edits render instantly (a local draft holds until the next push)
- Tap cycles: discrete `(value + 1) % palette.count`, continuous `0 ↔ vMax`
- Dragging paints the brush value chosen by the first cell touched — fill a row in one stroke
- Every cell change ticks a selection haptic and updates the control's stored dataset, so state [[sync|readback]] returns the edited grid
- `sendMode: "matrix"` batches an edit burst into a single dataset-sized action — ideal for schedule saves

## Notes
- `calendar`, `weekStartsOn` and `weeks` change nothing in a plain matrix grid; `editable`, `drag` and `sendMode` change nothing in calendar mode (read-only); `showScale` and `cellShape` apply as described above.
- Ragged rows render (short rows read as 0) and are padded rectangular on first edit
- A GitHub-style activity calendar is `calendar: true` fed by day keys (see Calendar); the app builds the 7-row × week grid
- A step sequencer is an editable discrete grid where the server plays column-by-column

## Related
- [[chart]] — cartesian series
- [[list]] — tabular rows
- [[color-picker]] — free-form color input
- [[actions]] — how `cellAction` fires
- [[sync]] — how the matrix arrives
