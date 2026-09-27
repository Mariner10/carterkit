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
    values: [filled, outlined, outline, ghost, tinted, icon-only]
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
  - name: repeatOnHold
    type: bool
    default: false
    description: Keep firing the action while held, using the system repeat behavior (ignored when longPressAction/longPressGroup is set)
  - name: valueMap
    type: object
    description: Synced value → button text ("default" catches the rest)
  - name: iconMap
    type: object
    description: Synced value → SF Symbol name (swaps with the native replace effect)
  - name: colorMap
    type: object
    description: Synced value → hex tint
themeFields:
  - name: cornerRadius
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
  - name: controlPadding
    min: 0
    max: 24
    step: 1
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
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
---

# Button

A tappable action trigger. Fires its [[actions|action]] on press. It stores no value of its own, but a
button with a `sync` can show server state through `valueMap` / `iconMap` / `colorMap` (a stateful key).

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
| `repeatOnHold` | bool | `false` | Hold to keep firing `action`, with the system's accelerating repeat (like [[stepper]]) |
| `valueMap` | object | — | Synced value → button text (`"default"` catches the rest) |
| `iconMap` | object | — | Synced value → SF Symbol name |
| `colorMap` | object | — | Synced value → hex tint |

### Repeat while held
`repeatOnHold: true` makes a held button refire its action at the system's native repeat
cadence (Apple's `buttonRepeatBehavior`, the same one [[stepper]] uses), like holding an
arrow key. Without the field a button fires once per tap. **`repeatOnHold` is ignored when
`longPressAction` or `longPressGroup` is set**: the long-press wrapper owns the touch, so a
hold opens the long-press instead.

### Stateful keys
Give a button a `sync` and the maps, and it shows the server's current state, like a Stream
Deck key. The synced value is matched against map keys the same way as on [[label]]
(`true`/`"Yes"`/`1` all hit `"true"`; `3`/`"3.00"` hit `"3"`; strings match case-insensitively).

- A hit shows the mapped text / symbol / tint. A changed symbol swaps with the native
  `.symbolEffect(.replace)` transition.
- No match, or no value received yet ⇒ the map's `"default"` entry, else the button's own
  `label` / `icon` / `tint`. A button that has never received a value never shows a `"false"`
  entry.
- Tapping still fires `action`; `{{value}}` in the payload is the current synced value.

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

### Hold-to-repeat arrow key
```json
{
  "type": "button",
  "id": "t-up",
  "position": [8, 2],
  "label": "Up",
  "icon": "arrow.up",
  "style": "outlined",
  "size": "compact",
  "repeatOnHold": true,
  "action": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "command", "key": "Up" } }
}
```

### Stateful play/pause key
```json
{
  "type": "button",
  "id": "btn-playpause",
  "position": [0, 2],
  "label": "Play/Pause",
  "icon": "playpause.fill",
  "size": "large",
  "hideLabel": true,
  "tint": "#FF2D55",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "cider_state" }, "valuePath": "playing" }],
  "valueMap": { "true": "Pause", "false": "Play" },
  "iconMap": { "true": "pause.fill", "false": "play.fill" },
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
    "position": [0, 0],
    "span": [2, 2],
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
- [[label]] — Value maps in depth
- [[stepper]] — The other `repeatOnHold` control
