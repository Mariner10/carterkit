---
kind: pattern
id: pet-feeder
family: home-and-devices
title: Pet feeder with portion slider
intents: ["pet feeder", "feed the cat", "portion size slider", "dispense food now", "feeding schedule status"]
parts: [{"type": "slider", "role": "portion size"}, {"type": "button", "role": "dispense now"}, {"type": "statusLight", "role": "hopper level"}]
surfaces: ["app", "widget"]
theme: kyoto-washi
rules: ["Put the portion slider directly above the dispense button it feeds.", "A statusLight reports hopper level so people know before they press.", "One button per action; do not combine feed and schedule."]
exampleRef: beginner/pet-feeder
---

A feeder has a quantity, a trigger and a state. Make the quantity adjustable, the trigger obvious, and the state always visible.

## Parts

- **slider** (portion size)
- **button** (dispense now)
- **statusLight** (hopper level)

## Rules

- Put the portion slider directly above the dispense button it feeds.
- A statusLight reports hopper level so people know before they press.
- One button per action; do not combine feed and schedule.

## Example

Derived from `layout-library/beginner/pet-feeder`. Decodes as a full layout.

```json
{
  "name": "Pet Feeder",
  "headerTitle": "Biscuit's Bowl",
  "id": "pet-feeder",
  "version": 1,
  "accentColor": "#FF9F0A",
  "tabs": [
    {
      "title": "Feeder",
      "icon": "pawprint.fill",
      "grid": {
        "columns": 2,
        "rows": 5
      },
      "children": [
        {
          "type": "label",
          "id": "pet-feeder-about",
          "position": [
            0,
            0
          ],
          "span": [
            1,
            2
          ],
          "icon": "info.circle",
          "style": "caption",
          "text": "Starter: one status message lights the hopper and updates last fed; the slider and button send commands."
        },
        {
          "type": "statusLight",
          "id": "pet-feeder-hopper",
          "position": [
            1,
            0
          ],
          "span": [
            1,
            1
          ],
          "label": "Hopper",
          "style": "badge",
          "defaultValue": "half",
          "statusColors": {
            "full": "#34C759",
            "half": "#FFCC00",
            "low": "#FF9500",
            "empty": "#FF3B30"
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "pet_feeder_status"
              },
              "valuePath": "hopper_level"
            }
          ]
        },
        {
          "type": "label",
          "id": "pet-feeder-last-fed",
          "position": [
            1,
            1
          ],
          "span": [
            1,
            1
          ],
          "icon": "clock",
          "align": "trailing",
          "text": "Last fed 7:30 AM",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "pet_feeder_status"
              },
              "valuePath": "last_fed"
            }
          ]
        },
        {
          "type": "divider",
          "id": "pet-feeder-divider",
          "label": "Feeding",
          "position": [
            2,
            0
          ],
          "span": [
            1,
            2
          ]
        },
        {
          "type": "slider",
          "id": "pet-feeder-portion",
          "position": [
            3,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "Portion (grams)",
          "min": 10,
          "max": 120,
          "step": 5,
          "defaultValue": 45,
          "continuous": false,
          "minIcon": "circle.bottomhalf.filled",
          "maxIcon": "circle.fill",
          "tint": "#FF9F0A",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "pet_feeder_set_portion",
              "grams": "{{value}}"
            }
          }
        },
        {
          "type": "button",
          "id": "pet-feeder-feed-now",
          "position": [
            4,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "Feed Now",
          "icon": "fork.knife",
          "style": "filled",
          "tint": "#FF9F0A",
          "haptic": "success",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "pet_feeder_feed_now",
              "source": "app"
            }
          }
        }
      ]
    }
  ]
}
```
