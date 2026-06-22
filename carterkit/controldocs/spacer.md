---
type: spacer
label: Spacer
icon: square.dashed
category: layout
defaultSpan: [1, 1]
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
```json
{
  "type": "spacer",
  "id": "gap-1",
  "position": [1, 2]
}
```

## Related
- [[shared-properties]] — Base fields
