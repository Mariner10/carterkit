---
type: boxPlot
depth: complete
label: Box Plot
icon: align.vertical.center
category: controls
defaultSpan: [3, 4]
addIntent: show
pickerCategory: Charts
friendlyName: Spread
oneLiner: How a set of numbers spreads out
aliases: [boxplot, distribution, quartile, whisker, spread, statistics]
starterPreset: {"label": "Spread"}
fields:
  - name: haptic
    tab: action
    type: enum
    values: [none, light, medium, heavy, soft, rigid, selection, success, warning, error]
    description: Touch feedback on interaction (supported hardware)
    summary: The buzz you feel on a tap
    does: Plays this haptic on the phone when you tap or scrub the plot, on supported hardware.
    valueHelp: {"none": "no vibration", "light": "a small soft tap", "medium": "a medium tap", "heavy": "a strong thud", "soft": "a cushioned, muffled tap", "rigid": "a firm sharp click", "selection": "the faint tick of picking an item", "success": "the double tap of a success", "warning": "a two-pulse warning", "error": "a sharp triple buzz of an error"}
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label above the plot
    summary: The plot's title
    does: Shows this text above the plot, with the selected box's median beside it.
  - name: boxStyle
    edit: look
    depth: surface
    title: Shape
    tab: style
    type: enum
    values: [box, violin]
    default: box
    description: "'box' (box-and-whisker) or 'violin' (kernel density body)"
    summary: Boxes or violins
    does: Draws each category as a box-and-whisker or as a smooth violin-shaped density body.
    valueHelp: {"box": "a box with whiskers marking the quartiles and median", "violin": "a smooth shape showing where the samples cluster (needs raw samples)"}
  - name: boxPlotConfig
    type: object
    description: Full configuration object (see BoxPlotConfig section)
    summary: Extra plot settings
    does: Groups the options for axes, whiskers, colors, scrubbing and the tap action.
  - name: tint
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: First-category color and palette seed
    summary: Main color
    does: Colors the first box and seeds the color of the others.
  - name: formatValue
    tab: data
    type: string
    description: Formatter for axis/readout numbers
    summary: How numbers are written
    does: Formats the axis labels and the median readout, e.g. as a unit or with fixed decimals.
  - name: boxAction
    tab: action
    type: object
    description: boxAction
    summary: What a tap does
    does: Fires this action when you tap a box, passing its five-number summary as {{value}}.
    group: boxPlotConfig
  - name: barCornerRadius
    edit: scrub
    depth: hold
    under: boxStyle
    title: Bar roundness
    unit: pt
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    default: 3
    description: Box corner rounding
    summary: Box roundness
    does: Rounds the box corners from square (0) to 30 points.
    group: boxPlotConfig
  - name: boxWidth
    edit: scrub
    depth: hold
    under: boxStyle
    title: Box width
    tab: style
    min: 0
    max: 1
    step: 0.05
    type: number
    default: 0.55
    description: Box width as a fraction of the category slot
    summary: How wide the boxes are
    does: Sets each box's width as a fraction (0 to 1) of its category slot.
    group: boxPlotConfig
  - name: colors
    edit: list
    depth: hold
    title: Box colors
    tab: style
    type: string[]
    description: Per-category color cycle
    summary: Colors for each box
    does: Cycles through this list of colors, one per category, instead of the built-in palette.
    group: boxPlotConfig
  - name: scrub
    type: bool
    default: false
    description: Drag sweeps the selection across categories with haptic ticks (readout only — the action still fires on tap)
    summary: Drag across the boxes
    does: Lets a drag sweep the selection across categories with a tick for each change; the action still fires only on tap.
    group: boxPlotConfig
  - name: showGrid
    edit: part
    depth: hold
    title: Grid lines
    type: bool
    default: true
    description: Horizontal grid lines
    summary: Grid lines on or off
    does: Shows or hides the horizontal grid lines behind the boxes.
    group: boxPlotConfig
  - name: showMean
    edit: part
    depth: hold
    title: Mean dot
    type: bool
    default: false
    description: Hollow dot at the mean
    summary: Mean dot on or off
    does: Shows or hides a hollow dot at each category's average.
    group: boxPlotConfig
  - name: showOutliers
    edit: part
    depth: hold
    title: Outliers
    type: bool
    default: true
    description: Outlier dots beyond the whiskers
    summary: Outlier dots on or off
    does: Shows or hides the dots for values beyond the whiskers.
    group: boxPlotConfig
  - name: showXAxis
    edit: part
    depth: hold
    title: Bottom axis
    type: bool
    default: true
    description: Category labels along the bottom
    summary: Category names on or off
    does: Shows or hides the category labels along the bottom.
    group: boxPlotConfig
  - name: showYAxis
    edit: part
    depth: hold
    title: Side axis
    type: bool
    default: true
    description: Value labels down the left gutter
    summary: Value scale on or off
    does: Shows or hides the value labels down the left side.
    group: boxPlotConfig
  - name: whiskers
    edit: look
    depth: hold
    under: boxStyle
    title: Whiskers
    type: enum
    values: [tukey, minmax]
    default: tukey
    description: "'tukey' (1.5 × IQR fences + outlier dots) or 'minmax' (full range)"
    summary: How far the whiskers reach
    does: Sets whether the whiskers stop at the Tukey fences with outliers as dots, or stretch to the full range.
    valueHelp: {"tukey": "whiskers stop at 1.5 times the spread and farther values show as dots", "minmax": "whiskers reach the smallest and largest values with no outlier dots"}
    group: boxPlotConfig
  - name: yMax
    bounds: none
    type: number
    description: Pin the value axis
    summary: Top of the scale
    does: Pins the top of the value axis instead of fitting it to the data.
    group: boxPlotConfig
  - name: yMin
    bounds: none
    type: number
    description: Pin the value axis
    summary: Bottom of the scale
    does: Pins the bottom of the value axis instead of fitting it to the data.
    group: boxPlotConfig
