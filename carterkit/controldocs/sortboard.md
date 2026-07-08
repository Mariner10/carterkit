---
type: sortboard
label: Sortboard
icon: rectangle.3.group.fill
category: input
defaultSpan: [10, 4]
fields:
  - name: label
    type: string
    description: Header label
  - name: controlHeight
    type: number
    default: 560
    description: Rendered height in points (required in flow-mode grids — see Sizing)
  - name: searchable
    type: bool
    default: false
    description: Show a filter field above the option area
    group: sortboardConfig
  - name: paletteLabel
    type: string
    default: Options
    description: Header for the option area
    group: sortboardConfig
  - name: hidePalette
    type: bool
    default: false
    description: Hide the option area (server-seeded boards where items start placed)
    group: sortboardConfig
  - name: columns
    type: number
    default: 2
    description: How many zone columns to lay out
    group: sortboardConfig
  - name: events
    type: object
    description: events
    group: sortboardConfig
  - name: items
    type: object
    description: items
    group: sortboardConfig
  - name: zones
    type: object
    description: zones
    group: sortboardConfig
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
        "method": "meshsocket", "mode": "send", "event": "route_msg",
        "payload": { "target_id": "tracker", "type": "move_ticket",
                     "payload": { "ticket": "{{item}}", "column": "{{to}}", "index": "{{index}}" } }
      },
      "layout": { "method": "meshsocket", "mode": "send", "event": "board_state" }
    }
  }
}
```

### 2 — Seating chart (`accepts` + `capacity`)

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
      "layout": { "method": "meshsocket", "mode": "send", "event": "seating_state" }
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
      "place": { "method": "meshsocket", "mode": "send", "event": "route_msg",
                 "payload": { "target_id": "pager", "type": "assign",
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
