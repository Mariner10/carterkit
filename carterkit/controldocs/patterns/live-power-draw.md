---
kind: pattern
id: live-power-draw
family: dashboards-and-readouts
title: Live draw with today’s trend
intents: ["energy dashboard", "power usage now", "electricity monitor", "solar and grid readout", "kilowatt hours today"]
parts: [{"type": "gauge", "role": "current draw, hero"}, {"type": "statTile", "role": "kWh today, cost"}, {"type": "sparkline", "role": "draw over the day"}]
surfaces: ["app", "widget", "liveActivity"]
theme: glass-cockpit
rules: ["Set the gauge max near the real peak so the needle moves.", "Show cumulative figures (kWh, cost) as statTiles, instantaneous ones as gauges.", "Declare the unit once on the control so it converts to the device locale."]
exampleRef: intermediate/home-energy
---

Energy needs the now-number and the day’s shape. The gauge answers “how much right now” and the tile and spark answer “is that normal”.

## Parts

- **gauge** (current draw, hero)
- **statTile** (kWh today, cost)
- **sparkline** (draw over the day)

## Rules

- Set the gauge max near the real peak so the needle moves.
- Show cumulative figures (kWh, cost) as statTiles, instantaneous ones as gauges.
- Declare the unit once on the control so it converts to the device locale.

## Example

Derived from `layout-library/intermediate/home-energy`. Decodes as a full layout.

```json
{
  "name": "Home Energy",
  "id": "live-power-draw",
  "version": 1,
  "headerTitle": "Home Energy",
  "accentColor": "#FFB347",
  "theme": {
    "accentColor": "#FFB347",
    "accentGradient": [
      "#FFB347",
      "#FF6F3C"
    ],
    "cornerRadius": 14,
    "tabBarTint": "#FFB347",
    "surfacePrimary": "#FFD9A014",
    "surfaceSecondary": "#FFD9A00A",
    "borderColor": "#FFD9A02E",
    "toggle": {
      "trackActiveColor": "#FFB347"
    }
  },
  "tabs": [
    {
      "title": "Live",
      "icon": "bolt.fill",
      "grid": {
        "columns": 2,
        "rows": 10
      },
      "children": [
        {
          "type": "gauge",
          "id": "he-live-watts",
          "position": [
            0,
            0
          ],
          "span": [
            3,
            2
          ],
          "label": "Whole-Home Draw",
          "icon": "bolt.fill",
          "min": 0,
          "max": 10000,
          "gaugeStyle": "half",
          "defaultValue": 3660,
          "formatValue": "suffix: W",
          "segments": [
            {
              "limit": 3000,
              "color": "#34C759"
            },
            {
              "limit": 6500,
              "color": "#FFB347"
            },
            {
              "limit": 10000,
              "color": "#FF3B30"
            }
          ],
          "colorBlend": 0.3,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "home_energy_live"
              },
              "valuePath": "watts"
            }
          ]
        },
        {
          "type": "label",
          "id": "he-today-kwh",
          "position": [
            3,
            0
          ],
          "label": "Today",
          "icon": "sum",
          "defaultValue": 18.4,
          "formatValue": "suffix: kWh",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "home_energy_today"
              },
              "valuePath": "kwh_total"
            }
          ]
        },
        {
          "type": "label",
          "id": "he-today-cost",
          "position": [
            3,
            1
          ],
          "label": "Cost so far",
          "icon": "dollarsign.circle",
          "defaultValue": "$3.12",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "home_energy_today"
              },
              "valuePath": "cost_display"
            }
          ]
        },
        {
          "type": "sparkline",
          "id": "he-kwh-trend",
          "position": [
            4,
            0
          ],
          "span": [
            2,
            2
          ],
          "label": "kWh per hour today",
          "tint": "#FFB347",
          "sparklineFill": true,
          "sparklinePoints": 24,
          "defaultValue": "[0.42,0.38,0.35,0.33,0.36,0.51,0.94,1.32,1.10,0.86,0.78,0.81,0.92,0.88,0.97,1.24,1.66,2.08,1.87]",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "home_energy_today"
              },
              "valuePath": "hourly_kwh"
            }
          ]
        },
        {
          "type": "pieChart",
          "id": "he-room-split",
          "position": [
            6,
            0
          ],
          "span": [
            4,
            2
          ],
          "label": "Draw by room",
          "pieStyle": "donut",
          "tint": "#FFB347",
          "pieConfig": {
            "centerText": "{{total}} W",
            "showLegend": true,
            "percent": true,
            "showLabels": false,
            "donutRatio": 0.62
          },
          "defaultValue": "{\"slices\":[{\"label\":\"Kitchen\",\"value\":1988,\"color\":\"#FFB347\"},{\"label\":\"HVAC\",\"value\":1320,\"color\":\"#5AC8FA\"},{\"label\":\"Office\",\"value\":212,\"color\":\"#A78BFA\"},{\"label\":\"Laundry\",\"value\":96,\"color\":\"#34C759\"},{\"label\":\"Other\",\"value\":84,\"color\":\"#8E8E93\"}]}",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "home_energy_rooms"
              },
              "valuePath": "split"
            }
          ]
        }
      ]
    }
  ]
}
```
