---
type: flipCard
depth: complete
label: Flip Card
icon: rectangle.portrait.rotate
category: controls
defaultSpan: [2, 2]
addIntent: organize
pickerCategory: Layout
friendlyName: Flip card
oneLiner: "Two sides: tap to flip"
aliases: [flip, card, reveal, two-sided, front back, flashcard]
addRank: 4
starterPreset: {"flipTrigger":"tap","flipAxis":"horizontal","panels":[{"type":"group","id":"front","label":"Front","position":[0,0],"grid":{"columns":1,"rows":1},"children":[{"type":"label","id":"front-text","position":[0,0],"text":"Front"}]},{"type":"group","id":"back","label":"Back","position":[0,0],"grid":{"columns":1,"rows":1},"children":[{"type":"label","id":"back-text","position":[0,0],"text":"Back"}]}]}
io:
  - emits: value
    when: tap
    title: When you flip it
    field: action
    type: number
    says: the number of the face now showing, counting from 0
    example: 1
    whenBy: {"flipTrigger": {"longPress": "hold"}}
    also: Faces flip in order and wrap round to the first
    since: next
  - receives: value
    role: follow
    type: number
    from: [hub, mqtt, http, store, default]
    says: the number of the face to show, counting from 0
    reacts: the card flips to that face, turning once for each face it passes
    example: 1
    since: next
  - sample: 0
    next: 1
card: {"draws": "each", "says": "Each face is a card of its own: the Background chip's padding, corners, border and shadow shape every face, and a face's own Background off drops its card.", "since": "next"}
fields:
  - name: flipTrigger
    effect: behavior
    edit: look
    depth: surface
    title: Flip by
    type: enum
    values: [tap, longPress]
    default: tap
    description: Gesture that advances to the next face
    summary: What makes it flip
    does: Chooses whether a tap or a long press turns the card to its next face.
    valueHelp: {"tap": "a quick tap flips the card", "longPress": "press and hold to flip, so taps reach controls on the face"}
    valueTitles: {"tap": "Tap", "longPress": "Press and hold"}
    valueSymbols: {"tap": "hand.tap.fill", "longPress": "hand.point.up.left.fill"}
  - name: flipAxis
    edit: look
    depth: surface
    title: Flip direction
    type: enum
    values: [horizontal, vertical]
    default: horizontal
    description: Axis the card rotates around
    summary: Which way it turns
    does: Turns the card left-to-right around a vertical axis or top-to-bottom around a horizontal one.
    valueHelp: {"horizontal": "spins left to right like a page of a book", "vertical": "tips top to bottom like a notepad"}
    valueTitles: {"horizontal": "Sideways", "vertical": "Up and down"}
    valueSymbols: {"horizontal": "arrow.left.and.right", "vertical": "arrow.up.and.down"}
  - name: panels
    chip: Panels
    type: object
    description: The panel groups this container pages through (group defs with children)
    summary: The faces of the card
    does: Lists the faces the card flips through, each a group with its own controls.
  - name: containerAnimation
    tab: style
    type: object
    description: Transition tuning, e.g. { profile, duration }
    summary: How the card animates when flipping
    does: Tunes the flip motion, such as speed, bounce and 3D depth.
  - name: defaultValue
    min: 0
    step: 1
    bounds: none
    type: number
    default: 0
    description: Initial face index
    summary: Which face shows first
    does: Picks the face shown at start, counting from 0.
themeFields:
  - name: surfacePrimary
    type: color
    default: "#FFFFFF0F"
    description: Face card background
    summary: Face background
    does: Fills each face card with this color.
  - name: cornerRadius
    unit: pt
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Face corner radius
    summary: How rounded the faces are
    does: Rounds each face corner from square (0) to 30 points.
  - name: blurEnabled
    title: Frosted glass
    type: bool
    default: true
    description: Blur the card background
    summary: Frosted glass look
    does: Blurs what is behind each face card when on.
  - use: borderColor
    summary: Outline color
    does: Colors the line around each face.
  - use: borderWidth
    summary: Outline thickness
    does: Sets how thick the face outline is, 0 to 5 points.
  - name: cardPadding
    unit: pt
    title: Card spacing
    min: 0
    max: 32
    step: 1
    type: number
    default: 12
    description: Padding inside each panel card
    summary: Space inside each face
    does: Sets the padding inside each face card, 0 to 32 points.
  - use: foregroundColor
    summary: Main text color
    does: Colors the main text on the faces.
