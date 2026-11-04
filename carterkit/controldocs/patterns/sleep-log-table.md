---
kind: pattern
id: sleep-log-table
family: trackers-and-logs
title: Nightly log table
intents: ["sleep log", "history of nights", "table of past readings", "daily log with chart", "feed and nap diary"]
parts: [{"type": "chart", "role": "last 7 days"}, {"type": "list", "role": "rows with columns"}]
surfaces: ["app"]
theme: nordic-aurora
rules: ["Chart first, table second: the chart answers “how is it going”, the table answers “what exactly”.", "Cap tables at about 7 rows; older history belongs to the server.", "Format numeric columns (decimal:1) so they align."]
exampleRef: intermediate/baby-monitor
---

A log is read far more than written. Lead with the trend, then give the exact rows below it on the same tab.

## Parts

- **chart** (last 7 days)
- **list** (rows with columns)

## Rules

- Chart first, table second: the chart answers “how is it going”, the table answers “what exactly”.
- Cap tables at about 7 rows; older history belongs to the server.
- Format numeric columns (decimal:1) so they align.

## Example

Derived from `layout-library/intermediate/baby-monitor`. Decodes as a full layout.

```json
{
  "name": "Baby Monitor",
  "id": "sleep-log-table",
  "version": 1,
  "headerTitle": "Nursery · Juniper",
  "accentColor": "#8E8CE0",
  "theme": {
    "accentColor": "#8E8CE0",
    "cornerRadius": 18,
    "fontDesign": "rounded",
    "dark": {
      "pageBackgroundGradient": [
        "#0C0E1C",
        "#161A30"
      ],
      "surfacePrimary": "#E6E8FF14",
      "surfaceSecondary": "#E6E8FF0A",
      "foregroundColor": "#EEF0FF",
      "borderColor": "#C8CCFF1F"
    },
    "light": {
      "pageBackgroundGradient": [
        "#F3F1FB",
        "#E4E6F7"
      ],
      "surfacePrimary": "#FFFFFFE6",
      "surfaceSecondary": "#F7F6FD",
      "foregroundColor": "#1D1B33",
      "borderColor": "#1D1B3314"
    },
    "slider": {
      "trackActiveColor": "#8E8CE0",
      "thumbColor": "#FFFFFF"
    }
  },
  "tabs": [
    {
      "title": "Sleep Log",
      "icon": "list.bullet.clipboard",
      "grid": {
        "columns": 4,
        "rows": 10
      },
      "children": [
        {
          "type": "datePicker",
          "id": "baby-monitor-wake-alarm",
          "position": [
            0,
            0
          ],
          "span": [
            1,
            4
          ],
          "label": "Gentle Wake",
          "datePickerMode": "time",
          "datePickerStyle": "compact",
          "defaultValue": "2026-09-25T06:30:00",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "baby_monitor_set_wake",
              "time": "{{value}}"
            }
          }
        },
        {
          "type": "chart",
          "id": "baby-monitor-sleep-chart",
          "position": [
            1,
            0
          ],
          "span": [
            4,
            4
          ],
          "label": "Nightly Sleep",
          "tint": "#8E8CE0",
          "chartConfig": {
            "showLegend": true,
            "barCornerRadius": 4
          },
          "defaultValue": "{\"categories\":[\"Wed\",\"Thu\",\"Fri\",\"Sat\",\"Sun\",\"Mon\",\"Tue\"],\"series\":[{\"name\":\"Hours\",\"type\":\"bar\",\"color\":\"#8E8CE0\",\"values\":[9.7,8.6,9.8,9.1,10.4,8.9,9.6]},{\"name\":\"Wakes\",\"type\":\"line\",\"color\":\"#FF9F0A\",\"values\":[2,4,1,2,1,3,2]}]}",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "baby_monitor_sleep_history"
              },
              "valuePath": "chart"
            }
          ]
        },
        {
          "type": "list",
          "id": "baby-monitor-sleep-log",
          "position": [
            5,
            0
          ],
          "span": [
            5,
            4
          ],
          "label": "Last 7 Nights",
          "listColumns": [
            {
              "key": "night",
              "label": "Night"
            },
            {
              "key": "down",
              "label": "Down"
            },
            {
              "key": "up",
              "label": "Up"
            },
            {
              "key": "hours",
              "label": "Hrs",
              "format": "decimal:1"
            },
            {
              "key": "wakes",
              "label": "Wakes",
              "format": "number"
            }
          ],
          "defaultValue": "[{\"night\":\"Tue 23\",\"down\":\"19:42\",\"up\":\"06:18\",\"hours\":9.6,\"wakes\":2},{\"night\":\"Mon 22\",\"down\":\"19:55\",\"up\":\"05:47\",\"hours\":8.9,\"wakes\":3},{\"night\":\"Sun 21\",\"down\":\"19:30\",\"up\":\"06:40\",\"hours\":10.4,\"wakes\":1},{\"night\":\"Sat 20\",\"down\":\"20:12\",\"up\":\"06:05\",\"hours\":9.1,\"wakes\":2},{\"night\":\"Fri 19\",\"down\":\"19:48\",\"up\":\"06:22\",\"hours\":9.8,\"wakes\":1},{\"night\":\"Thu 18\",\"down\":\"19:37\",\"up\":\"05:30\",\"hours\":8.6,\"wakes\":4},{\"night\":\"Wed 17\",\"down\":\"19:45\",\"up\":\"06:10\",\"hours\":9.7,\"wakes\":2}]",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "baby_monitor_sleep_log"
              },
              "valuePath": "rows"
            }
          ]
        }
      ]
    }
  ]
}
```
