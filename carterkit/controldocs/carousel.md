---
type: carousel
label: Carousel
icon: rectangle.stack
category: controls
defaultSpan: [3, 2]
addIntent: organize
pickerCategory: Layout
depth: complete
friendlyName: Pages
oneLiner: Swipe between pages
aliases: [swipe, slider, slideshow, gallery, pager, pages]
addRank: 3
starterPreset: {"carouselMode":"paged","indicator":"dots","panels":[{"type":"group","id":"page-1","label":"Page 1","position":[0,0],"grid":{"columns":1,"rows":1},"children":[{"type":"label","id":"page-1-text","position":[0,0],"text":"Page 1"}]},{"type":"group","id":"page-2","label":"Page 2","position":[0,0],"grid":{"columns":1,"rows":1},"children":[{"type":"label","id":"page-2-text","position":[0,0],"text":"Page 2"}]}]}
io:
  - emits: value
    when: change
    title: When you swipe to another page
    type: number
    says: the position of the page you landed on, counting from 0
    example: 1
    since: next
  - receives: value
    role: follow
    type: number
    from: [hub, mqtt, http, store, default]
    says: the position of the page to show, counting from 0
    reacts: the carousel pages to it with animation, riffling through any pages in between
    example: 1
    since: next
card: {"draws": "each", "says": "Each page is a card of its own: the Background chip's padding, corners, border and shadow shape every page, and a page's own Background off drops its card.", "since": "next"}
fields:
  - name: carouselMode
    effect: behavior
    edit: look
    depth: surface
    title: Style
    type: enum
    values: [paged, coverflow, deck]
    default: paged
    description: Presentation style for the panels
    summary: How the pages are laid out as you swipe
    does: "Switches between one full page at a time, a tilted row of neighbors, or a stack of cards."
    valueHelp: {"paged": "one full-width page at a time that snaps into place", "coverflow": "the active page centered with smaller tilted neighbors at the sides", "deck": "pages stacked like cards; the front card swipes away to show the next"}
    valueTitles: {"paged": "Paged", "coverflow": "Cover flow", "deck": "Deck"}
    valueSymbols: {"paged": "rectangle.fill", "coverflow": "rectangle.3.group.fill", "deck": "rectangle.stack.fill"}
  - name: indicator
    edit: look
    depth: surface
    title: Indicator
    type: enum
    values: [dots, bars, { value: numeric, since: next }, none]
    default: dots
    description: Page indicator style
    summary: The little marks that show which page you are on
    does: "Draws a row of dots or bars (or a page count) below the pages with the current one in the accent color, or hides it."
    valueHelp: {"dots": "a row of small round dots", "bars": "a row of short flat bars", "numeric": "the page number as text, such as 2 / 5", "none": "no page marks shown"}
    valueTitles: {"dots": "Dots", "bars": "Bars", "numeric": "Number", "none": "None"}
    valueSymbols: {"dots": "ellipsis", "bars": "minus", "numeric": "number", "none": "eye.slash"}
  - name: carouselPeek
    since: next
    edit: scrub
    depth: hold
    under: carouselMode
    title: Peek
    type: number
    min: 0
    max: 0.3
    step: 0.05
    default: 0
    description: Paged mode neighbour peek, as a fraction of the width
    summary: How much of the next page peeks in at the edge
    does: "In paged style, shows a sliver of the neighbouring pages at the sides (0 none, 0.3 a wide peek)."
  - name: carouselStyle
    since: next
    edit: look
    depth: surface
    title: Page look
    type: enum
    values: [glass, translucent, liquidGlass]
    default: glass
    description: Panel chrome style
    summary: The material of each page card
    does: "Chooses the page card material: standard glass, a see-through tint, or liquid glass."
    valueHelp: {"glass": "the standard frosted glass card", "translucent": "a lighter see-through card", "liquidGlass": "the liquid glass material"}
    valueTitles: {"glass": "Glass", "translucent": "Translucent", "liquidGlass": "Liquid glass"}
    valueSymbols: {"glass": "square.fill", "translucent": "square.dashed", "liquidGlass": "drop.fill"}
  - name: autoAdvance
    min: 0
    max: 60
    step: 1
    type: number
    default: 0
    description: Seconds between auto-advances (0 = off)
    summary: Turns the pages by itself on a timer
    does: "Moves to the next page every this many seconds (0 to 60); 0 keeps it manual."
  - name: loop
    edit: part
    depth: hold
    title: Loop
    type: bool
    default: false
    description: Wrap past the first/last page
    summary: Lets the pages go round in a circle
    does: "On, swiping past the last page returns to the first and the reverse; off, the ends resist with a rubber-band."
  - name: panels
    chip: Panels
    type: object
    description: The panel groups this container pages through (group defs with children)
    summary: The pages themselves
    does: "Supplies the list of pages; each group definition becomes one swipeable page holding its own controls."
  - name: containerAnimation
    tab: style
    type: object
    description: Transition tuning, e.g. { profile, duration }
    summary: How the pages animate when switching
    does: "Tunes the page transition: motion profile, duration, bounce and the side or stack shape in coverflow and deck."
  - name: defaultValue
    min: 0
    step: 1
    bounds: none
    type: number
    default: 0
    description: Initial page index
    summary: Which page shows first
    does: "Opens on this page number when the layout appears, counting from 0 for the first page."
