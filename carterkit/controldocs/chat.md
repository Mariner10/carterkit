---
type: chat
label: Chat
icon: bubble.left.and.bubble.right.fill
category: controls
defaultSpan: [4, 4]
fields:
  - name: label
    type: string
    description: Header label
  - name: config
    type: object
    description: "ChatConfig: target, showTypingIndicators, showReadReceipts, allowReactions, allowReplies, allowImages, historyCount, tint"
  - name: allowImages
    type: bool
    description: allowImages
    group: config
  - name: allowReactions
    type: bool
    description: allowReactions
    group: config
  - name: allowReplies
    type: bool
    description: allowReplies
    group: config
  - name: historyCount
    type: number
    description: historyCount
    group: config
  - name: showReadReceipts
    type: bool
    description: showReadReceipts
    group: config
  - name: showTypingIndicators
    type: bool
    description: showTypingIndicators
    group: config
  - name: systemMessageEvents
    type: string[]
    description: systemMessageEvents
    group: config
  - name: target
    type: string
    description: target
    group: config
  - name: tint
    type: color
    description: tint
    group: config
themeFields:
  - name: cornerRadius
    type: number
    default: 12
    description: Control corner radius
  - name: surfacePrimary
    type: color
    default: #FFFFFF0F
    description: Background fill
  - name: accentColor
    type: color
    default: #667eea
    description: Accent/tint color
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Secondary text color
  - name: borderColor
    type: color
    default: #FFFFFF1A
    description: Border color
  - name: borderWidth
    type: number
    default: 1
    description: Border width
  - name: labelFontSize
    type: number
    default: 12
    description: Label text size
---

# Chat

A real-time messaging interface that supports sending and receiving messages over MeshSocket. Ideal for device-to-device communication, command logs, or interactive chatbots.

## Type
`"chat"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | falls back to `id` | Header label |
| `config.target` | string | — | MeshSocket peer **name** to route messages to. Set this for companion/bot chat; omit for channel chat |
| `config.showTypingIndicators` | bool | `true` | Show typing bubbles |
| `config.showReadReceipts` | bool | `true` | Show read receipts |
| `config.allowReactions` | bool | `true` | Allow emoji reactions on messages |
| `config.allowReplies` | bool | `true` | Allow threaded replies |
| `config.allowImages` | bool | `false` | Allow image attachments |
| `config.historyCount` | number | `50` | Number of messages to keep in history |
| `config.tint` | string | `"#667eea"` | Chat bubble accent color |

## Examples

### Device-to-device chat
```json
{
  "type": "chat",
  "id": "team-chat",
  "position": [0, 0],
  "span": [4, 4],
  "label": "Team Chat",
  "config": {
    "target": "hub-server",
    "showTypingIndicators": true,
    "showReadReceipts": true,
    "allowReactions": true,
    "allowReplies": true,
    "historyCount": 100
  }
}
```

## Wire Protocol

When `config.target` is set, the chat routes to that peer by name (companion mode):

**Outgoing** — every message you send:
```json
"route_msg_noreply": {
  "target_name": "companion",
  "type": "chat_message",
  "payload": { "text": "your message" }
}
```

**Incoming** — the companion replies with a broadcast the chat listens for:
```json
"broadcast": { "event": "chat_response", "text": "the reply" }
```
The optional `name` / `sender.name` / `from` field on the broadcast sets the reply's display name; otherwise it falls back to the target name.

> The companion (server side) must wait for the MeshSocket welcome before routing — connect, `wait_until_ready()`, then wait for the welcome event before sending.

Without `config.target` (channel mode) the chat sends a `chat_message` event and listens on `chat_message` for the whole channel.

## Related
- [[control-def]] — Base fields
- [[sync]] — Real-time data sync

