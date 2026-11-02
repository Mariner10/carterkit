---
type: divider
label: Divider
icon: minus
category: layout
defaultSpan: [1, 4]
addIntent: organize
pickerCategory: Layout
friendlyName: Divider
oneLiner: A line between sections
aliases: [line, separator, rule, break, split, hr]
addRank: 1
starterPreset: {"label": "Section"}
fields:
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Optional section label centered on the divider
  - name: tint
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    default: "#FFFFFF"
    description: Line color
  - name: style
    edit: look
    depth: surface
    title: Line style
    tab: style
    type: enum
    values: [line, dashed]
    default: line
    description: Line style
  - name: lineThickness
    edit: scrub
    depth: hold
    under: style
    unit: pt
    title: Thickness
    tab: style
    type: number
    min: 0.5
    max: 8
    step: 0.5
    default: 1
    description: Line thickness in points
themeFields:
  - name: labelFontSize
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
  - name: foregroundColor
    title: Text color
    type: color
    default: #FFFFFF
    description: Primary text color
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
| `lineThickness` | number | `1` | Line thickness in points (0.5–8) |

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
