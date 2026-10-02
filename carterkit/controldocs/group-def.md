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
| `id` | string | yes | Unique identifier (among the layout's controls and groups; see [[layout-config#Identity]]) |
| `name` | string | no | Readable name the editor shows for this group. Never used for identity |
| `label` | string | no | Header text shown above the group. Set to `null` for no header |
| `position` | [row, col] | yes | Grid cell position within parent |
| `span` | [rows, cols] | no | Grid cells occupied. Default: `[1, 1]` |
| `landscape` | `{position, span}` or `{hidden: true}` | no | This group's cell when an iPhone is on its side; ignored in portrait. See [[grid-dimensions#Landscape and iPad]] |
| `regular` | `{position, span}` or `{hidden: true}` | no | This group's cell on an iPad-width page |
| `grid` | [[grid-dimensions]] | yes | Internal grid dimensions for this group's children |
| `children` | [[child-definition]][] | yes | Controls and nested groups |
| `dynamic` | string | no | Event name for [[dynamic-content\|runtime-injected children]] |
| `visible` | [[visibility\|VisibilityCondition]] | no | Show/hide based on another control's value |
| `enabled` | [[visibility\|VisibilityCondition]] | no | Enable/disable every child; false dims the group and ignores touches |
| `form` | [[form]] object | no | Make the group a form: its inputs write a draft, validated, written once by `submit` |
| `hideBackground` | bool | no | Remove glass card background (default: `false`) |
| `pulse` | [[pulse]] object | no | Flash a ring around the group when a live event lands |
| `theme` | object | no | Theme overrides for the group's label, card and every child (same keys as a control's `theme`; `$name` palette refs work). A child's own `theme` and `tint` still win. See [[theming#Cascade]] |
| `extensions` | object | no | Tool data keyed by reverse-DNS name; preserved, never interpreted, 64 KB cap. See [[document-contract#Extensions]] |

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

### Chunked decks (`rev`, `part`, `parts`)

The relay drops any websocket frame over its read limit (256 KiB on Connect+,
and an E2EE room seals and base64-encodes the frame, so it grows by about a
third on the wire). A server whose deck may come near that size splits it into
several broadcasts. Each one carries the same `msg_type` plus three extra keys:

| Key | Type | Rule |
|-----|------|------|
| `rev` | string | Identifies one deck. Every part of the deck carries the same `rev`; use a new `rev` (a counter, a timestamp, a content hash) for each new deck. At most 256 UTF-8 bytes. |
| `parts` | integer | Total number of parts, `2`...`64`. A frame with no `parts`, or with `parts` of `1` or less, is a normal single-frame deck. |
| `part` | integer | This frame's index. **Number parts `1`...`parts` (1-based).** CAR-TER 1.3 and later also accept 0-based `0`...`parts-1`. |
| `children` | array | This part's slice of the deck: whole child objects. Split between children, never inside one. |

```json
{ "msg_type": "player_state", "rev": "42", "part": 1, "parts": 2, "children": [ { "type": "label", "id": "dyn-title", "position": [0, 0], "span": [1, 4], "text": "Song" } ] }
{ "msg_type": "player_state", "rev": "42", "part": 2, "parts": 2, "children": [ { "type": "slider", "id": "dyn-volume", "position": [1, 0], "span": [1, 4], "min": 0, "max": 100 } ] }
```

How the app puts a deck back together:

- It buffers parts per group. Once it holds `parts` distinct `part` indices for
  one `rev`, it concatenates the `children` slices in ascending `part` order and
  applies the result as one deck. Parts can arrive in any order.
- A frame with a different `rev` or `parts` than the buffered deck throws away
  the unfinished deck and starts a new one. Only one deck is in flight per group.
  The newest deck wins, and an abandoned one never renders half-built.
- The app drops a frame, without logging it, if `parts` is not a whole number
  from `2` to `64`, if `part` is missing or outside `0`...`parts`, if `rev` is
  missing, not a string or longer than 256 bytes, or if `children` is not an array.
- Use one numbering convention for the whole deck. If a sender mixes them (say,
  `0`, `1` and `2` with `parts: 2`), the deck completes as soon as it has two
  distinct indices, so it can apply only part of the deck.
- The app keeps only `msg_type` and `children` from the reassembled deck. Any
  other top-level keys on the parts are ignored.
- Use 1-based numbering. Before 1.3, the app reassembled `1`...`parts` only:
  1.2.5 and 1.2.6 drop part `0`, so a 0-based deck never finishes, and older
  builds apply the deck without part `0`'s children.
- Chunking applies to dynamic **groups** only. A [[dynamic-content|dynamic tab]]
  always arrives as one frame.

`carterkit` builds these frames for you: `carterkit.dynamic.chunk_deck(event,
children)` returns the frame list (1-based), and `Hub.fill(group, children,
max_bytes=...)` sends a deck in parts when it is larger than `max_bytes`.

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
  "pulse": { "event": "broadcast", "filter": { "msg_type": "iCloudListen" }, "direction": "outward", "color": "34C759" }
}
```

## Theming

A group renders as a glass card whose surface, corner radius, border, and padding come from the active [[theming|theme]] (`surfacePrimary`, `cornerRadius`, `borderColor`, `borderWidth`, `cardPadding`). Set `hideBackground: true` for a transparent group (no card), e.g. a hero row of status lights. A group's own `theme` overrides those keys for the card, its label and everything inside it, e.g. `"theme": {"accentColor": "$leaf", "surfacePrimary": "#1B2A1F"}`; per-control `theme` overrides on the children still apply on top. See [[theming#Cascade]].

## Rendering
- Groups render as a glass card (frosted material + subtle border)
- The internal grid is independent of the parent grid
- Groups can be nested (a group's children can include other groups)

## Related
- [[control-def]] — controls within groups
- [[layout-config]] — the top-level structure
- [[grid-dimensions]] — Grid sizing
- [[visibility]] — The `visible` and `enabled` fields
- [[form]] — Draft, validate, submit
- [[dynamic-content]] — Runtime injection
- [[theming]] — Theme & appearance system
