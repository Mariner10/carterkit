---
kind: pattern
id: weather-now
family: dashboards-and-readouts
title: Current conditions readout
intents: ["weather dashboard", "current temperature and wind", "conditions at a glance", "station readout", "live sensor tiles"]
parts: [{"type": "statTile", "role": "temperature, wind, rain"}, {"type": "gauge", "role": "pressure or humidity"}, {"type": "sparkline", "role": "recent trend"}]
surfaces: ["app", "widget", "lockScreen"]
theme: nordic-aurora
rules: ["Use statTile for numbers you read and gauge only when range matters.", "Add a sparkline under any value people ask “is it going up?” about.", "A two-column grid fits a phone; do not cram four."]
exampleRef: intermediate/weather-station
---

A readout dashboard is a grid of tiles, each one value with its unit and a faint trend. Order them by how often people look.

## Parts

- **statTile** (temperature, wind, rain)
- **gauge** (pressure or humidity)
- **sparkline** (recent trend)

## Rules

- Use statTile for numbers you read and gauge only when range matters.
- Add a sparkline under any value people ask “is it going up?” about.
- A two-column grid fits a phone; do not cram four.

## Example

Derived from `layout-library/intermediate/weather-station`. Decodes as a full layout.

```json
{
  "name": "Backyard Weather Station",
  "id": "weather-now",
  "version": 1,
  "headerTitle": "Backyard Wx",
  "accentColor": "#4FB3E8",
  "theme": {
    "accentColor": "#4FB3E8",
    "accentGradient": [
      "#4FB3E8",
      "#2E6FD8"
    ],
    "cornerRadius": 14,
    "tabBarTint": "#4FB3E8",
    "surfacePrimary": "#9FD8FF14",
    "surfaceSecondary": "#9FD8FF0A",
    "borderColor": "#9FD8FF2E",
    "toggle": {
      "trackActiveColor": "#4FB3E8"
    },
    "slider": {
      "trackActiveColor": "#4FB3E8"
    }
  },
  "tabs": [
    {
      "title": "Now",
      "icon": "cloud.sun.fill",
      "grid": {
        "columns": 2,
        "rows": 8
      },
      "children": [
        {
          "type": "gauge",
          "id": "ws-temp",
          "position": [
            0,
            0
          ],
          "span": [
            3,
            1
          ],
          "label": "Outdoor Temp",
          "icon": "thermometer.medium",
          "min": -10,
          "max": 110,
          "gaugeStyle": "half",
          "defaultValue": 67.4,
          "formatValue": "suffix: °",
          "segments": [
            {
              "limit": 32,
              "color": "#6FA8FF"
            },
            {
              "limit": 80,
              "color": "#34C759"
            },
            {
              "limit": 110,
              "color": "#FF6B3D"
            }
          ],
          "colorBlend": 0.3,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "weather_station_current"
              },
              "valuePath": "temp"
            }
          ]
        },
        {
          "type": "gauge",
          "id": "ws-wind",
          "position": [
            0,
            1
          ],
          "span": [
            3,
            1
          ],
          "label": "Wind",
          "icon": "wind",
          "min": 0,
          "max": 60,
          "gaugeStyle": "half",
          "defaultValue": 8.2,
          "formatValue": "suffix: mph",
          "segments": [
            {
              "limit": 15,
              "color": "#34C759"
            },
            {
              "limit": 30,
              "color": "#FFB347"
            },
            {
              "limit": 60,
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
                "msg_type": "weather_station_current"
              },
              "valuePath": "wind_speed"
            }
          ]
        },
        {
          "type": "label",
          "id": "ws-gust",
          "position": [
            3,
            0
          ],
          "label": "Gust · Direction",
          "icon": "arrow.up.right.circle",
          "defaultValue": "14 mph · WNW",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "weather_station_current"
              },
              "valuePath": "gust_display"
            }
          ]
        },
        {
          "type": "label",
          "id": "ws-humidity",
          "position": [
            3,
            1
          ],
          "label": "Humidity",
          "icon": "humidity.fill",
          "defaultValue": 58,
          "formatValue": "suffix: %",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "weather_station_current"
              },
              "valuePath": "humidity"
            }
          ]
        },
        {
          "type": "label",
          "id": "ws-rain-today",
          "position": [
            4,
            0
          ],
          "label": "Rain today",
          "icon": "cloud.rain.fill",
          "defaultValue": "0.12 in",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "weather_station_rain"
              },
              "valuePath": "today_display"
            }
          ]
        },
        {
          "type": "statusLight",
          "id": "ws-link",
          "position": [
            4,
            1
          ],
          "label": "Sensor array",
          "style": "badge",
          "size": "default",
          "pulse": true,
          "statusColors": {
            "online": "#34C759",
            "weak": "#FFB347",
            "offline": "#FF3B30"
          },
          "defaultValue": "online",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "weather_station_health"
              },
              "valuePath": "array_link"
            }
          ]
        },
        {
          "type": "sparkline",
          "id": "ws-pressure",
          "position": [
            5,
            0
          ],
          "span": [
            2,
            2
          ],
          "label": "Pressure · 30.02 inHg falling",
          "tint": "#4FB3E8",
          "sparklineFill": true,
          "sparklinePoints": 48,
          "defaultValue": "[30.14,30.13,30.13,30.12,30.11,30.11,30.10,30.09,30.08,30.08,30.07,30.06,30.06,30.05,30.04,30.04,30.03,30.02]",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "weather_station_pressure"
              },
              "valuePath": "inhg"
            }
          ]
        },
        {
          "type": "segmentedControl",
          "id": "ws-units",
          "position": [
            7,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "Units",
          "options": [
            "imperial",
            "metric"
          ],
          "optionLabels": [
            "°F · mph · in",
            "°C · km/h · mm"
          ],
          "defaultValue": "imperial",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "weather_station_set_units",
              "system": "{{value}}"
            }
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "weather_station_settings"
              },
              "valuePath": "units"
            }
          ]
        }
      ]
    }
  ]
}
```
