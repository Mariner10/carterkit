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

## Related
- [[theming]] — Colors, fonts, per-control styling, light/dark variants
- [[layout-config]] — Where `appearance` lives
