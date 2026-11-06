---
type: pieChart
label: Pie Chart
icon: chart.pie.fill
category: controls
defaultSpan: [3, 3]
addIntent: show
pickerCategory: Charts
depth: complete
friendlyName: Pie
oneLiner: Parts of a whole
aliases: [pie, donut, doughnut, share, breakdown, proportion]
starterPreset: {"label": "Pie"}
io:
  - receives: slices
    role: show
    type: json
    shape: {"slices": [{"label": "text", "value": "number?", "color": "hex?", "icon": "symbol?"}]}
    from: [hub, mqtt, http, store, default]
    says: "slices: a label and a number each (a missing number counts as 1)"
    reacts: bigger numbers get bigger slices; new data re-slices the chart, and a wheel keeps its place
    example: {"slices": [{"label": "Sample A", "value": 3}]}
    since: next
  - emits: slice
    when: tap
    title: When you tap a slice
    field: pieConfig.sliceAction
    fallback: action
    type: string
    says: the tapped slice's label
    example: "Sample A"
    whenBy: {"pieStyle": {"wheel": "land"}}
    also: On a wheel it sends when the spin stops, with the label the pointer lands on; tapping or flicking a wheel only spins it
    since: next
  - sample: {"slices": [{"label": "Sample A", "value": 3}, {"label": "Sample B", "value": 2}, {"label": "Sample C", "value": 1}]}
    next: {"slices": [{"label": "Sample A", "value": 2}, {"label": "Sample B", "value": 3}, {"label": "Sample C", "value": 1}, {"label": "Sample D", "value": 1}]}
