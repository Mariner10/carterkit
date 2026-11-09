---
type: chart
depth: complete
label: Chart
icon: chart.bar.xaxis
category: controls
defaultSpan: [3, 4]
addIntent: show
pickerCategory: Charts
friendlyName: Chart
oneLiner: Lines or bars over time
aliases: [graph, plot, line chart, bar chart, trend, timeline]
starterPreset: {"label": "Chart", "defaultValue": "{\"categories\":[\"Mon\",\"Tue\",\"Wed\",\"Thu\"],\"series\":[{\"name\":\"Series 1\",\"values\":[3,5,2,6]}]}"}
io:
  - receives: series
    role: show
    type: json
    shape: {"categories": ["text?"], "series": [{"name": "text?", "type": "line|bar|area|scatter|histogram|waterfall?", "color": "hex?", "values": ["number?"], "points": [{"x": "number", "y": "number"}]}]}
    from: [hub, mqtt, http, store, default]
    says: "series: a list of numbers (or x and y points) each, with optional category names"
    reacts: the lines and bars redraw to the new numbers; a missing number leaves a gap
    example: {"categories": ["Item 1", "Item 2", "Item 3"], "series": [{"name": "Series 1", "values": [1, 3, 2]}]}
    since: next
  - emits: datum
    when: tap
    title: When you tap a bar or point
    field: chartConfig.datumAction
    fallback: action
    type: json
    says: the tapped bar or point, as JSON with its series, category, index and numbers
    example: {"index": 1, "y": 3, "series": "Series 1", "category": "Item 2"}
    since: next
  - sample: {"categories": ["Item 1", "Item 2", "Item 3"], "series": [{"name": "Series 1", "values": [1, 3, 2]}]}
    next: {"categories": ["Item 1", "Item 2", "Item 3"], "series": [{"name": "Series 1", "values": [3, 1, 2]}]}
