---
kind: pattern
id: doorbell-intercom
family: home-and-devices
title: Doorbell with reply and unlock
intents: ["doorbell and intercom", "who is at the door", "reply to a visitor", "unlock the front door", "visitor message"]
parts: [{"type": "statusLight", "role": "visitor present"}, {"type": "textInput", "role": "quick reply to speaker"}, {"type": "button", "role": "unlock or talk"}]
surfaces: ["app", "lockScreen"]
theme: backstage-blue
rules: ["The unlock button is its own control with a confirm, never next to a text field.", "Show visitor state at the top so the page is readable at a glance.", "Replies go through a textInput action, not a button per phrase."]
exampleRef: beginner/doorbell-intercom
---

A doorbell page answers one question first (is someone there) and then offers the two actions people take: talk and let them in.

## Parts

- **statusLight** (visitor present)
- **textInput** (quick reply to speaker)
- **button** (unlock or talk)

## Rules

- The unlock button is its own control with a confirm, never next to a text field.
- Show visitor state at the top so the page is readable at a glance.
- Replies go through a textInput action, not a button per phrase.

## Example

Derived from `layout-library/beginner/doorbell-intercom`. Decodes as a full layout.

```json
{
  "name": "Doorbell Intercom",
  "headerTitle": "Front Door",
  "id": "doorbell-intercom",
  "version": 1,
  "accentColor": "#30B0C7",
  "tabs": [
    {
      "title": "Intercom",
      "icon": "bell.and.waves.left.and.right",
      "grid": {
        "columns": 2,
        "rows": 8,
        "rowHeight": 56
      },
      "children": [
        {
          "type": "statusLight",
          "id": "visitor-state",
          "position": [
            0,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "Front Porch",
          "style": "badge",
          "size": "large",
          "pulse": true,
          "defaultValue": "ringing",
          "statusColors": {
            "idle": "#8E8E93",
            "ringing": "#FF9F0A",
            "talking": "#30B0C7",
            "unlocked": "#34C759"
          },
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "doorbell_intercom_state"
              },
              "valuePath": "visitor"
            }
          ]
        },
        {
          "type": "label",
          "id": "visitor-detail",
          "position": [
            1,
            0
          ],
          "span": [
            1,
            2
          ],
          "icon": "person.crop.circle.badge.clock",
          "style": "caption",
          "text": "Doorbell pressed at 4:18 PM - package courier",
          "sync": [
            {
              "method": "meshsocket",
              "type": "listen",
              "event": "broadcast",
              "filter": {
                "msg_type": "doorbell_intercom_state"
              },
              "valuePath": "detail"
            }
          ]
        },
        {
          "type": "button",
          "id": "talk",
          "position": [
            2,
            0
          ],
          "span": [
            1,
            1
          ],
          "label": "Talk",
          "icon": "mic.fill",
          "style": "tinted",
          "tint": "#30B0C7",
          "haptic": "light",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "doorbell_intercom_command",
              "command": "talk"
            }
          }
        },
        {
          "type": "button",
          "id": "unlock",
          "position": [
            2,
            1
          ],
          "span": [
            1,
            1
          ],
          "label": "Unlock",
          "icon": "lock.open.fill",
          "style": "filled",
          "tint": "#34C759",
          "haptic": "heavy",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "doorbell_intercom_command",
              "command": "unlock"
            }
          }
        },
        {
          "type": "textInput",
          "id": "quick-message",
          "position": [
            3,
            0
          ],
          "span": [
            2,
            2
          ],
          "label": "Quick message",
          "icon": "text.bubble",
          "placeholder": "Leave it by the side gate, thanks!",
          "autocorrect": true,
          "clearOnSubmit": true,
          "tint": "#30B0C7",
          "action": {
            "method": "meshsocket",
            "mode": "broadcast",
            "event": "broadcast_request",
            "payload": {
              "msg_type": "doorbell_intercom_message",
              "text": "{{value}}"
            }
          }
        },
        {
          "type": "divider",
          "id": "about-divider",
          "position": [
            5,
            0
          ],
          "span": [
            1,
            2
          ],
          "label": "About this layout",
          "tint": "#8E8E93"
        },
        {
          "type": "label",
          "id": "about",
          "position": [
            6,
            0
          ],
          "span": [
            2,
            2
          ],
          "style": "caption",
          "text": "Talk and Unlock send a doorbell_intercom_command. Typing a message and pressing Return sends it as {{value}}, spoken at the door. One doorbell_intercom_state broadcast updates both the light (visitor) and the caption (detail)."
        }
      ]
    }
  ]
}
```
