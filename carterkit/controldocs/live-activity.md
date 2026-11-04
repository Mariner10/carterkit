---
type: glance-live-activity
label: Live Activity and Dynamic Island
icon: platter.filled.top.and.arrow.up.iphone
category: system
depth: complete
fields:
  - name: liveActivity
    type: bool
    description: Glance field. Start a Live Activity while the layout is connected (default false; the island is prime space, so it is opt-in). live.activity.start can start it instead
    summary: Turn on the Dynamic Island
    does: Starts a Live Activity in the Dynamic Island and Lock Screen while the layout is connected; off by default.
  - name: compactLeading
    type: object
    description: island field. One tile for the left of the compact island (default the layout icon, which bounces on update)
    summary: Left side of the small island
    does: Fills the left of the compact island with one tile; without it the layout icon shows and bounces on update.
  - name: compactTrailing
    type: object
    description: island field. One tile for the right of the compact island (default the hero value, ring or dot)
    summary: Right side of the small island
    does: Fills the right of the compact island with one tile; without it the main value, ring or dot shows.
  - name: minimal
    type: object
    description: island field. One tile for the minimal island, shown when another app's activity shares it (default a freshness ring around the connection dot)
    summary: Tiny island view
    does: Fills the minimal island, used when another app's activity shares the island, with one tile; without it a freshness ring circles the connection dot.
  - name: expanded
    type: object
    description: island field. The four expanded regions leading, trailing, center and bottom, each a tile or a scene
    summary: The big island when you press it
    does: Fills the leading, trailing, center and bottom areas of the expanded island, each with a tile or a scene.
  - name: keyline
    type: string
    description: island field. The island outline colour, drawn by iOS only on a full-black background. accent (default), a hex like #FF9F0A, or none
    summary: Island outline color
    does: Colors the outline around the island; iOS only draws it on a full-black background. Use accent, a hex color or none.
  - name: live.tier
    type: enum
    values: [realtime, fresh, periodic, manual]
    default: fresh
    description: Preset for how live every surface is; explicit fields below override it
    summary: How live everything feels
    does: Sets a preset for how often the island, widgets and Control Center controls update; fields set explicitly override it.
    valueHelp: {"realtime": "updates every second or two and pushes widgets as things change, using up budgets quickly", "fresh": "live while the app is open and updated every few seconds from the relay, safe to leave on all day", "periodic": "updates slowly with a pull every 15 minutes, almost free", "manual": "only updates when the app itself pushes a change"}
  - name: live.activity.cadence
    type: number
    description: Seconds between updates while the app is open (floor 1)
    summary: Update speed while the app is open
    does: Sets how many seconds pass between island updates while the app is open, from 1 to 3600.
    min: 1
    max: 3600
    step: 1
  - name: live.activity.remoteCadence
    type: number
    description: Seconds between updates pushed by the relay (floor 2)
    summary: Update speed from the relay
    does: Sets how many seconds pass between island updates pushed by the relay when the app is closed, from 2 to 3600.
    min: 2
    max: 3600
    step: 1
  - name: live.activity.stale
    type: number
    description: Seconds until the surface marks its data stale (default 120, floor 30)
    summary: When the data counts as old
    does: Sets how many seconds until the island marks its data stale, ending the LIVE clock and greying the freshness dot (default 120, minimum 30).
    min: 30
    max: 3600
    step: 1
  - name: live.activity.priority
    type: enum
    values: [immediate, opportunistic]
    description: Push priority; immediate is budgeted by iOS
    summary: How urgently updates are pushed
    does: Chooses whether relay pushes ask iOS to deliver immediately or when convenient.
    valueHelp: {"immediate": "delivered right away but counted against an iOS budget", "opportunistic": "delivered when iOS finds it convenient, which can lag"}
  - name: live.activity.start
    type: enum
    values: [onConnect, remote, never]
    default: onConnect
    description: onConnect starts it when the layout connects; remote lets only a hub start it by push-to-start; never keeps it off
    summary: When the island starts
    does: Chooses what starts the Live Activity.
    valueHelp: {"onConnect": "it starts when the layout connects", "remote": "only a hub can start it, by push-to-start", "never": "it stays off"}
  - name: live.widgets.refresh
    type: enum
    values: [push, pull, app]
    description: How widgets refresh (see [[widgets]])
    summary: How widgets update
    does: Chooses how home screen widgets get fresh data.
    valueHelp: {"push": "the relay pushes widgets when data changes", "pull": "widgets fetch new data on a timer", "app": "widgets only change when the app updates them"}
  - name: live.widgets.pullEvery
    type: number
    description: Seconds between widget pulls in pull mode (floor 300)
    summary: How often widgets fetch
    does: Sets seconds between widget fetches in pull mode, from 300 to 86400.
    min: 300
    max: 86400
    step: 60
  - name: live.widgets.stale
    type: number
    description: Seconds until a widget calls its data stale (floor 30)
    summary: When widget data counts as old
    does: Sets how many seconds until a widget calls its data stale, from 30 to 86400.
    min: 30
    max: 86400
    step: 1
  - name: live.controls.refresh
    type: enum
    values: [push, app]
    description: How Control Center controls refresh (see [[control-center]])
    summary: How Control Center buttons update
    does: Chooses how Control Center controls get fresh data.
    valueHelp: {"push": "the relay pushes updates when data changes", "app": "controls only change when the app updates them"}
  - name: live.background.silentPush
    type: bool
    description: Also wake the app with a silent push on relay updates; heavily throttled by iOS, off by default
    summary: Also wake the app quietly
    does: When on, relay updates also send a silent push that wakes the app in the background; iOS throttles it heavily.
