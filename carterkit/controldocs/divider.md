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
depth: complete
starterPreset: {"label": "Section"}
io:
  - emits: none
  - receives: none
fields:
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Optional section label centered on the divider
    summary: A name shown in the middle of the line
    does: Shows this text centered on the divider with a line on each side, in the label font size and the line color; empty gives a plain line.
  - name: tint
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    default: "#FFFFFF"
    description: Line color
    summary: The line color
    does: Colors the line and the label text; if unset it is the text color at a faint 20% strength.
  - name: style
    edit: look
    depth: surface
    title: Line style
    tab: style
    type: enum
    values: [line, dashed]
    default: line
    description: Line style
    summary: Solid or dashed line
    does: Switches the line between solid and dashed.
    valueHelp: {"line": "one unbroken solid line", "dashed": "a row of short dashes with small gaps"}
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
    summary: How thick the line is
    does: Sets the line's height from 0.5 to 8 pt (default 1).
themeFields:
  - use: labelFontSize
    summary: How big the label is
    does: Sets the section label's text size from 8 to 24 pt (default 12).
  - use: foregroundColor
    does: Sets the base text color; the line and label fall back to a faint version of it when no color is set.
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
A dashed gray line with a centered title above the advanced settings.
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

### Plain rule
A thin default line between two groups, no text.
```json
{
  "type": "divider",
  "id": "plain-rule",
  "position": [1, 0],
  "span": [1, 4]
}
```

### Bold colored break
A thick accent line to mark a major change of topic.
```json
{
  "type": "divider",
  "id": "major-break",
  "position": [4, 0],
  "span": [1, 4],
  "style": "line",
  "lineThickness": 3,
  "tint": "#667eea"
}
```

## Related
- [[shared-properties]] — Base fields
