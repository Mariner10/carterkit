---
kind: pattern
id: control-center-switches
family: surface-first
title: Control Center and Action button switches
intents: ["garage door from control center", "action button opens the door", "lock screen shortcut for a switch", "one tap control without opening the app", "toggle from the lock screen corner"]
parts: [{"type": "button", "role": "the verb a user wants without opening the app"}, {"type": "toggle", "role": "a state worth flipping from the lock screen"}, {"type": "statusLight", "role": "current state beside the switch"}]
surfaces: ["app", "controlCenter", "widget"]
theme: darkroom-safelight
rules: ["Control Center takes only toggles and buttons: model every surface verb as a button or toggle first.", "Declare glance.controls[] with kind button/toggle/cycle/step; a slider becomes step or set buttons.", "Keep to three or fewer controls; the user places each one by hand.", "Give toggles on/off labels and icons so the control reads without color."]
exampleRef: beginner/garage-door
---

Some layouts are mostly a handful of switches the user wants within one tap of the lock screen. Build the in-app tab around the same buttons so the surface mirrors it.

## Parts

- **button** (the verb a user wants without opening the app)
- **toggle** (a state worth flipping from the lock screen)
- **statusLight** (current state beside the switch)

## Rules

- Control Center takes only toggles and buttons: model every surface verb as a button or toggle first.
- Declare glance.controls[] with kind button/toggle/cycle/step; a slider becomes step or set buttons.
- Keep to three or fewer controls; the user places each one by hand.
- Give toggles on/off labels and icons so the control reads without color.

## Example

Derived from `beginner/garage-door`. Decodes as a full layout.

```json
{
  "name": "Garage Switches",
  "id": "control-center-switches",
  "version": 1,
  "headerTitle": "Garage Switches",
  "accentColor": "#30D158",
  "tabs": [
    {
      "title": "Garage",
      "icon": "door.garage.closed",
      "grid": {
        "columns": 4,
        "rows": 5
      },
      "children": [
        {
          "type": "statusLight",
          "id": "door",
          "label": "Garage door",
          "defaultValue": "closed",
          "statusColors": {
            "closed": "#30D158",
            "open": "#FF9F0A",
            "moving": "#FF9F0A",
            "default": "#8E8E93"
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "state",
              "filter": {
                "msg_type": "garage_state"
              }
            }
          ],
          "position": [
            0,
            0
          ],
          "span": [
            1,
            4
          ]
        },
        {
          "type": "button",
          "id": "toggle-door",
          "label": "Open / close",
          "icon": "door.garage.open",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "garage_cmd",
              "cmd": "toggle"
            }
          },
          "position": [
            1,
            0
          ],
          "span": [
            2,
            4
          ]
        },
        {
          "type": "toggle",
          "id": "light",
          "label": "Garage light",
          "defaultValue": false,
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "garage_cmd",
              "on": "{{value}}"
            }
          },
          "position": [
            3,
            0
          ],
          "span": [
            1,
            2
          ]
        },
        {
          "type": "button",
          "id": "lock",
          "label": "Lock side door",
          "icon": "lock.fill",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "garage_cmd",
              "cmd": "lock"
            }
          },
          "position": [
            3,
            2
          ],
          "span": [
            1,
            2
          ]
        }
      ]
    }
  ],
  "glance": {
    "title": "Garage",
    "icon": "door.garage.closed",
    "tint": "#30D158",
    "hero": "door",
    "slots": [
      "door"
    ],
    "controls": [
      {
        "id": "door",
        "kind": "button",
        "label": "Garage door",
        "icon": "door.garage.open",
        "control": "toggle-door"
      },
      {
        "id": "light",
        "kind": "toggle",
        "label": "Light",
        "control": "light",
        "on": {
          "label": "Lit",
          "icon": "lightbulb.fill",
          "tint": "#FFD60A"
        },
        "off": {
          "label": "Dark",
          "icon": "lightbulb"
        }
      },
      {
        "id": "lock",
        "kind": "button",
        "label": "Lock",
        "icon": "lock.fill",
        "control": "lock"
      }
    ],
    "widgets": [
      {
        "id": "door",
        "title": "Door",
        "icon": "door.garage.closed",
        "families": [
          "systemSmall",
          "accessoryCircular"
        ],
        "scene": {
          "columns": 2,
          "rows": [
            [
              {
                "tile": "light",
                "control": "door"
              },
              {
                "tile": "button",
                "control": "toggle-door",
                "icon": "door.garage.open"
              }
            ]
          ]
        }
      }
    ]
  }
}
```
