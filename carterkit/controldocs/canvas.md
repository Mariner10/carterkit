---
type: canvas
label: Canvas
icon: square.on.square.dashed
category: input
defaultSpan: [10, 4]
fields:
  - name: label
    type: string
    description: Header label
  - name: controlHeight
    type: number
    default: 560
    description: Rendered height in points (required in flow-mode grids)
  - name: aspect
    type: number
    default: 1.0
    description: Surface aspect ratio (width ÷ height)
    group: canvasConfig
  - name: editable
    type: bool
    default: false
    description: Long-press lifts a card; drags emit place/layout and round-trip the synced value
    group: canvasConfig
  - name: showGrid
    type: bool
    default: false
    description: Faint dot lattice on the surface (uses the snap increment when set)
    group: canvasConfig
  - name: snap
    type: number
    default: 0
    description: Normalized snap increment applied on drop (0.05 = a 20×20 lattice; 0 = free)
    group: canvasConfig
  - name: maxZoom
    type: number
    default: 3
    description: Max pinch-zoom scale (1 disables zoom and panning)
    group: canvasConfig
  - name: items
    type: array
    description: The hosted controls with their normalized frames (see Config)
    group: canvasConfig
  - name: events
    type: object
    description: pickup / place / layout actions fired as cards are lifted and dropped
    group: canvasConfig
---

# Canvas

A freeform **container**: real, live controls hosted at normalized `(x, y, w, h)` on a
pannable, zoomable surface. Where [[pinboard]] places markers, `canvas` places whole
working controls — each card renders through the real renderer, so its bindings,
actions, sync and theming all work exactly as they would in a grid cell.

Pinch to zoom (up to `maxZoom`), drag empty surface to pan while zoomed. With
`editable: true`, **long-press lifts a card** (so hosted controls keep their own
taps/drags), dragging moves it, and dropping emits `place` + `layout` and round-trips
the synced value — a server or a peer can seed or rearrange the board.

The structural (Pattern-7) drag control; the on-device **Layout Editor** speaks the
same lift/snap language but authors real grid layouts.

## Type
`"canvas"`

## Sizing

In a `mode: "flow"` grid set `controlHeight` (e.g. 560); in a 2-D grid give it a real
`span` (rough guide: `[10, 4]`). `aspect` shapes the surface itself. See
[[grid-dimensions]].

## Config (`canvasConfig`)

| Field | Type | Description |
|-------|------|-------------|
| `items` | array | The hosted controls (below). Order is z-order: later items draw on top. |
| `aspect` | number | Surface width ÷ height (default 1.0). |
| `editable` | bool | Allow rearranging cards (default false — a static freeform dashboard). |
| `showGrid` | bool | Faint dot lattice (spatial affordance for editable boards). |
| `snap` | number | Normalized drop-snap increment; 0/absent = free placement. |
| `maxZoom` | number | Max pinch-zoom scale (default 3; 1 disables zoom/pan). |
| `events` | object | `pickup` / `place` / `layout` fired on drag (see [[DragEventActions]]). |

### Item `{ id, x, y, w, h, locked?, control }`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable card id — the key in the synced `frames` and in events. |
| `x`, `y` | number | Top-leading corner, 0…1 fractions of the surface. |
| `w`, `h` | number | Size, 0…1 fractions of the surface (default 0.25 each). |
| `locked` | bool | Card can't be moved in editable mode (still live/interactive). |
| `control` | object | Any control object. `position` may be omitted (it's meaningless on a canvas). |

## Events

Lifting a card fires `pickup` `{ item, from: "canvas" }`. Dropping (or a VoiceOver
nudge) fires `place` `{ item, x, y, w, h }` and `layout`
`{ frames: { id: {x,y,w,h} }, changed }`. Token substitution (`{{item}}`, `{{x}}`, …)
works as in every drag control.

## Accessibility

Cards keep their child elements (the hosted control stays fully usable) and expose
**Move left/right/up/down** actions that step by the snap increment (5% when unset) —
the whole surface works without drag.

## Synced value

`{ "frames": { "<id>": { "x": 0.1, "y": 0.2, "w": 0.4, "h": 0.25 } } }`. [[sync]] a
value in this shape to seed or rearrange cards; ids not in `items` are ignored, and
frames the push omits fall back to the item's configured spot.

## Examples

### Freeform status board

```json
{
  "type": "canvas",
  "id": "status-board",
  "position": [0, 0],
  "span": [10, 4],
  "controlHeight": 560,
  "label": "Ops Board",
  "canvasConfig": {
    "aspect": 1.2,
    "items": [
      { "id": "cpu", "x": 0.05, "y": 0.05, "w": 0.42, "h": 0.3,
        "control": { "type": "gauge", "id": "cpu-gauge", "label": "CPU", "min": 0, "max": 100,
                     "sync": [{ "method": "meshsocket", "event": "telemetry", "valuePath": "cpu" }] } },
      { "id": "temp", "x": 0.53, "y": 0.05, "w": 0.42, "h": 0.3,
        "control": { "type": "sparkline", "id": "temp-spark", "label": "Temp",
                     "sync": [{ "method": "meshsocket", "event": "telemetry", "valuePath": "temp" }] } },
      { "id": "power", "x": 0.05, "y": 0.42, "w": 0.42, "h": 0.18,
        "control": { "type": "toggle", "id": "rig-power", "label": "Rig Power",
                     "action": { "method": "meshsocket", "mode": "send", "event": "route_msg",
                                 "payload": { "target_id": "hub", "type": "power", "payload": { "on": "{{value}}" } } } } }
    ]
  }
}
```

### Editable, server-seeded board

```json
{
  "type": "canvas",
  "id": "war-room",
  "position": [0, 0],
  "span": [12, 4],
  "label": "War Room",
  "canvasConfig": {
    "editable": true,
    "showGrid": true,
    "snap": 0.05,
    "items": [
      { "id": "feed", "x": 0.05, "y": 0.05, "w": 0.9, "h": 0.35,
        "control": { "type": "logConsole", "id": "feed-log", "label": "Feed", "maxLines": 40 } },
      { "id": "arm", "x": 0.05, "y": 0.5, "w": 0.42, "h": 0.2, "locked": true,
        "control": { "type": "button", "id": "arm-btn", "label": "Arm",
                     "action": { "method": "meshsocket", "mode": "send", "event": "arm" } } }
    ],
    "events": {
      "place": { "method": "meshsocket", "mode": "send", "event": "route_msg",
                 "payload": { "target_id": "hub", "type": "board_place",
                              "payload": { "card": "{{item}}", "x": "{{x}}", "y": "{{y}}" } } },
      "layout": { "method": "meshsocket", "mode": "send", "event": "board_state" }
    }
  }
}
```

> **Try it:** the bundled **`canvas-demo`** layout has both — a live status board and
> an editable, snapping war-room board.

## Related
- [[pinboard]] — markers instead of whole controls
- [[actions]] · [[sync]] · [[grid-dimensions]]
