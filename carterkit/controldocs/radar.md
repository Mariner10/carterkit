---
type: radar
label: Radar
icon: hexagon.fill
category: controls
defaultSpan: [2, 2]
fields:
  - name: label
    type: string
    description: Label under the chart
  - name: radarConfig
    type: object
    description: Full configuration object (see RadarConfig section)
  - name: tint
    type: color
    default: "#667eea"
    description: First-series color and palette seed
  - name: formatValue
    type: string
    description: Formatter for vertex values
  - name: colors
    type: string[]
    description: Series color cycle (per-series color wins)
    group: radarConfig
  - name: curved
    type: bool
    default: false
    description: Rounded polygon instead of straight edges
    group: radarConfig
  - name: editable
    type: bool
    default: false
    description: Drag the **first** series' vertices along their axes
    group: radarConfig
  - name: fillOpacity
    type: number
    default: 0.25
    description: Polygon fill opacity 0–1
    group: radarConfig
  - name: maxValue
    type: number
    description: Per-axis maximum (payload max wins)
    group: radarConfig
  - name: rings
    type: number
    default: 4
    description: Concentric grid rings
    group: radarConfig
  - name: showAxisLabels
    type: bool
    default: true
    description: Axis names around the rim
    group: radarConfig
  - name: showLegend
    type: bool
    default: false
    description: Series legend under the chart
    group: radarConfig
  - name: showPoints
    type: bool
    default: true
    description: Vertex dots (always on while editing)
    group: radarConfig
  - name: showValues
    type: bool
    default: false
    description: Numeric value beside each vertex (the dragged vertex always shows)
    group: radarConfig
  - name: step
    type: number
    description: Snap dragged values to this step (e.g. 1, 5, 0.1)
    group: radarConfig
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
  "action": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast", "payload": { "msg_type": "eq_set", "bands": "{{value}}" } },
  "defaultValue": "{\"axes\":[\"60Hz\",\"250Hz\",\"1kHz\",\"4kHz\",\"12kHz\"],\"max\":10,\"series\":[{\"values\":[5,6,5,4,6]}]}"
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