colorSlots:
  - slot: title
    default: neutral
    since: next
    summary: The color of the face titles
    does: Colors the title at the top of each face; until the layout picks a color it follows the neutral role, the text color.
---

# Flip Card

A card with **N faces** that flips between them. Each face is a [[group-def|group]] (label,
grid, nested children). Two faces give the classic front/back; more faces flip through in
sequence and wrap. The active face index is the control value, so it **syncs** and fires
**actions**, and a jump of several faces chains a flip per step.

## Type
`"flipCard"`

## Relevant Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `panels` | [[group-def]][] | — | The faces (2+), each a group definition |
| `flipTrigger` | string | `"tap"` | `"tap"` or `"longPress"` |
| `flipAxis` | string | `"horizontal"` | `"horizontal"` (Y axis) or `"vertical"` (X axis) |
| `defaultValue` | number | `0` | Initial face index |
| `containerAnimation` | object | — | Motion customization (see below) |

Tapping/long-pressing advances to the next face (wrapping) and fires the
[[actions|action]] with the new index. An incoming [[sync]] flips to a target face.

## 3D Flip

The card rotates with perspective and **back-face culling** — the incoming face stays hidden
until the half-way point, so it never renders mirrored. Customize via `containerAnimation`:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `profile` | string | `bouncy` | Base spring profile |
| `duration` | number | — | Override flip seconds |
| `bounce` | number | — | Spring bounce 0–1 |
| `multiStep` | bool | `true` | Chain a flip per step on a multi-face jump |
| `stepInterval` | number | `0.12` | Seconds between chained flips |
| `flipPerspective` | number | `0.5` | 3D perspective amount |

## Examples

### Status front / actions back
A gauge on the front and two buttons on the back, flipping left to right with a snappy spring.
```json
{
  "type": "flipCard",
  "id": "status-card",
  "position": [0, 0],
  "span": [2, 2],
  "flipAxis": "horizontal",
  "containerAnimation": { "profile": "snappy", "flipPerspective": 0.7 },
  "panels": [
    { "type": "group", "id": "front", "label": "Status", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "gauge", "id": "f-cpu", "position": [0,0], "label": "CPU", "min": 0, "max": 100, "defaultValue": 42 } ] },
    { "type": "group", "id": "back", "label": "Actions", "position": [0,0], "grid": { "columns": 2, "rows": 1 },
      "children": [
        { "type": "button", "id": "b-restart", "position": [0,0], "label": "Restart", "icon": "arrow.clockwise" },
        { "type": "button", "id": "b-stop", "position": [0,1], "label": "Stop", "icon": "stop.fill" }
      ] }
  ]
}
```

### Flashcard with a long press
A two-face quiz card that starts on the question and only flips when you press and hold.
```json
{
  "type": "flipCard",
  "id": "quiz-card",
  "position": [0, 0],
  "span": [2, 2],
  "flipTrigger": "longPress",
  "defaultValue": 0,
  "panels": [
    { "type": "group", "id": "q", "label": "Question", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "label", "id": "q-text", "position": [0,0], "text": "Capital of France?" } ] },
    { "type": "group", "id": "a", "label": "Answer", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "label", "id": "a-text", "position": [0,0], "text": "Paris" } ] }
  ]
}
```

### Vertical flip with a slow, bouncy turn
A card that tips top to bottom, with a longer bouncy motion and deeper 3D perspective.
```json
{
  "type": "flipCard",
  "id": "tip-card",
  "position": [0, 0],
  "span": [2, 2],
  "flipAxis": "vertical",
  "containerAnimation": { "profile": "bouncy", "duration": 0.8, "bounce": 0.4, "flipPerspective": 0.8 },
  "panels": [
    { "type": "group", "id": "top", "label": "Today", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "label", "id": "t-text", "position": [0,0], "text": "Sunny" } ] },
    { "type": "group", "id": "bottom", "label": "Tomorrow", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "label", "id": "b-text", "position": [0,0], "text": "Rain" } ] }
  ]
}
```

## Theming
Faces are glass cards from the active [[theming|theme]]. Set `hideBackground` on a face for a
transparent card.

## Related
- [[group-def]] — each face is a group
- [[carousel]] — page horizontally instead of flipping
- [[accordion]] — vertical expand/collapse
- [[actions]] — `{{value}}` face index
- [[sync]] — drive the face from the server
- [[animations]] — base animation profiles
