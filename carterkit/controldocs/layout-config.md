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
    description: The author's revision label (required; never gates anything — see document-contract)
  - name: schemaVersion
    tab: advanced
    min: 1
    max: 2
    type: number
    description: Grammar version, optional (absent = 1); set by writers, bumped only when an older app would misread the file
  - name: extensions
    tab: advanced
    type: object
    description: Reverse-DNS keyed tool data the app preserves and never interprets (64 KB cap; see document-contract)
  - name: requires
    type: object
    description: "The app version and features this layout needs, e.g. {'app': '1.3', 'features': ['control.symbol']}; a soft gate, so an older app still renders what it can and shows one update banner (see Requires and fallback)"
  - name: headerTitle
    type: string
    description: Title shown in the header bar
  - name: accentColor
    tab: style
    type: string
    description: Hex accent for the layout's library card, switcher and glance fallback (e.g. "#5AC8FA"); controls use theme.accentColor (see theming#Cascade)
  - name: appearance
    type: object
    description: App shell appearance (color scheme, header, background image)
  - name: theme
    type: object
    description: Visual theme (colors, fonts, spacing, palette tokens)
  - name: connection
    tab: advanced
    type: object
    description: WebSocket connection config
  - name: tabs
    type: object[]
    description: Tab page definitions (required)
  - name: pollGroups
    tab: advanced
    type: object
    description: Periodic polling configuration
  - name: dynamicTabs
    tab: advanced
    type: object[]
    description: Runtime-injected tabs
  - name: sources
    type: object
    description: Named external data sources (MQTT brokers, HTTP APIs)
  - name: keepAwake
    type: bool
    description: Ask to suppress the iOS auto screen lock while this layout is open (a request the user can veto)
  - name: liveness
    type: object
    description: "Layout-wide staleness default for sync bindings, e.g. {'staleAfter': 120} (opt-in; see sync)"
  - name: batchPublishers
    tab: advanced
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
  "liveness": { "staleAfter": 120 },
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

## Document contract

`schemaVersion` vs `version`, the `extensions` block, reserved keys, provenance,
the sectioned form, the limits table and the asset rule are defined once in
[[document-contract]]. In short: `version` is your revision label and never gates
anything; `schemaVersion` (optional, absent = 1) names the grammar; put tool data
in `extensions`, not in new top-level keys.

## Requires and fallback

A layout written for a newer CAR-TER still opens on an older one. Two optional
keys tell the older app what to do.

**`requires`** (top level) names what the layout needs:

```json
"requires": { "app": "1.3", "features": ["control.symbol", "sync.mqtt", "layout.fallback"] }
```

| Field | Type | Description |
|-------|------|-------------|
| `app` | string | Minimum app version, dotted numbers (`"1.3"`, `"1.2.4"`). Compared number by number |
| `features` | string[] | Feature names, each `name` or `name@N` (`N` a positive integer; absent = 1). Met when the app speaks `name` at version `N` or higher |

Feature names: `control.<type>` (e.g. `control.gauge`), `sync.<method>`
(`meshsocket`, `mqtt`, `http`, `sensor`), `action.<method>` (`meshsocket`, `mqtt`,
`http`), and `layout.requires` / `layout.fallback`. An unknown name is unmet.

`requires` is a **soft gate**. When the app is older than `app`, or lacks a
feature, the layout still loads: it renders everything it can and shows one
update banner listing what is missing. A malformed `requires` (or a malformed
member) is ignored, never a load failure.

**`fallback`** (on any control) is the control to show instead when the app
doesn't know this control's `type`:

```json
{
  "type": "knob", "id": "vol", "position": [0, 0], "span": [2, 2],
  "label": "Volume", "min": 0, "max": 100,
  "fallback": { "type": "slider", "label": "Volume", "min": 0, "max": 100 }
}
```

- The fallback is used **only** when the type is unknown. An app that knows
  `knob` ignores it.
