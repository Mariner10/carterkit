---
kind: pattern
id: ceiling-fan-remote
family: home-and-devices
title: Fan remote with speed steps
intents: ["ceiling fan remote", "fan speed low medium high", "bedroom fan control", "power and speed selector", "fan with a timer"]
parts: [{"type": "toggle", "role": "power"}, {"type": "segmentedControl", "role": "speed steps"}, {"type": "stepper", "role": "timer minutes"}]
surfaces: ["app", "controlCenter"]
theme: paper-and-ink
rules: ["Power is a toggle so on/off state is visible; speed steps are a segmentedControl.", "Offer three to four speeds; more than that belongs on a slider.", "A stepper handles bounded counts like timer minutes."]
exampleRef: beginner/fan-remote
---

Appliance remotes are an on/off switch plus a small set of steps. Use controls that show their current value.

## Parts

- **toggle** (power)
- **segmentedControl** (speed steps)
- **stepper** (timer minutes)

## Rules

- Power is a toggle so on/off state is visible; speed steps are a segmentedControl.
- Offer three to four speeds; more than that belongs on a slider.
- A stepper handles bounded counts like timer minutes.

## Example

Derived from `layout-library/beginner/fan-remote`. Decodes as a full layout.

```json
{
  "name": "Ceiling Fan Remote",
  "headerTitle": "Bedroom Fan",
  "id": "ceiling-fan-remote",
  "version": 1,
  "accentColor": "#30B0C7",
  "tabs": [
    {
      "title": "Fan",
      "icon": "fan.ceiling.fill",
      "grid": {
        "columns": 2,
        "rows": 6
      },
      "children": [
        {
          "type": "label",
          "id": "fan-about",
          "position": [
            0,
            0
          ],
          "span": [
            2,
            2
          ],
          "style": "caption",
          "text": "Learn by example: each toggle, stepper, and segment sends one fan_remote_* broadcast, with {{value}} filled in from the control. The All Off button sends a fixed message. The status light is the only control that listens back (a sync on fan_remote_state).",
          "align": "leading"
        },
        {
          "type": "toggle",
          "id": "fan-power",
          "position": [
            2,
            0
          ],
          "span": [
            1,
            1
          ],
          "label": "Fan Power",
          "icon": "power",
          "defaultValue": true,
          "tint": "#30B0C7",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "fan_remote_power",
              "on": "{{value}}"
            }
          }
        },
        {
          "type": "statusLight",
          "id": "fan-state",
          "position": [
            2,
            1
          ],
          "span": [
            1,
            1
          ],
          "label": "Fan Reports",
          "style": "badge",
          "defaultValue": "spinning",
          "statusColors": {
            "spinning": "#34C759",
            "stopped": "#8E8E93",
            "fault": "#FF3B30"
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "fan_remote_state"
              },
              "valuePath": "status"
            }
          ]
        },
        {
          "type": "stepper",
          "id": "fan-speed",
          "position": [
            3,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "Speed",
          "icon": "wind",
          "min": 0,
          "max": 5,
          "step": 1,
          "defaultValue": 3,
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "fan_remote_speed",
              "level": "{{value}}"
            }
          }
        },
        {
          "type": "segmentedControl",
          "id": "fan-direction",
          "position": [
            4,
            0
          ],
          "span": [
            1,
            2
          ],
          "options": [
            "forward",
            "reverse"
          ],
          "optionLabels": [
            "Summer",
            "Winter"
          ],
          "optionIcons": [
            "sun.max.fill",
            "snowflake"
          ],
          "defaultValue": "forward",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "fan_remote_direction",
              "direction": "{{value}}"
            }
          }
        },
        {
          "type": "toggle",
          "id": "fan-light",
          "position": [
            5,
            0
          ],
          "span": [
            1,
            1
          ],
          "label": "Fan Light",
          "icon": "lightbulb.fill",
          "defaultValue": false,
          "tint": "#FFD60A",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "fan_remote_light",
              "on": "{{value}}"
            }
          }
        },
        {
          "type": "button",
          "id": "fan-all-off",
          "position": [
            5,
            1
          ],
          "span": [
            1,
            1
          ],
          "label": "All Off",
          "icon": "moon.zzz.fill",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "fan_remote_all_off"
            }
          }
        }
      ]
    }
  ]
}
```
