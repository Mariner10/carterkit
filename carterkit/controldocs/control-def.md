---
type: control-def
label: Control Definition
icon: square.dashed.inset.filled
category: models
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
| `hideValue` | bool | `false` | Hide the numeric readout (e.g. a ring/gauge's center value) so the control becomes a pure compact visual that scales to fill its cell. Also hides slider and stepper readouts while preserving interaction and accessibility |
| `hideBackground` | bool | `false` | Remove the glass card behind the control — it floats on the page and fills its cell. Pairs with `hideValue` for a minimal glyph |
| `formatValue` | string | — | Number formatter for displayed values (see below) |

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
