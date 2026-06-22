---
type: cardList
label: Card List
icon: list.bullet.rectangle.fill
category: display
defaultSpan: [4, 4]
fields:
  - name: hideBackground
    type: bool
    default: "true"
    description: Let the list fill its container without a card background
---

A searchable, scrollable browser that renders the same node data as the [[graph]]
control as a list of cards grouped by category. Each card shows a live example of
the control on the left with its name and summary; tapping a card opens the
control's documentation. Reads the same synced `GraphData` value as `graph` and
uses only the `nodes` (edges are ignored).

## Behavior

- A search field filters cards by name or category.
- Cards are grouped under category separators ([[label]] headers): Controls,
  Display, Layout, System, Models.
- Tap a card to open its doc page; see [[control-def]] for the shared fields.
