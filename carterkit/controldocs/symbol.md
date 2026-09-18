---
type: symbol
label: Symbol
icon: cloud.bolt.rain.fill
category: controls
defaultSpan: [2, 2]
fields:
  - name: systemName
    type: string
    description: SF Symbol name (the glyph at rest)
  - name: label
    type: string
    description: Caption under the glyph
  - name: hideLabel
    type: bool
    default: false
    description: Hide the caption
  - name: tint
    type: color
    description: Glyph colour (monochrome/hierarchical; palette primary)
  - name: hideBackground
    type: bool
    default: false
    description: Remove glass background
  - name: iconMap
    type: object
    description: Incoming value → SF Symbol name ("default" catches the rest)
  - name: colorMap
    type: object
    description: Incoming value → hex tint
  - name: haptic
    type: enum
    values: [none, light, medium, heavy, soft, rigid, selection, success, warning, error]
    description: Touch feedback on tap (default light)
  - name: renderingMode
    type: enum
    values: [monochrome, hierarchical, palette, multicolor]
    default: monochrome
    description: SF rendering mode — multicolor uses the symbol's own colours
    group: symbolConfig
  - name: palette
    type: array
    description: Hex colour per layer (primary, secondary, tertiary) for palette rendering
    group: symbolConfig
  - name: weight
    type: enum
    values: [ultraLight, thin, light, regular, medium, semibold, bold, heavy, black]
    default: regular
    description: Glyph weight
    group: symbolConfig
  - name: variant
    type: enum
    values: [none, fill, circle, square, rectangle, slash]
    default: none
    description: Symbol variant applied on top of the name
    group: symbolConfig
  - name: size
    min: 12
    max: 300
    step: 1
    type: number
    description: Explicit point size (default scales to the cell)
    group: symbolConfig
  - name: effect
    type: enum
    values: [none, rain, snow, sparkle, pulse, breathe, variableColor, rotate, wiggle, bounce, scale]
    default: none
    description: Native symbol effect or custom rain, snow, sparkle animation
    group: symbolConfig
  - name: particleColor
    type: color
    description: Custom particle colour (default tint; blue rain, white snow, yellow sparkles in multicolor)
    group: symbolConfig
  - name: particleIntensity
    type: number
    min: 0
    max: 1
    step: 0.05
    default: 0.65
    description: Rain, snow, sparkle density (0 hides particles)
    group: symbolConfig
  - name: particleAngle
    type: number
    min: -60
    max: 60
    step: 1
    default: -18
    description: Rain/snow direction in degrees from vertical (negative left, positive right)
    group: symbolConfig
  - name: effectOptions
    type: array
    description: "Effect modifiers in Apple's words: iterative, cumulative, reversing, hideInactiveLayers, up, down, clockwise, byLayer, wholeSymbol …"
    group: symbolConfig
  - name: loop
    type: enum
    values: [continuous, periodic, once]
    default: continuous
    description: How the effect repeats
    group: symbolConfig
  - name: loopCount
    min: 1
    max: 100
    step: 1
    type: number
    description: periodic only — plays before stopping (omit for forever)
    group: symbolConfig
  - name: loopDelay
    min: 0
    max: 30
    step: 0.1
    type: number
    default: 1
    description: periodic only — seconds between plays
    group: symbolConfig
  - name: speed
    min: 0.1
    max: 5
    step: 0.1
    type: number
    default: 1
    description: Playback speed multiplier
    group: symbolConfig
  - name: activeWhen
    type: string
    default: always
    description: "always | truthy | a state word the synced value must equal"
    group: symbolConfig
  - name: variableMin
    type: number
    bounds: none
    default: 0
    description: Numeric value at which the variable layers are empty
    group: symbolConfig
  - name: variableMax
    type: number
    bounds: none
    default: 100
    description: Numeric value at which the variable layers are full
    group: symbolConfig
  - name: transition
    type: enum
    values: [replace, replace.downUp, replace.upUp, replace.offUp, replace.magic, none]
    description: How a glyph change animates (default replace; none when the value is numeric)
    group: symbolConfig
  - name: tapEffect
    type: enum
    values: [none, bounce, pulse, variableColor, wiggle, rotate, breathe]
    default: none
    description: One-shot effect played on tap
    group: symbolConfig
  - name: triggers
    type: array
    description: "Server events that play a one-shot effect: [{ event, filter?, effect, effectOptions? }]"
    group: symbolConfig