- The fallback takes the original's `id`, `position` and `span`, so it lands in
  the same cell and keeps the same stored value and `sync` targeting. Don't set
  those three on the fallback (any you set are replaced; if the original lacks
  one, the fallback's is removed). Everything else, `label` and `sync` included,
  comes from the fallback itself.
- A fallback may carry its own `fallback`. The app follows the chain up to
  **4** hops and uses the first type it knows.
- A fallback may be a `group` in a tab, group, panel or `longPressGroup`, but
  not in a [[canvas]] item, which hosts one control.
- An unknown control with no usable fallback becomes a quiet placeholder tile in
  its cell (its label, a generic symbol, "Update CAR-TER"), and the app adds
  `control.<type>` to the layout's required features so the update banner
  names it. Saving the layout keeps the original control and its `fallback`.

**Authoring for older apps.** A control doc's frontmatter may carry
`since: "1.3"`: the first app version that knows that control (absent means
every supported app does). carterkit's validator uses it: a control newer than
the target app (the layout's `requires.app`, else the kit's `target_app`, else
the oldest supported app) with no usable `fallback` is reported as
`needs_newer_app`. It is a warning; the kit never adds fallbacks for you.

## Identity

Full rules (layout id = installation, `renameId`): [[document-contract#Identity]].

Every control and group has an `id`, unique among all of the layout's controls
and groups (a tab's `children` and, recursively, group `children`, container
`panels[].children` and `longPressGroup.children`; a panel's or popup's own `id`
is local to its host). A dynamic deck or tab pushed at runtime follows the same
rule and may not reuse one of the layout's ids: the app refuses such a deck. The id is the
stable key for stored values, `sync` targeting, visibility references and edits —
never parse it and never show it to people. Tabs may carry an optional `id` too;
without one the tab's `title` is its id, so give a tab an `id` before renaming it.

- **Hand-written and carterkit ids** stay readable slugs (`"pump-speed"`). They
  remain valid forever and the app never rewrites them.
- **App-created ids** (the on-device editor's add / insert / duplicate / group /
  page) are opaque: `c_` + 6 lowercase hex for controls (`c_7f3a9e`), `g_` for
  groups and pages, `t_` for tabs. Duplicating a group re-mints every id inside it.
- **`name`** (optional, controls and groups) is the readable label the editor
  shows — `name`, else `label`, else the type. It is not identity: names may
  repeat and renaming never moves stored data.
- A duplicate or empty id is repaired on disk loads (a later duplicate becomes
  `id~2`, an empty one `type-N`) and listed in the Layout Hub; strict loads
  (wire, import, join) and carterkit's validator refuse it.

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
| `liveness` | object | none | `{ "staleAfter": seconds }`: layout-wide staleness default for every sync binding; see [Liveness](#liveness) |
| `batchPublishers` | bool | `false` | Publish sensors as one `sensor_batch` frame per tick of the fastest interval — see [[publishers]] |

Battery note: a held screen drains fast off the charger. Reserve it for layouts
that really are the display — a car dashboard, a wall panel, a telemetry source —
not a remote that is glanced at and pocketed.

## Liveness

`"liveness": { "staleAfter": 120 }` sets a layout-wide default for how many
seconds a synced value may go without a new source arrival before it counts as
stale. Staleness is **opt-in**: without this block and without a per-binding
`staleAfter`, values look live forever, as before.

A sync entry's own `staleAfter` overrides this default, and `0` at either level
opts that binding out. Writes that do not come from a source (user gestures,
held or reverted command-ack values, defaults, Studio writes) never refresh the
clock. See [[sync]] for resolution, arrivals, `timestampPath`, and the sensor
heartbeat caveat. A malformed block is ignored rather than failing the layout.

## Glance surfaces

`glance` projects the layout outside the app: Home/Lock Screen widgets, the
Dynamic Island and lock-screen Live Activity, Control Center / Action-button
controls, StandBy, the watch Smart Stack and CarPlay — kept live by the relay
while the app is closed. Widgets and island regions are **scenes of tiles**
bound to control ids, Control Center tiles are toggles/buttons/cycles/steps,
and a `live` block says how fresh each surface should be. Absent block ⇒ an
auto-derived glance. Full reference: [[glance]].

## Related

- [[document-contract]] — versions, extensions, identity, limits, assets
- [[control-def]] `fallback` — what an older app shows for a control it doesn't know
- [[glance]] — widgets, Dynamic Island, lock screen, Control Center
- [[sources]] — MQTT/HTTP data sources
- [[theming]] — Full theme system, light/dark variants, live builder
- [[appearance]] — Color scheme, header, status bar, background image
- [[group-def]] — containers within tabs
- [[control-def]] — controls within groups
