---
kind: pattern
id: ev-charge-live-activity
family: surface-first
title: Charging session with remote start
intents: ["ev charging live activity", "car charging on lock screen", "see when my car is full", "charging session island", "electric car charge status"]
parts: [{"type": "progressRing", "role": "battery percent, island hero"}, {"type": "gauge", "role": "charge rate"}, {"type": "label", "role": "time until full (relative)"}, {"type": "button", "role": "stop"}]
surfaces: ["app", "liveActivity", "widget"]
theme: glass-cockpit
rules: ["Set activity.start to remote so the hub starts the activity when the car plugs in, with no app open.", "The same ring serves compactTrailing and minimal: one number the user cares about.", "Replace the charge-limit slider on the island with a step tile (delta 5); sliders exist only in the app.", "Add a small widget with the ring for when no session is running."]
exampleRef: advanced/ev-charger
---

A charging session starts and ends on its own. Let the relay start the activity and keep the surface to battery, rate and time-to-full.

## Parts

- **progressRing** (battery percent, island hero)
- **gauge** (charge rate)
- **label** (time until full (relative))
- **button** (stop)

## Rules

- Set activity.start to remote so the hub starts the activity when the car plugs in, with no app open.
- The same ring serves compactTrailing and minimal: one number the user cares about.
- Replace the charge-limit slider on the island with a step tile (delta 5); sliders exist only in the app.
- Add a small widget with the ring for when no session is running.

## Example

Derived from `advanced/ev-charger`. Decodes as a full layout.

```json
{
  "name": "EV Charge",
  "id": "ev-charge-live-activity",
  "version": 1,
  "headerTitle": "EV Charge",
  "accentColor": "#30D158",
  "tabs": [
    {
      "title": "Charge",
      "icon": "bolt.car.fill",
      "grid": {
        "columns": 4,
        "rows": 6
      },
      "children": [
        {
          "type": "progressRing",
          "id": "soc",
          "label": "Battery",
          "min": 0,
          "max": 100,
          "defaultValue": 54,
          "formatValue": "suffix:%",
          "tint": "#30D158",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "soc",
              "filter": {
                "msg_type": "ev_state"
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
          "id": "kw",
          "label": "Charge rate",
          "min": 0,
          "max": 11,
          "defaultValue": 7.2,
          "formatValue": "suffix: kW",
          "tint": "#64D2FF",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "kw",
              "filter": {
                "msg_type": "ev_state"
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
          "type": "statusLight",
          "id": "plug",
          "label": "Charger",
          "defaultValue": "charging",
          "statusColors": {
            "charging": "#30D158",
            "plugged": "#FF9F0A",
            "unplugged": "#8E8E93",
            "default": "#8E8E93"
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "plug",
              "filter": {
                "msg_type": "ev_state"
              }
            }
          ],
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
          "type": "label",
          "id": "done",
          "label": "Full at",
          "defaultValue": 1792800000,
          "formatValue": "relative",
          "icon": "bolt.badge.clock",
          "position": [
            2,
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
              "valuePath": "done_at",
              "filter": {
                "msg_type": "ev_state"
              }
            }
          ]
        },
        {
          "type": "slider",
          "id": "limit",
          "label": "Charge limit",
          "min": 0,
          "max": 100,
          "step": 5,
          "defaultValue": 80,
          "formatValue": "suffix:%",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "ev_limit",
              "value": "{{value}}"
            }
          },
          "position": [
            3,
            0
          ],
          "span": [
            1,
            4
          ]
        },
        {
          "type": "button",
          "id": "stop",
          "label": "Stop charging",
          "icon": "stop.circle",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "ev_cmd",
              "cmd": "stop"
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
        }
      ]
    }
  ],
  "glance": {
    "title": "EV Charger",
    "icon": "bolt.car.fill",
    "tint": "#30D158",
    "hero": "soc",
    "slots": [
      "kw",
      "plug"
    ],
    "liveActivity": true,
    "live": {
      "tier": "fresh",
      "activity": {
        "start": "remote"
      }
    },
    "island": {
      "compactLeading": {
        "tile": "icon",
        "icon": "bolt.car.fill",
        "effect": "pulse"
      },
      "compactTrailing": {
        "tile": "ring",
        "control": "soc"
      },
      "minimal": {
        "tile": "ring",
        "control": "soc"
      },
      "expanded": {
        "leading": {
          "tile": "icon",
          "icon": "bolt.car.fill"
        },
        "trailing": {
          "tile": "value",
          "control": "kw"
        },
        "center": {
          "tile": "timer",
          "control": "done",
          "label": "Full in"
        },
        "bottom": {
          "columns": 2,
          "rows": [
            [
              {
                "tile": "bar",
                "control": "soc",
                "span": 2
              }
            ],
            [
              {
                "tile": "button",
                "control": "stop",
                "icon": "stop.circle"
              },
              {
                "tile": "step",
                "control": "limit",
                "delta": 5
              }
            ]
          ]
        }
      }
    },
    "widgets": [
      {
        "id": "charge",
        "title": "Charge",
        "icon": "bolt.car.fill",
        "families": [
          "systemSmall",
          "accessoryCircular"
        ],
        "scene": {
          "columns": 1,
          "rows": [
            [
              {
                "tile": "ring",
                "control": "soc"
              }
            ]
          ]
        }
      }
    ]
  }
}
```