themeFields:
  - use: cornerRadius
  - name: surfacePrimary
    type: color
    default: #FFFFFF0F
    description: Background fill
    summary: Background color
    does: Fills the box plot background with this color.
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Axis label color
    summary: Axis label color
    does: Colors the axis labels on the box plot.
  - name: accentColor
    title: Accent color
    type: color
    default: #667eea
    description: Accent/tint color
    summary: Highlight color
    does: Sets the accent color used to tint the box plot when no tint is set.
  - name: borderColor
    title: Border color
    type: color
    default: #FFFFFF1A
    description: Border color
    summary: Outline color
    does: Colors the outline drawn around the box plot.
  - name: borderWidth
    title: Border thickness
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
    summary: Outline thickness
    does: Sets the outline width from 0 to 5 points.
  - name: controlPadding
    title: Inner spacing
    min: 0
    max: 24
    step: 1
    type: number
    default: 8
    description: Internal padding
    summary: Space inside the edges
    does: Adds padding between the box plot edge and its content, 0 to 24 points.
  - name: foregroundColor
    title: Text color
    type: color
    default: #FFFFFF
    description: Primary text color
    summary: Main text color
    does: Colors the primary text on the box plot.
  - name: labelFontSize
    title: Title text size
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
    summary: Label text size
    does: Sets the label text size from 8 to 24 points.
  - name: tertiaryColor
    title: Faint text color
    type: color
    default: #FFFFFF4D
    description: Tertiary text and ink color
    summary: Dimmed text color
    does: Colors the faintest text and ink on the chart.
---

# Box Plot

Distribution at a glance: one **box-and-whisker** (quartiles, median, Tukey
outliers) or **violin** (kernel density body) per category. Push raw samples
and the phone does the statistics — quartiles, 1.5 × IQR fences, gaussian KDE —
or push precomputed `stats` when the server already reduced them. Tapping a
distribution reads its median into the header and fires `boxAction` with the
full five-number summary, so a latency plot doubles as a drill-down picker.

## Type
`"boxPlot"`

## Recommended Size
Wide like [[chart]]: `[3, 4]`. In a flow grid it auto-sizes to a 16:10 cell.

