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
  - sample: {"nodes": [{"id": "item-1", "label": "Item 1", "group": "Row 1"}, {"id": "item-2", "label": "Item 2", "group": "Row 1"}, {"id": "item-3", "label": "Item 3", "group": "Row 2"}], "edges": []}
fields:
---

Not for store rows: this control browses documentation nodes. Rows from a store use the list control ([[list]]).

A searchable, scrollable browser that renders the same node data as the [[graph]]
control as a list of cards grouped by category. Each card shows a live example of
the control on the left with its name and summary; tapping a card opens the
control's documentation. Reads the same synced `GraphData` value as `graph` and
uses only the `nodes` (edges are ignored).

## Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `searchPlaceholder` | string | `"Search"` | Placeholder text shown in the search field while it is empty |

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
  "searchPlaceholder": "Search models",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "models" }, "valuePath": "graph" }]
}
```

## Behavior

- A search field filters cards by name or category.
- Cards are grouped under category separators ([[label]] headers): Controls,
  Display, Layout, System, Models.
- Tap a card to open its doc page; see [[control-def]] for the shared fields.
