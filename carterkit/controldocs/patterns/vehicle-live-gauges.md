---
kind: pattern
id: vehicle-live-gauges
family: dashboards-and-readouts
title: Instrument cluster
intents: ["car dashboard", "engine gauges", "obd readout", "rpm and speed", "instrument cluster"]
parts: [{"type": "gauge", "role": "rpm, coolant"}, {"type": "statTile", "role": "speed, fuel, battery"}, {"type": "statusLight", "role": "warning lamp"}]
surfaces: ["app"]
theme: racing-livery
rules: ["Give the primary dial the most cells and put it top-left.", "Use segments for redline and cold bands so the dial self-explains.", "Keep a warning lamp visible, never off-screen below the fold."]
exampleRef: intermediate/car-diagnostics
---

Instruments are read by position. Keep each dial where the eye expects it and let colour bands flag trouble.

## Parts

- **gauge** (rpm, coolant)
- **statTile** (speed, fuel, battery)
- **statusLight** (warning lamp)

## Rules

- Give the primary dial the most cells and put it top-left.
- Use segments for redline and cold bands so the dial self-explains.
- Keep a warning lamp visible, never off-screen below the fold.

## Example

Derived from `layout-library/intermediate/car-diagnostics`. Decodes as a full layout.

```json
{
  "name": "Car Diagnostics",
  "id": "vehicle-live-gauges",
  "version": 1,
  "headerTitle": "OBD Scanner",
  "accentColor": "#FF6B35",
  "theme": {
    "accentColor": "#FF6B35",
    "cornerRadius": 14,
    "fontDesign": "rounded",
    "dark": {
      "pageBackgroundGradient": [
        "#0B0D10",
        "#16191F"
      ],
      "surfacePrimary": "#FFFFFF12",
      "surfaceSecondary": "#FFFFFF0A",
      "foregroundColor": "#F2F4F7",
      "borderColor": "#FF6B3526"
    },
    "light": {
      "pageBackgroundGradient": [
        "#F2F3F5",
        "#E2E5EA"
      ],
      "surfacePrimary": "#FFFFFFEB",
      "surfaceSecondary": "#F7F8FA",
      "foregroundColor": "#15181D",
      "borderColor": "#15181D18"
    }
  },
  "tabs": [
    {
      "title": "Live",
      "icon": "gauge.with.dots.needle.bottom.50percent",
      "grid": {
        "columns": 4,
        "rows": 9
      },
      "children": [
        {
          "type": "statusLight",
          "id": "cd-link",
          "position": [
            0,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "OBD Link",
          "style": "badge",
          "defaultValue": "connected",
          "statusColors": {
            "connected": "#34C759",
            "searching": "#FF9F0A",
            "offline": "#FF453A"
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "car_diagnostics_status"
              },
              "valuePath": "link"
            }
          ]
        },
        {
          "type": "statusLight",
          "id": "cd-mil",
          "position": [
            0,
            2
          ],
          "span": [
            1,
            2
          ],
          "label": "Check Engine",
          "style": "badge",
          "pulse": true,
          "defaultValue": "on",
          "statusColors": {
            "off": "#34C759",
            "on": "#FF9F0A",
            "flashing": "#FF453A"
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "car_diagnostics_status"
              },
              "valuePath": "mil"
            }
          ]
        },
        {
          "type": "gauge",
          "id": "cd-rpm",
          "position": [
            1,
            0
          ],
          "span": [
            3,
            2
          ],
          "label": "Engine RPM",
          "icon": "gauge.with.dots.needle.67percent",
          "min": 0,
          "max": 7000,
          "step": 10,
          "gaugeStyle": "half",
          "defaultValue": 2350,
          "segments": [
            {
              "limit": 4500,
              "color": "#30D158"
            },
            {
              "limit": 6000,
              "color": "#FF9F0A"
            },
            {
              "limit": 7000,
              "color": "#FF453A"
            }
          ],
          "colorBlend": 0.25,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "car_diagnostics_telemetry"
              },
              "valuePath": "rpm"
            }
          ]
        },
        {
          "type": "gauge",
          "id": "cd-coolant",
          "position": [
            1,
            2
          ],
          "span": [
            3,
            2
          ],
          "label": "Coolant °C",
          "icon": "thermometer.medium",
          "min": 40,
          "max": 130,
          "step": 1,
          "gaugeStyle": "half",
          "defaultValue": 91,
          "segments": [
            {
              "limit": 75,
              "color": "#0A84FF"
            },
            {
              "limit": 105,
              "color": "#30D158"
            },
            {
              "limit": 130,
              "color": "#FF453A"
            }
          ],
          "colorBlend": 0.25,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "car_diagnostics_telemetry"
              },
              "valuePath": "coolant_c"
            }
          ]
        },
        {
          "type": "label",
          "id": "cd-speed",
          "position": [
            4,
            0
          ],
          "span": [
            2,
            2
          ],
          "label": "Speed km/h",
          "icon": "speedometer",
          "style": "large-mono",
          "align": "center",
          "formatValue": "decimal:0",
          "defaultValue": 64,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "car_diagnostics_telemetry"
              },
              "valuePath": "speed_kmh"
            }
          ]
        },
        {
          "type": "progressRing",
          "id": "cd-fuel",
          "position": [
            4,
            2
          ],
          "span": [
            3,
            2
          ],
          "label": "Fuel",
          "icon": "fuelpump.fill",
          "min": 0,
          "max": 100,
          "tint": "#FFD60A",
          "defaultValue": 58,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "car_diagnostics_telemetry"
              },
              "valuePath": "fuel_pct"
            }
          ]
        },
        {
          "type": "label",
          "id": "cd-battery",
          "position": [
            6,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "Battery V",
          "icon": "minus.plus.batteryblock",
          "style": "mono",
          "align": "center",
          "formatValue": "decimal:1",
          "defaultValue": 14.2,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "car_diagnostics_telemetry"
              },
              "valuePath": "battery_v"
            }
          ]
        },
        {
          "type": "sparkline",
          "id": "cd-rpm-trace",
          "position": [
            7,
            0
          ],
          "span": [
            2,
            4
          ],
          "label": "RPM (last 2 min)",
          "tint": "#FF6B35",
          "sparklineFill": true,
          "sparklinePoints": 120,
          "defaultValue": "[820,840,1500,2100,2650,3100,2800,2400,2300,2550,2900,2350]",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "car_diagnostics_telemetry"
              },
              "valuePath": "rpm"
            }
          ]
        }
      ]
    }
  ]
}
```
