---
type: theming
label: Theming
icon: paintbrush.pointed.fill
category: models
---

The `theme` block on a [[layout-config|layout]] controls colors, fonts, spacing, and per-control-type styling. Every control resolves its appearance from the active theme, and any control can override it locally via its own `theme` field.

The live builder above re-themes a small demo layout as you change values — flip light/dark, pick an accent, and adjust the shape, then copy the generated `theme` block.

## Base Fields

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `accentColor` | color | `#667eea` | Primary accent (gauges, toggles, highlights) |
| `accentGradient` | color[] | — | 2+ color accent gradient |
| `foregroundColor` | color | auto | Primary text (auto: white in dark, black in light) |
| `secondaryColor` | color | auto | Secondary text |
| `tertiaryColor` | color | auto | Tertiary text |
| `surfacePrimary` | color | auto | Card / control surface |
| `surfaceSecondary` | color | auto | Nested surface |
| `surfaceTertiary` | color | auto | Deepest surface |
| `borderColor` | color | auto | Border stroke |
| `borderWidth` | number | `1` | Border width |
| `cornerRadius` | number | `12` | Control/card corner radius |
| `controlPadding` | number | `8` | Inner control padding |
| `cardPadding` | number | `12` | Group card padding |
| `blurEnabled` | bool | `true` | Glass material blur |
| `fontFamily` | string | — | Custom font (e.g. `"Times New Roman"`) |
| `fontDesign` | string | `default` | `default`, `rounded`, `serif`, `monospaced` |
| `labelFontSize` | number | `12` | Label text size |
| `valueFontSize` | number | `14` | Value text size |
| `valueFontWeight` | string | `semibold` | Value weight |

Colors are hex strings and may include alpha: `"#RRGGBB"` or `"#RRGGBBAA"`.

## Light & Dark Variants

Most palettes differ between modes. Put scheme-sensitive colors in `light` / `dark` sub-objects — they are applied **last**, on top of the base, for the active mode. Keep scheme-neutral values (accent, radius, fonts) in the base.

```json
"theme": {
  "accentColor": "#5AC8FA",
  "cornerRadius": 16,
  "fontDesign": "rounded",
  "dark": {
    "pageBackgroundGradient": ["#0A0F1E", "#0E1A33"],
    "surfacePrimary": "#FFFFFF12",
    "foregroundColor": "#FFFFFF",
    "borderColor": "#FFFFFF1F"
  },
  "light": {
    "pageBackgroundGradient": ["#EAF0FB", "#D7E3F4"],
    "surfacePrimary": "#FFFFFFF2",
    "foregroundColor": "#0B1220",
    "borderColor": "#0B122014"
  }
}
```

A `light` / `dark` block accepts: `pageBackground`, `pageBackgroundGradient`, `headerBackground`, `headerBackgroundGradient`, `tabBarBackground`, `tabBarTint`, `surfacePrimary/Secondary/Tertiary`, `foregroundColor`, `secondaryColor`, `tertiaryColor`, `borderColor`, `accentColor`, `accentGradient`.

> The whole app stays in lockstep with the device color scheme — see [[appearance]] for `colorScheme`.

## Page & Chrome

| Key | Type | Description |
|-----|------|-------------|
| `pageBackground` | color | Solid page background |
| `pageBackgroundGradient` | color[] | Page gradient (top-leading → bottom-trailing) |
| `tabBarBackground` | color | Tab bar fill |
| `tabBarTint` | color | Tab bar icon tint |

Header chrome lives in [[appearance]] (`appearance.header`), not the theme.

## Per-Type Sub-Themes

Fine-tune a whole control family. Each is an object under the theme:

| Sub-theme | Notable keys |
|-----------|--------------|
| `toggle` | `trackColor`, `trackActiveColor`, `knobColor`, `trackWidth`, `trackHeight`, `knobSize`, `knobShadow` |
| `slider` | `trackColor`, `trackActiveColor`, `thumbColor`, `thumbSize`, `thumbBorderColor`, `trackHeight` |
| `stepper` | `buttonColor`, `iconColor`, `buttonSize`, `style` |
| `segmented` | `trackColor`, `selectedColor`, `textColor`, `selectedTextColor` |
| `progressBar` | `trackColor`, `trackActiveColor`, `trackHeight` |

```json
"theme": {
  "toggle": { "trackActiveColor": "#34C759", "knobShadow": true },
  "slider": { "thumbColor": "#FFFFFF", "trackActiveColor": "#5AC8FA" }
}
```

## Per-Control Overrides

Any control can override the theme for itself via its `theme` field — same keys as above plus its family's per-type keys. See [[control-def]].

## Related
- [[appearance]] — Color scheme, header, status bar, background image
- [[layout-config]] — Where `theme` lives
- [[control-def]] — Per-control `theme` overrides
- [[group-def]] — Group cards use theme surfaces
