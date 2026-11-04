---
kind: pattern
id: live-event-console
family: trackers-and-logs
title: Live event console
intents: ["show a log", "live console output", "firmware log", "event feed", "tail the server log"]
parts: [{"type": "logConsole", "role": "fills the tab"}]
surfaces: ["app"]
theme: terminal-phosphor
rules: ["Give a logConsole a tab to itself; it wants the whole height.", "Set maxLines (500) so memory stays bounded and autoScroll on for a live tail.", "Colour levels with logColors; keep error and warn clearly distinct."]
exampleRef: intermediate/3d-printer
---

A log is only useful if it is long enough to scroll. Put it on its own last tab so the status tabs stay uncluttered.

## Parts

- **logConsole** (fills the tab)

## Rules

- Give a logConsole a tab to itself; it wants the whole height.
- Set maxLines (500) so memory stays bounded and autoScroll on for a live tail.
- Colour levels with logColors; keep error and warn clearly distinct.

## Example

Derived from `layout-library/intermediate/3d-printer`. Decodes as a full layout.

```json
{
  "name": "3D Printer",
  "id": "live-event-console",
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
      "title": "Console",
      "icon": "terminal.fill",
      "grid": {
        "columns": 4,
        "rows": 8
      },
      "children": [
        {
          "type": "logConsole",
          "id": "p3d-log",
          "position": [
            0,
            0
          ],
          "span": [
            8,
            4
          ],
          "label": "Firmware log",
          "maxLines": 500,
          "fontSize": 11,
          "showTimestamps": true,
          "autoScroll": true,
          "controlHeight": 470,
          "logColors": {
            "error": "#FB5607",
            "warn": "#FFB703",
            "info": "#2EC4B6",
            "debug": "#5C7A78"
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "3d_printer_log"
              },
              "valuePath": "entry"
            }
          ]
        }
      ]
    }
  ]
}
```
