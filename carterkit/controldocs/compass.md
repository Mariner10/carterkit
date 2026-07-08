---
type: compass
label: Compass
icon: location.north.circle.fill
category: input
defaultSpan: [7, 3]
fields:
  - name: label
    type: string
    description: Header label
  - name: controlHeight
    type: number
    default: 420
    description: Rendered height in points (required in flow-mode grids)
  - name: tolerance
    type: number
    default: 15
    description: Half-angle (°) within which the needle counts as pointing at a puck
    group: compassConfig
  - name: dwell
    type: number
    default: 1.2
    description: Seconds to hold on a puck before its action fires (0 = instant)
    group: compassConfig
  - name: showCardinals
    type: bool
    default: true
    description: Draw N/E/S/W ticks
    group: compassConfig
  - name: editable
    type: bool
    default: true
    description: Allow dragging pucks to re-bearing them
    group: compassConfig
  - name: events
    type: object
    description: events
    group: compassConfig
  - name: pucks
    type: object
    description: pucks
    group: compassConfig
---

# Compass

A heading-driven **action ring**. The device's live heading rotates a needle; you
arrange action **pucks** around the ring; when the needle points at a puck (within
`tolerance`) for `dwell` seconds, that puck's `action` fires. Point your phone at a
thing to trigger it — no tapping. Pucks can be **dragged** around the ring to
re-bearing them (firing pickup/place/layout), so the same control authors and runs.

The first spatial (Pattern-3) drag control: puck placements ride a bearing coordinate
([[CARSpatialPlacementState]]) and the whole ring speaks the [[actions]] convention.

## Type
`"compass"`

## Heading (required)

The needle is driven by the control's **own value** — bind the compass sensor:

```json
"sync": [{ "method": "sensor", "sensor": "heading" }]
```

The bound value is the heading in degrees (0 = N, clockwise). No compass hardware (e.g.
the simulator)? Set a `defaultValue` (a number) to render a static needle for testing.

## Sizing

Square control. In a `mode: "flow"` grid set `controlHeight` (e.g. 420); in a 2-D grid
give it a real `span`. See [[grid-dimensions]].

## Config (`compassConfig`)

| Field | Type | Description |
|-------|------|-------------|
| `pucks` | array | The action pucks (below). |
| `tolerance` | number | Half-angle (°) the needle must be within to "point at" a puck (default 15). |
| `dwell` | number | Seconds to hold before firing (default 1.2; 0 = instant on entry). |
| `showCardinals` | bool | N/E/S/W ticks (default true). |
| `editable` | bool | Drag pucks to re-bearing them (default true). |
| `events` | object | `pickup` / `place` / `layout` fired on puck drag. |

### Puck `{ id, label?, icon?, tint?, bearing, action?, locked? }`

| Field | Type | Description |
|-------|------|-------------|
| `bearing` | number | Where it sits, degrees (0 = N, clockwise). |
| `action` | object | Fired on point-and-dwell. `{{value}}` = the puck id. |
| `locked` | bool | Can't be dragged (still activatable). |

## Events

Puck **drag** fires `place` `{ item, x, y, bearing }` and `layout`
`{ points: { id: {x,y,bearing} }, changed }` (see [[DragEventActions]]). Puck
**activation** fires that puck's own `action`.

## Examples

### Point-to-run scenes

```json
{
  "type": "compass",
  "id": "action-ring",
  "position": [0, 0],
  "span": [7, 4],
  "controlHeight": 420,
  "label": "Action Ring",
  "defaultValue": 5,
  "compassConfig": {
    "tolerance": 20,
    "dwell": 1.0,
    "pucks": [
      { "id": "lights", "label": "Lights", "icon": "lightbulb.fill", "tint": "#FF9500", "bearing": 0,
        "action": { "method": "meshsocket", "mode": "send", "event": "route_msg",
                    "payload": { "target_id": "home", "type": "scene", "payload": { "name": "{{value}}" } } } },
      { "id": "music", "label": "Music", "icon": "music.note", "tint": "#FF2D55", "bearing": 90,
        "action": { "method": "meshsocket", "mode": "send", "event": "route_msg",
                    "payload": { "target_id": "home", "type": "scene", "payload": { "name": "{{value}}" } } } },
      { "id": "lock", "label": "Lock", "icon": "lock.fill", "tint": "#34C759", "bearing": 180,
        "action": { "method": "meshsocket", "mode": "send", "event": "route_msg",
                    "payload": { "target_id": "home", "type": "scene", "payload": { "name": "{{value}}" } } } }
    ]
  },
  "sync": [{ "method": "sensor", "sensor": "heading" }]
}
```

> **Try it:** the bundled **`compass-demo`** layout has this ring (seeded to 5° so a
> needle shows in the simulator).

## Accessibility

Under VoiceOver each puck reads its bearing, **double-tap fires its action** (no
pointing needed), and the adjustable action (swipe up/down) rotates it 15° per step.

## Related
- [[sensors]] — the `heading` pipeline
- [[actions]] — puck actions and `{{value}}`
- [[sync]] · [[grid-dimensions]]
