---
kind: pattern
id: full-page-flow
family: organization-and-nesting
title: Full-page content in flow mode
intents: ["full screen map", "one big list on a tab", "chat tab", "page that is just a log", "scrolling content"]
parts: [{"type": "logConsole", "role": "single control filling the page"}]
surfaces: ["app"]
theme: mission-control-69
rules: ["Set grid mode to flow when one control (map, chat, list, log) is the whole tab.", "In flow mode rowSpan is ignored and heights are natural.", "Keep mixed dashboards in the default 2-D grid mode."]
exampleRef: advanced/drone-ground-station
---

The 2-D grid suits dashboards. A single scrolling control is simpler in flow mode and sizes itself.

## Parts

- **logConsole** (single control filling the page)

## Rules

- Set grid mode to flow when one control (map, chat, list, log) is the whole tab.
- In flow mode rowSpan is ignored and heights are natural.
- Keep mixed dashboards in the default 2-D grid mode.

## Example

Derived from `layout-library/advanced/drone-ground-station`. Decodes as a full layout.

```json
{
  "name": "Drone Ground Station",
  "id": "full-page-flow",
  "version": 1,
  "headerTitle": "HX-4 · GROUND",
  "accentColor": "#00E5FF",
  "theme": {
    "accentColor": "#00E5FF",
    "accentGradient": [
      "#00E5FF",
      "#0A84FF"
    ],
    "fontDesign": "monospaced",
    "cornerRadius": 10,
    "cardPadding": 12,
    "borderWidth": 0.5,
    "labelFontSize": 11,
    "valueFontSize": 14,
    "valueFontWeight": "semibold",
    "tabBarTint": "#00E5FF",
    "pageBackgroundGradient": [
      "#03070C",
      "#081421",
      "#0C1E2E"
    ],
    "surfacePrimary": "#7FDBFF12",
    "surfaceSecondary": "#7FDBFF0A",
    "surfaceTertiary": "#7FDBFF06",
    "borderColor": "#7FDBFF2E",
    "foregroundColor": "#E6F7FF",
    "secondaryColor": "#8FB8CC",
    "tertiaryColor": "#557A8C",
    "toggle": {
      "trackActiveColor": "#FF453A"
    },
    "slider": {
      "trackActiveColor": "#00E5FF",
      "thumbColor": "#E6F7FF"
    }
  },
  "appearance": {
    "colorScheme": "dark",
    "statusBarStyle": "light"
  },
  "tabs": [
    {
      "title": "Flight",
      "icon": "map.fill",
      "grid": {
        "columns": 4,
        "rows": 12
      },
      "children": [
        {
          "type": "map",
          "id": "dgs-map",
          "position": [
            0,
            0
          ],
          "span": [
            6,
            4
          ],
          "label": "Flight path · Marymoor Field",
          "mapStyle": "hybrid",
          "mapZoom": 0.008,
          "tint": "#00E5FF",
          "mapConfig": {
            "recenter": "auto"
          },
          "defaultValue": "{\"markers\": [{\"coordinate\": [47.6421, -122.1376], \"color\": \"#34C759\", \"size\": 14, \"label\": \"Home\"}, {\"coordinate\": [47.6433, -122.1359], \"color\": \"#FFD60A\", \"size\": 10, \"label\": \"WP1\"}, {\"coordinate\": [47.6447, -122.1362], \"color\": \"#FFD60A\", \"size\": 10, \"label\": \"WP2\"}, {\"coordinate\": [47.6452, -122.1384], \"color\": \"#FFD60A\", \"size\": 10, \"label\": \"WP3\"}, {\"coordinate\": [47.6444, -122.1373], \"color\": \"#00E5FF\", \"size\": 18, \"label\": \"HX-4 \\u00b7 62 m\", \"ripple\": {\"color\": \"#00E5FF\", \"period\": 1.6, \"radius\": 40}}], \"paths\": [{\"points\": [[47.6421, -122.1376], [47.6433, -122.1359], [47.6447, -122.1362], [47.6452, -122.1384], [47.644, -122.1401], [47.6426, -122.1395]], \"color\": \"#FFD60A80\"}, {\"points\": [[47.6421, -122.1376], [47.6433, -122.1359], [47.6447, -122.1362], [47.6444, -122.1373]], \"color\": \"#00E5FF\"}]}",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "drone_ground_station_position"
              },
              "valuePath": "map"
            }
          ]
        },
        {
          "type": "compass",
          "id": "dgs-compass",
          "position": [
            6,
            0
          ],
          "span": [
            4,
            2
          ],
          "label": "Heading · point to yaw",
          "defaultValue": 38,
          "compassConfig": {
            "tolerance": 12,
            "dwell": 1.5,
            "editable": false,
            "pucks": [
              {
                "id": "wp1",
                "label": "WP1",
                "icon": "1.circle.fill",
                "tint": "#FFD60A",
                "bearing": 45,
                "locked": true,
                "action": {
                  "method": "meshsocket",
                  "mode": "broadcast",
                  "event": "broadcast_request",
                  "payload": {
                    "msg_type": "drone_ground_station_yaw_to",
                    "target": "{{value}}"
                  }
                }
              },
              {
                "id": "wp3",
                "label": "WP3",
                "icon": "3.circle.fill",
                "tint": "#FFD60A",
                "bearing": 320,
                "locked": true,
                "action": {
                  "method": "meshsocket",
                  "mode": "broadcast",
                  "event": "broadcast_request",
                  "payload": {
                    "msg_type": "drone_ground_station_yaw_to",
                    "target": "{{value}}"
                  }
                }
              },
              {
                "id": "home",
                "label": "Home",
                "icon": "house.fill",
                "tint": "#34C759",
                "bearing": 200,
                "locked": true,
                "action": {
                  "method": "meshsocket",
                  "mode": "broadcast",
                  "event": "broadcast_request",
                  "payload": {
                    "msg_type": "drone_ground_station_yaw_to",
                    "target": "{{value}}"
                  }
                }
              }
            ]
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "drone_ground_station_attitude"
              },
              "valuePath": "heading_deg"
            }
          ]
        },
        {
          "type": "gauge",
          "id": "dgs-alt",
          "position": [
            6,
            2
          ],
          "span": [
            2,
            2
          ],
          "label": "Altitude AGL",
          "icon": "arrow.up.to.line",
          "min": 0,
          "max": 120,
          "step": 0.1,
          "formatValue": "suffix: m",
          "segments": [
            {
              "limit": 100,
              "color": "#00E5FF"
            },
            {
              "limit": 120,
              "color": "#FF9F0A"
            }
          ],
          "colorBlend": 0.3,
          "defaultValue": 62.4,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "drone_ground_station_telemetry"
              },
              "valuePath": "alt_agl"
            }
          ]
        },
        {
          "type": "gauge",
          "id": "dgs-batt",
          "position": [
            8,
            2
          ],
          "span": [
            2,
            2
          ],
          "label": "Battery",
          "icon": "battery.75percent",
          "min": 0,
          "max": 100,
          "formatValue": "suffix:%",
          "segments": [
            {
              "limit": 20,
              "color": "#FF453A"
            },
            {
              "limit": 35,
              "color": "#FF9F0A"
            },
            {
              "limit": 100,
              "color": "#30D158"
            }
          ],
          "defaultValue": 71,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "drone_ground_station_telemetry"
              },
              "valuePath": "battery_pct"
            }
          ]
        },
        {
          "type": "group",
          "id": "dgs-link",
          "position": [
            10,
            0
          ],
          "span": [
            2,
            4
          ],
          "grid": {
            "columns": 3,
            "rows": 1
          },
          "children": [
            {
              "type": "statusLight",
              "id": "dgs-rc",
              "position": [
                0,
                0
              ],
              "span": [
                1,
                1
              ],
              "label": "RC 2.4G",
              "style": "badge",
              "statusColors": {
                "strong": "#30D158",
                "weak": "#FF9F0A",
                "lost": "#FF453A"
              },
              "defaultValue": "strong",
              "sync": [
                {
                  "method": "meshsocket",
                  "type": "listen",
                  "event": "broadcast",
                  "filter": {
                    "msg_type": "drone_ground_station_link"
                  },
                  "valuePath": "rc"
                }
              ]
            },
            {
              "type": "statusLight",
              "id": "dgs-video",
              "position": [
                0,
                1
              ],
              "span": [
                1,
                1
              ],
              "label": "Video 5.8G",
              "style": "badge",
              "statusColors": {
                "strong": "#30D158",
                "weak": "#FF9F0A",
                "lost": "#FF453A"
              },
              "defaultValue": "weak",
              "pulse": true,
              "sync": [
                {
                  "method": "meshsocket",
                  "type": "listen",
                  "event": "broadcast",
                  "filter": {
                    "msg_type": "drone_ground_station_link"
                  },
                  "valuePath": "video"
                }
              ]
            },
            {
              "type": "statusLight",
              "id": "dgs-geofence",
              "position": [
                0,
                2
              ],
              "span": [
                1,
                1
              ],
              "label": "Geofence",
              "style": "badge",
              "statusColors": {
                "inside": "#30D158",
                "edge": "#FF9F0A",
                "breach": "#FF453A"
              },
              "defaultValue": "inside",
              "sync": [
                {
                  "method": "meshsocket",
                  "type": "listen",
                  "event": "broadcast",
                  "filter": {
                    "msg_type": "drone_ground_station_link"
                  },
                  "valuePath": "geofence"
                }
              ]
            }
          ],
          "label": "Link health"
        }
      ]
    },
    {
      "title": "Log",
      "icon": "terminal.fill",
      "grid": {
        "columns": 4,
        "rows": 2,
        "mode": "flow"
      },
      "children": [
        {
          "type": "label",
          "id": "dgs-log-hdr",
          "position": [
            0,
            0
          ],
          "span": [
            1,
            4
          ],
          "label": "MAVLink",
          "text": "HX-4 · sysid 1 · 57600 baud",
          "icon": "terminal",
          "style": "mono",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "drone_ground_station_status"
              },
              "valuePath": "link_text"
            }
          ]
        },
        {
          "type": "logConsole",
          "id": "dgs-log",
          "position": [
            1,
            0
          ],
          "span": [
            1,
            4
          ],
          "label": "Flight log",
          "maxLines": 400,
          "fontSize": 11,
          "controlHeight": 520,
          "logColors": {
            "error": "#FF453A",
            "warn": "#FF9F0A",
            "info": "#30D158",
            "debug": "#8E8E93"
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "drone_ground_station_log"
              },
              "valuePath": "line"
            }
          ]
        }
      ]
    }
  ]
}
```
