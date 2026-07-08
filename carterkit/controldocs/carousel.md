---
type: carousel
label: Carousel
icon: rectangle.stack
category: controls
defaultSpan: [3, 2]
fields:
  - name: carouselMode
    type: enum
    values: [paged, coverflow, deck]
    default: paged
    description: Presentation style for the panels
  - name: indicator
    type: enum
    values: [dots, bars, none]
    default: dots
    description: Page indicator style
  - name: autoAdvance
    type: number
    default: 0
    description: Seconds between auto-advances (0 = off)
  - name: loop
    type: bool
    default: false
    description: Wrap past the first/last page
  - name: panels
    type: object
    description: The panel groups this container pages through (group defs with children)
  - name: containerAnimation
    type: object
    description: Transition tuning, e.g. { profile, duration }
themeFields:
  - name: surfacePrimary
    type: color
    default: "#FFFFFF0F"
    description: Panel card background
  - name: accentColor
    type: color
    default: "#667eea"
    description: Active indicator color
  - name: cornerRadius
    type: number
    default: 12
    description: Panel corner radius
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
| `indicator` | string | `"dots"` | `"dots"`, `"bars"`, or `"none"` |
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

### Coverflow of scenes, synced
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
  "action": { "method": "meshsocket", "mode": "request", "event": "route_msg", "payload": { "target_id": "hub", "type": "scene", "payload": { "index": "{{value}}" } } },
  "panels": [
    { "type": "group", "id": "home", "label": "Home", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "label", "id": "home-l", "position": [0,0], "text": "Home scene" } ] },
    { "type": "group", "id": "away", "label": "Away", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "label", "id": "away-l", "position": [0,0], "text": "Away scene" } ] }
  ]
}
```

### Auto-advancing deck
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

## Theming
Panels render as glass cards from the active [[theming|theme]] (`surfacePrimary`,
`cornerRadius`, `borderColor`, `cardPadding`). The active indicator uses `accentColor`. Set
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
