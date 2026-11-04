---
type: statusLight
label: Status Light
icon: circle.fill
category: controls
defaultSpan: [1, 1]
addIntent: show
pickerCategory: Readouts
friendlyName: Status dot
oneLiner: "A colored dot: OK, busy, or off"
aliases: [led, indicator, status, health, up down, traffic light]
addRank: 6
depth: complete
starterPreset: {"label": "Status"}
lookPresets: [{"id": "dot","name": "Dot","symbol": "circle.fill","set": {"style": "dot","pulse": null}},{"id": "badge","name": "Badge","symbol": "capsule.fill","set": {"style": "badge","pulse": null}},{"id": "pulsing","name": "Pulsing","symbol": "dot.radiowaves.left.and.right","set": {"style": "dot","pulse": true}}]
fields:
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Text beside the indicator
    summary: The name shown next to the light
    does: Shows this text beside the dot in the label font size (8-24 pt, default 12).
  - name: tint
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    default: "#34C759"
    description: Default indicator color
    summary: The light's color when no state color applies
    does: Colors the dot or badge and its glow in this color until a state with its own color in statusColors is received.
  - name: statusColors
    title: Colors for each status
    tab: style
    type: object
    description: "Map state strings to hex colors: {\"online\": \"#34C759\", \"offline\": \"#FF3B30\"}"
    summary: Which color each status shows
    does: Recolors the light to the color matching the current state text; a state with no entry keeps the tint color.
  - name: size
    edit: look
    depth: surface
    title: Size
    tab: style
    type: enum
    values: [small, default, large]
    default: default
    description: "Indicator size: small (8pt), default (12pt), large (18pt)"
    summary: How big the light is drawn
    does: Sets the dot diameter to 8, 12 or 18 points; the badge style scales with it.
    valueHelp: {"small": "a tiny 8 pt dot for dense rows", "default": "a standard 12 pt dot", "large": "a bold 18 pt dot you can read across the room"}
  - name: style
    edit: look
    depth: surface
    title: Shape
    tab: style
    type: enum
    values: [dot, badge]
    default: dot
    description: "dot (circle) or badge (pill with state text)"
    summary: Plain dot or a pill with words
    does: Switches between a round dot beside the label and a capsule that spells out the current state in text.
    valueHelp: {"dot": "a round colored light with the label beside it", "badge": "a rounded pill that shows the state name in its tint"}
  - name: glow
    edit: scrub
    depth: hold
    under: tint
    title: Glow
    tab: style
    min: 0
    max: 1
    step: 0.05
    type: number
    default: 0.3
    description: Halo strength behind the light, 0 (none) to 1 (full). The badge style tints its pill by the same amount.
    summary: A soft halo around the light
    does: Sets the halo strength from 0 (flat) to 1 (full); in the badge shape it sets how strongly the pill is tinted.
  - name: pulse
    edit: part
    depth: hold
    under: tint
    title: Pulse
    type: bool
    default: false
    description: Pulse animation when active
    summary: Whether the light breathes
    does: Makes the light fade in and out continuously while true; false keeps it steady.
  - name: defaultValue
    title: Starting status
    type: string
    description: Initial state key
    summary: The status shown before any update arrives
    does: Picks which statusColors entry the light shows at first, until a synced value or a live update replaces it.
themeFields:
  - name: cornerRadius
    title: Corner roundness
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
    summary: How round the card corners are
    does: Rounds the card behind the light from square (0) to very round (30 pt).
  - name: controlPadding
    title: Inner spacing
    min: 0
    max: 24
    step: 1
    type: number
    default: 8
    description: Internal padding
    summary: Space between the card edge and the light
    does: Adds 0-24 pt of empty space inside the card around the dot and label.
  - name: surfacePrimary
    title: Card fill
    type: color
    default: "#FFFFFF0F"
    description: Background fill
    summary: The color of the card behind the light
    does: Fills the card in this color; a low alpha shows the layout behind it.
  - name: foregroundColor
    title: Text color
    type: color
    default: "#FFFFFF"
    description: Primary text color
    summary: The color of the label and badge words
    does: Colors the label and the state text in the badge.
  - name: secondaryColor
    title: Soft text color
    type: color
    default: "#FFFFFF99"
    description: Secondary text color
    summary: The color of the quieter text
    does: Colors the dimmer secondary text of the control.
  - name: borderColor
    title: Outline color
    type: color
    default: "#FFFFFF1A"
    description: Border color
    summary: The color of the card outline
    does: Draws the card outline in this color when the border width is above 0.
  - name: borderWidth
    title: Outline thickness
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
    summary: How thick the card outline is
    does: Sets the outline thickness from 0 (none) to 5 pt.
  - name: labelFontSize
    title: Label size
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
    summary: How large the label text is
    does: Sets the label height from 8 to 24 pt.
