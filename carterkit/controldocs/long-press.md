---
type: long-press
label: Long Press
icon: hand.tap.fill
category: system
fields:
  - name: longPressAction
    type: action
    description: Action fired on long press (no popup)
  - name: longPressGroup
    type: object
    description: Sub-group popup definition
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
