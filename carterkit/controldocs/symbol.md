---
type: symbol
depth: complete
label: Symbol
icon: cloud.bolt.rain.fill
category: controls
defaultSpan: [2, 2]
addIntent: show
pickerCategory: Readouts
friendlyName: Symbol
oneLiner: An icon that can animate
aliases: [icon, sf symbol, glyph, emoji, shape, picture]
addRank: 8
starterPreset: {"systemName": "star.fill","label": "Symbol"}
io:
  - emits: value
    when: tap
    title: When you tap the symbol
    type: string
    says: the name of the symbol being shown
    example: "Sample A"
    since: next
  - receives: value
    role: show
    type: string
    from: [hub, mqtt, http, store, default]
    says: a symbol name to show, a state word to match, or a number that fills the symbol
    reacts: the symbol swaps, tints or fills to match it, and plays its effect when active
    example: "Sample A"
    since: next
  - sample: true
fields:
  - name: systemName
    chip: Symbol
    edit: symbol
    depth: surface
    title: Symbol
    type: string
    description: SF Symbol name (the glyph at rest)
    summary: Which icon to show
    does: Draws this SF Symbol as the main glyph; a synced text value can swap it live.
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Caption under the glyph
    summary: The caption under the icon
    does: Shows this text under the glyph.
  - name: hideLabel
    edit: part
    depth: hold
    title: Title shown
    type: bool
    default: false
    description: Hide the caption
    summary: Hide the caption
    does: Turned on, the caption under the glyph is not shown.
  - name: tint
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    description: Glyph colour (monochrome/hierarchical; palette primary)
    summary: The icon's color
    does: Colors the glyph; multicolor symbols keep their own colors instead.
  - name: glowRadius
    edit: scrub
    depth: hold
    under: tint
    title: Glow
    unit: pt
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    default: 0
    description: Soft glow behind the glyph in its own colour, in points (0 = none). Cross-control, same on every control
    summary: A soft glow behind the icon
    does: Adds a blurred halo of the glyph's own color behind it, 0 for none up to 30 points.
  - name: hideBackground
    edit: part
    depth: hold
    title: Background
    tab: style
    type: bool
    default: false
    description: Remove glass background
    summary: Remove the card behind it
    does: Turned on, the glass card is removed and the icon floats on the page.
  - use: iconMap
  - name: colorMap
    tab: data
    type: object
    description: Incoming value → hex tint
    summary: Show different colors for different values
    does: Tints the glyph with the hex color listed for the incoming value.
  - name: haptic
    tab: action
    type: enum
    values: [none, light, medium, heavy, soft, rigid, selection, success, warning, error]
    description: Touch feedback on tap (default light)
    summary: Buzz when tapped
    does: Plays this haptic feedback each time the symbol is tapped; light when not set.
    valueHelp: {"none": "no haptic", "light": "a small light tap", "medium": "a medium tap", "heavy": "a strong tap", "soft": "a rounded cushioned tap", "rigid": "a sharp firm tap", "selection": "a tiny tick like scrolling a picker", "success": "a success pattern", "warning": "a warning pattern", "error": "an error pattern"}
  - name: renderingMode
    edit: look
    depth: hold
    under: tint
    title: Colouring
    tab: style
    type: enum
    values: [monochrome, hierarchical, palette, multicolor]
    default: monochrome
    description: SF rendering mode — multicolor uses the symbol's own colours
    summary: How the icon is colored
    does: Chooses how the symbol's layers take color.
    valueHelp: {"monochrome": "one color for the whole glyph", "hierarchical": "layers shaded from one color, strongest first", "palette": "each layer gets its own color from the palette list", "multicolor": "the symbol's own built-in colors and ignores the tint"}
    group: symbolConfig
  - name: palette
    tab: style
    type: array
    description: Hex colour per layer (primary, secondary, tertiary) for palette rendering
    summary: A color for each icon layer
    does: Colors the symbol's layers in order, primary first, when the colouring is palette.
    group: symbolConfig
  - name: weight
    category: look
    edit: look
    depth: hold
    under: effect
    title: Weight
    type: enum
    values: [ultraLight, thin, light, regular, medium, semibold, bold, heavy, black]
    default: regular
    description: Glyph weight
    summary: How thick the icon lines are
    does: Sets the stroke thickness of the glyph.
    valueHelp: {"ultraLight": "the thinnest lines", "thin": "very fine lines", "light": "fine lines", "regular": "normal lines", "medium": "slightly heavier lines", "semibold": "fairly heavy lines", "bold": "heavy lines", "heavy": "very heavy lines", "black": "the heaviest lines"}
    group: symbolConfig
  - name: variant
    edit: look
    depth: hold
    under: effect
    title: Variant
    tab: style
    type: enum
    values: [none, fill, circle, square, rectangle, slash]
    default: none
    description: Symbol variant applied on top of the name
    summary: An outline or badge style
    does: Applies a variant to the symbol name, such as a circle around it or a slash through it.
    valueHelp: {"none": "the symbol exactly as named", "fill": "the filled version", "circle": "the glyph inside a circle", "square": "the glyph inside a square", "rectangle": "the glyph inside a rectangle", "slash": "a diagonal slash through the glyph"}
    group: symbolConfig
  - name: size
    edit: scrub
    depth: hold
    under: effect
    title: Size
    min: 12
    max: 300
    step: 1
    type: number
    description: Explicit point size (default scales to the cell)
    summary: How big the icon is
    does: Sets the glyph's point size; left empty it scales to fill the cell.
    group: symbolConfig
  - name: effect
    edit: look
    depth: surface
    title: Effect
    type: enum
    values: [none, rain, snow, sparkle, pulse, breathe, variableColor, rotate, wiggle, bounce, scale]
    default: none
    description: Native symbol effect or custom rain, snow, sparkle animation
    summary: An animation that keeps playing
    does: Loops an animation on the glyph, either one of Apple's symbol effects or CAR-TER's own particles.
    valueHelp: {"none": "no animation", "rain": "slanted drops falling below the symbol", "snow": "flakes falling and drifting below the symbol", "sparkle": "four-point stars twinkling around the symbol", "pulse": "the icon fades in and out", "breathe": "the icon gently grows and shrinks", "variableColor": "the icon's layers light up in sequence", "rotate": "the icon spins", "wiggle": "the icon shakes to get attention", "bounce": "the icon hops", "scale": "the icon is held larger or smaller"}
    group: symbolConfig
  - name: particleColor
    tab: style
    type: color
    description: Custom particle colour (default tint; blue rain, white snow, yellow sparkles in multicolor)
    summary: Color of the rain, snow or sparkles
    does: Overrides the color of the custom particles instead of the tint or palette.
    group: symbolConfig
  - name: particleIntensity
    type: number
    min: 0
    max: 1
    step: 0.05
    default: 0.65
    description: Rain, snow, sparkle density (0 hides particles)
    summary: How much rain, snow or sparkle
    does: Sets how dense the particles are from 0 to 1, with 0 hiding them.
    group: symbolConfig
  - name: particleAngle
    type: number
    min: -60
    max: 60
    step: 1
    default: -18
    description: Rain/snow direction in degrees from vertical (negative left, positive right)
    summary: Which way the rain or snow falls
    does: Tilts falling particles from straight down, negative toward the left and positive toward the right.
    group: symbolConfig
  - name: effectOptions
    type: array
    description: "Effect modifiers in Apple's words: iterative, cumulative, reversing, hideInactiveLayers, up, down, clockwise, byLayer, wholeSymbol …"
    summary: Extra settings for the animation
    does: Adds Apple's modifiers such as byLayer, clockwise or iterative to a native effect.
    group: symbolConfig
  - name: loop
    type: enum
    values: [continuous, periodic, once]
    default: continuous
    description: How the effect repeats
    summary: How often the animation repeats
    does: Chooses whether the effect repeats forever, repeats with pauses, or plays a single time.
    valueHelp: {"continuous": "repeats without stopping", "periodic": "plays, waits the loop delay, then plays again", "once": "plays one time and stops"}
    group: symbolConfig
  - name: loopCount
    min: 1
    max: 100
    step: 1
    type: number
    description: periodic only — plays before stopping (omit for forever)
    summary: How many times it plays
    does: With periodic looping, stops the effect after this many plays; empty means forever.
    group: symbolConfig
  - name: loopDelay
    min: 0
    max: 30
    step: 0.1
    type: number
    default: 1
    description: periodic only — seconds between plays
    summary: Pause between plays
    does: With periodic looping, waits this many seconds between plays.
    group: symbolConfig
  - name: speed
    min: 0.1
    max: 5
    step: 0.1
    type: number
    default: 1
    description: Playback speed multiplier
    summary: How fast it animates
    does: Multiplies the animation speed; 2 plays twice as fast and 0.5 half as fast.
    group: symbolConfig
  - name: activeWhen
    type: string
    default: always
    description: "always | truthy | a state word the synced value must equal"
    summary: When the animation runs
    does: Plays the effect always, only when the synced value is true, or only when it equals the state word you give.
    group: symbolConfig
  - name: variableMin
    type: number
    bounds: none
    default: 0
    description: Numeric value at which the variable layers are empty
    summary: Number where the icon is empty
    does: The synced number at which the symbol's variable layers show as empty.
    group: symbolConfig
  - name: variableMax
    type: number
    bounds: none
    default: 100
    description: Numeric value at which the variable layers are full
    summary: Number where the icon is full
    does: The synced number at which the symbol's variable layers show as full.
    group: symbolConfig
  - name: transition
    tab: style
    type: enum
    values: [replace, replace.downUp, replace.upUp, replace.offUp, replace.magic, none]
    description: How a glyph change animates (default replace; none when the value is numeric)
    summary: How the icon changes to a new one
    does: Animates the swap when the glyph changes to a different symbol.
    valueHelp: {"replace": "the old glyph morphs into the new one", "replace.downUp": "the old glyph slides down and the new one comes up", "replace.upUp": "both glyphs move up", "replace.offUp": "the old glyph fades while the new one moves up", "replace.magic": "matching parts of the two glyphs morph into each other", "none": "swaps instantly with no animation"}
    group: symbolConfig
  - name: tapEffect
    tab: style
    type: enum
    values: [none, bounce, pulse, variableColor, wiggle, rotate, breathe]
    default: none
    description: One-shot effect played on tap
    summary: A little animation on tap
    does: Plays this effect once each time the symbol is tapped.
    valueHelp: {"none": "no animation", "bounce": "the icon hops once", "pulse": "the icon fades once", "variableColor": "the layers light up once in sequence", "wiggle": "the icon shakes once", "rotate": "the icon spins once", "breathe": "the icon grows and shrinks once"}
    group: symbolConfig
  - name: triggers
    type: array
    description: "Server events that play a one-shot effect: [{ event, filter?, effect, effectOptions? }]"
    summary: Events that play the symbol effect once
    does: Plays a one-shot effect each time a matching server event arrives.
    group: symbolConfig
  - name: symbolConfig
    type: object
    description: Full configuration object holding every field marked group symbolConfig
    summary: The animation and look settings bundle
    does: Holds the rendering, effect, particle, loop and tap settings below; leave it out for a still symbol.
themeFields:
  - use: cornerRadius
  - use: controlPadding
    summary: Space inside the card
    does: Sets the gap between the card edge and the icon, 0 to 24 points.
  - use: surfacePrimary
    does: Sets the color behind the icon.
  - name: foregroundColor
    type: color
    default: #FFFFFF
    description: Default glyph colour
    summary: The icon's default color
    does: Colors the glyph when no tint is set.
  - use: borderColor
    summary: The card's outline color
    does: Colors the outline around the card.
  - use: borderWidth
    does: Sets the card outline thickness in points; 0 removes it.
  - use: secondaryColor
    summary: The caption color
    does: Colors the caption text under the glyph.
colorSlots:
  - slot: glyph
    default: neutral
    alias: tint
    since: next
    summary: The color of the symbol
    does: Colors the symbol when no color map or layer palette applies; until set it follows the neutral role, the text color.
  - slot: particles
    default: neutral
    alias: symbolConfig.particleColor
    since: next
    summary: The color of the rain, snow or sparkles
    does: Colors the particle effect; until set it follows the second layer color, the multicolor weather colors or the symbol's color.
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
| `glowRadius` | number | `0` | Soft glow behind the glyph in its own colour, 0–30 pt (the same attribute on every control that has it) |
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