---

# Status Light

A compact indicator that displays state as a colored dot or badge. The color changes based on synced state values mapped through `statusColors`.

## Type
`"statusLight"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | falls back to `id` | Text beside the indicator |
| `tint` | color | `"#34C759"` | Default indicator color |
| `statusColors` | object | — | Map state strings to hex colors |
| `size` | string | `"default"` | `"small"` (8pt), `"default"` (12pt), `"large"` (18pt) |
| `style` | string | `"dot"` | `"dot"` (circle) or `"badge"` (pill with state text) |
| `glow` | number | `0.3` | Halo strength behind the light, 0–1 (the badge style tints its pill by the same amount) |
| `pulse` | bool | `false` | Pulse animation when active |
| `defaultValue` | string | — | Initial state key |

## Examples

### Plain dot with a fixed color
Shows the simplest light: a small green dot beside a name, with no live data, so it always shows the tint color.
```json
{
  "type": "statusLight",
  "id": "power-light",
  "position": [0, 0],
  "label": "Power",
  "tint": "#34C759"
}
```

### Starting status and state colors
Shows how `defaultValue` picks the first state: the light starts amber as "degraded" until a live value arrives.
```json
{
  "type": "statusLight",
  "id": "link-status",
  "position": [0, 1],
  "label": "Uplink",
  "statusColors": { "online": "#34C759", "degraded": "#FF9500", "offline": "#FF3B30" },
  "defaultValue": "degraded"
}
```

### Badge look
Shows the pill shape: the light becomes a capsule that spells out the current state ("online") in the state color.
```json
{
  "type": "statusLight",
  "id": "db-badge",
  "position": [1, 0],
  "label": "Database",
  "style": "badge",
  "statusColors": { "online": "#34C759", "offline": "#FF3B30" },
  "defaultValue": "online"
}
```

### Pulsing look
Shows the pulsing look: the dot breathes continuously to draw the eye to something that needs watching.
```json
{
  "type": "statusLight",
  "id": "alarm-light",
  "position": [1, 1],
  "label": "Alarm",
  "tint": "#FF3B30",
  "pulse": true
}
```

### Small and large sizes
Shows the size scale: a large 18 pt dot with a strong glow reads from across the room; set `"size": "small"` for an 8 pt dot in dense rows.
```json
{
  "type": "statusLight",
  "id": "big-light",
  "position": [2, 0],
  "label": "Garage door",
  "size": "large",
  "glow": 0.8,
  "tint": "#FF9500"
}
```

### Server status indicator (live data)
Shows a live binding: the server broadcasts `{"msg_type": "server_health", "state": "degraded"}` and `state` picks the `statusColors` key, so the badge turns amber and pulses.
```json
{
  "type": "statusLight",
  "id": "server-status",
  "position": [2, 1],
  "label": "API Server",
  "statusColors": {
    "online": "#34C759",
    "degraded": "#FF9500",
    "offline": "#FF3B30"
  },
  "size": "large",
  "style": "badge",
  "pulse": true,
  "defaultValue": "offline",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "server_health" }, "valuePath": "state" }]
}
```

## Notes
The status light has no tap, long-press or detail action; it only displays state. Every hinted editor field (Title, Color, Size, Shape, Glow, Pulse) changes something visible on screen.

## Related
- [[shared-properties]] — Base fields
- [[sync]] — Real-time data sync
