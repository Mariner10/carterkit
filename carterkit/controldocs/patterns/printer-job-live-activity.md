---
kind: pattern
id: printer-job-live-activity
family: surface-first
title: Long job on the Dynamic Island
intents: ["3d printer progress on lock screen", "dynamic island for a long job", "live activity for a print", "watch a job from the lock screen", "island shows progress and eta"]
parts: [{"type": "progressRing", "role": "job percent, island hero"}, {"type": "gauge", "role": "nozzle and bed temperature"}, {"type": "statusLight", "role": "job state, island minimal"}, {"type": "button", "role": "pause"}]
surfaces: ["app", "liveActivity", "lockScreen"]
theme: glass-cockpit
rules: ["Pick one hero (the progress ring) for compactTrailing; the minimal slot gets a statusLight so it still reads when another activity shares the island.", "Keep expanded.bottom to two rows: the island clips anything taller.", "Bind a timer tile to a unix-seconds ETA so it ticks with no updates; use tier fresh unless the job needs second-by-second data.", "A slider cannot go on the island; offer a button or step tile instead."]
exampleRef: intermediate/3d-printer
---

A job that runs for hours is read from the lock screen, not the app. Design the island first (one ring, one dot, two rows) and let the in-app tab carry the detail.

## Parts

- **progressRing** (job percent, island hero)
- **gauge** (nozzle and bed temperature)
- **statusLight** (job state, island minimal)
- **button** (pause)

## Rules

- Pick one hero (the progress ring) for compactTrailing; the minimal slot gets a statusLight so it still reads when another activity shares the island.
- Keep expanded.bottom to two rows: the island clips anything taller.
- Bind a timer tile to a unix-seconds ETA so it ticks with no updates; use tier fresh unless the job needs second-by-second data.
- A slider cannot go on the island; offer a button or step tile instead.

## Example

Derived from `intermediate/3d-printer`. Decodes as a full layout.

```json
{
  "name": "Printer Job",
  "id": "printer-job-live-activity",
  "version": 1,
  "headerTitle": "Printer Job",
  "accentColor": "#FF9F0A",
  "tabs": [
    {
      "title": "Job",
      "icon": "printer.fill",
      "grid": {
        "columns": 4,
        "rows": 6
      },
      "children": [
        {
          "type": "gauge",
          "id": "nozzle",
          "label": "Nozzle",
          "min": 0,
          "max": 260,
          "defaultValue": 213,
          "formatValue": "suffix:\u00b0",
          "tint": "#FF9F0A",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "nozzle",
              "filter": {
                "msg_type": "printer_state"
              }
            }
          ],
          "position": [
            0,
            0
          ],
          "span": [
            2,
            2
          ]
        },
        {
          "type": "gauge",
          "id": "bed",
          "label": "Bed",
          "min": 0,
          "max": 110,
          "defaultValue": 60,
          "formatValue": "suffix:\u00b0",
          "tint": "#64D2FF",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "bed",
              "filter": {
                "msg_type": "printer_state"
              }
            }
          ],
          "position": [
            0,
            2
          ],
          "span": [
            2,
            2
          ]
        },
        {
          "type": "progressRing",
          "id": "progress",
          "label": "Print",
          "min": 0,
          "max": 100,
          "defaultValue": 72,
          "formatValue": "suffix:%",
          "tint": "#FF9F0A",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "progress",
              "filter": {
                "msg_type": "printer_state"
              }
            }
          ],
          "position": [
            2,
            0
          ],
          "span": [
            2,
            2
          ]
        },
        {
          "type": "statusLight",
          "id": "state",
          "label": "State",
          "defaultValue": "printing",
          "statusColors": {
            "printing": "#30D158",
            "paused": "#FF9F0A",
            "idle": "#8E8E93",
            "default": "#8E8E93"
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "state",
              "filter": {
                "msg_type": "printer_state"
              }
            }
          ],
          "position": [
            2,
            2
          ],
          "span": [
            1,
            2
          ]
        },
        {
          "type": "label",
          "id": "eta",
          "label": "ETA",
          "defaultValue": 1792800000,
          "formatValue": "relative",
          "icon": "clock",
          "position": [
            3,
            2
          ],
          "span": [
            1,
            2
          ],
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "eta",
              "filter": {
                "msg_type": "printer_state"
              }
            }
          ]
        },
        {
          "type": "button",
          "id": "pause",
          "label": "Pause",
          "icon": "pause.circle",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "printer_cmd",
              "cmd": "pause"
            }
          },
          "position": [
            4,
            0
          ],
          "span": [
            1,
            2
          ]
        },
        {
          "type": "toggle",
          "id": "lights",
          "label": "Chamber light",
          "defaultValue": false,
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "printer_cmd",
              "on": "{{value}}"
            }
          },
          "position": [
            4,
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
    "title": "Printer",
    "icon": "printer.fill",
    "tint": "#FF9F0A",
    "hero": "progress",
    "slots": [
      "nozzle",
      "bed",
      "state"
    ],
    "liveActivity": true,
    "live": {
      "tier": "fresh",
      "activity": {
        "start": "onConnect"
      }
    },
    "island": {
      "compactLeading": {
        "tile": "icon",
        "icon": "printer.fill",
        "effect": "bounce"
      },
      "compactTrailing": {
        "tile": "ring",
        "control": "progress"
      },
      "minimal": {
        "tile": "light",
        "control": "state"
      },
      "expanded": {
        "leading": {
          "tile": "icon",
          "icon": "printer.fill"
        },
        "trailing": {
          "tile": "freshness"
        },
        "center": {
          "tile": "timer",
          "control": "eta",
          "label": "ETA"
        },
        "bottom": {
          "columns": 2,
          "rows": [
            [
              {
                "tile": "gauge",
                "control": "nozzle"
              },
              {
                "tile": "gauge",
                "control": "bed"
              }
            ],
            [
              {
                "tile": "button",
                "control": "pause",
                "icon": "pause.circle"
              },
              {
                "tile": "toggle",
                "control": "lights"
              }
            ]
          ]
        }
      }
    },
    "lockScreen": {
      "columns": 2,
      "rows": [
        [
          {
            "tile": "ring",
            "control": "progress"
          },
          {
            "tile": "value",
            "control": "nozzle"
          }
        ],
        [
          {
            "tile": "light",
            "control": "state"
          },
          {
            "tile": "timer",
            "control": "eta",
            "label": "ETA"
          }
        ]
      ]
    }
  }
}
```