fields:
  - name: haptic
    tab: action
    type: enum
    values: [none, light, medium, heavy, soft, rigid, selection, success, warning, error]
    description: Touch feedback on interaction (supported hardware)
    summary: "How a touch feels"
    does: "Plays the chosen buzz on the phone when a slice is tapped or a wheel lands; none stays silent."
    valueHelp: {"none": "no buzz", "light": "a faint tick", "medium": "a normal tap", "heavy": "a firm thump", "soft": "a muffled cushioned bump", "rigid": "a crisp hard click", "selection": "a tiny click like scrolling a picker", "success": "a short double-tap for done", "warning": "a sharper alert buzz", "error": "a harsh triple buzz for failure"}
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Label under the chart
    summary: "The name shown under the chart"
    does: "Writes this text under the chart in the title size; empty shows no title."
  - name: pieStyle
    edit: look
    title: Shape
    tab: style
    type: enum
    values: [pie, donut, wheel, menu]
    default: pie
    description: Classic pie, donut, spin-to-select wheel, or radial menu
    summary: "Which kind of round chart it is"
    does: "Switches the control between a solid pie, a ring with a hole, a spinning wheel and a radial button pad."
    valueHelp: {"pie": "a solid chart with no hole", "donut": "a ring with a hole and a center readout", "wheel": "a wheel you flick to spin and pick a winner", "menu": "equal slices that each act as a button"}
  - name: glowRadius
    edit: scrub
    depth: hold
    under: pieStyle
    title: Glow
    unit: pt
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    default: 0
    description: Soft glow behind the slices in their own colours, in points (0 = none). Cross-control, same on every control
    summary: "A soft halo behind the slices"
    does: "Adds a blurred glow in each slice's own color that reaches this many points out, from 0 (none) to 30."
  - name: pieConfig
    type: object
    description: Full configuration object (see PieConfig section)
    summary: "The detailed chart settings in one bundle"
    does: "Holds the options below (hole size and gaps and labels and legend and spin and actions); each one changes the chart as listed."
  - name: tint
    edit: color
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: First-slice color and palette seed
    summary: "The main slice color"
    does: "Colors the first slice and seeds the palette used for the other slices when no colors are listed."
  - name: formatValue
    tab: data
    type: string
    description: Formatter for slice/center values
    summary: "How numbers are written"
    does: "Reformats the numbers shown on slices and in the center, for example as a currency or a rounded figure."
  - name: centerText
    type: string
    description: Donut center text; {{total}} interpolates the slice sum
    summary: "Text shown in the middle of the donut"
    does: "Replaces the center readout of a donut with this text; {{total}} becomes the sum of all slices."
    group: pieConfig
  - name: colors
    edit: list
    title: Slice colors
    tab: style
    type: string[]
    description: Slice color cycle (per-slice color wins)
    summary: "The colors the slices take in turn"
    does: "Colors slice one with the first entry, slice two with the second and so on, repeating when slices outnumber colors."
    group: pieConfig
  - name: donutRatio
    edit: scrub
    depth: hold
    under: pieStyle
    title: Hole size
    tab: style
    min: 0
    max: 0.85
    step: 0.05
    type: number
    description: Inner-radius fraction 0–0.85 (pie 0, donut 0.62, wheel 0.18, menu 0.3)
    summary: "How big the hole in the middle is"
    does: "Sets the hole width as a fraction of the radius from 0 (solid) to 0.85 (thin ring); the default depends on the shape."
    group: pieConfig
  - name: sliceGap
    edit: scrub
    depth: hold
    under: pieStyle
    title: Slice gap
    unit: pt
    tab: style
    min: 0
    max: 12
    step: 1
    type: number
    default: 0
    description: Even-width gap between neighbouring slices in points (slices narrower than the gap drop it)
    summary: "Space between slices"
    does: "Leaves an even gap of this many points between neighbouring slices, from 0 to 12."
    group: pieConfig
  - name: sliceCornerRadius
    edit: scrub
    depth: hold
    under: pieStyle
    title: Slice corners
    unit: pt
    tab: style
    min: 0
    max: 16
    step: 1
    type: number
    default: 0
    description: Rounds every slice corner (outer and donut inner) in points, clamped for tiny slices
    summary: "How round the slice corners are"
    does: "Rounds the outer and inner corners of every slice by up to 16 points; tiny slices get less."
    group: pieConfig
  - name: explodeSelected
    type: bool
    description: Tapped slice pops outward (**wheels default false)
    summary: "Whether a tapped slice pops out"
    does: "On, the tapped slice slides outward from the center; off, it only highlights."
    group: pieConfig
  - name: percent
    edit: part
    depth: hold
    title: Percent
    type: bool
    default: false
    description: Show values as % of the total
    summary: "Numbers as shares of the whole"
    does: "On, slice values read as a percentage of the total instead of raw numbers."
    group: pieConfig
  - name: showLabels
    edit: part
    depth: hold
    title: Labels
    type: bool
    description: Slice labels (auto-hidden on thin slices; *menu defaults false — icons lead)
    summary: "Names written on the slices"
    does: "On, each slice shows its label; slices under about 4 percent of the circle hide theirs."
    group: pieConfig
  - name: showLegend
    edit: part
    depth: hold
    title: Legend
    type: bool
    default: false
    description: Wrapping dot-chip legend under the chart
    summary: "A key of the slices under the chart"
    does: "On, adds a wrapping row of colored dots with slice names below the chart."
    group: pieConfig
  - name: showValues
    edit: part
    depth: hold
    title: Value labels
    type: bool
    default: false
    description: Append each slice's value to its label
    summary: "Numbers next to the slice names"
    does: "On, each slice label also shows that slice's value."
    group: pieConfig
  - name: sliceAction
    tab: action
    type: object
    description: sliceAction
    summary: "What happens when a slice is chosen"
    does: "Runs this action on a slice tap or wheel landing, with {{value}} set to the slice label."
    group: pieConfig
  - name: spinDuration
    min: 0.1
    max: 10
    step: 0.1
    type: number
    default: 4
    description: Approximate seconds a full-strength spin takes to settle
    summary: "How long the wheel keeps turning"
    does: "Sets roughly how many seconds a full-strength spin takes to slow to a stop, from 0.1 to 10."
    group: pieConfig
  - name: spinTicks
    type: bool
    default: true
    description: Haptic tick per slice boundary while spinning
    summary: "The clicks while the wheel turns"
    does: "On, the phone ticks each time a slice boundary passes the pointer; off, the spin is silent."
    group: pieConfig
  - name: startAngle
    edit: scrub
    depth: hold
    under: pieStyle
    title: Start angle
    min: 0
    max: 360
    step: 1
    type: number
    default: 0
    description: Degrees the first slice starts at (0 = 12 o'clock, clockwise)
    summary: "Where the first slice begins"
    does: "Rotates the whole chart so the first slice starts at this many degrees clockwise from the top, 0 to 360."
    group: pieConfig
  - name: icon
    type: string
    description: SF Symbol in the wheel/menu hub before a result lands
    summary: "The symbol in the middle of the wheel"
    does: "Draws this SF Symbol in the wheel or menu hub until a result lands."
  - name: hideValue
    type: bool
    default: false
    description: Suppress the donut/hub center readout
    summary: "Hides the center number"
    does: "On, removes the readout from the donut center or hub; the slices still draw."
themeFields:
  - use: cornerRadius
    summary: "How round the card corners are"
    does: "Rounds the card corners from 0 (square) to 30 points."
  - name: surfacePrimary
    type: color
    default: #FFFFFF0F
    description: Background fill (also the hairline slice gap color)
    summary: "The card's fill color"
    does: "Fills the card behind the chart; it is also the hairline color between slices."
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Label text color
    summary: "The softer text color"
    does: "Colors the slice labels and legend text."
  - use: accentColor
    summary: "The highlight color"
    does: "Sets the accent used for the selected slice and highlights."
  - use: borderColor
    summary: "The outline around the card"
  - use: borderWidth
    does: "Sets the card outline width from 0 to 5 points."
  - use: controlPadding
    summary: "Space inside the card"
    does: "Sets the padding between the card edge and the chart from 0 to 24 points."
  - use: foregroundColor
    does: "Colors the title and the center readout."
  - use: labelFontSize
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
Square cells — `[3, 3]` minimum, larger for wheels with many slices. The control
keeps itself round.

## Relevant Fields
Inherits all [[control-def|shared fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `pieStyle` | string | `"pie"` | `pie` \| `donut` \| `wheel` \| `menu` |
| `pieConfig` | [[#PieConfig]] | — | Full configuration object (all optional) |
| `tint` | string | `"#667eea"` | First-slice color / palette seed |
| `glowRadius` | number | `0` | Soft glow behind the slices in their own colours, 0–30 pt (the same attribute on every control that has it) |
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

A grouped [[local-store]] result (`{"categories": […], "series": [{"values": […]}]}`,
what `"groupBy": "genre"` delivers) also reads: one slice per category, sized by its value.

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
  "span": [3, 3],
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
    "sliceAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "oncall_pick", "person": "{{value}}" } }
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
  "span": [3, 3],
  "label": "Scenes",
  "pieStyle": "menu",
  "icon": "sparkles",
  "pieConfig": {
    "sliceAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "scene", "name": "{{value}}" } }
  },
  "defaultValue": "{\"slices\":[{\"label\":\"Movie\",\"icon\":\"tv\"},{\"label\":\"Focus\",\"icon\":\"moon\"},{\"label\":\"Party\",\"icon\":\"music.note\"},{\"label\":\"Off\",\"icon\":\"power\"}]}"
}
```

### Plain pie with fixed slices
Shows a value on screen with no data source: a solid pie of three coloured shares with a legend, so the person sees parts of a whole at a glance.
```json
{
  "type": "pieChart",
  "id": "budget-pie",
  "position": [0, 0],
  "span": [3, 3],
  "label": "Budget",
  "pieStyle": "pie",
  "pieConfig": { "showLegend": true, "showValues": true, "startAngle": 90 },
  "defaultValue": "{\"slices\":[{\"label\":\"Rent\",\"value\":50,\"color\":\"#FF6B6B\"},{\"label\":\"Food\",\"value\":30,\"color\":\"#667eea\"},{\"label\":\"Fun\",\"value\":20}]}"
}
```

### Polished donut look
Shows the look settings together: a thin ring with rounded, separated slices and a soft glow, so the chart reads as a refined ring rather than a flat disc.
```json
{
  "type": "pieChart",
  "id": "polished-donut",
  "position": [0, 0],
  "span": [3, 3],
  "label": "Storage",
  "pieStyle": "donut",
  "glowRadius": 10,
  "pieConfig": { "donutRatio": 0.7, "sliceGap": 4, "sliceCornerRadius": 8, "colors": ["#4ECDC4", "#FFE66D", "#FF6B6B"], "centerText": "{{total}} GB" },
  "defaultValue": "{\"slices\":[{\"label\":\"Photos\",\"value\":64},{\"label\":\"Apps\",\"value\":32},{\"label\":\"Other\",\"value\":16}]}"
}
```

### Tap a slice to act
Shows the tap action and haptic: tapping a slice pops it outward, buzzes lightly and broadcasts that slice's label, so a pie doubles as a filter picker.
```json
{
  "type": "pieChart",
  "id": "room-filter",
  "position": [0, 0],
  "span": [3, 3],
  "label": "Rooms",
  "pieStyle": "donut",
  "haptic": "light",
  "pieConfig": {
    "explodeSelected": true,
    "sliceAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "room_focus", "room": "{{value}}" } }
  },
  "defaultValue": "{\"slices\":[{\"label\":\"Kitchen\",\"value\":3},{\"label\":\"Den\",\"value\":2},{\"label\":\"Garage\",\"value\":1}]}"
}
```

## Behavior
- Slice datasets animate between pushes; taps highlight (and optionally explode) a slice
- **Wheel**: flick to spin with your own force, or tap for a strong randomized spin; the pointer sits at 12 o'clock; each boundary crossing ticks; settling fires a success haptic + the action with the winner, and the hub shows the result
- **Menu**: every slice is a button; the hub echoes the last pick
- The wheel result is delivered via action only — the control's value stays the dataset, so a re-render never re-fires a pick

## Notes
- `hideValue`, `centerText` and `donutRatio` show nothing on a plain `pie` (no hole) or `menu`; they matter on `donut` and `wheel` hubs
- `spinDuration` and `spinTicks` only change the `wheel`; the other shapes never spin
- Wheel odds follow `value` weights — equal weights = fair spin, and the server can re-weight live between spins
- Slices under ~4% of the circle drop their inline label; use `showLegend` for long tails
- A polar/rose chart is a pie whose values map to radius — out of scope v1

## Related
- [[chart]] — cartesian bar/line/area/scatter
- [[gauge]] — single-value radial readout
- [[progress-ring]] — single-fraction ring
- [[actions]] — how slice/wheel actions fire
- [[sync]] — how slice data arrives
