---
kind: pattern
id: garage-door-remote
family: home-and-devices
title: Door remote with a state light
intents: ["garage door opener", "open and close a door remotely", "door state indicator", "gate remote", "three button remote"]
parts: [{"type": "statusLight", "role": "live door state"}, {"type": "button", "role": "open, stop, close commands"}, {"type": "label", "role": "last changed time"}]
surfaces: ["app", "widget", "controlCenter"]
theme: midnight
rules: ["One statusLight is the single source of truth for state; buttons only send commands.", "Color the light by state: green safe, amber moving, red open.", "Keep Open and Close at opposite ends so a thumb cannot hit the wrong one."]
exampleRef: beginner/garage-door
---

A remote that shows what the thing is doing before it lets you change it. Commands are fire and forget; the light updates from the device feed.

## Parts

- **statusLight** (live door state)
- **button** (open, stop, close commands)
- **label** (last changed time)

## Rules

- One statusLight is the single source of truth for state; buttons only send commands.
- Color the light by state: green safe, amber moving, red open.
- Keep Open and Close at opposite ends so a thumb cannot hit the wrong one.

## Example

Derived from `layout-library/beginner/garage-door`. Decodes as a full layout.

```json
{
  "name": "Garage Door",
  "headerTitle": "Garage",
  "id": "garage-door-remote",
  "version": 1,
  "accentColor": "#FF9F0A",
  "tabs": [
    {
      "title": "Door",
      "icon": "door.garage.closed",
      "grid": {
        "columns": 3,
        "rows": 6,
        "rowHeight": 56
      },
      "children": [
        {
          "type": "statusLight",
          "id": "door-state",
          "position": [
            0,
            0
          ],
          "span": [
            1,
            3
          ],
          "label": "Main Bay Door",
          "style": "badge",
          "size": "large",
          "defaultValue": "closed",
          "statusColors": {
            "closed": "#34C759",
            "opening": "#FF9F0A",
            "closing": "#FF9F0A",
            "open": "#FF3B30",
            "stopped": "#FFD60A"
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "garage_door_state"
              },
              "valuePath": "state"
            }
          ]
        },
        {
          "type": "label",
          "id": "door-last-changed",
          "position": [
            1,
            0
          ],
          "span": [
            1,
            3
          ],
          "icon": "clock",
          "style": "caption",
          "text": "Changed today, 7:42 AM",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "garage_door_state"
              },
              "valuePath": "changed_at"
            }
          ]
        },
        {
          "type": "button",
          "id": "door-open",
          "position": [
            2,
            0
          ],
          "span": [
            1,
            1
          ],
          "label": "Open",
          "icon": "arrow.up",
          "style": "tinted",
          "tint": "#FF9F0A",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "garage_door_command",
              "command": "open"
            }
          }
        },
        {
          "type": "button",
          "id": "door-stop",
          "position": [
            2,
            1
          ],
          "span": [
            1,
            1
          ],
          "label": "Stop",
          "icon": "stop.fill",
          "style": "filled",
          "tint": "#FF3B30",
          "haptic": "heavy",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "garage_door_command",
              "command": "stop"
            }
          }
        },
        {
          "type": "button",
          "id": "door-close",
          "position": [
            2,
            2
          ],
          "span": [
            1,
            1
          ],
          "label": "Close",
          "icon": "arrow.down",
          "style": "tinted",
          "tint": "#FF9F0A",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "garage_door_command",
              "command": "close"
            }
          }
        },
        {
          "type": "divider",
          "id": "about-divider",
          "position": [
            3,
            0
          ],
          "span": [
            1,
            3
          ],
          "label": "About this layout",
          "tint": "#8E8E93"
        },
        {
          "type": "label",
          "id": "about",
          "position": [
            4,
            0
          ],
          "span": [
            2,
            3
          ],
          "style": "caption",
          "text": "Each button sends a garage_door_command with open, stop, or close. The server answers with one garage_door_state broadcast: the light reads its state field, and the clock line shows changed_at, so send it ready to read (\"Changed today, 7:42 AM\")."
        }
      ]
    }
  ]
}
```
