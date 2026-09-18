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
    bounds: none
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
  - name: keepAwake
    type: bool
    description: Ask to suppress the iOS auto screen lock while this layout is open (a request the user can veto)
  - name: batchPublishers
    type: bool
    description: Send the publishers as one sensor_batch frame per tick of the fastest interval instead of one frame per reading (see publishers)
  - name: glance
    type: object
    description: Widgets, Dynamic Island, lock screen and Control Center surfaces projected from this layout (see glance)
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
  "dynamicTabs": [ ... ],
  "keepAwake": true,
  "glance": { "hero": "cpu", "liveActivity": true, "controls": [ ... ], "widgets": [ ... ] }
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

## Keep awake

A dashboard mounted in a car or on a desk is useless once iOS dims and locks it.
`"keepAwake": true` asks the app to suppress the auto screen lock for as long as
this layout is the one on screen (and CAR-TER is frontmost). A sun pill appears
in the header whenever the screen is being held awake, and tapping it opens the
Permissions panel.

It is a **request, not an order**. Layouts are untrusted JSON, so the user keeps
a veto: Permissions → Data Pipe → "Layouts May Keep Screen Awake" (on by default).

The user can also **designate any layout** as keep-awake from inside the app —
the layout's Layout Info & Permissions sheet (Permissions → Screen → "Keep Screen
Awake") or the Data Pipe card's "Keep “<layout>” Awake" row. Designating simply
writes `"keepAwake": true` into the layout's JSON file (and switching it off removes
the key), so the choice travels with the file and is subject to the same veto.
Independently of any layout, the user's own "Keep Screen Awake" gate can hold the
screen for every layout, or only while [[publishers]] are streaming. The screen is
held whenever *either* path says so.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `keepAwake` | bool | `false` | Hold the screen on while this layout is open, unless the user vetoed layout requests |
| `batchPublishers` | bool | `false` | Publish sensors as one `sensor_batch` frame per tick of the fastest interval — see [[publishers]] |

Battery note: a held screen drains fast off the charger. Reserve it for layouts
that really are the display — a car dashboard, a wall panel, a telemetry source —
not a remote that is glanced at and pocketed.

## Glance surfaces

`glance` projects the layout outside the app: Home/Lock Screen widgets, the
Dynamic Island and lock-screen Live Activity, Control Center / Action-button
controls, StandBy, the watch Smart Stack and CarPlay — kept live by the relay
while the app is closed. Widgets and island regions are **scenes of tiles**
bound to control ids, Control Center tiles are toggles/buttons/cycles/steps,
and a `live` block says how fresh each surface should be. Absent block ⇒ an
auto-derived glance. Full reference: [[glance]].

## Related

- [[glance]] — widgets, Dynamic Island, lock screen, Control Center
- [[sources]] — MQTT/HTTP data sources
- [[theming]] — Full theme system, light/dark variants, live builder
- [[appearance]] — Color scheme, header, status bar, background image
- [[group-def]] — containers within tabs
- [[control-def]] — controls within groups
