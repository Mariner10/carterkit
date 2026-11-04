---
kind: pattern
id: tally-counter
family: trackers-and-logs
title: Tally counter
intents: ["count things", "tally counter", "click counter", "keep score of taps", "add one and reset"]
parts: [{"type": "label", "role": "big running count"}, {"type": "button", "role": "+1 / -1 / reset"}, {"type": "stepper", "role": "step size"}]
surfaces: ["app", "controlCenter"]
theme: midnight
rules: ["The server owns the count; buttons only send events and a label listens for the result.", "Put the count first and biggest; the +1 button is the largest tap target below it.", "Make reset a smaller, tinted button away from +1 so it is not hit by accident."]
exampleRef: beginner/tally-counter
---

A counter is one number plus the few verbs that change it. Keep the number as a listening label and send each verb as its own broadcast so any device can add to it.

## Parts

- **label** (big running count)
- **button** (+1 / -1 / reset)
- **stepper** (step size)

## Rules

- The server owns the count; buttons only send events and a label listens for the result.
- Put the count first and biggest; the +1 button is the largest tap target below it.
- Make reset a smaller, tinted button away from +1 so it is not hit by accident.

## Example

Derived from `layout-library/beginner/tally-counter`. Decodes as a full layout.

```json
{
  "name": "Tally Counter",
  "id": "tally-counter",
  "version": 1,
  "headerTitle": "Tally Counter",
  "accentColor": "#30D158",
  "tabs": [
    {
      "title": "Count",
      "icon": "number.circle.fill",
      "grid": {
        "columns": 3,
        "rows": 6
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
            3
          ],
          "text": "Buttons send tally_counter_cmd; your server replies with tally_counter_state to set the number.",
          "icon": "lightbulb",
          "style": "caption",
          "tint": "#AEAEB2"
        },
        {
          "type": "label",
          "id": "count-display",
          "position": [
            1,
            0
          ],
          "span": [
            2,
            3
          ],
          "text": "128",
          "style": "title",
          "align": "center",
          "icon": "person.2.fill",
          "tint": "#30D158",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "tally_counter_state"
              },
              "valuePath": "count"
            }
          ],
          "formatValue": "decimal"
        },
        {
          "type": "button",
          "id": "btn-minus",
          "position": [
            3,
            0
          ],
          "span": [
            1,
            1
          ],
          "label": "-1",
          "icon": "minus",
          "style": "outlined",
          "haptic": "light",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "tally_counter_cmd",
              "cmd": "decrement"
            }
          }
        },
        {
          "type": "button",
          "id": "btn-plus",
          "position": [
            3,
            1
          ],
          "span": [
            1,
            1
          ],
          "label": "+1",
          "icon": "plus",
          "style": "filled",
          "tint": "#30D158",
          "haptic": "medium",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "tally_counter_cmd",
              "cmd": "increment"
            }
          }
        },
        {
          "type": "button",
          "id": "btn-reset",
          "position": [
            3,
            2
          ],
          "span": [
            1,
            1
          ],
          "label": "Reset",
          "icon": "arrow.counterclockwise",
          "style": "tinted",
          "tint": "#FF453A",
          "haptic": "warning",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "tally_counter_cmd",
              "cmd": "reset"
            }
          }
        },
        {
          "type": "divider",
          "id": "step-divider",
          "position": [
            4,
            0
          ],
          "span": [
            1,
            3
          ],
          "label": "Each tap counts",
          "style": "dashed",
          "tint": "#8E8E93"
        },
        {
          "type": "stepper",
          "id": "step-size",
          "position": [
            5,
            0
          ],
          "span": [
            1,
            3
          ],
          "label": "Step size",
          "icon": "arrow.up.arrow.down",
          "min": 1,
          "max": 10,
          "step": 1,
          "defaultValue": 1,
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "tally_counter_step",
              "step": "{{value}}"
            }
          }
        }
      ]
    }
  ]
}
```
