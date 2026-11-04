---
kind: pattern
id: climate-dials
family: dashboards-and-readouts
title: Climate dials with setpoints
intents: ["temperature humidity and co2", "greenhouse monitor", "climate control panel", "dials with a target", "hvac readout"]
parts: [{"type": "gauge", "role": "each measured quantity"}, {"type": "slider", "role": "setpoint"}, {"type": "toggle", "role": "vent or fan"}]
surfaces: ["app", "controlCenter"]
theme: botanical-greenhouse
rules: ["Put each setpoint directly under the gauge it controls.", "Controls that flip equipment (vent, fan) are toggles, not buttons, so state is visible.", "Keep readouts on the left or top and controls below."]
exampleRef: intermediate/greenhouse
---

A control panel pairs every reading with the lever that moves it. Keep the pair adjacent so cause and effect are one glance.

## Parts

- **gauge** (each measured quantity)
- **slider** (setpoint)
- **toggle** (vent or fan)

## Rules

- Put each setpoint directly under the gauge it controls.
- Controls that flip equipment (vent, fan) are toggles, not buttons, so state is visible.
- Keep readouts on the left or top and controls below.

## Example

Derived from `layout-library/intermediate/greenhouse`. Decodes as a full layout.

```json
{
  "name": "Greenhouse",
  "id": "climate-dials",
  "version": 1,
  "headerTitle": "GREENHOUSE · BAY 2",
  "accentColor": "#7BD88F",
  "theme": {
    "accentColor": "#7BD88F",
    "cornerRadius": 14,
    "fontDesign": "rounded",
    "tabBarTint": "#7BD88F",
    "pageBackgroundGradient": [
      "#07130C",
      "#0D2216",
      "#12301D"
    ],
    "surfacePrimary": "#A8F0C014",
    "surfaceSecondary": "#A8F0C00A",
    "borderColor": "#A8F0C02E",
    "foregroundColor": "#EFFFF4",
    "secondaryColor": "#9CC7AA",
    "toggle": {
      "trackActiveColor": "#7BD88F"
    },
    "slider": {
      "trackActiveColor": "#7BD88F"
    }
  },
  "appearance": {
    "colorScheme": "dark",
    "statusBarStyle": "light"
  },
  "tabs": [
    {
      "title": "Climate",
      "icon": "leaf.fill",
      "grid": {
        "columns": 4,
        "rows": 9
      },
      "children": [
        {
          "type": "gauge",
          "id": "gh-temp",
          "position": [
            0,
            0
          ],
          "span": [
            3,
            2
          ],
          "label": "Air Temp",
          "icon": "thermometer.medium",
          "min": 5,
          "max": 40,
          "step": 0.1,
          "formatValue": "suffix:°C",
          "arcAngle": 270,
          "arcRotation": 135,
          "colorBlend": 0.3,
          "segments": [
            {
              "limit": 12,
              "color": "#5AC8FA"
            },
            {
              "limit": 29,
              "color": "#7BD88F"
            },
            {
              "limit": 34,
              "color": "#FFB340"
            },
            {
              "limit": 40,
              "color": "#FF5A4F"
            }
          ],
          "defaultValue": 24.6,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "greenhouse_climate"
              },
              "valuePath": "temp_c"
            }
          ]
        },
        {
          "type": "gauge",
          "id": "gh-humidity",
          "position": [
            0,
            2
          ],
          "span": [
            3,
            2
          ],
          "label": "Humidity",
          "icon": "humidity.fill",
          "min": 0,
          "max": 100,
          "formatValue": "suffix:%",
          "arcAngle": 270,
          "arcRotation": 135,
          "colorBlend": 0.3,
          "segments": [
            {
              "limit": 45,
              "color": "#FFB340"
            },
            {
              "limit": 85,
              "color": "#5AC8FA"
            },
            {
              "limit": 100,
              "color": "#8E7CFF"
            }
          ],
          "defaultValue": 68,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "greenhouse_climate"
              },
              "valuePath": "humidity_pct"
            }
          ]
        },
        {
          "type": "gauge",
          "id": "gh-co2",
          "position": [
            3,
            0
          ],
          "span": [
            3,
            2
          ],
          "label": "CO₂",
          "icon": "aqi.medium",
          "min": 300,
          "max": 1600,
          "formatValue": "suffix: ppm",
          "gaugeStyle": "half",
          "segments": [
            {
              "limit": 600,
              "color": "#9CC7AA"
            },
            {
              "limit": 1200,
              "color": "#7BD88F"
            },
            {
              "limit": 1600,
              "color": "#FFB340"
            }
          ],
          "defaultValue": 842,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "greenhouse_climate"
              },
              "valuePath": "co2_ppm"
            }
          ]
        },
        {
          "type": "group",
          "id": "gh-actuators",
          "label": "Actuators",
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
              "type": "toggle",
              "id": "gh-vent",
              "position": [
                0,
                0
              ],
              "span": [
                1,
                2
              ],
              "label": "Roof Vent",
              "icon": "wind",
              "tint": "#7BD88F",
              "defaultValue": true,
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "greenhouse_vent_set",
                  "open": "{{value}}"
                }
              },
              "sync": [
                {
                  "method": "meshsocket",
                  "type": "listen",
                  "event": "broadcast",
                  "filter": {
                    "msg_type": "greenhouse_actuators"
                  },
                  "valuePath": "vent_open"
                }
              ]
            },
            {
              "type": "toggle",
              "id": "gh-mister",
              "position": [
                1,
                0
              ],
              "span": [
                1,
                2
              ],
              "label": "Mister",
              "icon": "drop.fill",
              "tint": "#5AC8FA",
              "defaultValue": false,
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "greenhouse_mister_set",
                  "on": "{{value}}"
                }
              },
              "sync": [
                {
                  "method": "meshsocket",
                  "type": "listen",
                  "event": "broadcast",
                  "filter": {
                    "msg_type": "greenhouse_actuators"
                  },
                  "valuePath": "mister_on"
                }
              ]
            }
          ]
        },
        {
          "type": "sparkline",
          "id": "gh-soil",
          "position": [
            6,
            0
          ],
          "span": [
            2,
            4
          ],
          "label": "Soil Moisture · Bed A",
          "tint": "#C8A46E",
          "sparklineFill": true,
          "sparklinePoints": 60,
          "defaultValue": "[41,40,40,39,38,38,37,52,55,54,53,52,51,50,49]",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "greenhouse_soil"
              },
              "valuePath": "moisture_pct"
            }
          ]
        },
        {
          "type": "statusLight",
          "id": "gh-controller",
          "position": [
            8,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "Controller",
          "style": "badge",
          "pulse": true,
          "statusColors": {
            "online": "#7BD88F",
            "degraded": "#FFB340",
            "offline": "#FF5A4F"
          },
          "defaultValue": "online",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "greenhouse_status"
              },
              "valuePath": "controller"
            }
          ]
        },
        {
          "type": "segmentedControl",
          "id": "gh-mode",
          "position": [
            8,
            2
          ],
          "span": [
            1,
            2
          ],
          "options": [
            "auto",
            "manual"
          ],
          "optionLabels": [
            "Auto",
            "Manual"
          ],
          "style": "pills",
          "tint": "#7BD88F",
          "defaultValue": "auto",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "greenhouse_mode_set",
              "mode": "{{value}}"
            }
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "greenhouse_status"
              },
              "valuePath": "mode"
            }
          ]
        }
      ]
    }
  ]
}
```
