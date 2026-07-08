---
type: pieChart
label: Pie Chart
icon: chart.pie.fill
category: controls
defaultSpan: [2, 2]
fields:
  - name: label
    type: string
    description: Label under the chart
  - name: pieStyle
    type: enum
    values: [pie, donut, wheel, menu]
    default: pie
    description: Classic pie, donut, spin-to-select wheel, or radial menu
  - name: pieConfig
    type: object
    description: Full configuration object (see PieConfig section)
  - name: tint
    type: color
    default: "#667eea"
    description: First-slice color and palette seed
  - name: formatValue
    type: string
    description: Formatter for slice/center values
  - name: centerText
    type: string
    description: Donut center text; {{total}} interpolates the slice sum
    group: pieConfig
  - name: colors
    type: string[]
    description: Slice color cycle (per-slice color wins)
    group: pieConfig
  - name: donutRatio
    type: number
    description: Inner-radius fraction 0–0.85 (pie 0, donut 0.62, wheel 0.18, menu 0.3)
    group: pieConfig
  - name: explodeSelected
    type: bool
    description: Tapped slice pops outward (**wheels default false)
    group: pieConfig
  - name: percent
    type: bool
    default: false
    description: Show values as % of the total
    group: pieConfig
  - name: showLabels
    type: bool
    description: Slice labels (auto-hidden on thin slices; *menu defaults false — icons lead)
    group: pieConfig
  - name: showLegend
    type: bool
    default: false
    description: Wrapping dot-chip legend under the chart
    group: pieConfig
  - name: showValues
    type: bool
    default: false
    description: Append each slice's value to its label
    group: pieConfig
  - name: sliceAction
    type: object
    description: sliceAction
    group: pieConfig
  - name: spinDuration
    type: number
    default: 4
    description: Approximate seconds a full-strength spin takes to settle
    group: pieConfig
  - name: spinTicks
    type: bool
    default: true
    description: Haptic tick per slice boundary while spinning
    group: pieConfig
  - name: startAngle
    type: number
    default: 0
    description: Degrees the first slice starts at (0 = 12 o'clock, clockwise)
    group: pieConfig
themeFields:
  - name: cornerRadius
    type: number
    default: 12
    description: Control corner radius
  - name: surfacePrimary
    type: color
    default: #FFFFFF0F
    description: Background fill (also the hairline slice gap color)
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Label text color
---

# Pie Chart

One radial control, four personalities. `pieStyle` picks the mode:

- **`pie` / `donut`** — the classic part-of-whole chart, with tappable slices, an
  optional exploding selection, and a donut center readout.
- **`wheel`** — a **spin-to-select wheel**: flick (or tap) to spin, physics wind it
  down with a haptic tick per slice, and the winning slice fires the action. Slice
  `value`s become raffle weights, so a weighted giveaway is just data.
- **`menu`** — a **radial command pad**: equal slices with icons, each slice a
  button. Eight actions in the footprint of one round control.

## Type
`"pieChart"`

## Recommended Size
Square cells — `[2, 2]` minimum, `[3, 3]` for wheels with many slices. The control
keeps itself round.

## Relevant Fields
Inherits all [[control-def|shared fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `pieStyle` | string | `"pie"` | `pie` \| `donut` \| `wheel` \| `menu` |
| `pieConfig` | [[#PieConfig]] | — | Full configuration object (all optional) |
| `tint` | string | `"#667eea"` | First-slice color / palette seed |
| `icon` | string | — | SF Symbol in the wheel/menu hub before a result lands |
| `formatValue` | string | — | Formatter for slice/center values |
| `hideValue` | bool | `false` | Suppress the donut/hub center readout |

## PieConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `donutRatio` | number | per style | Inner-radius fraction 0–0.85 (pie 0, donut 0.62, wheel 0.18, menu 0.3) |
| `startAngle` | number | `0` | Degrees the first slice starts at (0 = 12 o'clock, clockwise) |
| `showLegend` | bool | `false` | Wrapping dot-chip legend under the chart |
| `showLabels` | bool | `true`* | Slice labels (auto-hidden on thin slices; *menu defaults false — icons lead) |
| `showValues` | bool | `false` | Append each slice's value to its label |
| `percent` | bool | `false` | Show values as % of the total |
| `centerText` | string | — | Donut center text; `{{total}}` interpolates the slice sum |
| `explodeSelected` | bool | `true`** | Tapped slice pops outward (**wheels default false) |
| `colors` | string[] | built-in palette | Slice color cycle (per-slice `color` wins) |
| `sliceAction` | [[actions\|ActionDefinition]] | — | Fired on slice tap **and** wheel landing; `{{value}}` = slice label |
| `spinDuration` | number | `4` | Approximate seconds a full-strength spin takes to settle |
| `spinTicks` | bool | `true` | Haptic tick per slice boundary while spinning |

If `sliceAction` is omitted, taps/landings fall back to the control's own `action`.

## Sync Payload Structure

`{"slices": […]}` or a bare array of slices — natural JSON or an encoded string:

```json
{
  "slices": [
    { "label": "Heating", "value": 41, "color": "#FF6B6B" },
    { "label": "Compute", "value": 33, "color": "#667eea" },
    { "label": "Idle",    "value": 26 }
  ]
}
```

### Slice Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | yes | Display name — also the `{{value}}` an action receives |
| `value` | number | no | Share of the whole / raffle weight (default 1; menu mode ignores it) |
| `color` | string | no | Slice color (hex) |
| `icon` | string | no | SF Symbol drawn in the slice (menu mode leads with it) |

## Examples

### Donut with live total
```json
{
  "type": "pieChart",
  "id": "power-split",
  "position": [0, 0],
  "span": [2, 2],
  "label": "Power draw",
  "pieStyle": "donut",
  "pieConfig": { "centerText": "{{total}}W", "showLegend": true, "percent": true },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "power" }, "valuePath": "split" }]
}
```

### Spin-to-select wheel (weighted raffle)
```json
{
  "type": "pieChart",
  "id": "prize-wheel",
  "position": [0, 0],
  "span": [3, 3],
  "label": "Who's on call?",
  "pieStyle": "wheel",
  "pieConfig": {
    "spinDuration": 5,
    "sliceAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast", "payload": { "msg_type": "oncall_pick", "person": "{{value}}" } }
  },
  "defaultValue": "{\"slices\":[{\"label\":\"Ava\",\"value\":1},{\"label\":\"Ben\",\"value\":1},{\"label\":\"Cass\",\"value\":2},{\"label\":\"Drew\",\"value\":1}]}"
}
```

### Radial command menu
```json
{
  "type": "pieChart",
  "id": "scene-menu",
  "position": [0, 0],
  "span": [2, 2],
  "label": "Scenes",
  "pieStyle": "menu",
  "icon": "sparkles",
  "pieConfig": {
    "sliceAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast", "payload": { "msg_type": "scene", "name": "{{value}}" } }
  },
  "defaultValue": "{\"slices\":[{\"label\":\"Movie\",\"icon\":\"tv\"},{\"label\":\"Focus\",\"icon\":\"moon\"},{\"label\":\"Party\",\"icon\":\"music.note\"},{\"label\":\"Off\",\"icon\":\"power\"}]}"
}
```

## Behavior
- Slice datasets animate between pushes; taps highlight (and optionally explode) a slice
- **Wheel**: flick to spin with your own force, or tap for a strong randomized spin; the pointer sits at 12 o'clock; each boundary crossing ticks; settling fires a success haptic + the action with the winner, and the hub shows the result
- **Menu**: every slice is a button; the hub echoes the last pick
- The wheel result is delivered via action only — the control's value stays the dataset, so a re-render never re-fires a pick

## Notes
- Wheel odds follow `value` weights — equal weights = fair spin, and the server can re-weight live between spins
- Slices under ~4% of the circle drop their inline label; use `showLegend` for long tails
- A polar/rose chart is a pie whose values map to radius — out of scope v1

## Related
- [[chart]] — cartesian bar/line/area/scatter
- [[gauge]] — single-value radial readout
- [[progress-ring]] — single-fraction ring
- [[actions]] — how slice/wheel actions fire
- [[sync]] — how slice data arrives
