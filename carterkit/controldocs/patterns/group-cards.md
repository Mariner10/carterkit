---
kind: pattern
id: group-cards
family: organization-and-nesting
title: Group related controls into cards
intents: ["group related controls", "card with a heading", "status box", "cluster of readouts", "section of a screen"]
parts: [{"type": "group", "role": "titled glass card with its own grid"}, {"type": "label", "role": "status lines inside the card"}]
surfaces: ["app"]
theme: grouped
rules: ["A group has its own grid; children’s positions are relative to the group.", "Use a group when 2-6 controls share a title or a visibility rule; otherwise leave them on the tab grid.", "Span the group by the space its content needs, not the whole row."]
exampleRef: intermediate/3d-printer
---

A group is a labelled card. Use it to say “these belong together”, or to hide, enable or theme a cluster as one unit.

## Parts

- **group** (titled glass card with its own grid)
- **label** (status lines inside the card)

## Rules

- A group has its own grid; children’s positions are relative to the group.
- Use a group when 2-6 controls share a title or a visibility rule; otherwise leave them on the tab grid.
- Span the group by the space its content needs, not the whole row.

## Example

Derived from `layout-library/intermediate/3d-printer`. Decodes as a full layout.

```json
{
  "name": "3D Printer",
  "id": "group-cards",
  "version": 1,
  "headerTitle": "PRUSA MK4 · BAY 2",
  "accentColor": "#2EC4B6",
  "theme": {
    "accentColor": "#2EC4B6",
    "accentGradient": [
      "#2EC4B6",
      "#9BF6FF"
    ],
    "cornerRadius": 14,
    "tabBarTint": "#2EC4B6",
    "pageBackgroundGradient": [
      "#061214",
      "#0B1E22",
      "#10292E"
    ],
    "surfacePrimary": "#9BF6FF12",
    "surfaceSecondary": "#9BF6FF0A",
    "borderColor": "#9BF6FF2B",
    "foregroundColor": "#EAFBFA",
    "secondaryColor": "#8FB8B5"
  },
  "appearance": {
    "colorScheme": "dark",
    "statusBarStyle": "light"
  },
  "tabs": [
    {
      "title": "Print",
      "icon": "cube.fill",
      "grid": {
        "columns": 4,
        "rows": 10
      },
      "children": [
        {
          "type": "label",
          "id": "p3d-job-name",
          "position": [
            0,
            0
          ],
          "span": [
            1,
            4
          ],
          "style": "headline",
          "icon": "doc.text",
          "text": "benchy_hull_0.2mm_PETG.gcode",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "3d_printer_job"
              },
              "valuePath": "file"
            }
          ]
        },
        {
          "type": "progressRing",
          "id": "p3d-job-progress",
          "position": [
            1,
            0
          ],
          "span": [
            3,
            2
          ],
          "min": 0,
          "max": 100,
          "progressStyle": "ring",
          "tint": "#2EC4B6",
          "label": "Job",
          "icon": "printer.fill",
          "defaultValue": 62,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "3d_printer_job"
              },
              "valuePath": "percent"
            }
          ]
        },
        {
          "type": "group",
          "id": "p3d-status-group",
          "label": "Status",
          "position": [
            1,
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
              "type": "label",
              "id": "p3d-layer",
              "position": [
                0,
                0
              ],
              "span": [
                1,
                2
              ],
              "style": "mono",
              "icon": "square.stack.3d.up",
              "text": "Layer 148 / 240",
              "sync": [
                {
                  "method": "meshsocket",
                  "type": "listen",
                  "event": "broadcast",
                  "filter": {
                    "msg_type": "3d_printer_job"
                  },
                  "valuePath": "layer_text"
                }
              ]
            },
            {
              "type": "label",
              "id": "p3d-eta",
              "position": [
                1,
                0
              ],
              "span": [
                1,
                2
              ],
              "style": "mono",
              "icon": "clock",
              "text": "ETA 1h 42m",
              "sync": [
                {
                  "method": "meshsocket",
                  "type": "listen",
                  "event": "broadcast",
                  "filter": {
                    "msg_type": "3d_printer_job"
                  },
                  "valuePath": "eta_text"
                }
              ]
            }
          ]
        },
        {
          "type": "gauge",
          "id": "p3d-nozzle-temp",
          "position": [
            4,
            0
          ],
          "span": [
            3,
            2
          ],
          "label": "Nozzle",
          "icon": "flame.fill",
          "min": 0,
          "max": 300,
          "arcAngle": 270,
          "arcRotation": 135,
          "formatValue": "suffix:°C",
          "colorBlend": 0.3,
          "segments": [
            {
              "limit": 170,
              "color": "#3A7CA5"
            },
            {
              "limit": 250,
              "color": "#2EC4B6"
            },
            {
              "limit": 280,
              "color": "#FFB703"
            },
            {
              "limit": 300,
              "color": "#FB5607"
            }
          ],
          "defaultValue": 238,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "3d_printer_temps"
              },
              "valuePath": "nozzle_c"
            }
          ]
        },
        {
          "type": "gauge",
          "id": "p3d-bed-temp",
          "position": [
            4,
            2
          ],
          "span": [
            3,
            2
          ],
          "label": "Bed",
          "icon": "square.3.layers.3d.bottom.filled",
          "min": 0,
          "max": 120,
          "arcAngle": 270,
          "arcRotation": 135,
          "formatValue": "suffix:°C",
          "colorBlend": 0.3,
          "segments": [
            {
              "limit": 50,
              "color": "#3A7CA5"
            },
            {
              "limit": 90,
              "color": "#2EC4B6"
            },
            {
              "limit": 110,
              "color": "#FFB703"
            },
            {
              "limit": 120,
              "color": "#FB5607"
            }
          ],
          "defaultValue": 85,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "3d_printer_temps"
              },
              "valuePath": "bed_c"
            }
          ]
        },
        {
          "type": "sparkline",
          "id": "p3d-nozzle-trend",
          "position": [
            7,
            0
          ],
          "span": [
            2,
            4
          ],
          "label": "Nozzle · last 5 min",
          "tint": "#2EC4B6",
          "sparklinePoints": 120,
          "sparklineFill": true,
          "defaultValue": 238,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "3d_printer_temps"
              },
              "valuePath": "nozzle_c"
            }
          ]
        },
        {
          "type": "button",
          "id": "p3d-pause",
          "position": [
            9,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "Pause",
          "icon": "pause.fill",
          "style": "tinted",
          "tint": "#FFB703",
          "haptic": "medium",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "3d_printer_command",
              "command": "pause",
              "job": "benchy_hull_0.2mm_PETG.gcode"
            }
          }
        },
        {
          "type": "button",
          "id": "p3d-cancel",
          "position": [
            9,
            2
          ],
          "span": [
            1,
            2
          ],
          "label": "Cancel",
          "icon": "xmark.octagon.fill",
          "style": "tinted",
          "tint": "#FB5607",
          "haptic": "warning",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "3d_printer_command",
              "command": "cancel",
              "job": "benchy_hull_0.2mm_PETG.gcode"
            }
          }
        }
      ]
    }
  ]
}
```
