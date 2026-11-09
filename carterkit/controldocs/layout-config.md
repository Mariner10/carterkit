---
type: layout-config
depth: complete
label: Layout Config
icon: square.grid.2x2
category: models
fields:
  - name: name
    type: string
    description: Display name (required)
    summary: The layout's name
    does: Names the layout in the library and switcher.
  - name: version
    bounds: none
    type: number
    description: The author's revision label (required; never gates anything — see document-contract)
    summary: Your revision number
    does: Records your own revision label for the layout; it never changes how the layout loads.
  - name: schemaVersion
    tab: advanced
    min: 1
    max: 2
    type: number
    description: Grammar version, optional (absent = 1); set by writers, bumped only when an older app would misread the file
    summary: Format version
    does: Tells the app which layout grammar the file uses; leave it out for the original one.
  - name: extensions
    tab: advanced
    type: object
    description: Reverse-DNS keyed tool data the app preserves and never interprets (64 KB cap; see document-contract)
    summary: Other tools' notes
    does: Stores other tools' data in the file; the app keeps it and never uses it.
  - name: requires
    type: object
    description: "The app version and features this layout needs, e.g. {'app': '1.3', 'features': ['control.symbol']}; a soft gate, so an older app still renders what it can and shows one update banner (see Requires and fallback)"
    summary: What the layout needs
    does: Names the app version and features the layout needs; an older app still opens it and shows one update banner.
  - name: headerTitle
    type: string
    description: Title shown in the header bar
    summary: Title at the top
    does: Shows this text in the header bar.
  - name: accentColor
    tab: style
    type: string
    description: Hex accent for the layout's library card, switcher and glance fallback (e.g. "#5AC8FA"); controls use theme.accentColor (see theming#Cascade)
    summary: Layout's signature color
    does: Colors the layout's card in the library, the switcher and the glance fallback.
  - name: appearance
    type: object
    description: App shell appearance (color scheme, header, background image)
    summary: Look of the app shell
    does: Sets light or dark mode, the header, the status bar and the background image.
  - name: theme
    type: object
    description: Visual theme (colors, fonts, spacing, palette tokens)
    summary: Colors, fonts and spacing
    does: Sets the colors, fonts and spacing that every control in the layout inherits.
  - name: connection
    tab: advanced
    type: object
    description: WebSocket connection config
    summary: Link to a server
    does: Sets how the layout connects to a MeshSocket server.
  - name: tabs
    type: object[]
    description: Tab page definitions (required)
    summary: The pages
    does: Defines the tab pages that hold the layout's controls.
  - name: pollGroups
    tab: advanced
    type: object
    description: Periodic polling configuration
    summary: Repeating refreshes
    does: Defines groups of requests the app repeats on a timer.
  - name: dynamicTabs
    tab: advanced
    type: object[]
    description: Runtime-injected tabs
    summary: Pages added while running
    does: Lists tabs that a server can add to the layout while it is open.
  - name: sources
    type: object
    description: Named external data sources (MQTT brokers, HTTP APIs)
    summary: Where data comes from
    does: Names the MQTT brokers and web APIs that controls read from and write to.
  - name: secrets
    tab: advanced
    type: object[]
    description: "Credentials the layout's {{secret:name}} placeholders use: name, label, kind, hosts, mesh, allowInsecureHTTP. Names only; the values live in the phone's Keychain (see Secrets)"
    summary: Passwords kept on the phone
    does: Declares the secret names whose values stay in the phone's Keychain and fill in {{secret:name}} placeholders.
  - name: derive
    type: object
    description: "Values computed on the phone from other values, keyed by id, e.g. {'watts': {'mul': [{'control': 'volts'}, {'control': 'amps'}]}} (see derive)"
    summary: Math on other values
    does: Computes new values on the phone from other controls' values, for controls to show.
  - name: keepAwake
    type: bool
    description: Ask to suppress the iOS auto screen lock while this layout is open (a request the user can veto)
    summary: Stop the screen sleeping
    does: Asks the phone not to auto-lock while this layout is on screen, unless the user has turned this off.
  - name: liveness
    type: object
    description: "Layout-wide staleness default for sync bindings, e.g. {'staleAfter': 120} (opt-in; HTTP polls use max(this, 3x interval); see sync)"
    summary: When data counts as old
    does: Sets how many seconds a synced value may go without an update before it shows as stale.
  - name: batchPublishers
    tab: advanced
    type: bool
    description: Send the publishers as one sensor_batch frame per tick of the fastest interval instead of one frame per reading (see publishers)
    summary: Send sensors together
    does: Sends all sensor readings in one message per tick instead of one message per reading.
  - name: glance
    type: object
    description: Widgets, Dynamic Island, lock screen and Control Center surfaces projected from this layout (see glance)
    summary: Outside-the-app views
    does: Sets the widgets, Dynamic Island, lock screen and Control Center tiles built from this layout.
  - name: id
    type: string
    description: Stable layout identifier (see Identity); default scope for a local store namespace
    summary: Layout's unique key
    does: Identifies the layout for its saved data; installing a layout with the same id replaces the old one.
  - name: alerts
    type: object[]
    description: Alert rules the app evaluates on incoming events (id, event, valuePath, ...)
    summary: Notification rules
    does: Lists rules that check incoming events and raise an alert when one matches.
  - name: state
    type: object
    description: "State sync config: lets the layout's own control values sync through a mesh"
    summary: Share control values
    does: Lets the layout's own control values sync between devices through a mesh.
  - name: publishers
    type: object[]
    description: "Sensor publishers: device sensors streamed out as readings (see publishers)"
    summary: Send sensor readings out
    does: Streams the phone's sensors out as readings to a server.
  - name: sensorSetup
    type: object
    description: Which device sensors and permissions the layout asks the user to set up (see sensors)
    summary: Sensors to set up
    does: Lists the device sensors and permissions the layout asks the user to turn on.
  - name: sampleValues
    type: object
    description: "Control id to placeholder value: display only. Shown by Try and previews, and on the live page by a control with no value of its own until its first real one; never sent, saved or published. Applies without a tap unless a sample holds a link (see Sample values)"
    summary: Preview numbers
    does: Gives controls stand-in values that show until real data arrives; they are never sent.
  - name: hubSurfaces
    since: next
    tab: advanced
    type: object
    edit: surfaces
    depth: surface
    chip: Hub
    description: "What the layout's hub may draw in the app: false for nothing, or an object of the [[hub-surfaces]] keys (progress, toast, haptic, island, log), each default on; absent = all on. The person's own off wins (see docs/HUB-SURFACES.md)"
    summary: What your hub may show
    does: Lets the layout's hub show progress, toasts, haptics, logs and Island tasks, or turns each one off.
  - name: url
    group: connection
    type: string
    description: WebSocket URL of the mesh server
    summary: Server address
    does: Sets the WebSocket address of the mesh server to connect to.
  - name: token
    group: connection
    type: string
    description: Auth token; prefer a {{secret:name}} placeholder, never a literal secret
    summary: Server password
    does: Sends this token to authenticate with the server; use a secret placeholder, not the real value.
  - name: mode
    group: connection
    values: [pair, room]
    type: enum
    description: pair connects to one peer; room joins a shared room
    summary: Pair or room
    does: Chooses whether the layout connects to one peer or joins a shared room.
    valueHelp: {"pair": "connects to a single other device", "room": "joins a shared room with many devices"}
  - name: identity
    group: connection
    type: object
    description: "Who this device presents as: {name, ...}"
    summary: Who this device is
    does: Sets the name and details this device presents to the others.
  - name: e2eeKey
    group: connection
    type: string
    description: End-to-end encryption key or {{secret:name}} placeholder
    summary: Encryption key
    does: Encrypts the messages end to end with this key, so only devices holding it can read them.
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
  "secrets": [ { "name": "ha_token", "label": "Home Assistant token" } ],
  "tabs": [ ... ],
  "pollGroups": { ... },
  "dynamicTabs": [ ... ],
  "derive": { "watts": { "mul": [ {"control": "volts"}, {"control": "amps"} ] } },
  "keepAwake": true,
  "liveness": { "staleAfter": 120 },
  "glance": { "hero": "cpu", "liveActivity": true, "controls": [ ... ], "widgets": [ ... ] }
}
```

`connection` (a MeshSocket server) and `sources` ([[sources]] — MQTT/HTTP) are
both optional and freely mixed; a layout can run entirely on sources with no
server at all.

Each tab is `{ "id", "title", "icon", "grid", "children" }`. `icon` is an SF Symbol
name and may be left out: a missing, empty or non-string `icon` shows `square.grid.2x2`.
A tab may also carry an optional `palette`: the [[theming]] palette object (colour roles such as `primary`) for
that page only, merged over the layout's `theme.palette` (see theming "Colour roles").

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

## Examples

### A one-page remote
A minimal layout with a header title, an accent color and a single dial on one page.
```json
{
  "name": "Garage",
  "version": 1,
  "headerTitle": "Garage",
  "accentColor": "#5AC8FA",
  "tabs": [
    {
      "title": "Home",
      "children": [
        { "type": "gauge", "id": "temp", "position": [0, 0], "label": "Temperature", "min": 0, "max": 50 }
      ]
    }
  ]
}
```

### A wall display that stays on
A dashboard that holds the screen awake, follows the device's light or dark setting and marks readings stale after two minutes.
```json
{
  "name": "Wall Panel",
  "version": 1,
  "keepAwake": true,
  "liveness": { "staleAfter": 120 },
  "appearance": { "colorScheme": "system", "showHeader": false },
  "tabs": [
    {
      "title": "Status",
      "children": [
        { "type": "gauge", "id": "load", "position": [0, 0], "label": "Load", "min": 0, "max": 100 }
      ]
    }
  ]
}
```

### A computed value with a secret
A layout that reads from a web API with a token kept on the phone and shows a computed value on a dial.
```json
{
  "name": "Power",
  "version": 1,
  "sources": {
    "ha": { "type": "http", "baseURL": "https://ha.local:8123", "headers": { "Authorization": "Bearer {{secret:ha_token}}" } }
  },
  "secrets": [ { "name": "ha_token", "label": "Home Assistant token", "kind": "token" } ],
  "derive": { "watts": { "mul": [ { "control": "volts" }, { "control": "amps" } ] } },
  "tabs": [
    {
      "title": "Energy",
      "children": [
        { "type": "gauge", "id": "volts", "position": [0, 0], "label": "Volts", "min": 0, "max": 250 },
        { "type": "gauge", "id": "amps", "position": [1, 0], "label": "Amps", "min": 0, "max": 30 },
        { "type": "gauge", "id": "power", "position": [0, 1], "label": "Watts", "min": 0, "max": 7500, "sync": [ { "method": "derive", "from": "watts" } ] }
      ]
    }
  ]
}
```

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
(`meshsocket`, `mqtt`, `http`, `sensor`, `derive`), `action.<method>` (`meshsocket`, `mqtt`,
`http`), and `layout.requires` / `layout.fallback` / `layout.derive`. An unknown name is unmet.

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

## Secrets

A password, API key or bearer token does not belong in the layout JSON: anyone
who receives the file (a share, an export, an MCP readback) receives the
credential. Write a `{{secret:name}}` placeholder instead and declare the name
in `secrets`. The phone keeps the value in its Keychain, on this device only,
under this layout and that name. The layout stores only the placeholder.

```json
"sources": {
  "ha": { "type": "http", "baseURL": "https://ha.local:8123",
          "headers": { "Authorization": "Bearer {{secret:ha_token}}" } },
  "broker": { "type": "mqtt", "url": "mqtts://broker.local",
              "username": "ha", "password": "{{secret:mqtt_password}}" }
},
"secrets": [
  { "name": "ha_token", "label": "Home Assistant token", "kind": "token" },
  { "name": "mqtt_password", "label": "Broker password", "kind": "password" },
  { "name": "webhook_key", "hosts": ["hooks.example.com"] },
  { "name": "room_pin", "mesh": true }
]
```

| Field | Type | Meaning |
|---|---|---|
| `name` | string | The `name` in `{{secret:name}}` (required). |
| `label` | string | The name the phone shows for this secret. |
| `kind` | string | `token`, `password` or `apiKey`. A hint for how the phone asks; other values still load. |
| `hosts` | string[] | The only hosts this secret may be sent to. Replaces the default set (below). |
| `mesh` | bool | Allow this secret in a MeshSocket action payload. Default `false`. |
| `allowInsecureHTTP` | bool | Allow this secret on a plain `http://` request or a non-TLS `mqtt://` broker (a LAN device with no TLS). Default `false`: such a request is not sent. |