fields:
  - name: haptic
    tab: action
    type: enum
    values: [none, light, medium, heavy, soft, rigid, selection, success, warning, error]
    description: Touch feedback on interaction (supported hardware)
    summary: "The tap buzz on the phone"
    does: "Plays a vibration of the chosen strength when someone touches the chart on supported phones."
    valueHelp: {"none": "no vibration", "light": "a faint tap", "medium": "a clear tap", "heavy": "a strong thump", "soft": "a muffled cushioned tap", "rigid": "a sharp crisp tap", "selection": "the tiny tick used for scrolling pickers", "success": "a short double pulse for good news", "warning": "a firm pulse for caution", "error": "a harsh triple pulse for failure"}
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label above the chart
    summary: "The heading above the plot"
    does: "Shows this text at the top left of the chart; the selected reading appears beside it."
  - name: chartConfig
    type: object
    description: Full configuration object (see ChartConfig section)
    summary: "All the look and behavior settings in one bundle"
    does: "Groups the axis, series, streaming and tap options below; any entry left out uses its default."
  - name: tint
    edit: color
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: First-series color and palette seed
    summary: "The main color of the chart"
    does: "Colors the first series and seeds the colors of the rest, as any hex color."
  - name: formatValue
    tab: data
    type: string
    description: Formatter for axis/readout numbers (see control-def)
    summary: "How numbers are written on the axis and readout"
    does: "Formats the axis labels and the selection readout, for example with units or fixed decimals."
  - name: barCornerRadius
    edit: scrub
    depth: hold
    under: lineWidth
    title: Bar roundness
    unit: pt
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    default: 3
    description: Bar corner rounding
    summary: "How round the bar tops are"
    does: "Rounds the corners of every bar from square (0) to 30 points."
    group: chartConfig
  - name: defaultType
    edit: look
    title: Chart type
    tab: style
    type: enum
    values: [bar, line, area, scatter, histogram, waterfall]
    default: bar
    description: Drawing type for every series that sets no type of its own
    summary: "Bars, line or area for the whole chart"
    does: "Draws each series that has no type of its own as this kind; a series with its own type keeps it."
    valueHelp: {"bar": "vertical bars", "line": "a line joining the points", "area": "a line with the space beneath it filled", "scatter": "loose dots at x and y positions", "histogram": "raw samples grouped into frequency bars", "waterfall": "bars that step up and down from a running level"}
    valueTitles: {"bar": "Bar", "line": "Line", "area": "Area", "scatter": "Scatter", "histogram": "Histogram", "waterfall": "Waterfall"}
    valueSymbols: {"bar": "chart.bar.fill", "line": "chart.xyaxis.line", "area": "chart.line.uptrend.xyaxis", "scatter": "circle.grid.2x2.fill", "histogram": "chart.bar.xaxis", "waterfall": "chart.bar.doc.horizontal"}
    since: next
    group: chartConfig
  - name: bins
    edit: scrub
    depth: ai
    title: Histogram bins
    min: 1
    max: 50
    step: 1
    type: number
    description: Bin count for histogram series
    summary: "How many buckets a histogram has"
    does: "Splits the histogram samples into 1 to 50 bars; left unset it uses about the square root of the sample count."
    group: chartConfig
  - name: colors
    edit: list
    depth: hold
    under: tint
    title: Series colors
    tab: style
    type: string[]
    description: Series color cycle (per-series color wins)
    summary: "The colors the series take in turn"
    does: "Gives series one, two, three and so on these hex colors in order; a color set on a series itself wins."
    group: chartConfig
  - name: datumAction
    tab: action
    type: object
    description: datumAction
    summary: "What happens when a bar or point is tapped"
    does: "Runs this action on tap with the tapped datum as JSON in the value placeholder."
    group: chartConfig
  - name: horizontal
    edit: switch
    title: Horizontal bars
    depth: hold
    category: behaviour
    type: bool
    default: false
    description: Horizontal bars — categories run down the leading edge
    summary: "Bars lying sideways"
    does: "Turns the bars to run left to right with the categories listed down the left edge."
    group: chartConfig
  - name: lineWidth
    edit: scrub
    unit: pt
    title: Line width
    tab: style
    min: 0.5
    max: 12
    step: 0.5
    type: number
    default: 2
    description: Line/area stroke width
    summary: "How thick the lines are"
    does: "Sets the stroke of line and area series from 0.5 to 12 points."
    group: chartConfig
  - name: glowRadius
    edit: scrub
    depth: hold
    under: lineWidth
    title: Glow
    unit: pt
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    default: 0
    description: Soft glow behind bars, lines and points in their own colours, in points (0 = none). Cross-control, same on every control
    summary: "A soft halo around bars lines and points"
    does: "Adds a glow behind the marks in their own colors, 0 (off) to 30 points wide."
  - name: lineCap
    edit: look
    depth: hold
    under: lineWidth
    title: Line ends
    tab: style
    type: enum
    values: [round, butt, square]
    default: round
    description: End shape of the lines. Cross-control, same on every control
    summary: "The shape of the line ends"
    does: "Rounds, flattens or squares the ends of line strokes."
    valueHelp: {"round": "soft half-circle ends", "butt": "flat ends cut exactly at the last point", "square": "flat ends that extend a little past the last point"}
    valueTitles: {"round": "Round", "butt": "Flat", "square": "Square"}
    valueSymbols: {"round": "capsule.fill", "butt": "rectangle.fill", "square": "square.fill"}
  - name: maxPoints
    edit: scrub
    depth: ai
    title: Time window
    min: 10
    max: 1000
    step: 10
    type: number
    default: 100
    description: "Rolling window applied to {'append': …} pushes"
    summary: "How many recent points are kept"
    does: "Caps a streaming series at 10 to 1000 points so the oldest drop off as new ones are appended."
    group: chartConfig
  - name: negativeColor
    tab: style
    type: color
    description: Falling waterfall delta
    summary: "The color of falling steps in a waterfall"
    does: "Paints waterfall bars with a negative change in this color instead of system red."
    group: chartConfig
  - name: pointSize
    edit: scrub
    depth: hold
    under: lineWidth
    title: Point size
    tab: style
    min: 2
    max: 20
    step: 1
    type: number
    default: 6
    description: Scatter point / vertex dot diameter
    summary: "How big the dots are"
    does: "Sets the diameter of scatter points and line vertex dots from 2 to 20 points."
    group: chartConfig
  - name: positiveColor
    tab: style
    type: color
    description: Rising waterfall delta
    summary: "The color of rising steps in a waterfall"
    does: "Paints waterfall bars with a positive change in this color instead of system green."
    group: chartConfig
  - name: scrub
    effect: behavior
    edit: switch
    title: Touch to read values
    depth: hold
    type: bool
    default: false
    description: Drag shows a dashed crosshair + live readout (with a selection tick)
    summary: "Drag your finger along the chart to read values"
    does: "When on, dragging shows a dashed crosshair and a live readout with a tick at each point instead of tap selection."
    group: chartConfig
  - name: showGrid
    edit: part
    depth: hold
    title: Grid
    type: bool
    default: true
    description: Horizontal grid lines
    summary: "The faint guide lines behind the plot"
    does: "Shows or hides the horizontal grid lines across the plot."
    group: chartConfig
  - name: showLegend
    edit: part
    depth: hold
    title: Legend
    type: bool
    default: false
    description: Series legend under the plot
    summary: "A key naming each series"
    does: "Shows or hides a row under the plot listing every series with its color."
    group: chartConfig
  - name: showValues
    edit: part
    depth: hold
    title: Value labels
    type: bool
    default: false
    description: Numeric value above each bar / on each vertex
    summary: "Numbers printed on the marks"
    does: "Prints each value above its bar or on its line vertex when on."
    group: chartConfig
  - name: showXAxis
    edit: part
    depth: hold
    title: X axis
    type: bool
    default: true
    description: Category/x labels along the bottom (leading edge when horizontal)
    summary: "The labels along the bottom"
    does: "Shows or hides the category labels along the bottom (down the left edge for horizontal bars)."
    group: chartConfig
  - name: showYAxis
    edit: part
    depth: hold
    title: Y axis
    type: bool
    default: true
    description: Value labels down the left gutter
    summary: "The number scale on the left"
    does: "Shows or hides the value labels in the left gutter."
    group: chartConfig
  - name: smooth
    edit: part
    depth: hold
    title: Smoothing
    type: bool
    default: false
    description: Catmull-Rom curve smoothing for line/area series
    summary: "Curved instead of angular lines"
    does: "Draws line and area series as smooth curves rather than straight segments."
    group: chartConfig
  - name: stacked
    edit: switch
    title: Stack the series
    depth: hold
    category: behaviour
    type: bool
    default: false
    description: Stack bar/area series instead of grouping/overlaying
    summary: "Piling series on top of each other"
    does: "Stacks bar and area series so they add up, instead of sitting side by side or overlapping."
    group: chartConfig
  - name: totalColor
    tab: style
    type: color
    description: Waterfall running-total bars
    summary: "The color of the running-total bars in a waterfall"
    does: "Paints waterfall total bars in this color instead of the series color."
    group: chartConfig
  - name: yMax
    edit: scrub
    depth: hold
    under: lineWidth
    title: Axis top
    bounds: none
    type: number
    description: Pin the value axis (bars baseline at 0 by default)
    summary: "The top of the value scale"
    does: "Fixes the highest value on the vertical axis instead of fitting the data."
    group: chartConfig
  - name: yMin
    chip: Chart
    edit: scrub
    depth: hold
    under: lineWidth
    title: Axis bottom
    bounds: none
    type: number
    description: Pin the value axis (bars baseline at 0 by default)
    summary: "The bottom of the value scale"
    does: "Fixes the lowest value on the vertical axis instead of fitting the data."
    group: chartConfig
  - name: name
    group: data.series
    type: string
    description: Legend name and append routing key
    summary: "The series name"
    does: "Labels the series in the legend and is the key a streamed append uses to find it."
  - name: type
    category: look
    group: data.series
    values: [bar, line, area, scatter, histogram, waterfall]
    default: bar
    type: enum
    description: Series drawing type, matched by a switch in CARChart (anything else draws as bar); mix bar, line, area and scatter freely
    summary: "What kind of marks a series draws"
    does: "Draws that series as bars, a line, a filled area, dots, binned bars or a waterfall; series of different kinds share one chart."
    valueHelp: {"bar": "vertical bars", "line": "a line joining the points", "area": "a line with the space beneath it filled", "scatter": "loose dots at x and y positions", "histogram": "raw samples grouped into frequency bars", "waterfall": "bars that step up and down from a running level"}
    valueTitles: {"bar": "Bar", "line": "Line", "area": "Area", "scatter": "Scatter", "histogram": "Histogram", "waterfall": "Waterfall"}
    valueSymbols: {"bar": "chart.bar.fill", "line": "chart.xyaxis.line", "area": "chart.line.uptrend.xyaxis", "scatter": "circle.grid.2x2.fill", "histogram": "chart.bar.xaxis", "waterfall": "chart.bar.doc.horizontal"}
  - name: color
    group: data.series
    type: color
    description: Series colour (hex); wins over chartConfig.colors
    summary: "The color of one series"
    does: "Paints that series in this hex color, overriding the color list."
  - name: values
    group: data.series
    type: number[]
    description: Y values at implicit x = 0, 1, 2 (aligned with categories); null is a gap. Histogram - raw samples to bin; waterfall - signed deltas
    summary: "The numbers to plot"
    does: "Gives the height at each position in order lined up with the categories; null leaves a gap."
  - name: points
    group: data.series
    type: array
    description: Explicit [x, y] pairs for scatter or unevenly sampled series
    summary: "Exact x and y positions"
    does: "Places each mark at its own x and y pair, for scatter or unevenly spaced data."
  - name: sizes
    group: data.series
    type: number[]
    description: Per-point size multipliers (bubble scatter)
    summary: "Dot sizes for a bubble plot"
    does: "Scales each scatter dot by the matching multiplier, so 2 draws twice the normal size."
  - name: totals
    group: data.series
    type: number[]
    description: "Waterfall only: indices drawn as running totals from zero"
    summary: "Which waterfall steps are totals"
    does: "Draws the bars at these positions as running totals from zero instead of changes."
