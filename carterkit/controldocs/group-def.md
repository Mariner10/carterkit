---
type: group-def
label: Group Definition
icon: square.grid.3x3.square
category: models
---

A visual container that clusters controls into a glass card with its own internal grid.

## Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `"group"` | yes | Discriminator — must be `"group"` |
| `id` | string | yes | Unique identifier |
| `label` | string | no | Header text shown above the group. Set to `null` for no header |
| `position` | [row, col] | yes | Grid cell position within parent |
| `span` | [rows, cols] | no | Grid cells occupied. Default: `[1, 1]` |
| `grid` | [[grid-dimensions]] | yes | Internal grid dimensions for this group's children |
| `children` | [[child-definition]][] | yes | Controls and nested groups |
| `dynamic` | string | no | Event name for [[dynamic-content\|runtime-injected children]] |
| `visible` | [[visibility\|VisibilityCondition]] | no | Show/hide based on another control's value |
| `hideBackground` | bool | no | Remove glass card background (default: `false`) |
| `pulse` | [[pulse]] object | no | Flash a ring around the group when a live event lands |

## Example

```json
{
  "type": "group",
  "id": "bedroom",
  "label": "Bedroom",
  "position": [2, 0],
  "span": [2, 2],
  "grid": { "columns": 2, "rows": 2 },
  "children": [
    { "type": "toggle", "id": "br-light", "position": [0, 0], "label": "Light" },
    { "type": "toggle", "id": "br-fan", "position": [0, 1], "label": "Fan" },
    { "type": "slider", "id": "br-dim", "position": [1, 0], "span": [1, 2], "min": 0, "max": 100, "label": "Brightness" }
  ]
}
```

## Dynamic Groups

When `dynamic` is set, the group's `children` are replaced at runtime by content arriving over MeshSocket. The incoming broadcast must have `msg_type` matching the `dynamic` value and a `children` array.

```json
{
  "type": "group",
  "id": "now-playing",
  "label": "Now Playing",
  "position": [0, 0],
  "span": [3, 4],
  "grid": { "columns": 4, "rows": 3 },
  "children": [],
  "dynamic": "player_state"
}
```

## Pulse

Set `pulse` to make the group flash a ring whenever a server event arrives —
a lightweight way to visualise live data landing in a group without wiring a
control. The ring expands `outward` (e.g. data collected/leaving) or contracts
`inward` (e.g. data arriving/stored), then fades. An optional `filter` narrows
which payloads trigger it, matching keys the same way a [[sync]] filter does.

| Field | Type | Description |
|-------|------|-------------|
| `event` | string | Server event that fires the pulse |
| `color` | hex string | Ring colour (default: green `34C759`) |
| `direction` | `"outward"` \| `"inward"` | Pulse direction (default: `outward`) |
| `filter` | object | Optional payload match, e.g. `{ "device": "thunk-app" }` |

```json
{
  "type": "group",
  "id": "gps-collector",
  "label": "Live GPS",
  "position": [0, 0],
  "grid": { "columns": 2, "rows": 2 },
  "children": [],
  "pulse": { "event": "iCloudListen", "direction": "outward", "color": "34C759" }
}
```

## Theming

A group renders as a glass card whose surface, corner radius, border, and padding come from the active [[theming|theme]] (`surfacePrimary`, `cornerRadius`, `borderColor`, `borderWidth`, `cardPadding`). Set `hideBackground: true` for a transparent group (no card), e.g. a hero row of status lights. Per-control `theme` overrides on the children still apply inside the group.

## Rendering
- Groups render as a glass card (frosted material + subtle border)
- The internal grid is independent of the parent grid
- Groups can be nested (a group's children can include other groups)

## Related
- [[control-def]] — controls within groups
- [[layout-config]] — the top-level structure
- [[grid-dimensions]] — Grid sizing
- [[visibility]] — The `visible` field
- [[dynamic-content]] — Runtime injection
- [[theming]] — Theme & appearance system
