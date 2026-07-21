---
type: layout-config
label: Layout Config
icon: square.grid.2x2
category: models
fields:
  - name: name
    type: string
    description: Display name (required)
  - name: version
    type: number
    description: Schema version (required)
  - name: headerTitle
    type: string
    description: Title shown in the header bar
  - name: accentColor
    type: string
    description: Hex accent color (e.g. "#5AC8FA")
  - name: appearance
    type: object
    description: App shell appearance (color scheme, header, background image)
  - name: theme
    type: object
    description: Visual theme (colors, fonts, spacing)
  - name: connection
    type: object
    description: WebSocket connection config
  - name: tabs
    type: object[]
    description: Tab page definitions (required)
  - name: pollGroups
    type: object
    description: Periodic polling configuration
  - name: dynamicTabs
    type: object[]
    description: Runtime-injected tabs
  - name: sources
    type: object
    description: Named external data sources (MQTT brokers, HTTP APIs)
---

Top-level JSON structure for a CAR-TER remote.

```json
{
  "name": "My Remote",
  "headerTitle": "CAR-TER",
  "version": 1,
  "accentColor": "#667eea",
  "appearance": {
    "colorScheme": "system",
    "showHeader": true,
    "statusBarStyle": "auto",
    "backgroundImage": { ... }
  },
  "theme": {
    "fontFamily": "Times New Roman",
    "accentColor": "#667eea",
    "cornerRadius": 12
  },
  "connection": { "url": "...", "identity": {...} },
  "sources": { "broker": { "type": "mqtt", "url": "mqtt://..." } },
  "tabs": [ ... ],
  "pollGroups": { ... },
  "dynamicTabs": [ ... ]
}
```

`connection` (a MeshSocket server) and `sources` ([[sources]] — MQTT/HTTP) are
both optional and freely mixed; a layout can run entirely on sources with no
server at all.

## Appearance

Controls the app shell — color scheme, header visibility, status bar, and background image.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `colorScheme` | `"dark"` / `"light"` / `"system"` | `"system"` | Color scheme. `"system"` follows the device setting. |
| `showHeader` | bool | `true` | Show/hide the header bar |
| `statusBarStyle` | `"auto"` / `"light"` / `"dark"` | `"auto"` | Status bar content color. `"auto"` derives from colorScheme. |
| `header` | object | transparent | Header bar style (transparent / material / color) — see [[appearance]] |
| `backgroundImage` | object | — | Background image config (see below) |

### Background Image

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | string | — | Remote image URL (loaded async) |
| `asset` | string | — | Bundled image asset name |
| `contentMode` | `"fill"` / `"fit"` | `"fill"` | Image scaling mode |
| `blur` | number | — | Gaussian blur radius |
| `opacity` | number | `1.0` | Image opacity (0.0–1.0) |
| `overlay` | string | — | Hex color overlay for readability (e.g. `"#00000080"`) |

## Theme

Controls visual styling — colors, fonts, spacing, and per-control type themes.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `fontFamily` | string | — | Custom font name (e.g. `"Times New Roman"`, `"Courier New"`, `"Helvetica"`) |
| `fontDesign` | string | `"default"` | Font design: `"default"`, `"rounded"`, `"serif"`, `"monospaced"` |
| `labelFontSize` | number | `12` | Label text size |
| `valueFontSize` | number | `14` | Value text size |
| `valueFontWeight` | string | `"semibold"` | Value text weight |
| `accentColor` | string | `"#667eea"` | Primary accent color |
| `accentGradient` | string[] | — | Accent gradient (2+ hex colors) |
| `foregroundColor` | string | white/black | Primary text color |
| `secondaryColor` | string | — | Secondary text color |
| `tertiaryColor` | string | — | Tertiary text color |
| `surfacePrimary` | string | — | Primary surface/card color |
| `surfaceSecondary` | string | — | Secondary surface color |
| `surfaceTertiary` | string | — | Tertiary surface color |
| `pageBackground` | string | — | Page background color |
| `pageBackgroundGradient` | string[] | — | Page background gradient |
| `headerBackground` | string | — | Header bar background color |
| `headerBackgroundGradient` | string[] | — | Header bar gradient |
| `tabBarBackground` | string | — | Tab bar background color |
| `tabBarTint` | string | — | Tab bar icon tint |
| `cornerRadius` | number | `12` | Control corner radius |
| `controlPadding` | number | `8` | Inner control padding |
| `cardPadding` | number | `12` | Group card padding |
| `borderWidth` | number | `1` | Border stroke width |
| `borderColor` | string | — | Border color |
| `blurEnabled` | bool | `true` | Glass material blur |

Fonts set at the theme level propagate to all controls. Per-control overrides are supported via the `theme` field on any control definition.

For **light/dark variants** (`light` / `dark` sub-objects), **per-type sub-themes** (`toggle`, `slider`, `stepper`, `segmented`, `progressBar`), and a live theme builder, see [[theming]].

## Related

- [[sources]] — MQTT/HTTP data sources
- [[theming]] — Full theme system, light/dark variants, live builder
- [[appearance]] — Color scheme, header, status bar, background image
- [[group-def]] — containers within tabs
- [[control-def]] — controls within groups