themeFields:
  - name: cornerRadius
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
  - name: controlPadding
    min: 0
    max: 24
    step: 1
    type: number
    default: 8
    description: Internal padding
  - name: surfacePrimary
    type: color
    default: #FFFFFF0F
    description: Background fill
  - name: foregroundColor
    type: color
    default: #FFFFFF
    description: Default glyph colour
  - name: borderColor
    type: color
    default: #FFFFFF1A
    description: Border color
  - name: borderWidth
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
---

# Symbol

One SF Symbol with native rendering modes, variable layers, and configurable
animation effects, including custom rain, snow, and sparkles. Effects run locally without a stream of server updates.
The symbol's own annotations determine which parts move: for example,
`rotate` with `byLayer` spins a desk fan's blades while its housing stays still.

## Finding Apple's animations

Download [SF Symbols for Mac](https://developer.apple.com/sf-symbols/), select a
symbol, and open the **Animation inspector** in the right sidebar. Choose an
effect, its layer/direction options, and a repeat mode, then press **Preview**.
The inspector's **Copy** menu provides the corresponding code. Apple's
[Animate symbols in your app](https://developer.apple.com/videos/play/wwdc2023/10258/)
and [What's new in SF Symbols 6](https://developer.apple.com/videos/play/wwdc2024/10188/)
walk through the APIs and per-layer animation.

The **Animation examples** menu in this page's live preview loads the examples
below, including their symbol, colours, effect, and repeat settings. Numeric
variable-layer input is optional; leave it off to preview the full symbol.

**Rain and workout figures:** `variableColor` changes layer opacity; it does not
make raindrops travel diagonally. `wiggle.byLayer` uses the symbol's annotated
motion groups; it does not provide a running gait or an arbitrary joint animation.
Apple's public symbol effects do not expose a general “play this symbol's real-world
activity” API. Matching bespoke Weather or Workout app motion requires separately
authored animation. CAR-TER adds its own `rain`, `snow`, and `sparkle` effects,
described below. Running figures are not included.

## Type
`"symbol"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `systemName` | string | — | SF Symbol name at rest |
| `tint` | color | theme | Glyph colour (monochrome / hierarchical, or the palette primary) |
| `iconMap` / `colorMap` | object | — | Incoming value → symbol name / tint, as on [[image]] |
| `symbolConfig.renderingMode` | string | `monochrome` | `hierarchical`, `palette` (see `palette`), or `multicolor` (the symbol's own colours) |
| `symbolConfig.palette` | array | — | Hex colour per layer (primary, secondary, tertiary); a short list repeats its last entry |
| `symbolConfig.weight` | string | `regular` | `ultraLight` … `black` |
| `symbolConfig.variant` | string | — | `fill`, `circle`, `square`, `rectangle`, `slash` layered onto the name |
| `symbolConfig.effect` | string | — | Looping effect — see [[#Effects]] |
| `symbolConfig.particleColor` | color | tint/mode | Custom particle colour |
| `symbolConfig.particleIntensity` | number | `0.65` | Custom particle density, 0…1 |
| `symbolConfig.particleAngle` | number | `-18` | Rain/snow direction from vertical, -60…60 degrees |
| `symbolConfig.effectOptions` | array | — | Effect modifiers, in Apple's words |
| `symbolConfig.loop` | string | `continuous` | `periodic` (with `loopDelay`, `loopCount`) or `once` |
| `symbolConfig.speed` | number | `1` | Playback speed multiplier |
| `symbolConfig.activeWhen` | string | `always` | `truthy`, or a state word — gates the loop on the synced value |
| `symbolConfig.variableMin` / `variableMax` | number | `0` / `100` | A numeric value maps into this range to fill the variable layers |
| `symbolConfig.transition` | string | `replace` | How a glyph change animates; `none` is the default while the value is numeric |
| `symbolConfig.tapEffect` | string | — | One-shot effect on tap |
| `symbolConfig.triggers` | array | — | `[{ "event", "filter", "effect" }]` — server events that play a one-shot effect |

## Effects

Looping effects (`effect`) take the modifiers Apple gives them, spelled exactly
as in Swift — `effect: "variableColor"` with `effectOptions: ["iterative",
"hideInactiveLayers"]` is `.symbolEffect(.variableColor.iterative.hideInactiveLayers,
options: .repeat(.continuous))`. `byLayer` uses the motion groups annotated in
the symbol; it does not automatically separate every visible shape or limb.
Open a symbol in the SF Symbols app → Animation to preview the result. Put
supported modifier names into the `effectOptions` list.

| Effect | Modifiers | Reads as |
|---|---|---|
| `variableColor` | `iterative`, `cumulative`, `reversing`, `nonReversing`, `hideInactiveLayers`, `dimInactiveLayers` | The symbol's annotated layers sequence — raindrops cycling, a signal sweeping, bars filling |
| `pulse` | `byLayer`, `wholeSymbol` | Opacity breathing |
| `breathe` | `plain`, `pulse`, `byLayer`, `wholeSymbol` | Gentle grow-and-shrink |
| `rotate` | `clockwise`, `counterClockwise`, `byLayer`, `wholeSymbol` | Spinning — `byLayer` turns a `fan.fill`'s blades on their own hub; `wholeSymbol` turns a sun |
| `wiggle` | `up`, `down`, `left`, `right`, `forward`, `backward`, `clockwise`, `counterClockwise`, `byLayer`, `wholeSymbol` | Attention shake using the symbol's annotated motion groups |
| `scale` | `up`, `down`, `byLayer`, `wholeSymbol` | Held larger / smaller while active |
| `bounce` | `up`, `down`, `byLayer`, `wholeSymbol` | Discrete in iOS, so it loops as `periodic` |

Variable colour is layer sequencing, not a particle engine: the drops light up
in Apple's order, they do not travel. `hideInactiveLayers` blanks inactive layers
outright; on a symbol whose every layer is variable that includes the cloud for
an instant each cycle — the SF Symbols app preview shows you which.

One-shot effects (`tapEffect`, `triggers[].effect`): `bounce`, `pulse`,
`variableColor`, `wiggle`, `rotate`, `breathe`. A trigger is registered exactly
like a group [[pulse]]: name the `event` (`broadcast` for the shared channel),
optionally a `filter`, and the effect plays each time a matching frame lands.

**Reduce Motion** silences every effect, and a resident-but-hidden layout stops
the loop, so a decorative cloud never costs battery nobody can see.

## Custom particle effects

Set `symbolConfig.effect` to `rain`, `snow`, or `sparkle`. These are CAR-TER
animations rendered with SwiftUI Canvas; they are not extra Apple symbol presets.

- `rain`: slanted drops falling below the symbol.
- `snow`: small flakes falling and drifting below the symbol.
- `sparkle`: four-point stars twinkling around the symbol.

`particleIntensity` sets density from 0 to 1. `particleAngle` sets rain/snow
direction from -60° (left) to 60° (right). `particleColor` overrides particle
colour; otherwise palette mode uses its second colour, multicolor uses blue rain,
white snow, or yellow sparkles, and other modes use the control's tint.

For ordinary `cloud.rain`, `cloud.drizzle`, `cloud.heavyrain`, `cloud.snow`,
`cloud.sleet`, and `cloud.hail` names, including `.fill`, rain/snow use a plain
cloud and replace static precipitation with particles. `cloud.sun.rain`,
`cloud.moon.rain`, and `cloud.bolt.rain` retain their sun, moon, or bolt.
Other glyphs, including circle variants, remain intact and gain particles.
The synced name and the name sent by a tap action stay unchanged.

`speed`, `activeWhen`, `loop`, `loopDelay`, and `loopCount` work with custom
effects. One base cycle lasts 1.4 seconds for rain, 3.2 for snow, or 1.8 for
sparkles, divided by speed. `once` plays one cycle; `periodic` fades particles
between cycles and waits the specified delay (seconds, unaffected by speed).
Completed finite effects hide their particles and stop refreshing.

Reduce Motion, inactive apps, hidden layouts, and a false `activeWhen` stop the
clock and show static particles. Re-enabling the effect starts a fresh cycle.
Zero intensity also stops refreshing. Native `tapEffect` and trigger effects can
still animate the glyph; custom particles are currently looping effects only.
`effectOptions` applies only to native effects.

The approach is inspired by [Kieran Brown's raining-cloud example](https://gist.github.com/kieranb662/985c5274519d36e3d000634e046c7425)
and [Vortex's particle presets](https://github.com/twostraws/Vortex). CAR-TER's
implementation is original and adds no package dependency.

## Layers and colours

SF Symbols are built from up to three **palette layers**, and `palette` colours
them in order (`cloud.rain.fill` = cloud, drops; `moon.stars.fill` = moon,
stars). `multicolor` uses Apple's own annotation instead — a white cloud, blue
drops, a yellow bolt — and is the natural pairing for weather. To learn a
symbol's layer order, give it `renderingMode: "palette"` with three loud colours
once, or read it off the SF Symbols app in Palette rendering.

## What the synced value does

- A **string** picks the glyph: an `iconMap` hit, or — when it names a real
  symbol — the symbol itself, so a server can push `"cloud.bolt.rain.fill"`.
  A state word can also gate the loop through `activeWhen`.
- A **number** fills the symbol's variable layers (`wifi`, `speaker.wave.3`,
  `cloud.rain`, `rainbow` …) over `variableMin…variableMax`.
- A **bool** gates the loop with `activeWhen: "truthy"`.

## Examples

### Moving rain — custom particles
```json
{
  "type": "symbol", "id": "rain", "position": [0, 0], "span": [2, 2],
  "systemName": "cloud.rain.fill", "label": "Rain", "tint": "#8AA5BD",
  "defaultValue": true,
  "symbolConfig": {
    "effect": "rain", "particleColor": "#3DA9FC", "particleAngle": -22,
    "particleIntensity": 0.65, "activeWhen": "truthy"
  }
}
```

### Drifting snow — custom particles
```json
{
  "type": "symbol", "id": "snow", "position": [0, 2], "span": [2, 2],
  "systemName": "cloud.snow.fill", "label": "Snow", "tint": "#8AA5BD",
  "symbolConfig": { "effect": "snow", "particleColor": "#68BBDD", "particleAngle": 8 }
}
```

### Sparkling favourite — custom particles
```json
{
  "type": "symbol", "id": "sparkle", "position": [2, 0], "span": [2, 2],
  "systemName": "star.fill", "label": "Favourite", "tint": "#E6A323",
  "symbolConfig": { "effect": "sparkle", "particleColor": "#E6A323", "tapEffect": "bounce" }
}
```

### Fan — blades on their hub
```json
{
  "type": "symbol",
  "id": "fan",
  "position": [2, 2],
  "span": [2, 2],
  "systemName": "fan.desk.fill",
  "label": "Fan",
  "tint": "#8E8E93",
  "symbolConfig": { "renderingMode": "hierarchical", "effect": "rotate", "effectOptions": ["clockwise", "byLayer"], "speed": 1.5 }
}
```

### Rain — cycling layer opacity
```json
{
  "type": "symbol",
  "id": "rain",
  "position": [0, 0],
  "span": [2, 2],
  "systemName": "cloud.rain.fill",
  "label": "Rain",
  "symbolConfig": {
    "renderingMode": "multicolor",
    "effect": "variableColor",
    "effectOptions": ["iterative", "dimInactiveLayers"]
  }
}
```

This is `.symbolEffect(.variableColor.iterative.dimInactiveLayers, options:
.repeating)` on a multicolor image: eligible layers change opacity in sequence.
Inactive layers stay faintly visible so the icon does not disappear during the
cycle. Use `hideInactiveLayers` to hide them instead. The exact layers depend on
Apple's symbol annotations. This is not travelling rain.

### Workout figure — native wiggle
```json
{
  "type": "symbol",
  "id": "hiit",
  "position": [0, 2],
  "span": [2, 2],
  "systemName": "figure.highintensity.intervaltraining",
  "label": "Training",
  "tint": "#30D158",
  "defaultValue": true,
  "symbolConfig": { "effect": "wiggle", "effectOptions": ["byLayer"], "activeWhen": "truthy" },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "workout" }, "valuePath": "active" }]
}
```

`.wiggle.byLayer` with `.repeat(.continuous)` applies the standard wiggle effect.
It is not a workout movement or running cycle. `activeWhen` ties the effect to
the synced state — it runs while the workout is on.

### Storm with a server-fired strike
```json
{
  "type": "symbol",
  "id": "storm",
  "position": [2, 0],
  "span": [2, 2],
  "systemName": "cloud.bolt.rain.fill",
  "label": "Storm",
  "symbolConfig": {
    "renderingMode": "multicolor",
    "effect": "variableColor",
    "effectOptions": ["iterative"],
    "speed": 1.4,
    "triggers": [
      { "event": "broadcast", "filter": { "msg_type": "weather", "alert": "lightning" }, "effect": "bounce" }
    ]
  }
}
```

### Signal strength — a number fills the bars
```json
{
  "type": "symbol",
  "id": "signal",
  "position": [2, 0],
  "span": [2, 2],
  "systemName": "wifi",
  "label": "Wi-Fi",
  "tint": "#30D158",
  "defaultValue": 72,
  "symbolConfig": { "renderingMode": "hierarchical", "variableMin": 0, "variableMax": 100 },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "net" }, "valuePath": "rssi_pct" }]
}
```

### Alert that wiggles only while armed
```json
{
  "type": "symbol",
  "id": "armed",
  "position": [2, 2],
  "span": [2, 2],
  "systemName": "exclamationmark.triangle.fill",
  "label": "Alarm",
  "tint": "#FF9F0A",
  "defaultValue": true,
  "symbolConfig": { "effect": "wiggle", "loop": "periodic", "loopDelay": 1.5, "activeWhen": "truthy" },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "alarm" }, "valuePath": "armed" }]
}
```

### Tap to like
```json
{
  "type": "symbol",
  "id": "like",
  "position": [4, 0],
  "span": [2, 2],
  "systemName": "heart.fill",
  "tint": "#FF375F",
  "hideBackground": true,
  "symbolConfig": { "tapEffect": "bounce" },
  "action": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "like", "symbol": "{{value}}" } }
}
```

## Behavior
- The glyph **scales to its cell** like an [[image]] and never below ~28pt; in a
  `flow` grid set `controlHeight` (or `symbolConfig.size`) for a bigger tile —
  see [[grid-dimensions]]
- An unknown symbol name renders a dashed placeholder rather than a blank tile
- Tap fires the `action` with `{{value}}` = the symbol name shown, plus
  `tapEffect` and the `haptic`
- `multicolor` ignores `tint`; `palette` reads `symbolConfig.palette`, repeating
  its last entry for any missing layer, and falls back to `tint`
- With a numeric value, `transition` defaults to `none`: a replace transition on
  a ramping variable value re-renders every tick (measured, see the reel notes)

## Related
- [[image]] — pictures with a symbol fallback and the same value maps
- [[pulse]] — the group-level event ring `triggers` are modelled on
- [[animations]] — transition presets
- [[sync]] — receiving values and events