themeFields:
  - name: surfacePrimary
    type: color
    default: "#FFFFFF0F"
    description: Panel card background
    summary: The fill behind each page
    does: "Colors the card behind every page; a low-opacity white gives a faint glass tint."
  - name: accentColor
    edit: color
    depth: surface
    type: color
    default: "#667eea"
    description: Active indicator color
    summary: The color of the current page mark
    does: "Colors the dot or bar for the page you are on in the indicator."
  - name: cornerRadius
    unit: pt
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Panel corner radius
    summary: How round the page corners are
    does: "Rounds each page card's corners by this many points (0 square to 30 very round)."
  - name: blurEnabled
    title: Frosted glass
    type: bool
    default: true
    description: Blur the card background
    summary: Whether the page cards look like frosted glass
    does: "On, content behind each page card is blurred; off, the card is a plain flat fill."
  - use: borderColor
    summary: The color of the thin outline around each page
    does: "Colors the outline drawn around every page card."
  - use: borderWidth
    summary: How thick the page outline is
    does: "Sets the outline width around each page card in points (0 hides it, 5 is heavy)."
  - name: cardPadding
    unit: pt
    title: Card spacing
    min: 0
    max: 32
    step: 1
    type: number
    default: 12
    description: Padding inside each panel card
    summary: The breathing room between a page's edge and its contents
    does: "Insets the controls inside each page from the card edge by this many points (0 to 32)."
  - use: foregroundColor
    summary: The main color of writing on the pages
    does: "Colors the primary text inside the pages, such as titles."
  - use: secondaryColor
    summary: The softer color of supporting writing
    does: "Colors the secondary text inside the pages, such as captions and hints."
colorSlots:
  - slot: title
    default: neutral
    since: next
    summary: The color of the page titles
    does: Colors the title at the top of each page; until the layout picks a color it follows the neutral role, the text color.
  - slot: current
    default: primary
    since: next
    summary: The color of the current page mark
    does: Colors the dot or bar for the page you are on; until set it follows the primary role, the accent.
  - slot: indicator
    default: secondaryColor
    since: next
    summary: The color of the other page marks
    does: Colors the dots or bars for the other pages, faintly, and the page count; until set it keeps the theme's secondary text color.
---

# Carousel

A horizontally paged container that reveals one **panel** at a time. Each panel is a
[[group-def|group]] (its own label, grid, and nested children), so a carousel is a "set of
groups" you swipe between. The active page index is the control value, so it **syncs** and
fires **actions**, and a jump of several pages riffles through the intermediate ones.

## Type
`"carousel"`

## Relevant Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `panels` | [[group-def]][] | — | The pages, each a group definition |
| `carouselMode` | string | `"paged"` | `"paged"`, `"coverflow"`, or `"deck"` |
| `indicator` | string | `"dots"` | `"dots"`, `"bars"`, `"numeric"`, or `"none"` |
| `autoAdvance` | number | `0` | Seconds between auto-advances; `0` = off |
| `loop` | bool | `false` | Wrap past the ends |
| `defaultValue` | number | `0` | Initial page index |
| `containerAnimation` | object | — | Motion customization (see [[animations]] and below) |

The active page is a `.number` value. An incoming [[sync]] sets the page (animated);
swiping fires the [[actions|action]] with the new index as `{{value}}`.

## Modes

### `paged` (default)
One full-width panel at a time, with a spring snap and rubber-band at the ends (unless
`loop`).

### `coverflow`
The active panel is centered; neighbors are scaled down, pushed to the sides, rotated in 3D,
and faded. Tune with `containerAnimation.sideScale`, `sideRotation`, `sideSpacing`,
`sideOpacity`.

### `deck`
Panels stack in front of/behind each other with depth; the front card swipes away to reveal
the next. Tune with `containerAnimation.deckVisibleCount`, `deckScaleStep`, `deckOffsetStep`,
`deckRotation`.

## Animation Customization

