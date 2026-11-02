---
type: theming
label: Theming
icon: paintbrush.pointed.fill
category: models
fields:
  - name: pageBackground
    type: color
    description: Page background
  - name: headerBackground
    type: color
    description: Header bar background
  - name: tabBarBackground
    type: color
    description: Tab bar background
  - name: tabBarTint
    type: color
    description: Tab bar selected tint
  - name: surfacePrimary
    type: color
    description: Card / control surface
  - name: surfaceSecondary
    type: color
    description: Nested surface
  - name: surfaceTertiary
    type: color
    description: Deepest surface
  - name: accentColor
    type: color
    description: Primary accent
  - name: foregroundColor
    type: color
    description: Primary text
  - name: onAccent
    type: color
    description: Text/icon colour drawn on an accent fill
  - name: secondaryColor
    type: color
    description: Secondary text
  - name: tertiaryColor
    type: color
    description: Tertiary text
  - name: borderColor
    type: color
    description: Border stroke
  - name: statusOK
    type: color
    description: OK / success status colour
  - name: statusWarn
    type: color
    description: Warning status colour
  - name: statusError
    type: color
    description: Error status colour
  - name: statusInfo
    type: color
    description: Info status colour
  - name: scrimColor
    type: color
    description: Dimming scrim behind sheets and popups
  - name: pageBackgroundGradient
    type: string[]
    description: Page background gradient (2+ colours)
  - name: headerBackgroundGradient
    type: string[]
    description: Header background gradient (2+ colours)
  - name: accentGradient
    type: string[]
    description: Accent gradient (2+ colours)
  - name: borderWidth
    min: 0
    max: 6
    step: 0.5
    type: number
    description: Border width
  - name: cornerRadius
    min: 0
    max: 40
    step: 1
    type: number
    description: Control/card corner radius
  - name: controlPadding
    min: 0
    max: 32
    step: 1
    type: number
    description: Inner control padding
  - name: cardPadding
    min: 0
    max: 32
    step: 1
    type: number
    description: Group card padding
  - name: compactRadius
    min: 0
    max: 40
    step: 1
    type: number
    description: Radius for compact elements
  - name: controlRadius
    min: 0
    max: 40
    step: 1
    type: number
    description: Radius for controls
  - name: cardRadius
    min: 0
    max: 40
    step: 1
    type: number
    description: Radius for group cards
  - name: compactSpacing
    min: 0
    max: 32
    step: 1
    type: number
    description: Tight spacing
  - name: standardSpacing
    min: 0
    max: 48
    step: 1
    type: number
    description: Standard spacing
  - name: sectionSpacing
    min: 0
    max: 64
    step: 1
    type: number
    description: Spacing between sections
  - name: emphasizedBorderWidth
    min: 0
    max: 8
    step: 0.5
    type: number
    description: Border width for emphasised elements
  - name: labelFontSize
    min: 8
    max: 32
    step: 1
    type: number
    description: Label font size
  - name: valueFontSize
    min: 8
    max: 72
    step: 1
    type: number
    description: Value font size
  - name: readoutFontSize
    min: 8
    max: 96
    step: 1
    type: number
    description: Big readout font size
  - name: captionFontSize
    min: 8
    max: 24
    step: 1
    type: number
    description: Caption font size
  - name: blurEnabled
    type: bool
    description: Glass material blur
  - name: accent
    type: color
    description: Theme token. Accent colour; overrides the pack, loses to a control's own look
  - name: surface
    values: [glass, solid, paper]
    type: enum
    description: Theme token. Surface material
  - name: corners
    values: [sharp, soft, round]
    type: enum
    description: Theme token. Corner shape (4, 12 or 22 pt)
  - name: type
    values: [system, rounded, serif, mono]
    type: enum
    description: Theme token. Type face
  - name: density
    type: number
    min: 0.7
    max: 1.5
    step: 0.05
    description: Theme token. Padding scale
  - name: fontFamily
    type: string
    description: Custom font family name (e.g. Times New Roman)
  - name: fontDesign
    values: [default, rounded, serif, monospaced]
    type: enum
    description: Font design
  - name: valueFontWeight
    type: string
    description: Value font weight (e.g. semibold, bold)
  - name: toggle
    type: object
    description: Per-type toggle sub-theme; keys are the toggle group fields
  - name: slider
    type: object
    description: Per-type slider sub-theme; keys are the slider group fields
  - name: stepper
    type: object
    description: Per-type stepper sub-theme; keys are the stepper group fields
  - name: segmented
    type: object
    description: Per-type segmented sub-theme; keys are the segmented group fields
  - name: progressBar
    type: object
    description: Per-type progressBar sub-theme; keys are the progressBar group fields
  - name: light
    type: object
    description: Overrides applied last when the app is in light mode; keys are the schemeOverride group fields
  - name: dark
    type: object
    description: Overrides applied last when the app is in dark mode; keys are the schemeOverride group fields
  - name: palette
    type: object
    description: Named colours written once, referenced as $name in any colour field
  - name: pageBackground
    group: schemeOverride
    type: color
    description: Page background (scheme override)
  - name: headerBackground
    group: schemeOverride
    type: color
    description: Header bar background (scheme override)
  - name: tabBarBackground
    group: schemeOverride
    type: color
    description: Tab bar background (scheme override)
  - name: tabBarTint
    group: schemeOverride
    type: color
    description: Tab bar selected tint (scheme override)
  - name: surfacePrimary
    group: schemeOverride
    type: color
    description: Card / control surface (scheme override)
  - name: surfaceSecondary
    group: schemeOverride
    type: color
    description: Nested surface (scheme override)
  - name: surfaceTertiary
    group: schemeOverride
    type: color
    description: Deepest surface (scheme override)
  - name: accentColor
    group: schemeOverride
    type: color
    description: Primary accent (scheme override)
  - name: foregroundColor
    group: schemeOverride
    type: color
    description: Primary text (scheme override)
  - name: onAccent
    group: schemeOverride
    type: color
    description: Text/icon colour drawn on an accent fill (scheme override)
  - name: secondaryColor
    group: schemeOverride
    type: color
    description: Secondary text (scheme override)
  - name: tertiaryColor
    group: schemeOverride
    type: color
    description: Tertiary text (scheme override)
  - name: borderColor
    group: schemeOverride
    type: color
    description: Border stroke (scheme override)
  - name: statusOK
    group: schemeOverride
    type: color
    description: OK / success status colour (scheme override)
  - name: statusWarn
    group: schemeOverride
    type: color
    description: Warning status colour (scheme override)
  - name: statusError
    group: schemeOverride
    type: color
    description: Error status colour (scheme override)
  - name: statusInfo
    group: schemeOverride
    type: color
    description: Info status colour (scheme override)
  - name: scrimColor
    group: schemeOverride
    type: color
    description: Dimming scrim behind sheets and popups (scheme override)
  - name: pageBackgroundGradient
    group: schemeOverride
    type: string[]
    description: Page background gradient (2+ colours) (scheme override)
  - name: headerBackgroundGradient
    group: schemeOverride
    type: string[]
    description: Header background gradient (2+ colours) (scheme override)
  - name: accentGradient
    group: schemeOverride
    type: string[]
    description: Accent gradient (2+ colours) (scheme override)
  - name: trackColor
    group: toggle
    type: color
    description: Track colour (off)
  - name: trackActiveColor
    group: toggle
    type: color
    description: Track colour (on)
  - name: trackRadius
    group: toggle
    min: 0
    max: 30
    step: 1
    type: number
    description: Track corner radius
  - name: trackHeight
    group: toggle
    min: 8
    max: 60
    step: 1
    type: number
    description: Track height
  - name: trackWidth
    group: toggle
    min: 20
    max: 100
    step: 1
    type: number
    description: Track width
  - name: knobColor
    group: toggle
    type: color
    description: Knob colour (off)
  - name: knobActiveColor
    group: toggle
    type: color
    description: Knob colour (on)
  - name: knobRadius
    group: toggle
    min: 0
    max: 30
    step: 1
    type: number
    description: Knob corner radius
  - name: knobSize
    group: toggle
    min: 8
    max: 50
    step: 1
    type: number
    description: Knob diameter
  - name: knobShadow
    group: toggle
    type: bool
    description: Draw a shadow under the knob
  - name: trackColor
    group: slider
    type: color
    description: Track colour
  - name: trackActiveColor
    group: slider
    type: color
    description: Filled track colour
  - name: trackRadius
    group: slider
    min: 0
    max: 10
    step: 1
    type: number
    description: Track corner radius
  - name: trackHeight
    group: slider
    min: 2
    max: 20
    step: 1
    type: number
    description: Track height
  - name: thumbColor
    group: slider
    type: color
    description: Thumb colour
  - name: thumbRadius
    group: slider
    min: 0
    max: 20
    step: 1
    type: number
    description: Thumb corner radius
  - name: thumbSize
    group: slider
    min: 8
    max: 40
    step: 1
    type: number
    description: Thumb diameter
  - name: thumbShadow
    group: slider
    type: bool
    description: Draw a shadow under the thumb
  - name: thumbBorderColor
    group: slider
    type: color
    description: Thumb border colour
  - name: thumbBorderWidth
    group: slider
    min: 0
    max: 6
    step: 0.5
    type: number
    description: Thumb border width
  - name: buttonColor
    group: stepper
    type: color
    description: Button fill colour
  - name: buttonRadius
    group: stepper
    min: 0
    max: 30
    step: 1
    type: number
    description: Button corner radius
  - name: buttonSize
    group: stepper
    min: 20
    max: 64
    step: 1
    type: number
    description: Button size
  - name: iconColor
    group: stepper
    type: color
    description: Plus/minus icon colour
  - name: style
    group: stepper
    type: string
    description: Stepper style variant
  - name: trackColor
    group: segmented
    type: color
    description: Track colour
  - name: trackRadius
    group: segmented
    min: 0
    max: 30
    step: 1
    type: number
    description: Track corner radius
  - name: selectedColor
    group: segmented
    type: color
    description: Selected segment fill
  - name: selectedRadius
    group: segmented
    min: 0
    max: 30
    step: 1
    type: number
    description: Selected segment corner radius
  - name: selectedShadow
    group: segmented
    type: bool
    description: Draw a shadow under the selected segment
  - name: textColor
    group: segmented
    type: color
    description: Segment text colour
  - name: selectedTextColor
    group: segmented
    type: color
    description: Selected segment text colour
  - name: trackColor
    group: progressBar
    type: color
    description: Track colour
  - name: trackActiveColor
    group: progressBar
    type: color
    description: Filled track colour
  - name: trackRadius
    group: progressBar
    min: 0
    max: 20
    step: 1
    type: number
    description: Track corner radius
  - name: trackHeight
    group: progressBar
    min: 2
    max: 30
    step: 1
    type: number
    description: Track height
