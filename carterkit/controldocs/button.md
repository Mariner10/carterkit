---
type: button
label: Button
icon: hand.tap.fill
category: controls
defaultSpan: [1, 1]
fields:
  - name: label
    type: string
    default: "Button"
    description: Button text
  - name: icon
    type: string
    description: SF Symbol shown before label
  - name: style
    type: enum
    values: [filled, outlined, ghost, tinted, icon-only]
    default: filled
    description: Visual style variant ("outline" and "outlined" are both accepted)
  - name: size
    type: enum
    values: [compact, default, large]
    default: default
    description: Size variant
  - name: tint
    type: color
    default: "#667eea"
    description: Accent color
  - name: hideLabel
    type: bool
    default: false
    description: Show icon only
  - name: haptic
    type: enum
    values: [light, medium, heavy, success, warning, error, selection]
    default: medium
    description: Haptic feedback on press
themeFields:
  - name: cornerRadius
    type: number
    default: 12
    description: Control corner radius
  - name: controlPadding
    type: number
    default: 8
    description: Internal padding
  - name: accentColor
    type: color
    default: #667eea
    description: Accent/tint color
  - name: foregroundColor
    type: color
    default: #FFFFFF
    description: Primary text color
  - name: borderColor
    type: color
    default: #FFFFFF1A
    description: Border color
  - name: borderWidth
    type: number
    default: 1
    description: Border width
---

# Button

A tappable action trigger. Fires its [[actions|action]] on press. Does not store a value.

## Type
`"button"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | falls back to `id` | Button text |
| `icon` | string | — | SF Symbol shown before label |
| `style` | string | `"filled"` | `"filled"`, `"outlined"`, `"ghost"`, `"tinted"`, `"icon-only"` (`"outline"` also accepted) |
| `size` | string | `"default"` | `"compact"`, `"default"`, `"large"` |
| `tint` | string | `"#667eea"` | Accent color |
| `hideLabel` | bool | `false` | Show icon only |
| `action` | [[actions\|ActionDefinition]] | — | Command fired on tap |
| `haptic` | string | `"medium"` | Default haptic on press |

## Examples

### Simple button
```json
{
  "type": "button",
  "id": "all-off",
  "position": [0, 3],
  "label": "All Off",
  "action": { "method": "meshsocket", "mode": "request", "event": "route_msg", "payload": { "target_id": "hue-bridge", "type": "scene", "payload": { "name": "all_off" } } }
}
```

### Icon-only ghost button (large, for transport controls)
```json
{
  "type": "button",
  "id": "btn-play",
  "position": [0, 2],
  "label": "Play",
  "icon": "playpause.fill",
  "style": "ghost",
  "size": "large",
  "hideLabel": true,
  "tint": "#FF2D55",
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "player", "type": "command", "payload": { "command": "playpause" } } }
}
```

### Button with long-press detail popup
```json
{
  "type": "button",
  "id": "scene-movie",
  "position": [0, 0],
  "label": "Movie",
  "icon": "film",
  "style": "tinted",
  "action": { "method": "meshsocket", "mode": "request", "event": "route_msg", "payload": { "target_id": "home-hub", "type": "macro", "payload": { "name": "movie_mode" } } },
  "longPressGroup": {
    "id": "movie-detail",
    "label": "Movie Mode Settings",
    "grid": { "columns": 2, "rows": 2 },
    "children": [
      { "type": "slider", "id": "movie-brightness", "position": [0, 0], "span": [1, 2], "min": 0, "max": 100, "label": "Brightness" },
      { "type": "toggle", "id": "movie-auto-screen", "position": [1, 0], "label": "Auto Screen" },
      { "type": "toggle", "id": "movie-auto-audio", "position": [1, 1], "label": "Auto Audio" }
    ]
  }
}
```

## Related
- [[shared-properties]] — Base fields
- [[style-properties#Button Styles]] — Style variants
- [[actions]] — Action definition
- [[long-press]] — Long-press behavior
- [[haptics]] — Haptic feedback
