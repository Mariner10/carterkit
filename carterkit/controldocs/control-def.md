---
type: control-def
label: Control Definition
icon: square.dashed.inset.filled
category: models
fields:
  - name: type
    values: [button, toggle, slider, label, textInput, stepper, segmentedControl, colorPicker, image, gauge, sparkline, progressRing, map, picker, datePicker, graph, chat, list, statusLight, logConsole, divider, spacer, webView, joystick, qrCode, carousel, flipCard, accordion, cardList, camera, chart, pieChart, heatmap, radar, boxPlot, gantt, sankey, treemap, chord, sortboard, compass, pinboard, canvas, symbol, statTile, keyValue]
    type: enum
    description: Control type (required); decides which per-type fields apply
  - name: id
    type: string
    description: Unique identifier among the layout's controls and groups (required); used for value storage, sync targeting and visibility references
  - name: position
    type: array
    description: Zero-indexed [row, col] grid cell (required)
  - name: span
    type: array
    description: "[rowSpan, colSpan] grid cells occupied (default [1, 1])"
  - name: landscape
    type: object
    description: "Placement when an iPhone is on its side: {position, span} or {hidden: true}"
  - name: regular
    type: object
    description: "Placement on an iPad-width page: {position, span} or {hidden: true}"
  - name: name
    type: string
    description: Readable name the editor shows; never used for identity or on the wire
  - name: action
    type: object
    description: Command fired on interaction (an ActionDefinition, see actions)
  - name: longPressAction
    type: object
    description: Action fired on long-press (an ActionDefinition)
  - name: longPressGroup
    type: object
    description: Sub-group popup shown on long-press (a GroupDefinition, see long-press)
  - name: snapshotAction
    type: object
    description: "Camera only: action fired on shutter with {{image}} substitution"
  - name: sync
    type: object[]
    description: Live state listeners (SyncDefinition list, see sync)
  - name: visible
    type: object
    description: Show/hide condition (a VisibilityCondition, see visibility)
  - name: enabled
    type: object
    description: Enable/disable condition (a VisibilityCondition); false dims the control and ignores touches
  - name: role
    values: [submit]
    type: enum
    description: "On a button inside a form group: submit makes pressing it submit the form"
  - name: field
    type: string
    description: "Inside a form group: the draft field this input writes (default the id)"
  - name: theme
    type: object
    description: Per-control theme overrides; same keys as the layout theme block plus per-type keys (see theming)
  - name: unsupportedType
    type: string
    description: Written by the app when it replaces a control type it does not know; never authored
  - name: carouselStyle
    values: [glass, translucent, liquidGlass]
    type: enum
    description: Carousel panel chrome (default glass; translucent and liquidGlass use the material-glass look)
  - name: carouselPeek
    min: 0
    max: 0.3
    step: 0.05
    type: number
    description: Carousel paged mode - neighbour peek as a fraction of the container width, clamped 0 to 0.3
  - name: sortboardConfig
    type: object
    description: Config object for the matching control type; its keys are the sortboardConfig group fields in that control's doc
  - name: compassConfig
    type: object
    description: Config object for the matching control type; its keys are the compassConfig group fields in that control's doc
  - name: pinboardConfig
    type: object
    description: Config object for the matching control type; its keys are the pinboardConfig group fields in that control's doc
  - name: canvasConfig
    type: object
    description: Config object for the matching control type; its keys are the canvasConfig group fields in that control's doc
  - name: symbolConfig
    type: object
    description: Config object for the matching control type; its keys are the symbolConfig group fields in that control's doc
  - name: statTileConfig
    type: object
    description: Config object for the matching control type; its keys are the statTileConfig group fields in that control's doc
  - name: hideBackground
    title: Background on/off
    tab: style
    type: bool
    default: false
    description: Remove the glass card behind the control. The on/off switch in the Background chip (inverted)
  - name: backgroundColor
    edit: background
    title: Background
    tab: style
    type: color
    description: Card fill colour, #RRGGBB or #RRGGBBAA. Absent = the theme surface. Edit hint background = the pose's Background chip (on/off, colour, opacity, glass or solid)
  - name: backgroundOpacity
    title: Background opacity
    tab: style
    type: number
    min: 0
    max: 1
    description: Card fill opacity, 0-1; multiplies any alpha in backgroundColor. Absent = 1
  - name: backgroundMaterial
    title: Glass or solid
    tab: style
    type: enum
    values: [glass, solid]
    description: glass lays a translucent material under the fill; solid is a flat fill. Absent = the theme surface
  - name: backgroundPadding
    title: Padding
    tab: style
    type: number
    min: 0
    max: 32
    step: 1
    default: 8
    edit: scrub
    depth: hold
    under: backgroundColor
    unit: pt
    description: Space between the card edge and the control, in points. Absent = the theme's controlPadding (8)
  - name: backgroundCornerRadius
    title: Corner radius
    tab: style
    type: number
    min: 0
    max: 40
    step: 1
    default: 12
    edit: scrub
    depth: hold
    under: backgroundColor
    unit: pt
    description: Card corner radius in points. Absent = the theme's cornerRadius (12)
  - name: backgroundBorderWidth
    title: Border width
    tab: style
    type: number
    min: 0
    max: 8
    step: 0.5
    default: 1
    edit: scrub
    depth: hold
    under: backgroundColor
    unit: pt
    description: Card border width in points; 0 removes the border. Absent = the theme's borderWidth (1)
  - name: backgroundBorderColor
    title: Border colour
    tab: style
    type: color
    edit: color
    depth: ai
    description: Card border colour, #RRGGBB or #RRGGBBAA. Absent = the theme border
  - name: backgroundShadow
    title: Shadow
    tab: style
    type: number
    min: 0
    max: 24
    step: 1
    default: 0
    edit: scrub
    depth: hold
    under: backgroundColor
    unit: pt
    description: Elevation, the blur radius of a soft drop shadow under the card, in points. 0 = none
  - name: backgroundShadowOpacity
    title: Shadow opacity
    tab: style
    type: number
    min: 0
    max: 1
    step: 0.05
    default: 0.3
    edit: scrub
    depth: hold
    under: backgroundColor
    description: Opacity of the card drop shadow, 0-1. Needs backgroundShadow above 0; off when hideBackground is true
