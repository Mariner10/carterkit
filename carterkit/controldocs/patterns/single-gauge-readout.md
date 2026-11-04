---
kind: pattern
id: single-gauge-readout
family: dashboards-and-readouts
title: One big gauge with bands
intents: ["show one sensor reading", "soil moisture gauge", "simple meter", "a gauge with a good and bad range", "monitor a value"]
parts: [{"type": "gauge", "role": "hero reading with colour segments"}, {"type": "statusLight", "role": "plain-words state"}, {"type": "button", "role": "one action (water now)"}]
surfaces: ["app", "widget", "controlCenter"]
theme: botanical-greenhouse
rules: ["Use gauge segments for bands so colour carries meaning: warn, good, high.", "One hero reading per screen; everything else is secondary.", "Pair the number with a state word so colour is not the only signal."]
exampleRef: beginner/plant-monitor
---

The simplest useful dashboard is one number, its healthy range, and the one thing you can do about it.

## Parts

- **gauge** (hero reading with colour segments)
- **statusLight** (plain-words state)
- **button** (one action (water now))

## Rules

- Use gauge segments for bands so colour carries meaning: warn, good, high.
- One hero reading per screen; everything else is secondary.
- Pair the number with a state word so colour is not the only signal.

## Example

Derived from `layout-library/beginner/plant-monitor`. Decodes as a full layout.

```json
{
  "name": "Plant Monitor",
  "id": "single-gauge-readout",
  "version": 1,
  "headerTitle": "Monstera",
  "accentColor": "#34C759",
  "tabs": [
    {
      "title": "Plant",
      "icon": "leaf.fill",
      "grid": {
        "columns": 2,
        "rows": 7
      },
      "children": [
        {
          "type": "label",
          "id": "plant-about",
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
          "text": "Starter: one gauge listens for moisture, the light flags thirst, the button sends a command."
        },
        {
          "type": "gauge",
          "id": "plant-soil-moisture",
          "position": [
            1,
            0
          ],
          "span": [
            3,
            2
          ],
          "label": "Soil Moisture",
          "icon": "drop.fill",
          "min": 0,
          "max": 100,
          "gaugeStyle": "half",
          "defaultValue": 22,
          "formatValue": "suffix:%",
          "segments": [
            {
              "limit": 25,
              "color": "#FF9500"
            },
            {
              "limit": 70,
              "color": "#34C759"
            },
            {
              "limit": 100,
              "color": "#0A84FF"
            }
          ],
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "plant_monitor_reading"
              },
              "valuePath": "moisture_pct"
            }
          ]
        },
        {
          "type": "statusLight",
          "id": "plant-needs-water",
          "position": [
            4,
            0
          ],
          "span": [
            1,
            1
          ],
          "label": "Needs Water",
          "style": "badge",
          "pulse": true,
          "defaultValue": "thirsty",
          "statusColors": {
            "ok": "#34C759",
            "soon": "#FF9500",
            "thirsty": "#FF3B30"
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "plant_monitor_reading"
              },
              "valuePath": "water_status"
            }
          ]
        },
        {
          "type": "label",
          "id": "plant-last-watered",
          "position": [
            4,
            1
          ],
          "span": [
            1,
            1
          ],
          "icon": "clock",
          "text": "Watered 3 days ago",
          "align": "trailing"
        },
        {
          "type": "stepper",
          "id": "plant-dose",
          "position": [
            5,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "Dose (ml)",
          "icon": "drop.halffull",
          "min": 50,
          "max": 500,
          "step": 50,
          "defaultValue": 250,
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "plant_monitor_set_dose",
              "dose_ml": "{{value}}"
            }
          }
        },
        {
          "type": "button",
          "id": "plant-water-now",
          "position": [
            6,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "Water Now",
          "icon": "drop.fill",
          "style": "filled",
          "tint": "#0A84FF",
          "haptic": "success",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "plant_monitor_water_now",
              "source": "app"
            }
          }
        }
      ]
    }
  ]
}
```