---

The `theme` block on a [[layout-config|layout]] controls colors, fonts, spacing, and per-control-type styling. Every control resolves its appearance from the active theme, and any control can override it locally via its own `theme` field.

The live builder above re-themes a small demo layout as you change values — flip light/dark, pick an accent, and adjust the shape, then copy the generated `theme` block.

## Base Fields

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `accentColor` | color | `#667eea` | Primary accent (gauges, toggles, highlights) |
| `accentGradient` | color[] | — | 2+ color accent gradient |
| `foregroundColor` | color | auto | Primary text (auto: white in dark, black in light) |
| `onAccent` | color | auto | Text/icon colour drawn ON an accent or tint fill (filled buttons, solid stat-tile bands). Auto: white, or black when white would fall under 3:1 on that fill (so `#FFD60A` gets dark ink, `#0A84FF` white). Set it to force one ink everywhere |
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
| `readoutFontSize` | number | `17` | Primary readout size (gauge and stat values) |
| `captionFontSize` | number | `11` | Caption and small-print size |
| `statusOK` | color | `#34C759` | Success: status light on, good delta, log `success` |
| `statusWarn` | color | `#FF9500` | Warning: log `warn`, attention states |
| `statusError` | color | `#FF453A` | Error: status light off, bad delta, log `error` |
| `statusInfo` | color | `#5AC8FA` | Info: log `info` |
| `scrimColor` | color | auto | Wash behind chips and overlays (dark: black 35%, light: white 60%) |