## Relevant Fields
Inherits all [[control-def|shared fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Header label (selection readout appears beside it) |
| `boxStyle` | string | `"box"` | `"box"` or `"violin"` |
| `boxPlotConfig` | [[#BoxPlotConfig]] | — | Full configuration object (all optional) |
| `tint` | string | `"#667eea"` | First-category color / palette seed |
| `formatValue` | string | — | Formatter for axis + readout numbers |
| `action` | [[actions\|ActionDefinition]] | — | Fallback for `boxAction` |

## BoxPlotConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `showXAxis` | bool | `true` | Category labels along the bottom |
| `showYAxis` | bool | `true` | Value labels down the left gutter |
| `showGrid` | bool | `true` | Horizontal grid lines |
| `yMin` / `yMax` | number | data range | Pin the value axis |
| `whiskers` | string | `"tukey"` | `"tukey"` (1.5 × IQR fences + outlier dots) or `"minmax"` (full range) |
| `showOutliers` | bool | `true` | Outlier dots beyond the whiskers |
| `showMean` | bool | `false` | Hollow dot at the mean |
| `boxWidth` | number | `0.55` | Box width as a fraction of the category slot |
| `barCornerRadius` | number | `3` | Box corner rounding in points, 0–30 |
| `colors` | string[] | built-in palette | Per-category color cycle |
| `boxAction` | [[actions\|ActionDefinition]] | — | Fired on tap; `{{value}}` = the stats as JSON |
| `scrub` | bool | `false` | Drag sweeps the selection across categories with haptic ticks (readout only — the action still fires on tap) |

## Sync Payload Structure

Raw samples (the app computes the statistics) — natural JSON or an encoded string:

```json
{
  "categories": ["us-east", "eu-west", "ap-south"],
  "samples": [
    [42, 51, 38, 66, 47, 130, 44],
    [61, 72, 58, 66, 70, 64, 69],
    [88, 95, 91, 180, 86, 90, 84]
  ]
}
```

Shorthand: a bare 2-D array `[[…], […]]` is `samples` with numbered categories.

Or precomputed stats (wins over `samples` if both are present):

```json
{
  "categories": ["us-east"],
  "stats": [
    { "min": 38, "q1": 43, "median": 47, "q3": 58, "max": 66, "outliers": [130] }
  ]
}
```

Note: `boxStyle: "violin"` needs raw `samples` for the density body; with only
`stats` it falls back to the skeleton bar.

## Examples

### Latency by region (tap to inspect)
```json
{
  "type": "boxPlot",
  "id": "latency",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Latency (ms)",
  "boxPlotConfig": {
    "boxAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "inspect_region", "stats": "{{value}}" } }
  },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "latency_samples" }, "valuePath": "regions" }]
}
```

### Violin comparison
```json
{
  "type": "boxPlot",
  "id": "spread",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Sensor spread",
  "boxStyle": "violin",
  "boxPlotConfig": { "showMean": true },
  "defaultValue": "{\"categories\":[\"A\",\"B\"],\"samples\":[[5,6,6,7,7,7,8,9],[4,5,7,9,10,11,11,12]]}"
}
```

### Whiskers to the full range
Shows every value inside the whiskers, so no outlier dots appear, with a mean dot added.
```json
{
  "type": "boxPlot",
  "id": "full-range",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Response time",
  "boxPlotConfig": { "whiskers": "minmax", "showMean": true },
  "defaultValue": "{\"categories\":[\"A\",\"B\"],\"samples\":[[10,12,13,15,18,40],[20,22,25,26,30,31]]}"
}
```

## Behavior
- Dataset pushes animate via the control's `animation` profile
- Tap a category to select it (header shows `name ~median`); tap again or tap empty space to clear
- `scrub: true` lets a drag sweep the selection fluidly across categories with a tick per change
- Quartiles use type-7 linear interpolation (same as Numbers/NumPy); violin bandwidth is Silverman's rule
- The value axis pads 6% beyond the extremes so caps and outlier dots never clip

## Notes
- 2–6 categories read best; past ~8 the boxes get skinny on a phone
- The control's value **is the dataset JSON** — selection never overwrites it
- For a single streaming series use [[sparkline]]; for binned frequency shape use a [[chart]] `histogram` series

## Related
- [[chart]] — cartesian series (incl. `histogram` + `waterfall`)
- [[heatmap]] — 2-D matrix color map
- [[sync]] — how datasets arrive
- [[actions]] — how `boxAction` fires
