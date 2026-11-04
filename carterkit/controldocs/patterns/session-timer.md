---
kind: pattern
id: session-timer
family: trackers-and-logs
title: Session progress timer
intents: ["pomodoro timer", "focus session", "countdown with progress", "workout interval timer", "timer with start and stop"]
parts: [{"type": "progressRing", "role": "session percent, hero"}, {"type": "button", "role": "start / pause / skip"}, {"type": "stepper", "role": "session length"}]
surfaces: ["app", "liveActivity", "widget"]
theme: kyoto-washi
rules: ["The server ticks and reports percent; the layout never runs its own clock.", "This is a good Live Activity subject: one ring plus one button.", "Keep start and pause adjacent and the same size."]
exampleRef: beginner/pomodoro-lite
---

A timed session is one progress value and a few verbs. Because it is short-lived and glanceable it carries over to a Live Activity.

## Parts

- **progressRing** (session percent, hero)
- **button** (start / pause / skip)
- **stepper** (session length)

## Rules

- The server ticks and reports percent; the layout never runs its own clock.
- This is a good Live Activity subject: one ring plus one button.
- Keep start and pause adjacent and the same size.

## Example

Derived from `layout-library/beginner/pomodoro-lite`. Decodes as a full layout.

```json
{
  "name": "Pomodoro Lite",
  "id": "session-timer",
  "version": 1,
  "headerTitle": "Pomodoro Lite",
  "accentColor": "#FF6B5A",
  "tabs": [
    {
      "title": "Timer",
      "icon": "timer",
      "grid": {
        "columns": 3,
        "rows": 8
      },
      "children": [
        {
          "type": "segmentedControl",
          "id": "session-mode",
          "position": [
            0,
            0
          ],
          "span": [
            1,
            3
          ],
          "options": [
            "focus",
            "break"
          ],
          "optionLabels": [
            "Focus 25m",
            "Break 5m"
          ],
          "optionIcons": [
            "brain.head.profile",
            "cup.and.saucer.fill"
          ],
          "defaultValue": "focus",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "pomodoro_lite_mode",
              "mode": "{{value}}"
            }
          }
        },
        {
          "type": "progressRing",
          "id": "session-progress",
          "position": [
            1,
            0
          ],
          "span": [
            3,
            3
          ],
          "min": 0,
          "max": 100,
          "progressStyle": "ring",
          "tint": "#FF6B5A",
          "label": "Session 2 of 4",
          "icon": "flame.fill",
          "defaultValue": 62,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "pomodoro_lite_tick"
              },
              "valuePath": "percent"
            }
          ]
        },
        {
          "type": "button",
          "id": "btn-start",
          "position": [
            4,
            0
          ],
          "label": "Start",
          "icon": "play.fill",
          "style": "filled",
          "tint": "#34C759",
          "haptic": "success",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "pomodoro_lite_cmd",
              "cmd": "start"
            }
          }
        },
        {
          "type": "button",
          "id": "btn-pause",
          "position": [
            4,
            1
          ],
          "label": "Pause",
          "icon": "pause.fill",
          "style": "tinted",
          "tint": "#FF9F0A",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "pomodoro_lite_cmd",
              "cmd": "pause"
            }
          }
        },
        {
          "type": "button",
          "id": "btn-reset",
          "position": [
            4,
            2
          ],
          "label": "Reset",
          "icon": "arrow.counterclockwise",
          "style": "outlined",
          "tint": "#8E8E93",
          "haptic": "warning",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "pomodoro_lite_cmd",
              "cmd": "reset"
            }
          }
        },
        {
          "type": "divider",
          "id": "about-divider",
          "position": [
            5,
            0
          ],
          "span": [
            1,
            3
          ]
        },
        {
          "type": "label",
          "id": "about",
          "position": [
            6,
            0
          ],
          "span": [
            2,
            3
          ],
          "icon": "lightbulb",
          "style": "caption",
          "text": "How it works: Focus/Break and the three buttons each send one message (pomodoro_lite_mode / pomodoro_lite_cmd). A single sync fills the ring from the percent field of pomodoro_lite_tick."
        }
      ]
    }
  ]
}
```