themeFields:
  - use: cornerRadius
    does: "Rounds the chart card corners from square (0) to 30 points."
  - use: controlPadding
    does: "Adds 0 to 24 points between the card edge and the plot."
  - use: surfacePrimary
    summary: "The fill behind the plot"
    does: "Paints the chart card background in this color including transparency."
  - use: secondaryColor
    summary: "The color of the heading and axis labels"
    does: "Colors the heading, the selection readout and the axis labels in this softer color."
  - use: labelFontSize
    summary: "The size of the labels"
    does: "Sets the heading text from 8 to 24 points; the axis labels use a fixed small font and ignore it."
  - use: accentColor
    summary: "The theme highlight"
    does: "Colors the first series and selection highlights when no tint is set."
  - use: borderColor
    summary: "The outline color"
    does: "Draws the card outline in this color."
  - use: borderWidth
    summary: "How heavy the outline is"
    does: "Sets the card outline from none (0) to 5 points."
  - use: foregroundColor
    does: "Colors the heading and the selection readout."
  - use: tertiaryColor
    summary: "The faintest ink"
    does: "Colors the grid lines and the least prominent text."
colorSlots:
  - slot: main
    default: primary
    alias: tint
    since: next
    summary: The chart's own primary color
    does: Colors the first series, and every primary entry of the series colors; until the layout picks a color it follows the primary role.
  - slot: series
    default: [primary, secondary, tertiary, "#34C759", "#FF9500", "#FF6B6B", "#4D96FF", "#BF5AF2", "#FFD93D"]
    since: next
    summary: The colors the series take in turn
    does: Gives series one, two, three and so on these colors in order unless the series colors list is set, and a color on a series itself wins; secondary and tertiary join once a palette sets them.
  - slot: positive
    default: "#34C759"
    alias: chartConfig.positiveColor
    since: next
    summary: The color of a waterfall rise
    does: Colors the waterfall bars that go up; until set it is green, whatever the palette.
  - slot: negative
    default: "#FF6B6B"
    alias: chartConfig.negativeColor
    since: next
    summary: The color of a waterfall fall
    does: Colors the waterfall bars that go down; until set it is a soft red, whatever the palette.
  - slot: total
    default: primary
    alias: chartConfig.totalColor
    since: next
    summary: The color of a waterfall total
    does: Colors the waterfall's total bars; until set they take their series' color.
