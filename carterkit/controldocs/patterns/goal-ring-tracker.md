---
kind: pattern
id: goal-ring-tracker
family: trackers-and-logs
title: Daily goal ring with quick-log buttons
intents: ["track water intake", "daily goal progress", "log a drink", "habit tracker with a goal", "steps toward a target"]
parts: [{"type": "progressRing", "role": "percent of goal, hero"}, {"type": "button", "role": "one-tap log amounts"}, {"type": "stepper", "role": "edit the goal"}]
surfaces: ["app", "widget", "liveActivity"]
theme: nordic-aurora
rules: ["The ring takes a 0-100 percent from the server; do the arithmetic server-side, not in the layout.", "Offer two or three quick-log amounts as buttons, never a text field.", "Put the goal stepper below a divider so logging stays the main action."]
exampleRef: beginner/water-tracker
---

Progress toward a daily goal reads best as one ring with the common log amounts under it. Logging is a tap, the goal is set rarely.

## Parts

- **progressRing** (percent of goal, hero)
- **button** (one-tap log amounts)
- **stepper** (edit the goal)

## Rules

- The ring takes a 0-100 percent from the server; do the arithmetic server-side, not in the layout.
- Offer two or three quick-log amounts as buttons, never a text field.
- Put the goal stepper below a divider so logging stays the main action.

## Example

Derived from `layout-library/beginner/water-tracker`. Decodes as a full layout.

```json
{
  "name": "Water Tracker",
  "id": "goal-ring-tracker",
  "version": 1,
  "headerTitle": "Water Tracker",
  "accentColor": "#0A84FF",
  "tabs": [
    {
      "title": "Today",
      "icon": "drop.fill",
      "grid": {
        "columns": 4,
        "rows": 7
      },
      "children": [
        {
          "type": "label",
          "id": "about",
          "position": [
            0,
            0
          ],
          "span": [
            1,
            4
          ],
          "text": "Learn: buttons send an action, the ring listens to one sync, and the stepper sends its {{value}}. Your server does the math.",
          "icon": "lightbulb",
          "style": "caption",
          "tint": "#AEAEB2"
        },
        {
          "type": "progressRing",
          "id": "intake-ring",
          "position": [
            1,
            0
          ],
          "span": [
            3,
            4
          ],
          "min": 0,
          "max": 100,
          "defaultValue": 70,
          "progressStyle": "ring",
          "tint": "#0A84FF",
          "label": "of daily goal",
          "icon": "drop.fill",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "water_tracker_state"
              },
              "valuePath": "percent_of_goal"
            }
          ]
        },
        {
          "type": "button",
          "id": "btn-add-250",
          "position": [
            4,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "+250 ml",
          "icon": "cup.and.saucer.fill",
          "style": "tinted",
          "tint": "#64D2FF",
          "haptic": "light",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "water_tracker_log",
              "amount_ml": 250
            }
          }
        },
        {
          "type": "button",
          "id": "btn-add-500",
          "position": [
            4,
            2
          ],
          "span": [
            1,
            2
          ],
          "label": "+500 ml",
          "icon": "waterbottle.fill",
          "style": "filled",
          "tint": "#0A84FF",
          "haptic": "medium",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "water_tracker_log",
              "amount_ml": 500
            }
          }
        },
        {
          "type": "divider",
          "id": "goal-divider",
          "position": [
            5,
            0
          ],
          "span": [
            1,
            4
          ],
          "label": "Daily goal",
          "style": "dashed",
          "tint": "#8E8E93"
        },
        {
          "type": "stepper",
          "id": "goal-stepper",
          "position": [
            6,
            0
          ],
          "span": [
            1,
            4
          ],
          "label": "Goal (ml)",
          "icon": "target",
          "min": 1000,
          "max": 4000,
          "step": 250,
          "defaultValue": 2500,
          "repeatOnHold": true,
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "water_tracker_goal",
              "goal_ml": "{{value}}"
            }
          }
        }
      ]
    }
  ]
}
```
