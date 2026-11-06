---
type: sortboard
depth: complete
label: Sortboard
icon: rectangle.3.group.fill
category: input
defaultSpan: [10, 4]
addIntent: change
pickerCategory: Inputs
friendlyName: Sort board
oneLiner: Drag cards between columns
aliases: [kanban, drag, reorder, sort, buckets, ranking]
starterPreset: {"label": "Board"}
io:
  - emits: pickup
    when: lift
    title: When you lift a card
    field: sortboardConfig.events.pickup
    type: id
    says: the lifted card's id
    example: "item-1"
    tokens: {"item": "the card's id", "from": "the column it left"}
    hub: {"item": "item-1", "from": "palette"}
    also: The options area has the column id palette
    since: next
  - emits: place
    when: drop
    title: When you drop a card
    field: sortboardConfig.events.place
    type: id
    says: the dropped card's id
    example: "item-1"
    tokens: {"item": "the card's id", "from": "the column it left", "to": "the column it landed in", "index": "its place in that column, counting from 0"}
    hub: {"item": "item-1", "from": "palette", "to": "column-1", "index": 0}
    since: next
  - emits: layout
    when: settle
    title: When the board settles
    field: sortboardConfig.events.layout
    type: json
    says: every column's cards in order, plus the move that just happened
    example: {"zones": {"palette": [], "column-1": ["item-1"]}, "changed": {"item": "item-1", "from": "palette", "to": "column-1", "index": 0}}
    also: Keys you add to this action's payload are sent along with the arrangement
    since: next
  - receives: arrangement
    role: follow
    type: json
    shape: {"zones": {"columnId": ["itemId"]}}
    from: [hub, mqtt, http, store]
    says: which cards sit in which column
    reacts: cards move to the columns it names; ids the board does not know are dropped and cards it leaves out go back to the options area
    example: {"zones": {"column-1": ["item-2"]}}
    since: next
  - sample: {"items": [{"id": "item-1", "label": "Item 1"}, {"id": "item-2", "label": "Item 2"}, {"id": "item-3", "label": "Item 3"}], "zones": [{"id": "column-1", "label": "Column 1"}, {"id": "column-2", "label": "Column 2"}]}
    into: sortboardConfig
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
    does: Shows this text as the header of the board.
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
    description: Rendered height in points (required in flow-mode grids — see Sizing)
    summary: How tall the board is
    does: Sets the board height in points in a flow grid; in a 2-D grid the span sets it instead.
  - name: searchable
    effect: behavior
    edit: part
    depth: hold
    title: Search
    type: bool
    default: false
    description: Show a filter field above the option area
    summary: A search box over the cards
    does: Adds a filter field above the option area so you can find an item by its label.
    group: sortboardConfig
  - name: paletteLabel
    edit: inline
    depth: surface
    title: Palette title
    type: string
    default: Options
    description: Header for the option area
    summary: The name of the card pile
    does: Sets the header over the option area, e.g. Backlog instead of Options.
    group: sortboardConfig
  - name: hidePalette
    effect: behavior
    edit: part
    depth: hold
    title: Palette
    tab: style
    type: bool
    default: false
    description: Hide the option area (server-seeded boards where items start placed)
    summary: Hide the card pile
    does: Removes the option area so only the columns show, for boards whose items all start placed.
    group: sortboardConfig
  - name: columns
    edit: scrub
    depth: surface
    title: Columns
    min: 1
    max: 12
    step: 1
    type: number
    default: 2
    description: How many zone columns to lay out
    summary: How many columns
    does: Lays the zones out in this many columns side by side, 1 to 12.
    group: sortboardConfig
  - name: events
    tab: advanced
    type: object
    description: events
    summary: What happens when you drag
    does: Holds the pickup, place and layout actions that fire as you lift, drop and settle a card.
    group: sortboardConfig
  - name: items
    type: object
    description: items
    summary: The cards you can move
    does: Lists the cards, each with an id, label, icon, tint, optional starting zone and a locked flag.
    group: sortboardConfig
  - name: zones
    type: object
    description: zones
    summary: The columns cards go into
    does: Lists the zones, each with an id, label, tint and optional accepts, capacity and locked limits.
    group: sortboardConfig
  - name: sortboardConfig
    type: object
    description: Grouped config object (see grouped fields)
    summary: The board settings in one bundle
    does: Groups the search, palette, columns, events, items and zones settings; any entry left out uses its default.
