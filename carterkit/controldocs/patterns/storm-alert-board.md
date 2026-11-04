---
kind: pattern
id: storm-alert-board
family: surface-first
title: Alert level on the lock screen
intents: ["storm warning on lock screen", "status light for an alert level", "severe weather live activity", "show danger level at a glance", "lock screen accessory widget"]
parts: [{"type": "statusLight", "role": "alert level, every surface hero"}, {"type": "gauge", "role": "wind"}, {"type": "gauge", "role": "rain rate"}]
surfaces: ["app", "liveActivity", "lockScreen", "widget"]
theme: clinical-ward
rules: ["Use statusColors so the level reads as a word and a color; accessory widgets draw it monochrome, so the word must carry the meaning.", "Set activity.stale so a quiet feed greys out instead of looking safe.", "Pair the surface with an alert rule: every fired alert also refreshes the glance, even after a force-quit.", "Island and lock screen get one row of two readings; the level light is the hero in every slot."]
exampleRef: template-catalog/storm-alerts
---

When the question is “is it bad right now”, a status light answers faster than any gauge. Put it in every surface slot and let the numbers sit beneath.

## Parts

- **statusLight** (alert level, every surface hero)
- **gauge** (wind)
- **gauge** (rain rate)

## Rules

- Use statusColors so the level reads as a word and a color; accessory widgets draw it monochrome, so the word must carry the meaning.
- Set activity.stale so a quiet feed greys out instead of looking safe.
- Pair the surface with an alert rule: every fired alert also refreshes the glance, even after a force-quit.
- Island and lock screen get one row of two readings; the level light is the hero in every slot.

## Example

Derived from `template-catalog/storm-alerts`. Decodes as a full layout.

```json
{
  "name": "Storm Board",
  "id": "storm-alert-board",
  "version": 1,
  "headerTitle": "Storm Board",
  "accentColor": "#FF3B30",
  "tabs": [
    {
      "title": "Storm",
      "icon": "cloud.bolt.rain.fill",
      "grid": {
        "columns": 4,
        "rows": 6
      },
      "children": [
        {
          "type": "statusLight",
          "id": "level",
          "label": "Alert level",
          "defaultValue": "clear",
          "statusColors": {
            "clear": "#30D158",
            "watch": "#FF9F0A",
            "warning": "#FF3B30",
            "default": "#8E8E93"
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "level",
              "filter": {
                "msg_type": "storm_state"
              }
            }
          ],
          "position": [
            0,
            0
          ],
          "span": [
            2,
            4
          ]
        },
        {
          "type": "gauge",
          "id": "wind",
          "label": "Wind",
          "min": 0,
          "max": 120,
          "defaultValue": 18,
          "formatValue": "suffix: km/h",
          "tint": "#64D2FF",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "wind_kph",
              "filter": {
                "msg_type": "storm_state"
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
          "type": "gauge",
          "id": "rain",
          "label": "Rain rate",
          "min": 0,
          "max": 50,
          "defaultValue": 2,
          "formatValue": "suffix: mm/h",
          "tint": "#5E5CE6",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "rain_mm",
              "filter": {
                "msg_type": "storm_state"
              }
            }
          ],
          "position": [
            2,
            2
          ],
          "span": [
            2,
            2
          ]
        },
        {
          "type": "label",
          "id": "note",
          "text": "Alerts also arrive as notifications; the lock screen shows the current level.",
          "style": "caption",
          "icon": "info.circle",
          "position": [
            4,
            0
          ],
          "span": [
            1,
            4
          ]
        }
      ]
    }
  ],
  "glance": {
    "title": "Storm",
    "icon": "cloud.bolt.rain.fill",
    "tint": "#FF3B30",
    "hero": "level",
    "slots": [
      "wind",
      "rain"
    ],
    "liveActivity": true,
    "live": {
      "tier": "fresh",
      "activity": {
        "stale": 300
      }
    },
    "island": {
      "compactLeading": {
        "tile": "icon",
        "icon": "cloud.bolt.rain.fill",
        "effect": "pulse"
      },
      "compactTrailing": {
        "tile": "light",
        "control": "level"
      },
      "minimal": {
        "tile": "light",
        "control": "level"
      },
      "expanded": {
        "leading": {
          "tile": "icon",
          "icon": "cloud.bolt.rain.fill"
        },
        "trailing": {
          "tile": "freshness"
        },
        "center": {
          "tile": "light",
          "control": "level"
        },
        "bottom": {
          "columns": 2,
          "rows": [
            [
              {
                "tile": "gauge",
                "control": "wind"
              },
              {
                "tile": "gauge",
                "control": "rain"
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
            "tile": "light",
            "control": "level"
          },
          {
            "tile": "value",
            "control": "wind"
          }
        ]
      ]
    },
    "widgets": [
      {
        "id": "lock",
        "title": "Storm level",
        "icon": "cloud.bolt",
        "families": [
          "accessoryCircular",
          "accessoryRectangular",
          "accessoryInline"
        ],
        "scene": {
          "columns": 2,
          "rows": [
            [
              {
                "tile": "light",
                "control": "level"
              },
              {
                "tile": "value",
                "control": "wind"
              }
            ]
          ]
        }
      }
    ]
  }
}
```
