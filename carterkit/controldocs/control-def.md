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
| `type` | string | Control type. One of: `button`, `toggle`, `slider`, `stepper`, `segmentedControl`, `picker`, `datePicker`, `textInput`, `colorPicker`, `label`, `image`, `gauge`, `sparkline`, `progressRing`, `map`, `graph`, `chat`, `list`, `statusLight`, `logConsole`, `divider`, `spacer`, `webView`, `joystick`, `qrCode` |
| `id` | string | Unique identifier. Used for value storage, sync targeting, and visibility references |
| `position` | [row, col] | Zero-indexed grid cell placement |

## Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `span` | [rows, cols] | `[1, 1]` | Grid cells occupied (column width; **row count is advisory** — see `controlHeight`) |
| `controlHeight` | number | — | Explicit rendered height in points. The grid lays controls out as natural-height rows, so tall controls (`map`, `list`, `graph`, `sparkline`) need this to claim vertical space. Opt-in: omit to keep the control's intrinsic height. |
| `label` | string | — | Display label for the control |
| `defaultValue` | bool/number/string | — | Initial value before sync |
| `action` | [[actions\|ActionDefinition]] | — | Command fired on interaction |
| `sync` | [[sync\|SyncDefinition]][] | — | Live state listeners |
| `visible` | [[visibility\|VisibilityCondition]] | — | Show/hide condition |
| `haptic` | string | varies by type | Haptic feedback profile. See [[haptics]] |
| `animation` | string or object | varies by type | Animation override. See [[animations]] |
| `longPressAction` | [[actions\|ActionDefinition]] | — | Action fired on long-press |
| `longPressGroup` | [[long-press\|GroupDefinition]] | — | Sub-group popup on long-press |
| `theme` | object | — | Per-control theme overrides (see below) |

## Style Fields (shared)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `icon` | string | — | SF Symbol name |
| `tint` | string | `"#667eea"` | Hex color for accents |
| `style` | string | varies | Style variant (per control type) |
| `hideLabel` | bool | `false` | Suppress the label |
| `hideBackground` | bool | `false` | Remove the glass card background |
| `formatValue` | string | — | Number formatter for displayed values (see below) |

## Value Types

Controls store their value as one of three types:

| Type | JSON | Used by |
|------|------|---------|
| Boolean | `true`/`false` | toggle |
| Number | `42`, `3.14` | slider, stepper, gauge, progressRing, sparkline |
| String | `"text"` | label, textInput, segmentedControl, picker, datePicker, colorPicker, image, map |

## Value Formatters

`formatValue` formats numeric values for `label`, `gauge`, `progressRing`, `slider`, and `stepper`.

| Format | Example input | Output |
|--------|---------------|--------|
| `percent` | `50.8` | `50.8%` |
| `decimal:N` | `3.14159` | `decimal:2` → `3.14` |
| `suffix:X` | `63.5` | `suffix:°C` → `63.5°C` |
| `bytes` | `1048576` | `1.00 MB` |
| `bytesKB` | `873740` | source is **KB** → `853.26 MB` |
| `bps` | `1500000` | `1.50 Mbps` |
| `duration` | `3725` | `1h 2m` |
| `time` | `125` | `2:05` |

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

## Related
- [[group-def]] — containers for controls
- [[layout-config]] — the top-level structure
- [[theming]] — Theme system & live theme builder
- [[appearance]] — App shell appearance (color scheme, header, background)
- [[actions]] — How `action` and `longPressAction` work
- [[sync]] — How `sync` delivers live values
- [[visibility]] — How `visible` works
- [[haptics]] — Haptic profile names
- [[animations]] — Animation profile names and overrides