**Where a placeholder works.** The value is filled in at the moment a request
goes out, and only in the parts of the layout you wrote: an HTTP source's or
action's `headers`, the path and query of a sync or action `url`/`path`, an
HTTP or MQTT action `payload`, an MQTT source's `username` / `password`, and a
MeshSocket action `payload` (only with `mesh: true`). It is never filled in
while the layout loads, and never in an export, the studio mirror, readback or
telemetry. Those always carry the placeholder. A value a control produces (a
typed `{{value}}`, a peer's synced value, a scanned QR code) is inserted as
plain text: a `{{secret:x}}` typed into a text field is sent as those
characters, never as the secret. A placeholder in a URL's host or port is
refused.

**Where the value may go.** A secret is sent only to a destination its
declaration allows:

- **Default:** the hosts of the layout's declared `sources` (each HTTP
  `baseURL` host and MQTT broker host). These are the servers the layout
  already talks to, and no others.
- **`hosts`** replaces that set for one secret. List a host here when an action
  or sync names an absolute `url` on another host, or to narrow a secret to one
  of several sources.
- **`mesh: true`** also lets the secret ride in a MeshSocket action payload.
  Every peer in the room can read that payload, so it is off by default.

A placeholder whose name is not declared still resolves by name, under the
default rule.

**When a request cannot be sent.** The request is dropped and the data pipe in
the header turns red with the reason:

