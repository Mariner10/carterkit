---
kind: pattern
id: thermostat-stepper
family: home-and-devices
title: Thermostat with stepper setpoint
intents: ["home thermostat", "raise or lower the temperature", "heating and cooling mode", "setpoint with plus and minus", "room temperature control"]
parts: [{"type": "gauge", "role": "current room temperature"}, {"type": "stepper", "role": "target temperature"}, {"type": "segmentedControl", "role": "heat, cool, off mode"}]
surfaces: ["app", "widget"]
theme: nordic-aurora
rules: ["Use a stepper, not a slider, for setpoints people change by one degree.", "Mode is a segmentedControl so every option is visible.", "Show current and target as separate controls; never overwrite one with the other."]
exampleRef: beginner/thermostat-basic
---

A thermostat is one reading, one target and one mode. Keeping them as three separate controls stops the target from being mistaken for the measurement.

## Parts

- **gauge** (current room temperature)
- **stepper** (target temperature)
- **segmentedControl** (heat, cool, off mode)

## Rules

- Use a stepper, not a slider, for setpoints people change by one degree.
- Mode is a segmentedControl so every option is visible.
- Show current and target as separate controls; never overwrite one with the other.

## Example

Derived from `layout-library/beginner/thermostat-basic`. Decodes as a full layout.

```json
{
  "name": "Basic Thermostat",
  "headerTitle": "Living Room",
  "id": "thermostat-stepper",
  "version": 1,
  "accentColor": "#FF8A3D",
  "tabs": [
    {
      "title": "Climate",
      "icon": "thermometer.medium",
      "grid": {
        "columns": 2,
        "rows": 9
      },
      "children": [
        {
          "type": "label",
          "id": "thermo-about",
          "position": [
            0,
            0
          ],
          "span": [
            2,
            2
          ],
          "style": "caption",
          "text": "Learn by example: the gauge listens for thermostat_basic_reading broadcasts (sync + valuePath). The stepper, mode picker, and button each send a thermostat_basic_* broadcast carrying {{value}}.",
          "align": "leading"
        },
        {
          "type": "gauge",
          "id": "thermo-current",
          "position": [
            2,
            0
          ],
          "span": [
            3,
            2
          ],
          "min": 50,
          "max": 90,
          "gaugeStyle": "half",
          "label": "Current °F",
          "icon": "thermometer.medium",
          "defaultValue": 68,
          "segments": [
            {
              "limit": 64,
              "color": "#0A84FF"
            },
            {
              "limit": 76,
              "color": "#34C759"
            },
            {
              "limit": 90,
              "color": "#FF9500"
            }
          ],
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "thermostat_basic_reading"
              },
              "valuePath": "current_f"
            }
          ]
        },
        {
          "type": "stepper",
          "id": "thermo-target",
          "position": [
            5,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "Target °F",
          "icon": "target",
          "min": 60,
          "max": 85,
          "step": 1,
          "repeatOnHold": true,
          "defaultValue": 70,
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "thermostat_basic_set_target",
              "target_f": "{{value}}"
            }
          }
        },
        {
          "type": "segmentedControl",
          "id": "thermo-mode",
          "position": [
            6,
            0
          ],
          "span": [
            1,
            2
          ],
          "options": [
            "heat",
            "cool",
            "off"
          ],
          "optionLabels": [
            "Heat",
            "Cool",
            "Off"
          ],
          "optionIcons": [
            "flame.fill",
            "snowflake",
            "power"
          ],
          "defaultValue": "heat",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "thermostat_basic_set_mode",
              "mode": "{{value}}"
            }
          }
        },
        {
          "type": "divider",
          "id": "thermo-divider",
          "position": [
            7,
            0
          ],
          "span": [
            1,
            2
          ]
        },
        {
          "type": "button",
          "id": "thermo-eco",
          "position": [
            8,
            0
          ],
          "span": [
            1,
            1
          ],
          "label": "Eco 62°",
          "icon": "leaf.fill",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "thermostat_basic_preset",
              "preset": "eco"
            }
          }
        },
        {
          "type": "button",
          "id": "thermo-schedule",
          "position": [
            8,
            1
          ],
          "span": [
            1,
            1
          ],
          "label": "Schedule",
          "icon": "calendar.badge.clock",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "thermostat_basic_preset",
              "preset": "schedule"
            }
          }
        }
      ]
    }
  ]
}
```
