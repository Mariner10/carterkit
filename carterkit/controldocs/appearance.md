---
type: appearance
depth: complete
label: Appearance
icon: macwindow
category: models
fields:
  - name: colorScheme
    values: [system, dark, light]
    type: enum
    description: Pins the whole app to dark or light, or follows the device
    summary: Light, dark or follow the phone
    does: Switches the whole app between light and dark, or follows the device live.
    valueHelp: {"system": "follow the phone's light or dark setting", "dark": "always dark", "light": "always light"}
  - name: showHeader
    type: bool
    description: Show or hide the header bar
    summary: Show the top bar
    does: Shows or hides the header bar above the grid.
  - name: statusBarStyle
    values: [auto, light, dark]
    type: enum
    description: Status bar content colour
    summary: Colour of the clock and battery
    does: Sets whether the status bar text and icons are light or dark.
    valueHelp: {"auto": "picks whichever reads against the page", "light": "light text for dark backgrounds", "dark": "dark text for light backgrounds"}
  - name: header
    type: object
    description: "Header bar style, e.g. {style: transparent}"
    summary: How the top bar looks
    does: Styles the header bar as see-through, frosted or filled with a colour that extends into the status bar.
  - name: backgroundImage
    type: object
    description: "Page background image: {asset, blur, opacity}"
    summary: A picture behind everything
    does: Draws an image behind all controls on every tab, with optional blur, opacity and overlay.
  - name: backgroundAnimation
    type: object
    description: "Animated page background: {style, colors, speed, intensity}"
    summary: A moving colour backdrop
    does: Animates the page background behind all controls with a hue shift, drifting gradient, aurora or pulse; an unknown style shows the plain page background.
    since: next
---

The `appearance` block on a [[layout-config|layout]] controls the app shell — color scheme, header bar, status bar, and background image. Colors and control styling live in [[theming|theme]]; appearance is about the chrome around your grid.

```json
"appearance": {
  "colorScheme": "system",
  "showHeader": true,
  "statusBarStyle": "auto",
  "header": { "style": "transparent" },
  "backgroundImage": { "asset": "bg", "blur": 20, "opacity": 0.5 }
}
```

## Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `colorScheme` | `dark` / `light` / `system` | `system` | `system` follows the device and adapts the palette live. `dark`/`light` pin the whole app. |
| `showHeader` | bool | `true` | Show or hide the header bar |
| `statusBarStyle` | `auto` / `light` / `dark` | `auto` | Status bar content color |
| `header` | object | transparent | Header bar style (see below) |
| `backgroundImage` | object | — | Page background image (see below) |
| `backgroundAnimation` | object | — | Animated page background (see below) |

## Header

Omit `header` for a **transparent** bar — the page background shows through the bar and the status bar. Provide a color/gradient for a filled bar that **extends up into the status bar**.

| Field | Type | Description |
|-------|------|-------------|
| `style` | `transparent` / `material` / `color` | Inferred as `color` when `light`/`dark` are set; otherwise `transparent` |
| `light` | color or color[] | Fill for light mode — a hex string or a 2+ color gradient |
| `dark` | color or color[] | Fill for dark mode |

```json
"header": {
  "style": "color",
  "dark":  ["#0A0F1E", "#0E1A33"],
  "light": "#EAF0FBF2"
}
```

- **transparent** — no fill; seamless with the page. No divider.
- **material** — frosted glass bar (stays within the safe area).
- **color** — solid or gradient fill that bleeds into the status bar. If the active mode's fill is missing, it falls back to transparent.

## Background Image

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | string | — | Remote image URL (loaded async) |
| `asset` | string | — | Bundled image asset name |
| `contentMode` | `fill` / `fit` | `fill` | Scaling mode |
| `blur` | number | — | Gaussian blur radius |
| `opacity` | number | `1.0` | Image opacity (0–1) |
| `overlay` | color | — | Hex overlay for readability (e.g. `"#00000080"`) |

The image sits above the page background/gradient and below all controls, on every tab.

## Background Animation

An animated page background drawn behind all controls on every tab. An unknown or missing `style` renders the static page background.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `style` | `hueShift` / `gradientDrift` / `aurora` / `pulse` | — | Which animation to run |
| `colors` | color[] (2–6) | theme page background and accent | Hex colours the animation moves between; extras beyond 6 are ignored, fewer than 2 falls back to the theme |
| `light` | color[] (2–6) | `colors` | Colours used in light mode |
| `dark` | color[] (2–6) | `colors` | Colours used in dark mode |
| `speed` | number, 0.1–4 | `1` | Speed multiplier; out-of-range values are clamped |
| `intensity` | number, 0–1 | `0.6` | How strong the colour movement is; clamped |
| `angle` | number, degrees | `0` | Direction of the drift (`gradientDrift` only) |

- **hueShift** — the colours slowly cycle in hue.
- **gradientDrift** — a linear gradient that drifts at `angle`.
- **aurora** — soft blobs of colour that float and blend.
- **pulse** — the colours breathe in and out.

## Examples

### Pin the app to dark
Always dark with a see-through header and light status bar text.
```json
{
"appearance": {
  "colorScheme": "dark",
  "statusBarStyle": "light",
  "header": { "style": "transparent" }
}
}
```

### Filled gradient header
A colored header that follows light and dark mode and extends into the status bar.
```json
{
"appearance": {
  "colorScheme": "system",
  "header": {
    "style": "color",
    "dark": ["#0A0F1E", "#0E1A33"],
    "light": "#EAF0FBF2"
  }
}
}
```

### Blurred photo background
A bundled image behind the grid, softened and darkened for readability, with no header bar.
```json
{
"appearance": {
  "showHeader": false,
  "backgroundImage": { "asset": "bg", "blur": 20, "opacity": 0.5, "overlay": "#00000080" }
}
}
```

### Hue shift background
```json
{ "appearance": { "backgroundAnimation": { "style": "hueShift", "colors": ["#0A0F1E", "#1B2A5C"], "speed": 0.5 } } }
```

### Drifting gradient background
```json
{ "appearance": { "backgroundAnimation": { "style": "gradientDrift", "colors": ["#0A0F1E", "#3A1C71", "#D76D77"], "angle": 45, "intensity": 0.7 } } }
```

### Aurora background
```json
{ "appearance": { "backgroundAnimation": { "style": "aurora", "dark": ["#0B132B", "#1C7C7D", "#6FFFE9"], "light": ["#EAF0FB", "#B5E2FA", "#F9F7F3"], "speed": 1.5 } } }
```

### Pulse background
```json
{ "appearance": { "backgroundAnimation": { "style": "pulse", "colors": ["#111111", "#2D1B69"], "intensity": 0.4, "speed": 0.8 } } }
```

## Related
- [[theming]] — Colors, fonts, per-control styling, light/dark variants
- [[layout-config]] — Where `appearance` lives
