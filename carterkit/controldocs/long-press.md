---
type: long-press
depth: complete
label: Long Press
icon: hand.tap.fill
category: system
fields:
  - name: longPressAction
    tab: action
    type: action
    description: Action fired on long press (no popup)
    summary: What happens when you hold
    does: Runs this action when the control is held down, with no popup.
  - name: longPressGroup
    tab: action
    type: object
    description: Sub-group popup definition
    summary: A pop-up menu on hold
    does: Opens a frosted popup of child controls from the control when it is held down.
---

3D-Touch-style sub-group popups.

## Sub-Group

```json
"longPressGroup": {
  "id": "menu",
  "label": "Quick Actions",
  "grid": { "columns": 3, "rows": 2 },
  "children": [ ... ]
}
```

## Examples

### Quick actions popup
Demonstrates `longPressGroup`: holding the button opens a frosted two-button popup.
```json
{
  "type": "button", "id": "lights", "position": [0, 0], "label": "Lights",
  "longPressGroup": {
    "id": "lights-menu", "label": "Lights",
    "grid": { "columns": 2, "rows": 1 },
    "children": [
      { "type": "button", "id": "all-on", "position": [0, 0], "label": "All on" },
      { "type": "button", "id": "all-off", "position": [1, 0], "label": "All off" }
    ]
  }
}
```

### Hold to fire an action
Demonstrates `longPressAction`: holding runs the action directly, with no popup.
```json
{ "type": "button", "id": "panic", "position": [0, 0], "label": "Alarm", "longPressAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "alarm" } } }
```

### Hold on a toggle
Demonstrates `longPressAction` on a non-button host: the toggle flips on tap and the hold runs a separate action.
```json
{ "type": "toggle", "id": "fan", "position": [0, 0], "label": "Fan", "longPressAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "fan_boost" } } }
```

## Features

- Frosted blur background
- Bouncy spring from source
- Dismiss: tap outside / swipe down
- [[haptics]]: medium on open

## Action Only

```json
"longPressAction": { ... }
```

Fires without popup. See [[actions]].

## Related

- [[group-def]] — the popup is a group
- [[button]] — most common host for long press
