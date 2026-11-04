---
kind: pattern
id: dense-four-column-deck
family: organization-and-nesting
title: Four-column control deck
intents: ["button grid", "control deck", "stream deck layout", "four columns", "many small buttons"]
parts: [{"type": "button", "role": "one-cell scene or action"}, {"type": "toggle", "role": "mic and camera"}, {"type": "statTile", "role": "viewers and health"}]
surfaces: ["app", "controlCenter"]
theme: backstage-blue
rules: ["Four columns is the phone default: size things 1, 2 or 4 columns wide.", "Pair 2 + 2 or 1 + 1 + 2 so every row sums to 4.", "Buttons need at least one row of height; do not shrink below a thumb."]
exampleRef: intermediate/stream-deck
---

The 4-column grid gives quarter, half and full widths. Plan each row to total four and the layout stays aligned.

## Parts

- **button** (one-cell scene or action)
- **toggle** (mic and camera)
- **statTile** (viewers and health)

## Rules

- Four columns is the phone default: size things 1, 2 or 4 columns wide.
- Pair 2 + 2 or 1 + 1 + 2 so every row sums to 4.
- Buttons need at least one row of height; do not shrink below a thumb.

## Example

Derived from `layout-library/intermediate/stream-deck`. Decodes as a full layout.

```json
{
  "name": "Stream Deck",
  "id": "dense-four-column-deck",
  "version": 1,
  "headerTitle": "PIXELVESPER · LIVE",
  "accentColor": "#9B7BFF",
  "theme": {
    "accentColor": "#9B7BFF",
    "cornerRadius": 14,
    "tabBarTint": "#9B7BFF",
    "pageBackgroundGradient": [
      "#0B0914",
      "#170F2A"
    ],
    "surfacePrimary": "#FFFFFF10",
    "surfaceSecondary": "#FFFFFF08",
    "borderColor": "#9B7BFF33",
    "foregroundColor": "#F2EEFF",
    "secondaryColor": "#B4A8D6",
    "toggle": {
      "trackActiveColor": "#34C759"
    },
    "slider": {
      "trackActiveColor": "#9B7BFF"
    }
  },
  "appearance": {
    "colorScheme": "dark",
    "statusBarStyle": "light"
  },
  "tabs": [
    {
      "title": "Live",
      "icon": "dot.radiowaves.left.and.right",
      "grid": {
        "columns": 4,
        "rows": 13
      },
      "children": [
        {
          "type": "statusLight",
          "id": "sd-onair",
          "position": [
            0,
            0
          ],
          "span": [
            1,
            4
          ],
          "label": "Broadcast · twitch.tv/pixelvesper",
          "style": "badge",
          "size": "large",
          "pulse": true,
          "statusColors": {
            "live": "#FF3B5C",
            "starting": "#FFB347",
            "offline": "#8E8E93"
          },
          "defaultValue": "live",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "stream_deck_status"
              },
              "valuePath": "state"
            }
          ]
        },
        {
          "type": "group",
          "id": "sd-grp-scenes",
          "label": "Scenes · OBS",
          "position": [
            1,
            0
          ],
          "span": [
            4,
            4
          ],
          "grid": {
            "columns": 4,
            "rows": 3
          },
          "children": [
            {
              "type": "button",
              "id": "sd-scene-0",
              "position": [
                0,
                0
              ],
              "span": [
                1,
                2
              ],
              "label": "Starting Soon",
              "icon": "clock.fill",
              "style": "tinted",
              "tint": "#9B7BFF",
              "haptic": "medium",
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "stream_deck_scene",
                  "scene": "Starting Soon",
                  "source": "deck"
                }
              }
            },
            {
              "type": "button",
              "id": "sd-scene-1",
              "position": [
                0,
                2
              ],
              "span": [
                1,
                2
              ],
              "label": "Just Chatting",
              "icon": "person.wave.2.fill",
              "style": "tinted",
              "tint": "#5AC8FA",
              "haptic": "medium",
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "stream_deck_scene",
                  "scene": "Just Chatting",
                  "source": "deck"
                }
              }
            },
            {
              "type": "button",
              "id": "sd-scene-2",
              "position": [
                1,
                0
              ],
              "span": [
                1,
                2
              ],
              "label": "Gameplay",
              "icon": "gamecontroller.fill",
              "style": "filled",
              "tint": "#34C759",
              "haptic": "medium",
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "stream_deck_scene",
                  "scene": "Gameplay",
                  "source": "deck"
                }
              }
            },
            {
              "type": "button",
              "id": "sd-scene-3",
              "position": [
                1,
                2
              ],
              "span": [
                1,
                2
              ],
              "label": "Gameplay + Cam",
              "icon": "rectangle.inset.bottomright.filled",
              "style": "tinted",
              "tint": "#2ECC9A",
              "haptic": "medium",
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "stream_deck_scene",
                  "scene": "Gameplay + Cam",
                  "source": "deck"
                }
              }
            },
            {
              "type": "button",
              "id": "sd-scene-4",
              "position": [
                2,
                0
              ],
              "span": [
                1,
                2
              ],
              "label": "BRB",
              "icon": "cup.and.saucer.fill",
              "style": "tinted",
              "tint": "#FFB347",
              "haptic": "medium",
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "stream_deck_scene",
                  "scene": "BRB",
                  "source": "deck"
                }
              }
            },
            {
              "type": "button",
              "id": "sd-scene-5",
              "position": [
                2,
                2
              ],
              "span": [
                1,
                2
              ],
              "label": "Ending",
              "icon": "moon.stars.fill",
              "style": "tinted",
              "tint": "#FF5A8A",
              "haptic": "medium",
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "stream_deck_scene",
                  "scene": "Ending",
                  "source": "deck"
                }
              }
            }
          ]
        },
        {
          "type": "group",
          "id": "sd-grp-sources",
          "label": "Sources",
          "position": [
            5,
            0
          ],
          "span": [
            3,
            4
          ],
          "grid": {
            "columns": 4,
            "rows": 2
          },
          "children": [
            {
              "type": "toggle",
              "id": "sd-mic",
              "position": [
                0,
                0
              ],
              "span": [
                1,
                2
              ],
              "label": "Mic · Shure SM7B",
              "icon": "mic.fill",
              "tint": "#34C759",
              "defaultValue": true,
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "stream_deck_source",
                  "source": "mic",
                  "enabled": "{{value}}"
                }
              }
            },
            {
              "type": "toggle",
              "id": "sd-cam",
              "position": [
                0,
                2
              ],
              "span": [
                1,
                2
              ],
              "label": "Cam · Sony ZV-E10",
              "icon": "video.fill",
              "tint": "#34C759",
              "defaultValue": true,
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "stream_deck_source",
                  "source": "cam",
                  "enabled": "{{value}}"
                }
              }
            },
            {
              "type": "slider",
              "id": "sd-desktop-vol",
              "position": [
                1,
                0
              ],
              "span": [
                1,
                4
              ],
              "label": "Game audio",
              "min": 0,
              "max": 100,
              "step": 1,
              "formatValue": "percent",
              "minIcon": "speaker.fill",
              "maxIcon": "speaker.wave.3.fill",
              "tint": "#9B7BFF",
              "defaultValue": 62,
              "continuous": false,
              "action": {
                "method": "meshsocket",
                "mode": "broadcast",
                "event": "broadcast_request",
                "payload": {
                  "msg_type": "stream_deck_mixer",
                  "channel": "desktop",
                  "level": "{{value}}"
                }
              }
            }
          ]
        },
        {
          "type": "sparkline",
          "id": "sd-viewers",
          "position": [
            8,
            0
          ],
          "span": [
            2,
            4
          ],
          "label": "Viewers",
          "tint": "#9B7BFF",
          "sparklineFill": true,
          "sparklinePoints": 60,
          "defaultValue": "[412,430,455,471,468,502,538,561,549,587,612,640,633,671,698,724]",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "stream_deck_stats"
              },
              "valuePath": "viewers"
            }
          ]
        },
        {
          "type": "gauge",
          "id": "sd-bitrate",
          "position": [
            10,
            0
          ],
          "span": [
            3,
            2
          ],
          "label": "Bitrate · kbps",
          "min": 0,
          "max": 8000,
          "gaugeStyle": "half",
          "icon": "antenna.radiowaves.left.and.right",
          "segments": [
            {
              "limit": 2500,
              "color": "#FF3B5C"
            },
            {
              "limit": 4500,
              "color": "#FFB347"
            },
            {
              "limit": 8000,
              "color": "#34C759"
            }
          ],
          "defaultValue": 6120,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "stream_deck_stats"
              },
              "valuePath": "bitrate_kbps"
            }
          ]
        },
        {
          "type": "gauge",
          "id": "sd-dropped",
          "position": [
            10,
            2
          ],
          "span": [
            3,
            2
          ],
          "label": "Dropped frames · %",
          "min": 0,
          "max": 10,
          "step": 0.1,
          "gaugeStyle": "half",
          "icon": "film.stack",
          "segments": [
            {
              "limit": 1,
              "color": "#34C759"
            },
            {
              "limit": 4,
              "color": "#FFB347"
            },
            {
              "limit": 10,
              "color": "#FF3B5C"
            }
          ],
          "defaultValue": 0.4,
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "stream_deck_stats"
              },
              "valuePath": "dropped_pct"
            }
          ]
        }
      ]
    }
  ]
}
```
