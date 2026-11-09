---
type: spacer
depth: complete
label: Spacer
icon: square.dashed
category: layout
defaultSpan: [1, 1]
addIntent: organize
pickerCategory: Layout
friendlyName: Space
oneLiner: An empty gap
aliases: [gap, space, padding, blank, empty, filler]
addRank: 2
starterPreset: {}
io:
  - emits: none
  - receives: none
card: {"draws": "when-set", "says": "Empty until you set a Background field; then the gap is a card, a block of colour the Background chip shapes.", "since": "next"}
fields:
---

# Spacer

An invisible layout element that reserves grid cells. Use spacers to create gaps or push other controls into specific positions.

## Type
`"spacer"`

## Relevant Fields
Inherits all [[shared-properties]]. The spacer has no control-specific fields.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `span` | array | `[1, 1]` | Number of grid cells to reserve `[rows, cols]` |

## Examples

### Single-cell gap
Leaves one empty cell at row 1, column 2.
```json
{
  "type": "spacer",
  "id": "gap-1",
  "position": [1, 2]
}
```

### Wide gap
Reserves a block two rows tall and two columns wide so neighbours sit apart.
```json
{
  "type": "spacer",
  "id": "gap-wide",
  "position": [0, 0],
  "span": [2, 2]
}
```

### Push a control to the right
Fills the first columns of a row so the next control starts further along.
```json
{
  "type": "spacer",
  "id": "left-pad",
  "position": [3, 0],
  "span": [1, 2]
}
```

## Related
- [[shared-properties]] — Base fields