Content tokens only: app chrome (`chrome*`, `glassWave`) is not a layout key and stays with the app.

### Shape & Spacing Ladder

Controls draw from a small scale of radii and spacings rather than one-off numbers.
Every rung is optional. Unset, it derives from the base fields above, so a layout that
sets only `cornerRadius` or `controlPadding` keeps today's look.

| Field | Type | Default (derived) | Description |
|-------|------|-------------------|-------------|
| `compactRadius` | number | `cornerRadius / 3` (`4`) | Small chips, badges, tick marks |
| `controlRadius` | number | `cornerRadius * 2 / 3` (`8`) | Buttons, fields, inner controls |
| `cardRadius` | number | `cornerRadius` (`12`) | Cards and group containers |
| `compactSpacing` | number | `controlPadding / 2` (`4`) | Tight gaps inside a control |
| `standardSpacing` | number | `controlPadding` (`8`) | Default gap between control parts |
| `sectionSpacing` | number | `controlPadding * 2` (`16`) | Gap between groups or sections |
| `emphasizedBorderWidth` | number | `1.5` | The one emphasis stroke beyond `borderWidth` |

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

A `light` / `dark` block accepts: `pageBackground`, `pageBackgroundGradient`, `headerBackground`, `headerBackgroundGradient`, `tabBarBackground`, `tabBarTint`, `surfacePrimary/Secondary/Tertiary`, `foregroundColor`, `onAccent`, `secondaryColor`, `tertiaryColor`, `borderColor`, `accentColor`, `accentGradient`, `statusOK`, `statusWarn`, `statusError`, `statusInfo`, `scrimColor`.

