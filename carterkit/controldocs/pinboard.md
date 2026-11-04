---
type: pinboard
depth: complete
label: Pinboard
icon: mappin.and.ellipse
category: input
defaultSpan: [10, 4]
addIntent: change
pickerCategory: Inputs
friendlyName: Pin board
oneLiner: Pin things onto a picture
aliases: [board, notes, sticky, pins, corkboard, cards]
starterPreset: {"label": "Pin board"}
fields:
  - name: haptic
    edit: look
    depth: hold
    under: label
    tab: action
    type: enum
    values: [none, light, medium, heavy, soft, rigid, selection, success, warning, error]
    description: Touch feedback on interaction (supported hardware)
    summary: The buzz you feel when you drag
    does: Plays this haptic on the phone when you interact with the board.
    valueHelp: {"none": "no buzz", "light": "a small soft tap", "medium": "a medium tap", "heavy": "a strong thud", "soft": "a gentle muffled tap", "rigid": "a firm sharp click", "selection": "the faint tick of picking an item", "success": "the double tap of a success", "warning": "a two-pulse warning", "error": "a sharp triple buzz of an error"}
  - name: label
    edit: inline
    depth: surface
    title: Label
    type: string
    description: Header label
    summary: The title above the board
    does: Shows this text as the header of the pin board.
  - name: controlHeight
    effect: behavior
    edit: scrub
    depth: surface
    title: Height
    min: 100
    max: 1200
    step: 10
    type: number
    default: 560
    description: Rendered height in points (required in flow-mode grids)
    summary: How tall the board is
    does: Sets the board height in points in a flow grid; in a 2-D grid the span sets it instead.
  - name: background
    type: string
    description: SF Symbol drawn faint behind the surface (floor-plan / map backdrop)
    summary: A faint picture behind the surface
    does: Draws this SF Symbol faintly behind the surface, e.g. house.fill for a floor plan or map for a map.
    group: pinboardConfig
  - name: surfaceAspect
    edit: scrub
    depth: hold
    under: controlHeight
    title: Shape
    min: 0.2
    max: 5
    step: 0.1
    type: number
    default: 1.4
    description: Surface aspect ratio (width ÷ height)
    summary: How wide the surface is
    does: Sets the surface shape as width divided by height, 0.2 to 5; 1.4 is wider than tall.
    group: pinboardConfig
  - name: searchable
    effect: behavior
    edit: part
    depth: hold
    title: Search
    type: bool
    default: false
    description: Show a filter field above the option area
    summary: A search box over the pile
    does: Adds a filter field above the option area so you can find an item by its label.
    group: pinboardConfig
  - name: paletteLabel
    edit: inline
    depth: surface
    title: Palette title
    type: string
    default: Items
    description: Header for the option area
    summary: The name of the item pile
    does: Sets the header over the option area, e.g. Unplaced devices instead of Items.
    group: pinboardConfig
  - name: hidePalette
    effect: behavior
    edit: part
    depth: hold
    title: Palette
    tab: style
    type: bool
    default: false
    description: Hide the option area (surfaces whose markers all start placed)
    summary: Hide the item pile
    does: Removes the option area so only the surface shows, for boards whose markers all start placed.
    group: pinboardConfig
  - name: events
    tab: advanced
    type: object
    description: events
    summary: What happens when you drag
    does: Holds the pickup, place and layout actions that fire as you lift, drop and settle a marker.
    group: pinboardConfig
  - name: items
    type: object
    description: items
    summary: The things you can pin
    does: Lists the items, each with an id, label, icon, tint, optional starting x and y, a tap action and a locked flag.
    group: pinboardConfig
  - name: pinboardConfig
    type: object
    description: Grouped config object (see grouped fields)
    summary: The board settings in one bundle
    does: Groups the backdrop, shape, search, palette, events and items settings; any entry left out uses its default.
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
Demonstrates a house backdrop, one device pre-placed with a tap action, and place and layout events.

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
        "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply",
                    "payload": { "target_name": "hub", "type": "toggle", "payload": { "device": "{{value}}" } } } },
      { "id": "front-door", "label": "Front Door", "icon": "door.left.hand.closed", "tint": "#34C759",
        "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply",
                    "payload": { "target_name": "hub", "type": "toggle", "payload": { "device": "{{value}}" } } } }
    ],
    "events": {
      "place": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply",
                 "payload": { "target_name": "hub", "type": "place_device",
                              "payload": { "device": "{{item}}", "x": "{{x}}", "y": "{{y}}" } } },
      "layout": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "floorplan_state" } }
    }
  }
}
```

### Map with a search box
Demonstrates `searchable` and `surfaceAspect`: a wide map backdrop with a filter over the pile of pins.
```json
{
  "type": "pinboard",
  "id": "site-map",
  "position": [0, 0],
  "span": [10, 4],
  "controlHeight": 480,
  "label": "Site Map",
  "pinboardConfig": {
    "background": "map",
    "surfaceAspect": 2,
    "searchable": true,
    "paletteLabel": "Cameras",
    "items": [
      { "id": "cam-gate", "label": "Gate", "icon": "video.fill", "tint": "#FF3B30" },
      { "id": "cam-yard", "label": "Yard", "icon": "video.fill", "tint": "#5AC8FA" },
      { "id": "cam-shed", "label": "Shed", "icon": "video.fill", "tint": "#FF9500" }
    ]
  }
}
```

### Server-seeded markers
Demonstrates `hidePalette` with items already placed by `x` and `y`, one locked so it cannot be dragged.
```json
{
  "type": "pinboard",
  "id": "seat-map",
  "position": [0, 0],
  "span": [8, 4],
  "controlHeight": 420,
  "label": "Seat Map",
  "pinboardConfig": {
    "hidePalette": true,
    "surfaceAspect": 1.6,
    "items": [
      { "id": "seat-a", "label": "A", "icon": "chair.fill", "tint": "#667eea", "x": 0.25, "y": 0.5 },
      { "id": "seat-b", "label": "B", "icon": "chair.fill", "tint": "#34C759", "x": 0.7, "y": 0.5, "locked": true }
    ]
  }
}
```

> **Try it:** the bundled **`pinboard-demo`** layout has this floor plan (three devices
> pre-placed, two in the tray).

## Related
- [[actions]] — marker actions and `{{value}}`
- [[sync]] · [[grid-dimensions]]
