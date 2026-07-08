---
type: flipCard
label: Flip Card
icon: rectangle.portrait.rotate
category: controls
defaultSpan: [2, 2]
fields:
  - name: flipTrigger
    type: enum
    values: [tap, longPress]
    default: tap
    description: Gesture that advances to the next face
  - name: flipAxis
    type: enum
    values: [horizontal, vertical]
    default: horizontal
    description: Axis the card rotates around
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
    description: Face card background
  - name: cornerRadius
    type: number
    default: 12
    description: Face corner radius
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