---

# Chart

The cartesian workhorse: **bar**, **line**, **area**, **scatter**, **histogram**,
and **waterfall** series on one canvas — grouped or stacked, vertical or
horizontal, straight or smoothed. Datasets push over [[sync]] as natural JSON and
every datum is tappable, so a bar chart can double as a live voting panel, a
queue selector, or a preset picker. Histogram series bin raw samples client-side;
waterfall series accumulate signed deltas with hand-off connectors.

## Type
`"chart"`

## Recommended Size
Plots read best wide: `[3, 4]` or larger. In a flow grid the chart auto-sizes to a
16:10 landscape cell.

## Relevant Fields
Inherits all [[control-def|shared fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Header label (the live selection readout appears beside it) |
| `chartConfig` | [[#ChartConfig]] | — | Full configuration object (all optional) |
| `tint` | string | `"#667eea"` | First-series color / palette seed |
| `glowRadius` | number | `0` | Soft glow behind bars, lines and points in their own colours, 0–30 pt (the same attribute on every control that has it) |
| `lineCap` | enum | `round` | End shape of the lines: `round`, `butt` or `square` (the same attribute on every control that has it) |
| `formatValue` | string | — | Formatter for axis + readout numbers |

## ChartConfig

All fields optional with sensible defaults.

### Axes & Chrome

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `showXAxis` | bool | `true` | Category/x labels along the bottom (leading edge when `horizontal`) |
| `showYAxis` | bool | `true` | Value labels down the left gutter |
| `showGrid` | bool | `true` | Horizontal grid lines |
| `showLegend` | bool | `false` | Series legend under the plot |
| `showValues` | bool | `false` | Numeric value above each bar / on each vertex |
| `yMin` / `yMax` | number | data range | Pin the value axis (bars baseline at 0 by default) |

### Series Presentation

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `stacked` | bool | `false` | Stack bar/area series instead of grouping/overlaying |
| `horizontal` | bool | `false` | Horizontal bars — categories run down the leading edge |
| `smooth` | bool | `false` | Catmull-Rom curve smoothing for line/area series |
| `barCornerRadius` | number | `3` | Bar corner rounding |
| `lineWidth` | number | `2` | Line/area stroke width |
| `pointSize` | number | `6` | Scatter point / vertex dot diameter |
| `colors` | string[] | built-in palette | Series color cycle (per-series `color` wins) |

### Streaming

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `maxPoints` | number | `100` | Rolling window applied to `{"append": …}` pushes |

### Statistical Series

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `bins` | number | √n (5–20) | Bin count for `histogram` series |
| `positiveColor` | string | system green | Rising waterfall delta |
| `negativeColor` | string | system red | Falling waterfall delta |
| `totalColor` | string | series color | Waterfall running-total bars |

### Interaction

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `datumAction` | [[actions\|ActionDefinition]] | — | Fired when a bar/point is tapped; `{{value}}` = the datum as JSON `{"series", "category", "index", "x", "y"}` |
| `scrub` | bool | `false` | Drag shows a dashed crosshair + live readout (with a selection tick) |

If `datumAction` is omitted, a tap falls back to the control's own `action`.

## Sync Payload Structure

The chart receives its dataset via [[sync]]. The payload can be a **natural JSON
object** (no string-encoding needed) or an encoded string — both work:

```json
{
  "categories": ["Mon", "Tue", "Wed", "Thu", "Fri"],
  "series": [
    { "name": "CPU", "type": "line", "color": "#667eea", "values": [42, 51, 38, 66, 47] },
    { "name": "Jobs", "type": "bar", "values": [4, 7, 2, 9, 5] }
  ]
}
```

Shorthands: `{"values": [1, 2, 3]}` or a bare `[1, 2, 3]` render one anonymous series.

### Series Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | no | Legend name + `append` routing key |
| `type` | string | no | `bar` (default), `line`, `area`, `scatter`, `histogram`, `waterfall` — mix the cartesian four freely |
| `color` | string | no | Series color (hex) |
| `values` | number[] | no* | Y values at implicit x = 0, 1, 2, … (aligned with `categories`); a `null` is a gap (no bar or point; a line bridges it). For `histogram`: the **raw samples** to bin. For `waterfall`: the **signed deltas** |
| `points` | [x, y][] | no* | Explicit pairs for scatter / unevenly sampled series |
| `sizes` | number[] | no | Per-point size multipliers (bubble scatter) |
| `totals` | number[] | no | Waterfall only: indices drawn as running totals from zero (their value is ignored) |

*One of `values` or `points` per series.

### Histogram & Waterfall

```json
{ "series": [ { "type": "histogram", "values": [42.1, 38.9, 44.6, 51.2, 40.3] } ] }
```
The chart bins the samples (`chartConfig.bins`, default √n) into contiguous bars;
tap payloads carry `{"binStart", "binEnd", "count"}`.

```json
{ "categories": ["Start", "Sales", "Refunds", "Costs", "Net"],
  "series": [ { "type": "waterfall", "values": [1200, 480, -160, -390, 0], "totals": [0, 4] } ] }
```
Deltas step from each running level with dashed connectors; `totals` indices
render as full bars from zero — with value `0` they checkpoint the running
level (a "Net" bar), with a nonzero value they anchor it (an opening balance,
as with `Start` above). Tap payloads carry `{"delta"|"total", "level"}`.
Both are single-series statisticals — give each its own chart rather than mixing
them with other series types.

### Streaming Append

Servers streaming one reading per tick don't resend history — push an append op
and the device merges it into the stored dataset, trimmed to `maxPoints`:

```json
{ "append": { "CPU": 63.2, "GPU": 41.0 }, "category": "12:05" }
```

Forms: `{"CPU": 63.2}` (per-series by name — unknown names create new series),
`[63.2, 41.0]` (positional), or a bare number (first series). The optional
`category` string appends an x label alongside.

## Examples

### Live multi-series telemetry
```json
{
  "type": "chart",
  "id": "cpu-chart",
  "position": [0, 0],
  "span": [3, 4],
  "label": "CPU / GPU",
  "chartConfig": { "showLegend": true, "smooth": true, "maxPoints": 60 },
  "defaultValue": "{\"series\":[{\"name\":\"CPU\",\"type\":\"area\",\"values\":[42,51,38,64,55]},{\"name\":\"GPU\",\"type\":\"line\",\"values\":[20,34,28,41,36]}]}",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "telemetry" }, "valuePath": "chart" }]
}
```

### Tappable bar chart (voting panel)
```json
{
  "type": "chart",
  "id": "poll",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Vote for lunch",
  "chartConfig": {
    "showValues": true,
    "barCornerRadius": 6,
    "datumAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "vote", "choice": "{{value}}" } }
  },
  "defaultValue": "{\"categories\":[\"Pizza\",\"Sushi\",\"Tacos\"],\"series\":[{\"values\":[3,5,2]}]}",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "poll_update" }, "valuePath": "results" }]
}
```

### Static horizontal bars
```json
{
  "type": "chart",
  "id": "storage",
  "position": [0, 0],
  "span": [2, 4],
  "label": "Storage by volume",
  "chartConfig": { "horizontal": true, "showValues": true, "showGrid": false },
  "defaultValue": "{\"categories\":[\"System\",\"Media\",\"Docs\"],\"series\":[{\"values\":[128,412,64]}]}"
}
```

Each example below shows one capability and the effect to expect on the phone.

### Stacked areas, smoothed
Demonstrates `stacked`, `smooth` and `colors`: two area series pile into one curved band, tinted from the color list.
```json
{
  "type": "chart",
  "id": "traffic",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Traffic",
  "chartConfig": { "stacked": true, "smooth": true, "colors": ["#667eea", "#f6ad55"], "showLegend": true },
  "defaultValue": "{\"categories\":[\"Mon\",\"Tue\",\"Wed\"],\"series\":[{\"name\":\"Web\",\"type\":\"area\",\"values\":[10,14,12]},{\"name\":\"API\",\"type\":\"area\",\"values\":[5,8,9]}]}"
}
```

### Scatter with bubble sizes
Demonstrates `points`, `sizes` and `pointSize`: loose dots at exact x and y positions, the larger multipliers drawing bigger bubbles.
```json
{
  "type": "chart",
  "id": "bubbles",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Latency vs load",
  "chartConfig": { "pointSize": 8 },
  "defaultValue": "{\"series\":[{\"name\":\"Hosts\",\"type\":\"scatter\",\"points\":[[1,20],[2,35],[4,50]],\"sizes\":[1,2,3]}]}"
}
```

### Histogram of samples
Demonstrates the `histogram` series and `bins`: raw samples are grouped into six frequency bars.
```json
{
  "type": "chart",
  "id": "latency-hist",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Response times",
  "chartConfig": { "bins": 6 },
  "defaultValue": "{\"series\":[{\"type\":\"histogram\",\"values\":[42.1,38.9,44.6,51.2,40.3,43.8,47.5]}]}"
}
```

### Waterfall
Demonstrates `waterfall`, `totals`, `positiveColor`, `negativeColor` and `totalColor`: green rises, red falls, and the first and last bars are totals.
```json
{
  "type": "chart",
  "id": "cashflow",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Cash flow",
  "chartConfig": { "positiveColor": "#48bb78", "negativeColor": "#f56565", "totalColor": "#667eea", "showValues": true },
  "defaultValue": "{\"categories\":[\"Start\",\"Sales\",\"Refunds\",\"Costs\",\"Net\"],\"series\":[{\"type\":\"waterfall\",\"values\":[1200,480,-160,-390,0],\"totals\":[0,4]}]}"
}
```

### Scrub crosshair with pinned axis
Demonstrates `scrub`, `yMin`, `yMax` and `formatValue`: dragging shows a dashed crosshair with a live readout, on a value axis fixed from 0 to 100.
```json
{
  "type": "chart",
  "id": "battery-trend",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Battery",
  "haptic": "selection",
  "formatValue": "%.0f%%",
  "chartConfig": { "scrub": true, "yMin": 0, "yMax": 100, "showGrid": false },
  "defaultValue": "{\"series\":[{\"type\":\"line\",\"values\":[92,88,80,71,65,52]}]}"
}
```

### Streaming append
Demonstrates `maxPoints` and the append push: each tick adds a reading, and the oldest drop off past 30 points. The payload below is what the server pushes over [[sync]].
```json
{
  "type": "chart",
  "id": "live-cpu",
  "position": [0, 0],
  "span": [3, 4],
  "label": "CPU live",
  "chartConfig": { "maxPoints": 30, "smooth": true },
  "defaultValue": "{\"series\":[{\"name\":\"CPU\",\"type\":\"line\",\"values\":[40,44]}]}",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "cpu_tick" }, "valuePath": "append" }]
}
```

### Glow, line ends and thick lines
Demonstrates `glowRadius`, `lineCap`, `lineWidth` and `tint`: a thick glowing line with flat ends.
```json
{
  "type": "chart",
  "id": "neon",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Neon trend",
  "tint": "#00e5ff",
  "glowRadius": 10,
  "lineCap": "butt",
  "chartConfig": { "lineWidth": 4, "showGrid": false },
  "defaultValue": "{\"series\":[{\"type\":\"line\",\"values\":[3,7,4,9,6]}]}"
}
```

### Themed chart
Demonstrates the theme fields: a squarer card with a heavier border, tinted background and softer axis text.
```json
{
  "type": "chart",
  "id": "themed-chart",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Themed",
  "theme": { "cornerRadius": 4, "borderWidth": 2, "borderColor": "#667eea", "surfacePrimary": "#667eea22", "secondaryColor": "#A0AEC0", "labelFontSize": 14 },
  "defaultValue": "{\"categories\":[\"A\",\"B\",\"C\"],\"series\":[{\"values\":[4,6,5]}]}"
}
```

The chart has no look variants that change its type and no long-press detail; a tap or scrub drag is its only interaction (see the voting example above for `datumAction`).

## Behavior
- Dataset changes animate smoothly (bars grow, lines morph) via the control's `animation` profile
- Tap near a datum to select it: bars highlight the whole column, points ring; the header shows the reading
- `scrub: true` swaps tap-selection for a drag crosshair with haptic ticks per datum
- Append pushes ride the same coalesced sync path as sparklines — high-rate streams stay smooth

## Notes
- The control's value **is the dataset JSON** — selection never overwrites it, so state [[sync|readback]] round-trips
- For quartile/density views of a distribution use [[box-plot]]; the `histogram` series here shows binned frequency shape
- For a single fast-scrolling series, [[sparkline]] is lighter

## Related
- [[sparkline]] — single-series micro trend
- [[box-plot]] — quartile/violin distributions
- [[pie-chart]] — part-of-whole / wheel / radial menu
- [[heatmap]] — 2-D matrix color map
- [[radar]] — multivariate profile
- [[sync]] — how datasets arrive
- [[actions]] — how `datumAction` fires