---

# Sortboard

A searchable option area plus one or more bound **placement zones** you drag items
between — a kanban board, a triage inbox, a seating chart, a tier list. Each item
lives in exactly one place at a time. On every drop the board fires up to three events
and writes the whole arrangement back through its synced value, so a server can seed
the initial layout or push a new one in the same shape.

Drag is **instant** — touch a chip and it lifts and follows your finger right away
(no long-press wait). A grip glyph marks what's moveable; a **locked** item or zone
shows a lock badge, stays put, and rejects drops. Dropping between chips inserts by
position; dropping into empty space appends.

## Type
`"sortboard"`

## Sizing (read this first)

The board manages its own internal scrolling, so it needs a real height or it
collapses to one row. Two ways, matching the grid's mode:

- **`mode: "flow"` grid** → set **`controlHeight`** (e.g. `560`). This is the simplest
  and what the bundled demo uses.
- **`mode: "grid"`/2-D grid** → give it a real **`span`** rowSpan (e.g. `[9, 4]`);
  `controlHeight` is ignored in 2-D. See [[grid-dimensions]].

## Config (`sortboardConfig`)

| Field | Type | Description |
|-------|------|-------------|
| `items` | array | The option catalog. Each: `{ id, label?, icon?, tint?, zone?, locked? }`. `zone` pre-places an item in that zone id (omitted ⇒ option area); `locked: true` pins it — it shows a lock badge and can't be dragged. |
| `zones` | array | The bins. Each: `{ id, label?, tint?, accepts?, capacity?, locked? }`. `accepts` is a list of item ids the zone allows (omitted ⇒ any); `capacity` caps the count; `locked: true` fixes the whole column (nothing moves in or out). |
| `searchable` | bool | Filter field above the option area. |
| `paletteLabel` | string | Header for the option area (default "Options"). |
| `hidePalette` | bool | Hide the option area entirely — for boards whose items all start placed. |
| `columns` | number | Zone columns (default 2). |
| `events` | object | The `pickup` / `place` / `layout` actions (below). |

`icon` is any SF Symbol name; `tint` is a hex string.

## Events (`sortboardConfig.events`)

Each is a standard [[actions|action definition]]. An author `payload` receives
`{{item}}`, `{{from}}`, `{{to}}`, `{{index}}` token substitution; with no `payload`,
the tokens are sent as a flat object.

| Event | Fires | Default payload |
|-------|-------|-----------------|
| `pickup` | An item is lifted / picked up | `{ "item", "from" }` |
| `place` | An item is dropped into a zone | `{ "item", "from", "to", "index" }` |
| `layout` | The board settles after a drop | `{ "zones": { zoneId: [itemId…] }, "changed": {…} }` |

`from`/`to` are zone ids; the reserved id `"palette"` is the option area.

## Accessibility

Under VoiceOver each chip is its own element: it reads its label and current zone,
and exposes a named **"Move to <zone>"** action per eligible destination (plus
"Return to <palette>") — the full board works without drag.

## Synced value

The control's value is the arrangement JSON:
`{ "zones": { "<zoneId>": ["<itemId>", …] } }`. Point a [[sync]] binding at a value in
this shape to let a server rearrange the board live. Unknown ids are dropped and any
declared item the server omits is parked back in the option area, so nothing silently
disappears.

## Examples

> **Try it now:** the bundled **`sortboard-demo`** layout has both boards below,
> ready to drag. Everything here is copy-paste-ready into a `mode: "flow"` tab.

### 1 — Sprint board (searchable kanban with a WIP limit)
Demonstrates `searchable`, `capacity` on the In Progress column and place and layout events.

