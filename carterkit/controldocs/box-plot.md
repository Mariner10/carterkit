---
type: boxPlot
label: Box Plot
icon: align.vertical.center
category: controls
defaultSpan: [3, 4]
fields:
  - name: label
    type: string
    description: Header label above the plot
  - name: boxStyle
    type: string
    default: box
    description: '"box" (box-and-whisker) or "violin" (kernel density body)'
  - name: boxPlotConfig
    type: object
    description: Full configuration object (see BoxPlotConfig section)
  - name: tint
    type: color
    default: "#667eea"
    description: First-category color and palette seed
  - name: formatValue
    type: string
    description: Formatter for axis/readout numbers
  - name: boxAction
    type: object
    description: boxAction
    group: boxPlotConfig
  - name: boxWidth
    type: number
    default: 0.55
    description: Box width as a fraction of the category slot
    group: boxPlotConfig
  - name: colors
    type: string[]
    description: Per-category color cycle
    group: boxPlotConfig
  - name: scrub
    type: bool
    default: false
    description: Drag sweeps the selection across categories with haptic ticks (readout only — the action still fires on tap)
    group: boxPlotConfig
  - name: showGrid
    type: bool
    default: true
    description: Horizontal grid lines
    group: boxPlotConfig
  - name: showMean
    type: bool
    default: false
    description: Hollow dot at the mean
    group: boxPlotConfig
  - name: showOutliers
    type: bool
    default: true
    description: Outlier dots beyond the whiskers
    group: boxPlotConfig
  - name: showXAxis
    type: bool
    default: true
    description: Category labels along the bottom
    group: boxPlotConfig
  - name: showYAxis
    type: bool
    default: true
    description: Value labels down the left gutter
    group: boxPlotConfig
  - name: whiskers
    type: string
    description: 'tukey' (1.5 × IQR fences + outlier dots) or 'minmax' (full range)
    group: boxPlotConfig
  - name: yMax
    type: number
    description: Pin the value axis
    group: boxPlotConfig
  - name: yMin
    type: number
    description: Pin the value axis
    group: boxPlotConfig
themeFields:
  - name: cornerRadius
    type: number
    default: 12
    description: Control corner radius
  - name: surfacePrimary
    type: color
    default: #FFFFFF0F
    description: Background fill
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Axis label color
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
    "boxAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast", "payload": { "msg_type": "inspect_region", "stats": "{{value}}" } }
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
