---
type: appearance
label: Appearance
icon: macwindow
category: models
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

## Related
- [[theming]] — Colors, fonts, per-control styling, light/dark variants
- [[layout-config]] — Where `appearance` lives