| Detail | Cause |
|---|---|
| `needs secret ha_token` | No value is stored for that name on this phone. |
| `secret ha_token not allowed for host h` | The request's host is not in the secret's allowed hosts. |
| `secret ha_token not allowed for the mesh` | A MeshSocket action carries a secret without `mesh: true` (logged; the action is not sent). |
| `secret cannot be placed in the url` | The placeholder sits in a host or port, or the URL cannot be parsed. |

carterkit writes this block with `ui.secret(...)` and the placeholder with
`bind.secret("name")`. Its validator warns when a literal credential is
embedded, when a placeholder's destination is not allowed, and when a secret
rides a mesh action without `mesh: true`.

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
`staleAfter`, values look live forever, as before. HTTP polls are the exception:
one without its own `staleAfter` goes stale at the larger of this default and
3 x its poll interval (3 x the interval when this block is absent).

A sync entry's own `staleAfter` overrides this default, and `0` at either level
opts that binding out (a layout `0` covers HTTP polls too). Writes that do not come from a source (user gestures,
held or reverted command-ack values, defaults, Studio writes) never refresh the
clock. See [[sync]] for resolution, arrivals, `timestampPath`, and the sensor
heartbeat caveat. A malformed block is ignored rather than failing the layout.

## Derive

`derive` computes values on the phone from other values: a closed JSON op tree
(`add`, `mul`, `avg`, `clamp`, `scale`, `band`, `since`, ...) keyed by id. A
control shows one with `"sync": [{"method": "derive", "from": "watts"}]`.
Derived values never go on the wire; every device computes its own. Full
reference: [[derive]].

