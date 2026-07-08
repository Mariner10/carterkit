---
type: chart
label: Chart
icon: chart.bar.xaxis
category: controls
defaultSpan: [3, 4]
fields:
  - name: label
    type: string
    description: Header label above the chart
  - name: chartConfig
    type: object
    description: Full configuration object (see ChartConfig section)
  - name: tint
    type: color
    default: "#667eea"
    description: First-series color and palette seed
  - name: formatValue
    type: string
    description: Formatter for axis/readout numbers (see control-def)
  - name: barCornerRadius
    type: number
    default: 3
    description: Bar corner rounding
    group: chartConfig
  - name: bins
    type: number
    description: Bin count for histogram series
    group: chartConfig
  - name: colors
    type: string[]
    description: Series color cycle (per-series color wins)
    group: chartConfig
  - name: datumAction
    type: object
    description: datumAction
    group: chartConfig
  - name: horizontal
    type: bool
    default: false
    description: Horizontal bars — categories run down the leading edge
    group: chartConfig
  - name: lineWidth
    type: number
    default: 2
    description: Line/area stroke width
    group: chartConfig
  - name: maxPoints
    type: number
    default: 100
    description: Rolling window applied to {'append': …} pushes
    group: chartConfig
  - name: negativeColor
    type: color
    description: Falling waterfall delta
    group: chartConfig
  - name: pointSize
    type: number
    default: 6
    description: Scatter point / vertex dot diameter
    group: chartConfig
  - name: positiveColor
    type: color
    description: Rising waterfall delta
    group: chartConfig
  - name: scrub
    type: bool
    default: false
    description: Drag shows a dashed crosshair + live readout (with a selection tick)
    group: chartConfig
  - name: showGrid
    type: bool
    default: true
    description: Horizontal grid lines
    group: chartConfig
  - name: showLegend
    type: bool
    default: false
    description: Series legend under the plot
    group: chartConfig
  - name: showValues
    type: bool
    default: false
    description: Numeric value above each bar / on each vertex
    group: chartConfig
  - name: showXAxis
    type: bool
    default: true
    description: Category/x labels along the bottom (leading edge when horizontal)
    group: chartConfig
  - name: showYAxis
    type: bool
    default: true
    description: Value labels down the left gutter
    group: chartConfig
  - name: smooth
    type: bool
    default: false
    description: Catmull-Rom curve smoothing for line/area series
    group: chartConfig
  - name: stacked
    type: bool
    default: false
    description: Stack bar/area series instead of grouping/overlaying
    group: chartConfig
  - name: totalColor
    type: color
    description: Waterfall running-total bars
    group: chartConfig
  - name: yMax
    type: number
    description: Pin the value axis (bars baseline at 0 by default)
    group: chartConfig
  - name: yMin
    type: number
    description: Pin the value axis (bars baseline at 0 by default)
    group: chartConfig
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
  - name: labelFontSize
    type: number
    default: 12
    description: Label text size
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
| `values` | number[] | no* | Y values at implicit x = 0, 1, 2, … (aligned with `categories`). For `histogram`: the **raw samples** to bin. For `waterfall`: the **signed deltas** |
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
    "datumAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast", "payload": { "msg_type": "vote", "choice": "{{value}}" } }
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