> The whole app stays in lockstep with the device color scheme — see [[appearance]] for `colorScheme`.

**System layouts carry both palettes.** With `colorScheme: system` (or none) the layout follows the device, so a palette written for one scheme breaks contrast in the other. The editor keeps such a layout balanced: scheme-sensitive colours live in `light` and `dark`, both blocks colour the same slots, and in each the text clears 4.5:1 on the page and the accent 3:1 (a missing palette is derived from the other, same hue with the lightness flipped). A layout that sets no page colours keeps the built-in palettes, which already flip. Layouts pinned to `dark` or `light` are not touched.

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
- **Resolution happens at load**. The saved file keeps the `$name` refs, so editors (the designer, carterkit, the MCP) edit tokens, not the hexes behind them. Children pushed at runtime into a `dynamic` group or tab resolve against the active layout's palette the same way, with the same unknown-token fallback.
- **Lint**: carterkit's `validate_layout` and the MCP warn when a raw colour equals a palette token and suggest the `$name`.

Starting palettes: the playbook theme packs in `layout-library/playbook/themes/<slug>.theme.json` (24 packs of `{theme, appearance, accentColor}`) are the presets; copy one's `theme` and name its colours. Each of the 19 packs has a doc in `ControlDocs/themes/<slug>.md` whose frontmatter carries its vibe words, accent, light/dark notes, when to use, specimen reference and the `tokens` object to copy. The numeric style rules (one accent, card alpha `0F`-`24`, `cornerRadius` 14-16, `controlPadding` 12 or less, 10 rows on iPhone, the `64n - 8` cell height, light/dark parity) are in [[style-rules]].

## Cascade

What a control finally draws with, from lowest to highest priority. This is the order `ResolvedTheme` and `GridRenderer` actually apply (pinned by the app's `PaletteTokenTests.cascadeTable`):

| # | Level | Where | Notes |
|---|-------|-------|-------|
| 1 | Built-in defaults | — | Dark glass palette, accent `#667eea` |
| 2 | Light palette | [[appearance]] `colorScheme` | When the layout renders light: black ink, light page `#F2F2F7`, light tracks. Never overrides a key the theme sets |
| 3 | Layout theme | `theme` | The base keys above. Per-type sub-themes (`toggle`, `slider`, `stepper`, `progressBar`) follow the accent unless they set their own colours |
| 4 | Scheme override | `theme.light` / `theme.dark` | Applied last at the layout level, for the active mode only. Its `accentColor` also becomes the accent the per-type tracks follow in that mode (a sub-theme's own colours still win) |
| 5 | Group theme | group `theme` | Applied over 4 for the group's label, card and every child, recursively through nested groups |
| 6 | Control theme | control `theme` | Applied over 5 for that control. An `accentColor` here also re-points the toggle / slider / stepper / progress tracks that were following the accent |
| 7 | Control tint | control `tint` | Most controls draw their accent as `tint ?? theme accent`, so `tint` beats even the control's own `theme.accentColor` |

Two colour settings are **not** part of the cascade:
- The top-level [[layout-config]] `accentColor` tints the layout's card in the library, the layout switcher and the [[glance]] fallback. It does not colour controls inside the layout; set `theme.accentColor` for that.
- [[appearance]] holds the colour **scheme** and the header fills, not control colours.

Theming levels 3–6 are Pro features: without Pro the layout renders with the default glass theme (level 1–2) and the `theme` fields are ignored. `tint` always applies.

## Related
- [[style-rules]] — Machine-checkable style rules from the playbook
- [[appearance]] — Color scheme, header, status bar, background image
- [[layout-config]] — Where `theme` lives
- [[control-def]] — Per-control `theme` overrides
- [[group-def]] — Group `theme` overrides and theme surfaces on group cards
- [[document-contract]] — The `styles` section, where per-control `theme`/`tint` may live
