---
kind: pattern
id: home-screen-widget-readout
family: surface-first
title: Home Screen widget readout
intents: ["widget for room temperature", "home screen widget with live numbers", "glanceable readout widget", "medium widget with a trend", "smart home widget"]
parts: [{"type": "gauge", "role": "hero number, widget tile"}, {"type": "gauge", "role": "companion number"}, {"type": "sparkline", "role": "24-point history under the numbers"}]
surfaces: ["app", "widget"]
theme: grouped
rules: ["Declare widgets[] with a scene per size family; give systemSmall its own one-tile scene so it is never a cropped medium.", "Widgets cannot scroll or animate freely, so a scene is at most three rows.", "Use tier periodic for a readout that changes slowly; reserve realtime for live sessions.", "Tile control ids that do not exist are dropped, so keep them in step with the layout ids."]
exampleRef: intermediate/home-energy
---

A widget is a tiny dashboard the user never opens. Pick the one number, add a trend, and let each size family show a cut of the same scene.

## Parts

- **gauge** (hero number, widget tile)
- **gauge** (companion number)
- **sparkline** (24-point history under the numbers)

## Rules

- Declare widgets[] with a scene per size family; give systemSmall its own one-tile scene so it is never a cropped medium.
- Widgets cannot scroll or animate freely, so a scene is at most three rows.
- Use tier periodic for a readout that changes slowly; reserve realtime for live sessions.
- Tile control ids that do not exist are dropped, so keep them in step with the layout ids.

## Example

Derived from `intermediate/home-energy`. Decodes as a full layout.

```json
{
  "name": "Room Readout",
  "id": "home-screen-widget-readout",
  "version": 1,
  "headerTitle": "Room Readout",
  "accentColor": "#FF9F0A",
  "tabs": [
    {
      "title": "Room",
      "icon": "thermometer.medium",
      "grid": {
        "columns": 4,
        "rows": 5
      },
      "children": [
        {
          "type": "gauge",
          "id": "temp",
          "label": "Temperature",
          "min": 0,
          "max": 40,
          "defaultValue": 22,
          "formatValue": "suffix:\u00b0",
          "tint": "#FF9F0A",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "temp",
              "filter": {
                "msg_type": "room_state"
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
          "id": "humidity",
          "label": "Humidity",
          "min": 0,
          "max": 100,
          "defaultValue": 45,
          "formatValue": "suffix:%",
          "tint": "#64D2FF",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "humidity",
              "filter": {
                "msg_type": "room_state"
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
          "type": "sparkline",
          "id": "trend",
          "label": "Temperature trend",
          "min": 0,
          "max": 40,
          "defaultValue": 22,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "temp",
              "filter": {
                "msg_type": "room_state"
              }
            }
          ],
          "position": [
            2,
            0
          ],
          "span": [
            1,
            4
          ]
        },
        {
          "type": "label",
          "id": "co2",
          "label": "CO\u2082",
          "defaultValue": 620,
          "formatValue": "suffix: ppm",
          "icon": "aqi.low",
          "position": [
            3,
            0
          ],
          "span": [
            1,
            4
          ],
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "valuePath": "co2",
              "filter": {
                "msg_type": "room_state"
              }
            }
          ]
        }
      ]
    }
  ],
  "glance": {
    "title": "Room",
    "icon": "thermometer.medium",
    "tint": "#FF9F0A",
    "hero": "temp",
    "slots": [
      "humidity",
      "co2"
    ],
    "live": {
      "tier": "periodic"
    },
    "widgets": [
      {
        "id": "small",
        "title": "Room now",
        "icon": "thermometer",
        "families": [
          "systemSmall",
          "accessoryCircular",
          "accessoryInline"
        ],
        "scene": {
          "columns": 1,
          "rows": [
            [
              {
                "tile": "gauge",
                "control": "temp"
              }
            ]
          ]
        }
      },
      {
        "id": "medium",
        "title": "Room readout",
        "icon": "thermometer.medium",
        "families": [
          "systemMedium",
          "systemLarge",
          "accessoryRectangular"
        ],
        "scene": {
          "columns": 2,
          "rows": [
            [
              {
                "tile": "gauge",
                "control": "temp"
              },
              {
                "tile": "gauge",
                "control": "humidity"
              }
            ],
            [
              {
                "tile": "sparkline",
                "control": "temp",
                "span": 2
              }
            ]
          ]
        },
        "systemSmall": {
          "columns": 1,
          "rows": [
            [
              {
                "tile": "gauge",
                "control": "temp"
              }
            ]
          ]
        }
      }
    ]
  }
}
```