constraints: {"surface":"live-activity","requires":"liveActivity true, or live.activity.start other than never","limits":{"stateBytesPerUpdate":4096,"maxSessionHours":8,"expandedBottomMaxRows":2},"island":{"compactLeading":{"maxTiles":1},"compactTrailing":{"maxTiles":1},"minimal":{"maxTiles":1},"expanded":{"leading":{"maxTiles":1},"trailing":{"maxTiles":1},"center":{"maxTiles":1},"bottom":{"maxRows":2,"maxTiles":null}},"regionAcceptsScene":["expanded.leading","expanded.trailing","expanded.center","expanded.bottom"],"keyline":["accent","#RRGGBB","none"],"interactiveTiles":["toggle","button","step"],"interactiveFits":"about two in expanded.bottom","allowedTiles":["value","gauge","ring","bar","light","sparkline","text","icon","spacer","timer","freshness","toggle","button","step","open"],"compactRecommendedTiles":["value","gauge","ring","light","icon","text","timer","freshness"],"motion":["numericText roll","symbol effect on change","add/remove transition","self-ticking timer and ring"]},"liveness":{"tiers":["realtime","fresh","periodic","manual"],"defaultTier":"fresh","floors":{"activityCadenceSeconds":1,"activityRemoteCadenceSeconds":2,"widgetReloadSpacingSeconds":60,"widgetPullEverySeconds":300,"staleSeconds":30},"activity":{"start":["onConnect","remote","never"],"priority":["immediate","opportunistic"],"staleDefaultSeconds":120},"widgetsRefresh":["push","pull","app"],"controlsRefresh":["push","app"],"tierTable":{"realtime":{"activity":"1 s in app, 2 s remote, immediate","widgets":"pushed on change, at least 60 s apart","controls":"pushed on change","cost":"burns Live Activity and widget budgets"},"fresh":{"activity":"1 s in app, 5 s remote, immediate","widgets":"pushed on change, at least 5 min apart","controls":"pushed on change","cost":"safe indefinitely"},"periodic":{"activity":"1 s in app, 30 s remote, opportunistic","widgets":"pulled every pullEvery (15 min)","controls":"pulled on system reload","cost":"near zero"},"manual":{"activity":"app-driven only","widgets":"app-driven only","controls":"app-driven only","cost":"the v1 behaviour"}}}}
---

The **Live Activity** is the glance block's most visible surface: the Dynamic Island
(compact, minimal and expanded) and, on the Lock Screen, a banner. This page covers
the island and the liveness settings; the banner is [[lock-screen]]. Tiles are
defined in [[glance]].

Set `"liveActivity": true` (or `live.activity.start` to `onConnect` or `remote`) or
nothing starts. The relay pushes the island directly, so it keeps updating while the
app is closed or force-quit.

