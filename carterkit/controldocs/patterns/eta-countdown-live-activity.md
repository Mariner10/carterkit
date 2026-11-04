---
kind: pattern
id: eta-countdown-live-activity
family: surface-first
title: Delivery or trip countdown
intents: ["delivery tracking live activity", "rideshare eta on the island", "countdown to arrival", "package on its way", "track a trip from the lock screen"]
parts: [{"type": "progressRing", "role": "trip percent, minimal slot"}, {"type": "label", "role": "ETA as a ticking timer tile"}, {"type": "statusLight", "role": "phase"}, {"type": "button", "role": "contact"}]
surfaces: ["app", "liveActivity", "lockScreen"]
theme: nordic-aurora
rules: ["Bind a timer tile to the arrival time so the clock ticks on the device with no per-second updates.", "Start remotely (activity.start remote): the trip begins on a server event, not an app launch.", "Keep compactTrailing to the timer; a ring there would hide the ETA people open the island for.", "Activities end after 8 hours and carry 4 KB of state; send only the percent, phase and arrival time."]
exampleRef: template-catalog/orbit-iss
---

A trip is a countdown with a phase. The timer tile is the hero, the bar is context, and the server pushes the start and the finish.

## Parts

- **progressRing** (trip percent, minimal slot)
- **label** (ETA as a ticking timer tile)
- **statusLight** (phase)
- **button** (contact)

## Rules

- Bind a timer tile to the arrival time so the clock ticks on the device with no per-second updates.
- Start remotely (activity.start remote): the trip begins on a server event, not an app launch.
- Keep compactTrailing to the timer; a ring there would hide the ETA people open the island for.
- Activities end after 8 hours and carry 4 KB of state; send only the percent, phase and arrival time.

## Example

Derived from `template-catalog/orbit-iss`. Decodes as a full layout.

```json
{
  "name": "Trip Tracker",
  "id": "eta-countdown-live-activity",
  "version": 1,
  "headerTitle": "Trip Tracker",
  "accentColor": "#30D158",
  "tabs": [
    {
      "title": "Trip",
      "icon": "shippingbox.fill",
      "grid": {
        "columns": 4,
        "rows": 5
      },
      "children": [
        {
          "type": "progressRing",
          "id": "trip",
          "label": "Trip progress",
          "min": 0,
          "max": 100,
          "defaultValue": 35,
          "formatValue": "suffix:%",
          "tint": "#30D158",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "percent",
              "filter": {
                "msg_type": "trip_state"
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
          "type": "label",
          "id": "arrival",
          "label": "Arrives",
          "defaultValue": 1792800000,
          "formatValue": "relative",
          "icon": "clock.fill",
          "position": [
            0,
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
                "msg_type": "trip_state"
              }
            }
          ]
        },
        {
          "type": "statusLight",
          "id": "phase",
          "label": "Status",
          "defaultValue": "enroute",
          "statusColors": {
            "preparing": "#FF9F0A",
            "enroute": "#30D158",
            "arrived": "#64D2FF",
            "default": "#8E8E93"
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "phase",
              "filter": {
                "msg_type": "trip_state"
              }
            }
          ],
          "position": [
            1,
            2
          ],
          "span": [
            1,
            2
          ]
        },
        {
          "type": "button",
          "id": "call",
          "label": "Contact",
          "icon": "phone.fill",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "trip_cmd",
              "cmd": "call"
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
          "id": "share",
          "label": "Share ETA",
          "icon": "square.and.arrow.up",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "trip_cmd",
              "cmd": "share"
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
    "title": "Trip",
    "icon": "shippingbox.fill",
    "tint": "#30D158",
    "hero": "trip",
    "slots": [
      "phase"
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
        "icon": "shippingbox.fill",
        "effect": "bounce"
      },
      "compactTrailing": {
        "tile": "timer",
        "control": "arrival"
      },
      "minimal": {
        "tile": "ring",
        "control": "trip"
      },
      "expanded": {
        "leading": {
          "tile": "icon",
          "icon": "shippingbox.fill"
        },
        "trailing": {
          "tile": "freshness"
        },
        "center": {
          "tile": "timer",
          "control": "arrival",
          "label": "Arrives"
        },
        "bottom": {
          "columns": 2,
          "rows": [
            [
              {
                "tile": "bar",
                "control": "trip",
                "span": 2
              }
            ],
            [
              {
                "tile": "light",
                "control": "phase"
              },
              {
                "tile": "button",
                "control": "call",
                "icon": "phone.fill"
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
            "tile": "timer",
            "control": "arrival",
            "label": "Arrives"
          },
          {
            "tile": "light",
            "control": "phase"
          }
        ],
        [
          {
            "tile": "bar",
            "control": "trip",
            "span": 2
          }
        ]
      ]
    }
  }
}
```
