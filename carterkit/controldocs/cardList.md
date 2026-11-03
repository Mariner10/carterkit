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

## Behavior

- A search field filters cards by name or category.
- Cards are grouped under category separators ([[label]] headers): Controls,
  Display, Layout, System, Models.
- Tap a card to open its doc page; see [[control-def]] for the shared fields.