## Sample values

`sampleValues` maps a control id to a placeholder in the shape the control
shows: a number, a string, list rows, a chart's data. The AI connector fills
each new control's ControlDoc `io:` sample here, so a layout it built does not
open dead. A sample is **display only**:

- It shows on a control that has nothing of its own when the layout opens: no
  `defaultValue`, no value the app kept from the last visit. A control the
  phone's own store feeds never shows one (its rows arrive at once).
- The control's first value of any kind replaces it: a hub frame, a poll, a
  derive, or the person's own touch.
- It is never sent, saved or published: no action, form, hub request, widget,
  alert or derive sees it. A button tapped while it shows sends what it would
  with no sample, and a `visible` / `enabled` rule sees no value.
- Try uses the same map for controls with no live data.
- The editor previews the same way: a control with nothing of its own shows
  this map's sample, else its ControlDoc `io:` sample, under a SAMPLE badge,
  and the pose's **Try** plays the doc's `next` (and the control's action,
  recorded and never sent). None of it is written to the layout.

Because nothing leaves the phone, a change that sets `sampleValues` applies
without a tap. One exception asks first: a sample holding a link (any string
with `://`), since showing it could fetch or open that link.

```json
"sampleValues": { "lamp": 40, "rows": [{ "id": "row-1", "name": "Item 1" }] }
```

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
- [[derive]] — values computed on the phone
- [[theming]] — Full theme system, light/dark variants, live builder
- [[appearance]] — Color scheme, header, status bar, background image
- [[group-def]] — containers within tabs
- [[control-def]] — controls within groups