---

Every control — regardless of type — shares the same base fields. A control is one cell (or span of cells) in a tab or [[group-def|group]] grid.

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Control type. One of: `button`, `toggle`, `slider`, `stepper`, `segmentedControl`, `picker`, `datePicker`, `textInput`, `colorPicker`, `label`, `image`, `gauge`, `sparkline`, `progressRing`, `map`, `graph`, `chart`, `pieChart`, `heatmap`, `radar`, `boxPlot`, `gantt`, `sankey`, `treemap`, `chord`, `chat`, `list`, `statusLight`, `logConsole`, `divider`, `spacer`, `webView`, `joystick`, `qrCode`, `camera` |
| `id` | string | Unique identifier. Used for value storage, sync targeting, and visibility references. Any non-empty string unique among the layout's controls and groups; see [[layout-config#Identity]] |
| `position` | [row, col] | Zero-indexed grid cell placement |

## Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `span` | [rowSpan, colSpan] | `[1, 1]` | Grid cells occupied. `colSpan` sets width; in a 2-D grid `rowSpan` sets height (`rowSpan × rowHeight`). Make a control bigger by spanning more cells. See [[grid-dimensions]]. |
| `landscape` | `{position, span}` or `{hidden: true}` | — | Where this control sits when an iPhone is on its side; ignored in portrait. Also writable in the document's `placements` section. See [[grid-dimensions#Landscape and iPad]] |
| `regular` | `{position, span}` or `{hidden: true}` | — | Where this control sits on an iPad-width page. See [[grid-dimensions#Landscape and iPad]] |
| `controlHeight` | number | — | **Override** the grid-derived height with an exact point value. Rarely needed: in a 2-D grid the cell (`rowSpan × rowHeight`) is the height, and in a `flow` grid shaped controls auto-size to their aspect. Use it to pin a height the grid wouldn't otherwise give. See [[grid-dimensions]]. |
| `name` | string | — | Readable name the editor shows for this control (e.g. `"Water level"`). Never used for identity or on the wire; omit it and the editor shows `label`, then the type |
| `label` | string | — | Display label for the control |
| `defaultValue` | bool/number/string, or a seed | — | Initial value before sync. Buffer and dataset controls also take a JSON seed; see [[#defaultValue per type]] |
| `action` | [[actions\|ActionDefinition]] | — | Command fired on interaction |
| `sync` | [[sync\|SyncDefinition]][] | — | Live state listeners |
| `visible` | [[visibility\|VisibilityCondition]] | — | Show/hide condition |
| `enabled` | [[visibility\|VisibilityCondition]] | — | Enable/disable condition: false dims the control and ignores touches |
| `role` | `"submit"` | — | On a [[button]] inside a [[form]] group: pressing it submits the form |
| `field` | string | the `id` | Inside a [[form]] group: the draft field this input writes |
| `haptic` | string | varies by type | Haptic feedback profile. See [[haptics]] |
| `confirm` | bool | `false` | "Show confirmation": after each of this control's local writes, a 3-second pill naming the change, with Undo. See [[actions#Confirmation and Undo]] |
| `animation` | string or object | varies by type | Animation override. See [[animations]] |
| `longPressAction` | [[actions\|ActionDefinition]] | — | Action fired on long-press |
| `longPressGroup` | [[long-press\|GroupDefinition]] | — | Sub-group popup on long-press |
| `theme` | object | — | Per-control theme overrides (see below) |
| `extensions` | object | — | Tool data keyed by reverse-DNS name; preserved, never interpreted, 64 KB cap. See [[document-contract#Extensions]] |
| `fallback` | object | — | The control an older app shows instead when it doesn't know this `type` (a control object, or a `group`; may chain up to 4 hops). It takes this control's `id`, `position` and `span`; ignored by an app that knows the type. See [[layout-config#Requires and fallback]] |

## Style Fields (shared)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `icon` | string | — | SF Symbol name |
| `tint` | string | `"#667eea"` | Hex color for accents |
| `style` | string | varies | Style variant (per control type) |
| `hideLabel` | bool | `false` | Suppress the label |
| `emptyText` | string | `"No <label> yet"` | list/table: line shown when there are no rows |
| `hideValue` | bool | `false` | Hide the numeric readout (e.g. a ring/gauge's center value) so the control becomes a pure compact visual that scales to fill its cell. Also hides slider and stepper readouts while preserving interaction and accessibility |
| `hideBackground` | bool | `false` | Remove the glass card behind the control — it floats on the page and fills its cell. Pairs with `hideValue` for a minimal glyph |
| `backgroundColor` | string | — | Card fill colour, `#RRGGBB` or `#RRGGBBAA`. Absent = the theme surface |
| `backgroundOpacity` | number | `1` | Card fill opacity, 0–1 (multiplies any alpha in `backgroundColor`) |
| `backgroundMaterial` | string | — | `glass` (translucent material under the fill) or `solid`. Absent = the theme surface |
| `backgroundPadding` | number | `8` | Card inner padding in points, 0–32. Absent = the theme `controlPadding` |
| `backgroundCornerRadius` | number | `12` | Card corner radius in points, 0–40. Absent = the theme `cornerRadius` |
| `backgroundBorderWidth` | number | `1` | Card border width in points, 0–8 (0 = none). Absent = the theme `borderWidth` |
| `backgroundBorderColor` | string | — | Card border colour, `#RRGGBB` or `#RRGGBBAA`. Absent = the theme border |
| `backgroundShadow` | number | `0` | Card drop-shadow blur radius (elevation) in points, 0–24 |
| `backgroundShadowOpacity` | number | `0.3` | Card drop-shadow opacity, 0–1 (shadow needs `backgroundShadow` > 0; off when `hideBackground`) |
| `formatValue` | string | — | Number formatter for displayed values (see below) |
| `lineCap` | string | `"round"` | Cross-control attribute (aif-wakfb.8): `"round"` or `"butt"` ends on a ring or dial arc (progressRing, gauge) |
| `lineWidth` | number | auto | Cross-control attribute (aif-wakfb.8): trend-line stroke in points, 0.5–12 (sparkline auto-scales, statTile 2; chart takes the same name in `chartConfig`) |
| `glow` | number | `0.3` | statusLight: halo strength behind the light, 0–1 |
| `valueSize` | number | `34` | statTile: point size of the big number, 14–80 |
| `barCornerRadius` | number | `4` | progressRing: corner rounding of the linear bar, 0–30 pt. A cross-control attribute: chart, gantt and boxPlot take the same name in their config (defaults 3, 5, 3), and treemap, heatmap and sankey take `cellCornerRadius` the same way. Catalogue row 4 in docs/superpowers/specs/2026-10-27-cross-control-attributes.md |
| `glowRadius` | number | `0` | Soft glow behind the control's data mark (arc, ring, line, bars, slices, glyph, text) in the mark's own colours, 0–30 pt. A cross-control attribute: the same name, range, unit and default wherever a control lists it (gauge, progressRing, sparkline, statTile, chart, radar, pieChart, symbol, label; graph's node glow is `graphConfig.glowRadius`, default 6). The catalogue is docs/superpowers/specs/2026-10-27-cross-control-attributes.md |
| `lineCap` | enum | `round` | End shape of the control's stroked marks: `round`, `butt` or `square`. A cross-control attribute: the same name, values and default wherever a control lists it (gauge track, arc and segments; progressRing ring and linear bar; sparkline; statTile curve; chart lines; radar outline corners). The catalogue is docs/superpowers/specs/2026-10-27-cross-control-attributes.md |

**Edit hint — the Background chip.** `backgroundColor` carries `edit: background`: every control's edit pose shows one Background chip whose pop-out holds the on/off switch (`hideBackground`), colour swatches and a custom colour, an opacity slider (0–100 %) and Glass | Solid. A control's own doc need not repeat it; the pose adds the chip to every control. Groups keep only `hideBackground`.

**Hold petals under the Background chip.** Press and hold the chip: padding, corner radius, border width and shadow fan out as `scrub` petals (`depth: hold`, `under: backgroundColor`, `unit: pt`). Their dials snap to 0, the theme default (padding 8, corner 12, border 1) and 4, 8, 12, 16, 20, 24 pt. `backgroundBorderColor` stays at AI depth. The card chrome (`controlSurface`) draws all five once for every control; absent fields reproduce the theme look exactly.

## Value Types

Controls store their value as one of three types:

| Type | JSON | Used by |
|------|------|---------|
| Boolean | `true`/`false` | toggle |
| Number | `42`, `3.14` | slider, stepper, gauge, progressRing, sparkline |
| String | `"text"` | label, textInput, segmentedControl, picker, datePicker, colorPicker, image, map, camera (last scanned value) |

### defaultValue per type

`defaultValue` is what a control shows before its first sync, in the shape that sync
would deliver:

| Control | `defaultValue` |
|---------|----------------|
| scalar controls (toggle, slider, stepper, gauge, progressRing, label, picker, …) | a bool, number or string |
| sparkline | a number, or an **array of numbers** that seeds the series (`[41, 40, 39]`; trimmed to `sparklinePoints`; the readout shows the last point) |
| list | an **array of row objects**, the rows shown until the first sync |
| logConsole | an **array of lines** (strings or `{text, level}` objects) |
| chart, pieChart, heatmap, radar, boxPlot, gantt, sankey, treemap, chord, graph, cardList, sortboard, pinboard, canvas, map | the control's dataset, as JSON (`{"series": […]}`) or as that JSON encoded in a string |

A seed may be at most 4 KB once encoded (the string cap). Saving keeps it exactly as
written: an array stays an array. A seed on any other control, or
a seed of the wrong shape (a sparkline array with no numbers), is dropped with a
"Repaired on load" note: one control's `defaultValue` never stops a layout loading.

## Value Formatters

`formatValue` formats numeric values for `label`, `gauge`, `progressRing`, `slider`, and `stepper`.

| Format | Example input | Output |
|--------|---------------|--------|
| `percent` | `50.8` | `50.8%` |
| `decimal:N` | `3.14159` | `decimal:2` → `3.14`; N clamps to 0–12 |
| `suffix:X` | `63.5` | `suffix:°C` → `63.5°C` |
| `bytes` | `1048576` | `1.00 MB` |
| `bytesKB` | `873740` | source is **KB** → `853.26 MB` |
| `bps` | `1500000` | `1.50 Mbps` |
| `duration` | `3725` | `1h 2m` |
| `time` | `125` | `2:05` |
| `relative` | `"2026-09-22T08:15:00Z"` / epoch | `4 days ago`, `In 2 hours` (label + widget slots; a date, not a number) |
| `relative:day` | `"2026-09-25"` | `Yesterday` — whole local calendar days; no date → `placeholder` (`Never`) |
| `date` | `"2026-09-25"` | `Sep 25, 2026` — the date itself (label); no date → `placeholder` |
| `date:time` | `"2026-09-25T14:03:00Z"` | `Sep 25, 2026 at 2:03 PM` (label) |

Numeric readouts preserve positive step precision (for example, `step: 0.01` shows `0.12`, and `step: 0.25` shows `0.25`). Precision is capped at 12 decimal places. Non-finite values display `—`; `none` still hides them. Negative time and duration values use one leading minus sign. Times outside the integer range display seconds in scientific notation instead of failing conversion.

## Per-Control Theme Overrides

The `theme` object overrides theme values for a single control. It accepts the same keys as the layout [[theming|theme]] block, plus per-type keys for the control's family:

```json
{
  "type": "toggle",
  "id": "wifi",
  "label": "Wi-Fi",
  "theme": {
    "accentColor": "#34C759",
    "cornerRadius": 20,
    "fontDesign": "rounded",
    "trackActiveColor": "#34C759",
    "knobColor": "#FFFFFF"
  }
}
```

Common override keys: `accentColor`, `foregroundColor`, `secondaryColor`, `surfacePrimary`, `borderColor`, `borderWidth`, `cornerRadius`, `controlPadding`, `fontFamily`, `fontDesign`, `labelFontSize`, `valueFontSize`. Toggle/slider/progress controls also accept `trackColor`, `trackActiveColor`, `thumbColor`, `knobColor`, etc. See each control's **Theme Overrides** table for its specific keys, and [[theming]] for the full system.

## Look card formats and presets (doc frontmatter)

A control doc may declare two optional one-line JSON lists that the editor's
**Look** card turns into chips. Neither is a layout field: they are named sets of
ordinary field writes.

- `lookFormats`: how the value shows (Text: Plain / Number / Last time / Date;
  Dial: Dial / Ring / Bar).
- `lookPresets`: 2 to 4 named looks ("Headline", "Big number", "Quiet").

Each item is `{"id", "name", "symbol", "set"}`: `symbol` is an SF Symbol name (never
an emoji), `set` maps field names to the values the chip writes, and `null` removes
the field (back to the doc default). A `set` may change `type` between
interchangeable controls (Dial's **Bar** turns a gauge into a `progressRing` bar).
A chip shows as chosen when the control already carries every value in its `set`.

## Related
- [[grid-dimensions]] — how `position` / `span` map to size; grid modes
- [[group-def]] — containers for controls
- [[layout-config]] — the top-level structure
- [[layout-config#Requires and fallback]] — `fallback` and `requires` for older apps
- [[theming]] — Theme system & live theme builder
- [[appearance]] — App shell appearance (color scheme, header, background)
- [[actions]] — How `action` and `longPressAction` work
- [[sync]] — How `sync` delivers live values
- [[visibility]] — How `visible` and `enabled` work
- [[haptics]] — Haptic profile names
- [[animations]] — Animation profile names and overrides
