---
type: colorPicker
depth: complete
label: Color Picker
icon: paintpalette.fill
category: controls
defaultSpan: [1, 1]
addIntent: change
pickerCategory: Inputs
friendlyName: Color
oneLiner: Pick a color
aliases: [colour, palette, swatch, hue, rgb, paint]
starterPreset: {"label": "Color"}
io:
  - emits: value
    when: change
    title: When you choose a color
    type: color
    says: the color you chose, as a hex code
    example: "#7F8CFF"
    also: The system color sheet sends as you drag through colors, so one visit can send several times; there is no transparency
    since: next
  - receives: value
    role: follow
    type: color
    from: [hub, mqtt, http, store, default]
    says: a color to show on the swatch, as a hex code
    reacts: the swatch changes to it without sending anything; your next choice replaces it
    example: "#7F8CFF"
    since: next
  - sample: "#7F8CFF"
    next: "#7FFF8C"
fields:
  - name: label
    edit: inline
    depth: surface
    title: Label
    type: string
    description: Display label
    summary: The name shown above
    does: Shows this text above the color swatch.
  - name: defaultValue
    edit: color
    depth: surface
    type: string
    description: Initial hex color
    summary: The starting color
    does: Sets the color shown before anyone picks one, as a hex value like #F4B860.
  - use: confirm
themeFields:
  - name: cornerRadius
    edit: scrub
    depth: hold
    under: defaultValue
    unit: pt
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
    summary: How round the corners are
    does: Rounds the control's corners, from 0 (square) to 30 pt.
  - use: controlPadding
    summary: Space inside the edges
    does: Sets the gap between the control's edge and its content, 0 to 24 pt.
  - use: surfacePrimary
    summary: The background color
    does: Fills the control's background with this color.
  - use: foregroundColor
    does: Colors the main text on the control.
  - use: secondaryColor
    summary: The quieter text color
    does: Colors the smaller, secondary text.
  - name: borderColor
    edit: color
    depth: hold
    under: defaultValue
    type: color
    default: #FFFFFF1A
    description: Border color
    summary: The outline color
    does: Colors the outline drawn around the control.
  - name: borderWidth
    edit: scrub
    depth: hold
    under: defaultValue
    unit: pt
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
    summary: How thick the outline is
    does: Sets the outline thickness from 0 (none) to 5 pt.
  - use: labelFontSize
    summary: Size of the title text
    does: Sets the title text size from 8 to 24 pt.
---

# Color Picker

A color selection control. Stores a `.string` value (hex color like `"#FF6B6B"`).

## Type
`"colorPicker"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Display label |
| `defaultValue` | string | — | Initial hex color (e.g., `"#F4B860"`) |

## Examples

### Room light color

```json
{
  "type": "colorPicker",
  "id": "lr-color",
  "position": [1, 3],
  "defaultValue": "#F4B860",
  "label": "Color",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "hue-bridge", "type": "color", "payload": { "room": "living", "hex": "{{value}}" } } }
}
```

### Accent color with an undo note
Tap to pick a color, with a short Undo pill after each change.
```json
{
  "type": "colorPicker",
  "id": "accent-color",
  "position": [0, 0],
  "label": "Accent",
  "defaultValue": "#667EEA",
  "confirm": true
}
```

### Labelled swatch with a custom look
A squarer swatch with a thicker outline and larger label.
```json
{
  "type": "colorPicker",
  "id": "strip-color",
  "position": [0, 1],
  "label": "Strip",
  "defaultValue": "#FF6B6B",
  "cornerRadius": 4,
  "borderWidth": 2,
  "labelFontSize": 16
}
```

## Behavior
- Shows the iOS system color picker on tap
- Value stored and transmitted as `#RRGGBB` hex string
- `{{value}}` in actions is the hex string

## Related
- [[shared-properties]] — Base fields
- [[actions]] — `{{value}}` substitution
