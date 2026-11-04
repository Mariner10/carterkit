---
kind: pattern
id: workout-cockpit
family: dashboards-and-readouts
title: Training cockpit
intents: ["workout dashboard", "power cadence heart rate", "cycling trainer", "live fitness metrics", "ride screen"]
parts: [{"type": "gauge", "role": "power, cadence, heart rate"}, {"type": "slider", "role": "resistance"}, {"type": "button", "role": "start / lap"}]
surfaces: ["app", "liveActivity"]
theme: arcade-vapor
rules: ["Three big dials max; more reads as noise mid-effort.", "Make start and lap the largest buttons on the tab.", "Send resistance on release (continuous: false), not on every drag."]
exampleRef: intermediate/bike-trainer
---

When hands and eyes are busy, show few things large. The numbers update live, so avoid anything that needs reading closely.

## Parts

- **gauge** (power, cadence, heart rate)
- **slider** (resistance)
- **button** (start / lap)

## Rules

- Three big dials max; more reads as noise mid-effort.
- Make start and lap the largest buttons on the tab.
- Send resistance on release (continuous: false), not on every drag.

## Example

Derived from `layout-library/intermediate/bike-trainer`. Decodes as a full layout.

```json
{
  "name": "Bike Trainer",
  "id": "workout-cockpit",
  "version": 1,
  "headerTitle": "PAIN CAVE · TRAINER",
  "accentColor": "#FF6B35",
  "theme": {
    "accentColor": "#FF6B35",
    "accentGradient": [
      "#FF6B35",
      "#FFD60A"
    ],
    "cornerRadius": 14,
    "tabBarTint": "#FF6B35",
    "pageBackgroundGradient": [
      "#0A0B10",
      "#14161F"
    ],
    "surfacePrimary": "#FFFFFF10",
    "surfaceSecondary": "#FFFFFF08",
    "borderColor": "#FF6B3530",
    "foregroundColor": "#F5F6FA",
    "secondaryColor": "#A3A8B8"
  },
  "appearance": {
    "colorScheme": "dark",
    "statusBarStyle": "light"
  },
  "tabs": [
    {
      "title": "Ride",
      "icon": "bicycle",
      "grid": {
        "columns": 4,
        "rows": 9
      },
      "children": [
        {
          "type": "gauge",
          "id": "bt-power",
          "position": [
            0,
            0
          ],
          "span": [
            3,
            2
          ],
          "label": "Power",
          "icon": "bolt.fill",
          "min": 0,
          "max": 600,
          "arcAngle": 270,
          "arcRotation": 135,
          "formatValue": "suffix: W",
          "segments": [
            {
              "limit": 150,
              "color": "#5E8BFF"
            },
            {
              "limit": 250,
              "color": "#34C759"
            },
            {
              "limit": 350,
              "color": "#FFD60A"
            },
            {
              "limit": 450,
              "color": "#FF9F0A"
            },
            {
              "limit": 600,
              "color": "#FF375F"
            }
          ],
          "defaultValue": 247,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "bike_trainer_telemetry"
              },
              "valuePath": "power_w"
            }
          ]
        },
        {
          "type": "gauge",
          "id": "bt-cadence",
          "position": [
            0,
            2
          ],
          "span": [
            3,
            2
          ],
          "label": "Cadence",
          "icon": "arrow.triangle.2.circlepath",
          "min": 0,
          "max": 130,
          "arcAngle": 270,
          "arcRotation": 135,
          "formatValue": "suffix: rpm",
          "tint": "#2BD9C8",
          "defaultValue": 91,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "bike_trainer_telemetry"
              },
              "valuePath": "cadence_rpm"
            }
          ]
        },
        {
          "type": "gauge",
          "id": "bt-hr",
          "position": [
            3,
            0
          ],
          "span": [
            3,
            2
          ],
          "label": "Heart Rate",
          "icon": "heart.fill",
          "min": 60,
          "max": 200,
          "gaugeStyle": "full",
          "formatValue": "suffix: bpm",
          "segments": [
            {
              "limit": 114,
              "color": "#8E8E93"
            },
            {
              "limit": 133,
              "color": "#5E8BFF"
            },
            {
              "limit": 152,
              "color": "#34C759"
            },
            {
              "limit": 171,
              "color": "#FF9F0A"
            },
            {
              "limit": 200,
              "color": "#FF375F"
            }
          ],
          "defaultValue": 148,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "bike_trainer_telemetry"
              },
              "valuePath": "heart_bpm"
            }
          ]
        },
        {
          "type": "group",
          "id": "bt-resistance-group",
          "label": "Resistance",
          "position": [
            3,
            2
          ],
          "span": [
            3,
            2
          ],
          "grid": {
            "columns": 2,
            "rows": 2
          },
          "children": [
            {
              "type": "slider",
              "id": "bt-resistance",
              "position": [
                0,
                0
              ],
              "span": [
                1,
                2
              ],
              "label": "Level",
              "min": 0,
              "max": 100,
              "step": 1,
              "formatValue": "percent",
              "minIcon": "tortoise.fill",
              "maxIcon": "hare.fill",
              "tint": "#FF6B35",
              "continuous": false,
              "defaultValue": 42,
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "bike_trainer_set_resistance",
                  "level": "{{value}}"
                }
              },
              "sync": [
                {
                  "method": "meshsocket",
                  "type": "listen",
                  "event": "broadcast",
                  "filter": {
                    "msg_type": "bike_trainer_telemetry"
                  },
                  "valuePath": "resistance_pct"
                }
              ]
            },
            {
              "type": "stepper",
              "id": "bt-grade",
              "position": [
                1,
                0
              ],
              "span": [
                1,
                2
              ],
              "label": "Sim Grade %",
              "icon": "mountain.2.fill",
              "min": -10,
              "max": 20,
              "step": 0.5,
              "defaultValue": 3.5,
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "bike_trainer_set_grade",
                  "grade": "{{value}}"
                }
              },
              "sync": [
                {
                  "method": "meshsocket",
                  "type": "listen",
                  "event": "broadcast",
                  "filter": {
                    "msg_type": "bike_trainer_telemetry"
                  },
                  "valuePath": "grade_pct"
                }
              ]
            }
          ]
        },
        {
          "type": "sparkline",
          "id": "bt-power-trend",
          "position": [
            6,
            0
          ],
          "span": [
            2,
            4
          ],
          "label": "Power · last 2 min",
          "sparklinePoints": 120,
          "sparklineFill": true,
          "tint": "#FF6B35",
          "defaultValue": "[212,225,238,244,251,249,262,270,255,241,236,248,259,266,247]",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "bike_trainer_telemetry"
              },
              "valuePath": "power_w"
            }
          ]
        },
        {
          "type": "label",
          "id": "bt-elapsed",
          "position": [
            8,
            0
          ],
          "span": [
            1,
            2
          ],
          "icon": "timer",
          "style": "large-mono",
          "formatValue": "duration",
          "text": "0h 32m",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "bike_trainer_telemetry"
              },
              "valuePath": "elapsed_s"
            }
          ]
        },
        {
          "type": "label",
          "id": "bt-speed",
          "position": [
            8,
            2
          ],
          "span": [
            1,
            2
          ],
          "icon": "speedometer",
          "style": "large-mono",
          "align": "trailing",
          "formatValue": "suffix: km/h",
          "text": "34.8 km/h",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "bike_trainer_telemetry"
              },
              "valuePath": "speed_kph"
            }
          ]
        }
      ]
    }
  ]
}
```