```json
{
  "type": "sortboard",
  "id": "sprint-board",
  "position": [0, 0],
  "span": [10, 4],
  "controlHeight": 560,
  "label": "Sprint Board",
  "sortboardConfig": {
    "searchable": true,
    "paletteLabel": "Backlog",
    "columns": 3,
    "items": [
      { "id": "AUTH-14", "label": "OAuth refresh", "icon": "person.badge.key.fill", "tint": "#FF9500" },
      { "id": "UI-88", "label": "Dark mode", "icon": "moon.fill", "tint": "#667eea" },
      { "id": "PERF-5", "label": "Cold start", "icon": "bolt.fill", "tint": "#FF6B6B" },
      { "id": "DOC-9", "label": "API docs", "icon": "book.fill", "tint": "#5AC8FA", "zone": "doing" },
      { "id": "BUG-72", "label": "Crash on launch", "icon": "ant.fill", "tint": "#FF3B30", "zone": "done" }
    ],
    "zones": [
      { "id": "todo", "label": "To Do" },
      { "id": "doing", "label": "In Progress", "capacity": 3, "tint": "#FF9500" },
      { "id": "done", "label": "Done", "tint": "#34C759" }
    ],
    "events": {
      "place": {
        "method": "meshsocket", "mode": "send", "event": "route_msg_noreply",
        "payload": { "target_name": "tracker", "type": "move_ticket",
                     "payload": { "ticket": "{{item}}", "column": "{{to}}", "index": "{{index}}" } }
      },
      "layout": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "board_state" } }
    }
  }
}
```

### 2 — Seating chart (`accepts` + `capacity`)
Demonstrates two tables that each hold at most two guests, with a layout event on every drop.

```json
{
  "type": "sortboard",
  "id": "seating-board",
  "position": [0, 0],
  "span": [10, 4],
  "controlHeight": 560,
  "label": "Table Assignments",
  "sortboardConfig": {
    "paletteLabel": "Guests",
    "columns": 2,
    "items": [
      { "id": "ada", "label": "Ada", "icon": "person.fill" },
      { "id": "linus", "label": "Linus", "icon": "person.fill" },
      { "id": "grace", "label": "Grace", "icon": "person.fill" }
    ],
    "zones": [
      { "id": "table-1", "label": "Table 1", "capacity": 2, "tint": "#667eea" },
      { "id": "table-2", "label": "Table 2", "capacity": 2, "tint": "#FF9500" }
    ],
    "events": {
      "layout": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "seating_state" } }
    }
  }
}
```

### 3 — Server-seeded board (no option area, driven by `sync`)

The board starts empty; the server pushes the arrangement in the synced shape and the
user only rearranges between zones.

```json
{
  "type": "sortboard",
  "id": "duty-roster",
  "position": [0, 0],
  "span": [8, 4],
  "controlHeight": 460,
  "label": "On-Call Roster",
  "sortboardConfig": {
    "hidePalette": true,
    "columns": 2,
    "items": [
      { "id": "sam", "label": "Sam", "icon": "person.fill" },
      { "id": "riley", "label": "Riley", "icon": "person.fill" }
    ],
    "zones": [
      { "id": "primary", "label": "Primary", "capacity": 1, "tint": "#FF3B30" },
      { "id": "backup", "label": "Backup", "tint": "#34C759" }
    ],
    "events": {
      "place": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply",
                 "payload": { "target_name": "pager", "type": "assign",
                              "payload": { "who": "{{item}}", "role": "{{to}}" } } }
    }
  },
  "sync": [
    { "method": "meshsocket", "type": "listen", "event": "broadcast",
      "filter": { "kind": "roster" }, "valuePath": "state" }
  ]
}
```

A `broadcast` whose `state` is `{ "zones": { "primary": ["sam"], "backup": ["riley"] } }`
seats everyone from the server.

## Related
- [[actions]] — Action definition and payload tokens
- [[sync]] — Pushing an arrangement in from a server
- [[grid-dimensions]] — Sizing (`controlHeight` vs. `span`)
- [[shared-properties]] — Base fields
