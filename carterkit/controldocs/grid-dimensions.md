---
type: grid-dimensions
label: Grid Dimensions
icon: square.grid.3x3
category: models
fields:
  - name: columns
    type: number
    description: Number of columns the grid is divided into (required)
  - name: rows
    type: number
    description: Number of rows the grid is divided into (required)
  - name: mode
    type: string
    description: '"grid" (2-D, default) or "flow" (legacy row-banded)'
  - name: rowHeight
    type: number
    description: Points per row-unit in 2-D mode (default 56)
---

Every tab and every [[group-def|group]] lays its children out on a **grid** of
`columns` × `rows`. A child declares where it sits with `position: [row, col]`
and how many cells it covers with `span: [rowSpan, colSpan]` (see [[control-def]]).

```json
"grid": { "columns": 4, "rows": 6 }
```

## Modes

| `mode` | Layout | Best for |
|--------|--------|----------|
| `"grid"` *(default)* | **True 2-D.** Each child occupies a real `row × col` rectangle. Columns divide the width evenly; rows are a fixed `rowHeight` unit. A child can span **both** axes, so a tall control can sit **beside** two stacked shorter ones (masonry / L-shapes). | Dashboards and mixed screens — gauges, rings, inputs, maps together. |
| `"flow"` | **Legacy row-banded.** Children are grouped by their row index into horizontal bands; `colSpan` sets proportional width but heights are natural (or `controlHeight`). `rowSpan` is ignored. | Full-page content (a single `map` / `chat` / `cardList` filling the tab) and pure forms where natural heights read best. |

`mode` is optional — omit it for the default 2-D grid. Set `"flow"` to opt a tab
or group out.

```json
"grid": { "columns": 4, "rows": 8, "mode": "flow" }
```

## How spans map to size

| | 2-D (`"grid"`) | `"flow"` |
|--|----------------|----------|
| **`colSpan`** (width) | `colSpan / columns` of the row width | `colSpan / columns` of the row width |
| **`rowSpan`** (height) | `rowSpan × rowHeight` points | ignored — height is natural / `controlHeight` |

So in 2-D a 1×1 cell is genuinely small, and you make a control bigger by spanning
more cells. Visual controls scale all of their internals (stroke, glyph, font) to
the cell they're given — a small ring is tight and legible, a large ring is bold.

## `rowHeight`

The height of one row-unit, in points (2-D mode only; default **56**). One unit is
a comfortable input row, so:

- inputs (`slider`, `toggle`, `segmentedControl`, …) sit in **1 row**,
- a square control (`progressRing`, full `gauge`) wants **~3 rows** to read square,
- tall content (`map`, `list`, `graph`, `image`) spans **as many rows as you give it**.

```json
"grid": { "columns": 4, "rows": 10, "rowHeight": 64 }
```

## Sizing a control

You usually don't set a height at all — in 2-D the cell (`rowSpan × rowHeight`)
*is* the height, and in flow shaped controls auto-size to their natural aspect.
`controlHeight` (see [[control-def]]) is an **override** for the rare case you want
an exact point height regardless of the grid.

## Example — a 2-D dashboard with an L-shape

```json
{
  "grid": { "columns": 4, "rows": 5 },
  "children": [
    { "type": "progressRing", "id": "cpu", "position": [0, 0], "span": [3, 2], "label": "CPU" },
    { "type": "gauge",        "id": "mem", "position": [0, 2], "span": [2, 2], "label": "Memory" },
    { "type": "statusLight",  "id": "net", "position": [2, 2], "span": [1, 2], "label": "Uplink" }
  ]
}
```

The CPU ring is a tall 2×2-plus block on the left; Memory and the Uplink light
stack to its right — placement that the flow renderer can't express.

## Related
- [[control-def]] — `position`, `span`, `controlHeight`, `hideValue`, `hideBackground`
- [[group-def]] — a group has its own grid (and its own `mode`)
- [[layout-config]] — the top-level structure