All motion lives in the optional `containerAnimation` object:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `profile` | string | `bouncy` | `snappy`/`smooth`/`bouncy`/`gentle`/`instant` |
| `duration` | number | — | Override transition seconds |
| `bounce` | number | — | Spring bounce 0–1 |
| `multiStep` | bool | `true` | Riffle through pages on a multi-page jump |
| `stepInterval` | number | `0.12` | Seconds per intermediate step |
| `sideScale` | number | `0.82` | (coverflow) neighbor scale |
| `sideRotation` | number | `45` | (coverflow) neighbor 3D rotation° |
| `sideSpacing` | number | `0.55` | (coverflow) neighbor offset, fraction of width |
| `sideOpacity` | number | `0.6` | (coverflow) neighbor opacity |
| `deckVisibleCount` | number | `3` | (deck) visible stacked cards |
| `deckScaleStep` | number | `0.06` | (deck) scale reduction per layer |
| `deckOffsetStep` | number | `14` | (deck) point offset per layer |
| `deckRotation` | number | `0` | (deck) fan rotation° per layer |

## Examples

### Paged (the default) with a starting page
Shows the default `paged` style, the dots indicator and `defaultValue`: it opens on the second page and snaps one page at a time.
```json
{
  "type": "carousel",
  "id": "pages",
  "position": [0, 0],
  "span": [3, 3],
  "carouselMode": "paged",
  "indicator": "dots",
  "defaultValue": 1,
  "panels": [
    { "type": "group", "id": "p1", "label": "One", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "label", "id": "p1-l", "position": [0,0], "text": "First page" } ] },
    { "type": "group", "id": "p2", "label": "Two", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "label", "id": "p2-l", "position": [0,0], "text": "Second page" } ] }
  ]
}
```

### Coverflow of scenes, synced
Shows `coverflow` with `loop`, tuned side tilt, a `sync` that sets the page from the server and an `action` that sends the new page index when you swipe.
```json
{
  "type": "carousel",
  "id": "scenes",
  "position": [0, 0],
  "span": [3, 4],
  "carouselMode": "coverflow",
  "indicator": "dots",
  "loop": true,
  "containerAnimation": { "profile": "smooth", "sideScale": 0.78, "sideRotation": 50 },
  "defaultValue": 0,
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "scene" }, "valuePath": "index" }],
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "hub", "type": "scene", "payload": { "index": "{{value}}" } } },
  "panels": [
    { "type": "group", "id": "home", "label": "Home", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "label", "id": "home-l", "position": [0,0], "text": "Home scene" } ] },
    { "type": "group", "id": "away", "label": "Away", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "label", "id": "away-l", "position": [0,0], "text": "Away scene" } ] }
  ]
}
```

### Auto-advancing deck
Shows `deck` with the bars indicator, `autoAdvance` and `loop`: the front card swipes away every 4 seconds, forever, over a fanned stack of four cards.
```json
{
  "type": "carousel",
  "id": "promos",
  "position": [0, 0],
  "carouselMode": "deck",
  "indicator": "bars",
  "autoAdvance": 4,
  "loop": true,
  "containerAnimation": { "deckVisibleCount": 4, "deckOffsetStep": 18, "deckRotation": 3 },
  "panels": []
}
```

### Bare pages with no indicator
Shows `indicator: none` with `loop` off: no page marks, and the ends rubber-band instead of wrapping.
```json
{
  "type": "carousel",
  "id": "quiet",
  "position": [0, 0],
  "indicator": "none",
  "loop": false,
  "containerAnimation": { "profile": "instant", "multiStep": false },
  "panels": []
}
```

### Themed glass pages with square edges
Shows the theme fields: a darker tinted card, a green current-page mark, sharper corners, a thicker border and tighter inner spacing.
```json
{
  "type": "carousel",
  "id": "themed",
  "position": [0, 0],
  "theme": { "accentColor": "#34C759", "surfacePrimary": "#00000040", "cornerRadius": 4, "borderWidth": 2, "borderColor": "#34C75966", "cardPadding": 6, "blurEnabled": false, "foregroundColor": "#FFFFFF", "secondaryColor": "#FFFFFF80" },
  "panels": []
}
```

### Note on editor fields
Every hinted field here (Style, Indicator, Loop) changes something on screen; `panels` and `containerAnimation` are edited in the layout structure and the animation tab rather than by a single control.

## Theming
Panels render as glass cards from the active [[theming|theme]] (`surfacePrimary`,
`cornerRadius`, `borderColor`, `cardPadding`). Page titles draw the `title` colour slot, the current page mark
`current` (the primary role, `accentColor` until a palette sets it) and the other marks and the count `indicator`. Set
`hideBackground` on a panel for a transparent page, or per-child `theme` overrides inside a
panel.

## Related
- [[group-def]] — each panel is a group
- [[flip-card]] — flip between faces instead of paging
- [[accordion]] — vertical expand/collapse
- [[actions]] — `{{value}}` page index
- [[sync]] — drive the page from the server
- [[animations]] — base animation profiles
- [[theming]] — theme & appearance
