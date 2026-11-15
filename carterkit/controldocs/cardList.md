---
type: cardList
label: Card List
icon: list.bullet.rectangle.fill
category: display
defaultSpan: [4, 4]
addIntent: show
pickerCategory: Readouts
friendlyName: Cards
oneLiner: A stack of cards
aliases: [cards, feed, tiles, items, results, stack]
starterPreset: {}
card: {"draws": "each", "padding": "10", "says": "There is no outer card: the search box and every row are cards, and the Background chip shapes each of them.", "since": "next"}
depth: complete
io:
  - emits: none
  - receives: nodes
    role: show
    type: json
    shape: {"nodes": [{"id": "text", "label": "text?", "group": "text?", "icon": "symbol?", "color": "hex?"}], "edges": []}
    from: [hub, mqtt, http, store]
    says: "nodes: an id with an optional name, category and icon each (links between nodes are ignored)"
    reacts: the cards are rebuilt under their category headers; the search box keeps filtering them
    example: {"nodes": [{"id": "item-1", "label": "Item 1", "group": "Row 1"}], "edges": []}
    since: next
  - receives: rows
    role: show
    type: json
    shape: [{"id": "text", "title": "text?"}]
    from: [hub, mqtt, http, store]
    says: "rows: card rows for itemTemplate, a store's rows, or hub pages (paging)"
    reacts: one card per row, grouped by categoryField
    since: next
  - sample: {"nodes": [{"id": "item-1", "label": "Item 1", "group": "Row 1"}, {"id": "item-2", "label": "Item 2", "group": "Row 1"}, {"id": "item-3", "label": "Item 3", "group": "Row 2"}], "edges": []}
fields:
  - name: itemTemplate
    chip: Cards
    edit: template
    depth: surface
    since: next
    title: Card template
    type: object
    description: "A group definition ({grid, children}) drawn once per card; {{item.<field>}} in its children is replaced from that row. With grid.scale auto a card whose group is 1x5 holding a 3x15 inner grid draws its children at 1/3. Absent: the docs-browser card."
    summary: Draw each card from controls
    does: "Lays out each card as its own small grid of controls filled in from that row; the inner grid shrinks to fit the card."
  - name: cardColumns
    edit: scrub
    depth: hold
    since: next
    title: Columns
    type: int
    description: "Cards side by side, 1-3 (default: 1 for the docs browser, else as many as the width fits)."
    summary: How many cards sit side by side
    does: Sets one to three columns of cards.
  - name: cardStyle
    edit: look
    depth: hold
    under: itemTemplate
    since: next
    title: Card look
    type: string
    values: [tile, glass, hero]
    valueTitles: {"tile": "Tile", "glass": "Glass", "hero": "Hero"}
    valueSymbols: {"tile": "square", "glass": "square.fill.on.square.fill", "hero": "photo.on.rectangle"}
    default: tile
    description: "The card look: tile (flat rounded tiles), glass (frosted cards) or hero (large preview above the name)."
    summary: The look of each card
    does: Switches every card between the tile, glass and hero looks.
  - name: categoryField
    depth: hold
    since: next
    title: Group by
    type: string
    description: "The row field cards are grouped under, with a header per value (docs browser: group)."
    summary: The field that makes category headers
    does: Puts a header above each run of cards that share this field.
  - name: itemSpacing
    edit: scrub
    depth: hold
    since: next
    title: Card spacing
    type: number
    default: 8
    description: "Points between cards (0-64)."
    summary: Gap between cards
    does: Widens or tightens the space between cards.
  - name: search
    edit: pick-control
    depth: hold
    since: next
    title: Search source
    type: string
    values: [builtin, none]
    default: builtin
    description: "builtin: the list's own search box (default for old layouts); none: no filtering; or the id of a search box control that filters this list."
    summary: Which search box filters the cards
    does: Points the cards at their own box, at none, or at a separate search box control.
  - name: placeholder
    edit: inline
    depth: surface
    since: next
    title: Search hint
    type: string
    default: Search
    description: "Placeholder text shown in the search field while it is empty (default: Search)."
    summary: The hint inside the search box
    does: Replaces the grey word shown in the search box until you type, e.g. Search models.
colorSlots:
  - slot: icon
    default: primary
    since: next
    summary: The color of the card symbols
    does: Colors the symbol a card shows when it has no live example; until the layout picks a color it follows the primary role.
  - slot: text
    default: neutral
    since: next
    summary: The color of the card names
    does: Colors each card's name and the faint tile behind its symbol; until set it follows the neutral role, the text color. Descriptions and category names keep the softer text color.
---

Cards run on the shared list engine ([[list]]); Table and Cards are two entries over one engine. Feed them `{nodes}` (the docs browser adapter), static rows, a store, or hub pages (`paging`, `@hub.pages`).

A searchable, scrollable browser that renders the same node data as the [[graph]]
control as a list of cards grouped by category. Each card shows a live example of
the control on the left with its name and summary; tapping a card opens the
control's documentation. Reads the same synced `GraphData` value as `graph` and
uses only the `nodes` (edges are ignored).

## Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `placeholder` | string | `"Search"` | Placeholder text shown in the search field while it is empty |

## Examples

### Control browser pane
A full-size browser fed by a catalog broadcast.

```json
{
  "type": "cardList",
  "id": "control-browser",
  "position": [0, 0],
  "span": [6, 4],
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "catalog" }, "valuePath": "graph" }]
}
```

The server feeds it with a `broadcast_request` whose payload is `{"msg_type": "catalog", "graph": {…}}`.

### Custom search hint
A compact card list with its own placeholder text.

```json
{
  "type": "cardList",
  "id": "doc-browser",
  "position": [0, 0],
  "span": [4, 4],
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "catalog" }, "valuePath": "graph" }]
}
```

### Side panel of cards
A narrow tall list beside other controls.

```json
{
  "type": "cardList",
  "id": "side-cards",
  "position": [6, 0],
  "span": [3, 6],
  "placeholder": "Search models",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "models" }, "valuePath": "graph" }]
}
```

### Template cards from a store
Each card is an `itemTemplate` group; with `grid.scale` auto a 3x15 inner grid draws at 1/3 inside a 1x5 card.

```json
{
  "type": "cardList",
  "id": "models",
  "position": [0, 0],
  "span": [6, 6],
  "cardColumns": 2,
  "cardStyle": "glass",
  "categoryField": "group",
  "itemSpacing": 10,
  "itemTemplate": {
    "grid": {"scale": "auto"},
    "children": [
      {"type": "label", "position": [0, 0], "span": [3, 8], "text": "{{item.title}}"},
      {"type": "label", "position": [0, 8], "span": [3, 7], "text": "{{item.subtitle}}"}
    ]
  }
}
```

## Behavior

- A search field filters cards by name or category; it is the shared search source (`search: builtin`), or a search box's id.
- Cards are grouped under category separators ([[label]] headers): Controls,
  Display, Layout, System, Models.
- Tap a card to open its doc page; see [[control-def]] for the shared fields.
