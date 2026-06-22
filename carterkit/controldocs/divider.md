---
type: divider
label: Divider
icon: minus
category: layout
defaultSpan: [1, 4]
fields:
  - name: label
    type: string
    description: Optional section label centered on the divider
  - name: tint
    type: color
    default: "#FFFFFF"
    description: Line color
  - name: style
    type: enum
    values: [line, dashed]
    default: line
    description: Line style
themeFields:
  - name: labelFontSize
    type: number
    default: 12
    description: Label text size
---

# Divider

A horizontal rule used to visually separate sections within a tab. Can optionally display a centered section label.

## Type
`"divider"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Optional section label centered on the divider |
| `tint` | color | `"#FFFFFF"` | Line color |
| `style` | string | `"line"` | `"line"` or `"dashed"` |

## Examples

### Section divider with label
```json
{
  "type": "divider",
  "id": "section-break",
  "position": [2, 0],
  "span": [1, 4],
  "label": "Advanced Settings",
  "style": "dashed",
  "tint": "#8E8E93"
}
```

## Related
- [[shared-properties]] — Base fields
