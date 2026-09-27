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

Any control can override the theme for itself via its `theme` field — same keys as above plus its family's per-type keys. See [[control-def]]. A [[group-def|group]] takes the same `theme` object and hands it to everything inside it.

## Palette Tokens

Name your colours once in `theme.palette`, then write `"$name"` in any colour field instead of a hex. Recolouring the layout ("make it blue") is then a one-key edit: change the palette entry and every field that refers to it follows.

```json
"theme": {
  "palette": { "brand": "#0A84FF", "leaf": "#34C759", "ink": "#101418" },
  "accentColor": "$brand",
  "pageBackgroundGradient": ["$ink", "#1C2230"],
  "dark": { "foregroundColor": "$leaf" }
}
```

```json
{ "type": "gauge", "id": "c_soil", "tint": "$leaf", "theme": { "trackColor": "$ink" } }
```

- **Where refs work**: any string in a colour position — a key that names a colour (`tint`, `accentColor`, `*Color`, `*Background`, `*Gradient`, `colors`, `fill`, `stroke`), each element of an array under such a key, anything inside a `theme` object (layout, [[group-def|group]] or control, including `light`/`dark` and the per-type sub-themes), and the [[appearance]] `header` fills. A ref in the [[document-contract|`styles` section]] resolves exactly like one written inline.
- **Never rewritten**: labels, text and other non-colour strings, and the wire blocks (`sync`, `action`, `longPressAction`, `connection`, `sources`, `alerts`, `publishers`, `extensions`). A label of `"$brand"` stays `"$brand"`.
- **Palette values** are literal colours (the same hex forms as everywhere else). A value that is itself a `$ref`, is not a string, or has a name other than letters, digits, `_` and `-` is ignored with a warning. Up to 64 tokens.
- **Unknown tokens** (`"$nope"`) never crash and never render black: the field is dropped with a warning ("Repaired on load" in the Layout Hub) and falls back to whatever it would inherit.
- **Resolution happens at load**. The saved file keeps the `$name` refs, so editors (the designer, carterkit, the MCP) edit tokens, not the hexes behind them. Children pushed at runtime into a `dynamic` group or tab are not resolved against the palette: use literal colours there.
- **Lint**: carterkit's `validate_layout` and the MCP warn when a raw colour equals a palette token and suggest the `$name`.

Starting palettes: the playbook theme packs in `layout-library/playbook/themes/<slug>.theme.json` (24 packs of `{theme, appearance, accentColor}`) are the presets; copy one's `theme` and name its colours.

## Cascade

What a control finally draws with, from lowest to highest priority. This is the order `ResolvedTheme` and `GridRenderer` actually apply (pinned by the app's `PaletteTokenTests.cascadeTable`):

| # | Level | Where | Notes |
|---|-------|-------|-------|
| 1 | Built-in defaults | — | Dark glass palette, accent `#667eea` |
| 2 | Light palette | [[appearance]] `colorScheme` | When the layout renders light: black ink, light page `#F2F2F7`, light tracks. Never overrides a key the theme sets |
| 3 | Layout theme | `theme` | The base keys above. Per-type sub-themes (`toggle`, `slider`, …) are built here from the **base** `accentColor` unless they set their own colours |
| 4 | Scheme override | `theme.light` / `theme.dark` | Applied last at the layout level, for the active mode only. Its `accentColor` does **not** re-tint the per-type tracks already built in step 3 |
| 5 | Group theme | group `theme` | Applied over 4 for the group's label, card and every child, recursively through nested groups |
| 6 | Control theme | control `theme` | Applied over 5 for that control. An `accentColor` here also re-points the toggle / slider / stepper / progress tracks that were following the accent |
| 7 | Control tint | control `tint` | Most controls draw their accent as `tint ?? theme accent`, so `tint` beats even the control's own `theme.accentColor` |

Two colour settings are **not** part of the cascade:
- The top-level [[layout-config]] `accentColor` tints the layout's card in the library, the layout switcher and the [[glance]] fallback. It does not colour controls inside the layout; set `theme.accentColor` for that.
- [[appearance]] holds the colour **scheme** and the header fills, not control colours.

Theming levels 3–6 are Pro features: without Pro the layout renders with the default glass theme (level 1–2) and the `theme` fields are ignored. `tint` always applies.

## Related
- [[appearance]] — Color scheme, header, status bar, background image
- [[layout-config]] — Where `theme` lives
- [[control-def]] — Per-control `theme` overrides
- [[group-def]] — Group `theme` overrides and theme surfaces on group cards
- [[document-contract]] — The `styles` section, where per-control `theme`/`tint` may live