## Regions

| Region | Takes | Default |
|---|---|---|
| `compactLeading` | exactly one tile | layout icon, bounces on update |
| `compactTrailing` | exactly one tile | hero value, ring or dot |
| `minimal` | exactly one tile | freshness ring around the connection dot |
| `expanded.leading` / `.trailing` / `.center` | one tile (a scene is accepted but the sides are narrow) | icon + title / freshness / the LIVE session clock |
| `expanded.bottom` | a scene | hero + slot chips + hero sparkline + two controls |

The compact regions are a few points wide (the trailing one about 56 pt): use a
`ring`, `light`, `icon`, `timer` or short `value`, never a `gauge` with a label.
Keep `expanded.bottom` to **two rows**: the island has a hard height budget and
clips. Interactive tiles fit about two in the bottom region.

Hard limits from iOS: 4 KB of state per update, 8 hours maximum per session, and the
user can turn Live Activities off per app. Custom `withAnimation` is ignored; use the
tile `effect` and `transition` fields and the self-ticking `timer` and `ring`.

## Liveness

Pick a `live.tier`, then override single fields if you must.

| Tier | Live Activity (in app / remote) | Widgets | Controls | Cost |
|---|---|---|---|---|
| `realtime` | 1 s / 2 s, immediate | pushed on change, 60 s apart at most | pushed on change | burns budgets; genuinely live sessions only |
| `fresh` (default) | 1 s / 5 s, immediate | pushed on change, 5 min apart at most | pushed on change | safe indefinitely |
| `periodic` | 1 s / 30 s, opportunistic | pulled every `pullEvery` (15 min) | pulled on system reload | near zero |
| `manual` | app-driven | app-driven | app-driven | the v1 behaviour |

Floors are enforced by the app and the relay (cadence 1 s, remote cadence 2 s, widget
reload spacing 60 s, widget pull 300 s, stale window 30 s); a lower value is raised
to the floor and the connection console says so. A surface always shows its age: a
stale window ends the LIVE clock and greys the freshness dot.

## Constraints

The frontmatter `constraints` block holds all of the above as JSON: region tile
limits, the 4 KB / 8 h limits, the allowed tile kinds, the tier table and every
floor. `SurfaceSceneValidator` reports more than one tile in a side region and a
tile that cannot fit its columns.

## Examples

### Printer island

Compact ring and light, expanded gauges with a timer in the centre.

```json
{
  "title": "Printer", "icon": "printer.fill", "tint": "#FF9F0A",
  "hero": "nozzle", "slots": ["bed", "progress"],
  "liveActivity": true,
  "live": { "tier": "fresh" },
  "island": {
    "compactLeading":  { "tile": "icon", "effect": "bounce" },
    "compactTrailing": { "tile": "ring", "control": "progress" },
    "minimal":         { "tile": "light", "control": "state" },
    "expanded": {
      "leading":  { "tile": "icon" },
      "trailing": { "tile": "freshness" },
      "center":   { "tile": "timer", "control": "eta" },
      "bottom":   { "rows": [ [ { "tile": "gauge", "control": "nozzle" }, { "tile": "gauge", "control": "bed" } ],
                              [ { "tile": "button", "control": "pause" }, { "tile": "step", "control": "fan-speed", "delta": 10 } ] ] }
    }
  }
}
```

### Quiet island

Only the compact trailing value and a keyline; every other region keeps its default.

```json
{
  "liveActivity": true,
  "hero": "nozzle",
  "live": { "tier": "periodic", "activity": { "stale": 300 } },
  "island": {
    "compactTrailing": { "tile": "value", "control": "nozzle" },
    "keyline": "none"
  }
}
```

### Remote-started session

A hub starts the activity by push-to-start; cadence is set explicitly.

```json
{
  "liveActivity": true,
  "live": {
    "tier": "realtime",
    "activity": { "cadence": 1, "remoteCadence": 2, "stale": 60, "priority": "immediate", "start": "remote" },
    "background": { "silentPush": false }
  },
  "island": {
    "minimal": { "tile": "ring", "control": "progress" },
    "expanded": { "center": { "tile": "timer", "control": "eta" } }
  }
}
```
