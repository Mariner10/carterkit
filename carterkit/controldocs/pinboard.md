---
type: pinboard
label: Pinboard
icon: mappin.and.ellipse
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
  - name: background
    type: string
    description: SF Symbol drawn faint behind the surface (floor-plan / map backdrop)
    group: pinboardConfig
  - name: surfaceAspect
    type: number
    default: 1.4
    description: Surface aspect ratio (width ÷ height)
    group: pinboardConfig
  - name: searchable
    type: bool
    default: false
    description: Show a filter field above the option area
    group: pinboardConfig
  - name: paletteLabel
    type: string
    default: Items
    description: Header for the option area
    group: pinboardConfig
  - name: hidePalette
    type: bool
    default: false
    description: Hide the option area (surfaces whose markers all start placed)
    group: pinboardConfig
  - name: events
    type: object
    description: events
    group: pinboardConfig
  - name: items
    type: object
    description: items
    group: pinboardConfig
---

# Pinboard

An option area plus a freeform **surface** you drag items onto at any (x, y) — a
floor-plan device placer, a map pin board, a seating chart on a photo. Drag a palette
item onto the surface to **place** it, drag a marker to **reposition**, drag it back to
the palette to **remove**, and **tap** a placed marker to fire its action.

The second spatial (Pattern-3) drag control: placements ride normalized x/y
([[CARSpatialPlacementState]]) and round-trip through the synced value, so a server can
seed or push a layout.

## Type
`"pinboard"`

## Sizing

In a `mode: "flow"` grid set `controlHeight` (e.g. 560); in a 2-D grid give it a real
`span`. `surfaceAspect` controls the surface's shape. See [[grid-dimensions]].

## Config (`pinboardConfig`)

| Field | Type | Description |
|-------|------|-------------|
| `items` | array | The catalog (below). An item with both `x` and `y` starts placed; otherwise it's in the option area. |
| `background` | string | SF Symbol drawn faint behind the surface (e.g. `"house.fill"`, `"map"`). Omitted ⇒ a plain surface. |
| `surfaceAspect` | number | Surface width ÷ height (default 1.4). |
| `searchable` | bool | Filter field over the option area. |
| `paletteLabel` | string | Option-area header (default "Items"). |
| `hidePalette` | bool | Hide the option area. |
| `events` | object | `pickup` / `place` / `layout` fired on drag. |

### Item `{ id, label?, icon?, tint?, x?, y?, action?, locked? }`

| Field | Type | Description |
|-------|------|-------------|
| `x`, `y` | number | Initial normalized position 0…1. Both present ⇒ starts placed. |
| `action` | object | Fired when the *placed* marker is tapped. `{{value}}` = the id. |
| `locked` | bool | Can't be dragged (still tappable). |

## Events

Placing/moving a marker fires `place` `{ item, x, y }` and `layout`
`{ points: { id: {x,y} }, changed }` (see [[DragEventActions]]). Tapping a placed marker
fires that item's `action`. Removing a marker (drag back to the palette) fires `layout`.

## Accessibility

Under VoiceOver tray chips expose a **"Place at center"** action and markers read
their position ("28% across, 40% down"), fire on double-tap, and expose **"Return
to <tray>"** — the full surface works without drag.

## Synced value

`{ "points": { "<id>": { "x": 0.28, "y": 0.4 } } }`. [[sync]] a value in this shape to
let a server seed or rearrange placements; ids not in the catalog are ignored.

## Examples

### Floor-plan device placement

```json
{
  "type": "pinboard",
  "id": "home-plan",
  "position": [0, 0],
  "span": [10, 4],
  "controlHeight": 560,
  "label": "Home Devices",
  "pinboardConfig": {
    "background": "house.fill",
    "surfaceAspect": 1.6,
    "paletteLabel": "Unplaced devices",
    "items": [
      { "id": "living-lamp", "label": "Living Lamp", "icon": "lamp.table.fill", "tint": "#FF9500", "x": 0.28, "y": 0.4,
        "action": { "method": "meshsocket", "mode": "send", "event": "route_msg",
                    "payload": { "target_id": "hub", "type": "toggle", "payload": { "device": "{{value}}" } } } },
      { "id": "front-door", "label": "Front Door", "icon": "door.left.hand.closed", "tint": "#34C759",
        "action": { "method": "meshsocket", "mode": "send", "event": "route_msg",
                    "payload": { "target_id": "hub", "type": "toggle", "payload": { "device": "{{value}}" } } } }
    ],
    "events": {
      "place": { "method": "meshsocket", "mode": "send", "event": "route_msg",
                 "payload": { "target_id": "hub", "type": "place_device",
                              "payload": { "device": "{{item}}", "x": "{{x}}", "y": "{{y}}" } } },
      "layout": { "method": "meshsocket", "mode": "send", "event": "floorplan_state" }
    }
  }
}
```

> **Try it:** the bundled **`pinboard-demo`** layout has this floor plan (three devices
> pre-placed, two in the tray).

## Related
- [[actions]] — marker actions and `{{value}}`
- [[sync]] · [[grid-dimensions]]
