---
kind: pattern
id: nested-groups
family: organization-and-nesting
title: Groups inside groups
intents: ["nested sections", "a card within a card", "rooms and devices hierarchy", "sub-sections", "zone with several machines"]
parts: [{"type": "group", "role": "outer zone card"}, {"type": "group", "role": "inner machine card"}]
surfaces: ["app"]
theme: foundry-ember
rules: ["Nest at most two levels; a third makes the cards smaller than a thumb.", "The inner grid is independent: pick its own columns, usually 2.", "Ids stay unique across the whole layout, including inside nested groups."]
exampleRef: advanced/brewery-ops
---

When a tab holds several instances of the same kind of thing (fermenters, rooms, machines), make one outer card per zone and an inner card per instance.

## Parts

- **group** (outer zone card)
- **group** (inner machine card)

## Rules

- Nest at most two levels; a third makes the cards smaller than a thumb.
- The inner grid is independent: pick its own columns, usually 2.
- Ids stay unique across the whole layout, including inside nested groups.

## Example

Derived from `layout-library/advanced/brewery-ops`. Decodes as a full layout.

```json
{
  "name": "Brewery Ops",
  "id": "nested-groups",
  "version": 1,
  "headerTitle": "COPPERLINE · CELLAR",
  "accentColor": "#F2A516",
  "theme": {
    "accentColor": "#F2A516",
    "accentGradient": [
      "#F2A516",
      "#C8661B"
    ],
    "fontFamily": "Avenir Next",
    "fontDesign": "rounded",
    "labelFontSize": 12,
    "valueFontSize": 15,
    "valueFontWeight": "semibold",
    "cornerRadius": 16,
    "cardPadding": 12,
    "borderWidth": 0.5,
    "pageBackgroundGradient": [
      "#0C0703",
      "#1D1106",
      "#2E1B07"
    ],
    "surfacePrimary": "#FFB84D14",
    "surfaceSecondary": "#FFB84D0B",
    "surfaceTertiary": "#FFB84D06",
    "borderColor": "#F2A5162E",
    "foregroundColor": "#FFF1DC",
    "secondaryColor": "#D8B07A",
    "tertiaryColor": "#8C6A55",
    "tabBarTint": "#F2A516",
    "tabBarBackground": "#140C05E6",
    "toggle": {
      "trackActiveColor": "#F2A516"
    },
    "segmented": {
      "selectedColor": "#F2A516",
      "selectedTextColor": "#1D1106"
    }
  },
  "appearance": {
    "colorScheme": "dark",
    "statusBarStyle": "light"
  },
  "tabs": [
    {
      "title": "Cellar",
      "icon": "drop.halffull",
      "grid": {
        "columns": 4,
        "rows": 15
      },
      "children": [
        {
          "type": "symbol",
          "id": "cellar-activity",
          "position": [
            0,
            0
          ],
          "span": [
            3,
            2
          ],
          "systemName": "bubbles.and.sparkles.fill",
          "label": "Active ferment",
          "haptic": "soft",
          "defaultValue": true,
          "symbolConfig": {
            "renderingMode": "palette",
            "palette": [
              "#F2A516",
              "#FFE2A8"
            ],
            "effect": "breathe",
            "effectOptions": [
              "byLayer"
            ],
            "activeWhen": "truthy",
            "tapEffect": "bounce",
            "speed": 0.8,
            "triggers": [
              {
                "event": "broadcast",
                "filter": {
                  "msg_type": "brewery_ops_blowoff"
                },
                "effect": "wiggle"
              }
            ]
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "brewery_ops_cellar"
              },
              "valuePath": "fermenting"
            }
          ]
        },
        {
          "type": "statusLight",
          "id": "glycol-loop",
          "position": [
            0,
            2
          ],
          "span": [
            1,
            2
          ],
          "label": "Glycol loop",
          "style": "badge",
          "pulse": true,
          "statusColors": {
            "nominal": "#7BC67E",
            "warm": "#F2A516",
            "fault": "#D9412B"
          },
          "defaultValue": "nominal",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "brewery_ops_cellar"
              },
              "valuePath": "glycol_state"
            }
          ]
        },
        {
          "type": "label",
          "id": "cellar-ambient",
          "position": [
            1,
            2
          ],
          "span": [
            1,
            2
          ],
          "label": "Cellar ambient",
          "icon": "thermometer.variable",
          "formatValue": "suffix:°F",
          "defaultValue": 58.4,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "brewery_ops_cellar"
              },
              "valuePath": "ambient_f"
            }
          ]
        },
        {
          "type": "label",
          "id": "cellar-co2",
          "position": [
            2,
            2
          ],
          "span": [
            1,
            2
          ],
          "label": "CO₂ room",
          "icon": "aqi.medium",
          "formatValue": "suffix: ppm",
          "defaultValue": 820,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "brewery_ops_cellar"
              },
              "valuePath": "co2_ppm"
            }
          ]
        },
        {
          "type": "group",
          "id": "hall-a",
          "label": "Hall A · Ales",
          "position": [
            3,
            0
          ],
          "span": [
            6,
            4
          ],
          "grid": {
            "columns": 4,
            "rows": 5
          },
          "children": [
            {
              "type": "group",
              "id": "fv1-tank",
              "label": "FV-1 · Hazy IPA",
              "position": [
                0,
                0
              ],
              "span": [
                5,
                2
              ],
              "grid": {
                "columns": 2,
                "rows": 4
              },
              "children": [
                {
                  "type": "gauge",
                  "id": "fv1-temp",
                  "position": [
                    0,
                    0
                  ],
                  "span": [
                    2,
                    2
                  ],
                  "label": "Temp °F",
                  "icon": "thermometer.medium",
                  "min": 30,
                  "max": 85,
                  "gaugeStyle": "half",
                  "step": 0.1,
                  "formatValue": "suffix:°",
                  "colorBlend": 0.35,
                  "segments": [
                    {
                      "limit": 40,
                      "color": "#6FA8DC"
                    },
                    {
                      "limit": 70,
                      "color": "#F2A516"
                    },
                    {
                      "limit": 78,
                      "color": "#E8742A"
                    },
                    {
                      "limit": 85,
                      "color": "#D9412B"
                    }
                  ],
                  "defaultValue": 66.2,
                  "sync": [
                    {
                      "method": "meshsocket",
                      "type": "listen",
                      "event": "broadcast",
                      "filter": {
                        "msg_type": "brewery_ops_tank",
                        "tank": "fv1"
                      },
                      "valuePath": "temp_f"
                    }
                  ]
                },
                {
                  "type": "sparkline",
                  "id": "fv1-gravity",
                  "position": [
                    2,
                    0
                  ],
                  "span": [
                    2,
                    2
                  ],
                  "label": "Gravity SG",
                  "tint": "#F2A516",
                  "sparklinePoints": 96,
                  "sparklineFill": true,
                  "sync": [
                    {
                      "method": "meshsocket",
                      "type": "listen",
                      "event": "broadcast",
                      "filter": {
                        "msg_type": "brewery_ops_tank",
                        "tank": "fv1"
                      },
                      "valuePath": "gravity"
                    }
                  ]
                }
              ]
            },
            {
              "type": "group",
              "id": "fv3-tank",
              "label": "FV-3 · Oat Stout",
              "position": [
                0,
                2
              ],
              "span": [
                5,
                2
              ],
              "grid": {
                "columns": 2,
                "rows": 4
              },
              "children": [
                {
                  "type": "gauge",
                  "id": "fv3-temp",
                  "position": [
                    0,
                    0
                  ],
                  "span": [
                    2,
                    2
                  ],
                  "label": "Temp °F",
                  "icon": "thermometer.medium",
                  "min": 30,
                  "max": 85,
                  "gaugeStyle": "half",
                  "step": 0.1,
                  "formatValue": "suffix:°",
                  "colorBlend": 0.35,
                  "segments": [
                    {
                      "limit": 40,
                      "color": "#6FA8DC"
                    },
                    {
                      "limit": 70,
                      "color": "#F2A516"
                    },
                    {
                      "limit": 78,
                      "color": "#E8742A"
                    },
                    {
                      "limit": 85,
                      "color": "#D9412B"
                    }
                  ],
                  "defaultValue": 68.0,
                  "sync": [
                    {
                      "method": "meshsocket",
                      "type": "listen",
                      "event": "broadcast",
                      "filter": {
                        "msg_type": "brewery_ops_tank",
                        "tank": "fv3"
                      },
                      "valuePath": "temp_f"
                    }
                  ]
                },
                {
                  "type": "sparkline",
                  "id": "fv3-gravity",
                  "position": [
                    2,
                    0
                  ],
                  "span": [
                    2,
                    2
                  ],
                  "label": "Gravity SG",
                  "tint": "#C8661B",
                  "sparklinePoints": 96,
                  "sparklineFill": true,
                  "sync": [
                    {
                      "method": "meshsocket",
                      "type": "listen",
                      "event": "broadcast",
                      "filter": {
                        "msg_type": "brewery_ops_tank",
                        "tank": "fv3"
                      },
                      "valuePath": "gravity"
                    }
                  ]
                }
              ]
            }
          ]
        },
        {
          "type": "group",
          "id": "hall-b",
          "label": "Hall B · Lagers & Farmhouse",
          "position": [
            9,
            0
          ],
          "span": [
            6,
            4
          ],
          "grid": {
            "columns": 4,
            "rows": 5
          },
          "children": [
            {
              "type": "group",
              "id": "fv2-tank",
              "label": "FV-2 · Czech Pils",
              "position": [
                0,
                0
              ],
              "span": [
                5,
                2
              ],
              "grid": {
                "columns": 2,
                "rows": 4
              },
              "children": [
                {
                  "type": "gauge",
                  "id": "fv2-temp",
                  "position": [
                    0,
                    0
                  ],
                  "span": [
                    2,
                    2
                  ],
                  "label": "Temp °F",
                  "icon": "thermometer.medium",
                  "min": 30,
                  "max": 85,
                  "gaugeStyle": "half",
                  "step": 0.1,
                  "formatValue": "suffix:°",
                  "colorBlend": 0.35,
                  "segments": [
                    {
                      "limit": 40,
                      "color": "#6FA8DC"
                    },
                    {
                      "limit": 70,
                      "color": "#F2A516"
                    },
                    {
                      "limit": 78,
                      "color": "#E8742A"
                    },
                    {
                      "limit": 85,
                      "color": "#D9412B"
                    }
                  ],
                  "defaultValue": 50.4,
                  "sync": [
                    {
                      "method": "meshsocket",
                      "type": "listen",
                      "event": "broadcast",
                      "filter": {
                        "msg_type": "brewery_ops_tank",
                        "tank": "fv2"
                      },
                      "valuePath": "temp_f"
                    }
                  ]
                },
                {
                  "type": "sparkline",
                  "id": "fv2-gravity",
                  "position": [
                    2,
                    0
                  ],
                  "span": [
                    2,
                    2
                  ],
                  "label": "Gravity SG",
                  "tint": "#FFD36B",
                  "sparklinePoints": 96,
                  "sparklineFill": true,
                  "sync": [
                    {
                      "method": "meshsocket",
                      "type": "listen",
                      "event": "broadcast",
                      "filter": {
                        "msg_type": "brewery_ops_tank",
                        "tank": "fv2"
                      },
                      "valuePath": "gravity"
                    }
                  ]
                }
              ]
            },
            {
              "type": "group",
              "id": "fv4-tank",
              "label": "FV-4 · Saison",
              "position": [
                0,
                2
              ],
              "span": [
                5,
                2
              ],
              "grid": {
                "columns": 2,
                "rows": 4
              },
              "children": [
                {
                  "type": "gauge",
                  "id": "fv4-temp",
                  "position": [
                    0,
                    0
                  ],
                  "span": [
                    2,
                    2
                  ],
                  "label": "Temp °F",
                  "icon": "thermometer.medium",
                  "min": 30,
                  "max": 85,
                  "gaugeStyle": "half",
                  "step": 0.1,
                  "formatValue": "suffix:°",
                  "colorBlend": 0.35,
                  "segments": [
                    {
                      "limit": 40,
                      "color": "#6FA8DC"
                    },
                    {
                      "limit": 70,
                      "color": "#F2A516"
                    },
                    {
                      "limit": 78,
                      "color": "#E8742A"
                    },
                    {
                      "limit": 85,
                      "color": "#D9412B"
                    }
                  ],
                  "defaultValue": 74.6,
                  "sync": [
                    {
                      "method": "meshsocket",
                      "type": "listen",
                      "event": "broadcast",
                      "filter": {
                        "msg_type": "brewery_ops_tank",
                        "tank": "fv4"
                      },
                      "valuePath": "temp_f"
                    }
                  ]
                },
                {
                  "type": "sparkline",
                  "id": "fv4-gravity",
                  "position": [
                    2,
                    0
                  ],
                  "span": [
                    2,
                    2
                  ],
                  "label": "Gravity SG",
                  "tint": "#E88A3A",
                  "sparklinePoints": 96,
                  "sparklineFill": true,
                  "sync": [
                    {
                      "method": "meshsocket",
                      "type": "listen",
                      "event": "broadcast",
                      "filter": {
                        "msg_type": "brewery_ops_tank",
                        "tank": "fv4"
                      },
                      "valuePath": "gravity"
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```
