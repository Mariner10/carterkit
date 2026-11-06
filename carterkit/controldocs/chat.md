---
type: chat
label: Chat
icon: bubble.left.and.bubble.right.fill
category: controls
defaultSpan: [4, 4]
addIntent: show
pickerCategory: Readouts
friendlyName: Chat
oneLiner: Messages back and forth
aliases: [messages, conversation, assistant, ai, talk, inbox]
depth: complete
starterPreset: {"label": "Chat"}
fields:
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label
    summary: The name shown above the chat
    does: Shows this text in the chat's header bar.
  - name: config
    type: object
    description: "ChatConfig: target, showTypingIndicators, showReadReceipts, allowReactions, allowReplies, allowImages, historyCount, tint"
    summary: Chat settings grouped together
    does: Holds the chat's options (target, typing dots, receipts, reactions, replies, images, history, color) in one object.
  - name: allowClear
    type: bool
    description: "Show the local \"Clear Chat\" affordance in the header (default true). Server-driven clears are always honored regardless."
    group: config
    summary: Lets you wipe the chat from here
    does: Shows a Clear Chat menu in the header that empties this device's messages only; other people's windows are untouched.
  - name: allowImages
    effect: behavior
    edit: part
    depth: hold
    title: Images
    type: bool
    description: allowImages
    group: config
    summary: Lets people attach pictures
    does: Turns image attachments on or off for this chat.
  - name: allowReactions
    edit: part
    depth: hold
    title: Reactions
    type: bool
    description: allowReactions
    group: config
    summary: Lets people react to messages
    does: Adds a React choice to the long-press menu and shows emoji reactions on messages when on.
  - name: allowReplies
    edit: part
    depth: hold
    title: Replies
    type: bool
    description: allowReplies
    group: config
    summary: Lets people reply to a message
    does: Adds a Reply choice to the long-press menu and shows replies in threads when on.
  - name: historyCount
    min: 1
    max: 50
    step: 1
    type: number
    description: historyCount
    group: config
    summary: How many messages are kept
    does: Keeps only this many of the latest messages (1 to 50, default 50) in the window and in history sent to peers.
  - name: showReadReceipts
    edit: part
    depth: hold
    title: Read receipts
    type: bool
    description: showReadReceipts
    group: config
    summary: Shows when messages are delivered
    does: Shows delivery and read marks under your messages when on.
  - name: showTypingIndicators
    edit: part
    depth: hold
    title: Typing dots
    type: bool
    description: showTypingIndicators
    group: config
    summary: Shows when someone is typing
    does: Shows animated typing dots while the other side is typing when on.
  - name: systemMessageEvents
    type: string[]
    description: systemMessageEvents
    group: config
    summary: Events that show as notices
    does: Lists event names meant to appear as system notes in the chat; the app does not act on it yet.
  - name: target
    type: string
    description: target
    group: config
    summary: Who to chat with
    does: Sends your messages to the named MeshSocket peer as a private companion chat; leave it empty to chat with the whole channel.
  - name: tint
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    description: tint
    group: config
    summary: The chat's accent color
    does: Sets the accent color used by the chat bubbles.
themeFields:
  - use: cornerRadius
    summary: How round the card corners are
    does: Rounds the chat card's corners from 0 to 30 pt (default 12).
  - name: surfacePrimary
    title: Background color
    type: color
    default: #FFFFFF0F
    description: Background fill
    summary: The card's fill color
    does: Fills the card behind the chat with this color, default a faint white wash.
  - name: accentColor
    title: Accent color
    type: color
    default: #667eea
    description: Accent/tint color
    summary: The main highlight color
    does: Sets the accent color the chat uses for highlights, default a soft indigo.
  - name: secondaryColor
    title: Second text color
    type: color
    default: #FFFFFF99
    description: Secondary text color
    summary: The softer text color
    does: Colors secondary text such as names and timestamps, default a dimmed white.
  - name: borderColor
    title: Border color
    type: color
    default: #FFFFFF1A
    description: Border color
    summary: The card's outline color
    does: Colors the outline drawn around the card.
  - name: borderWidth
    title: Border thickness
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
    summary: How thick the outline is
    does: Sets the card outline from 0 to 5 pt (default 1); 0 hides it.
  - name: labelFontSize
    title: Title text size
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
    summary: How big the title is
    does: Sets the header label size from 8 to 24 pt (default 12).
  - use: foregroundColor
    does: Colors the main message and label text, default white.
  - use: tertiaryColor
    does: Colors the faintest text and ink, default a very dim white.
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
| `config.allowClear` | bool | `true` | Show the local **Clear Chat** control in the header. Server-driven `chat_clear` frames are honored regardless of this flag |
| `config.historyCount` | number | `50` | Number of messages to keep in history |
| `config.tint` | string | `"#667eea"` | Chat bubble accent color |

## Message actions (long-press)

Long-press any message bubble for an iMessage-style menu: **Copy** (the message text),
**Reply** (when `allowReplies`), **React** (emoji, when `allowReactions`), and **Delete**
(removes it from *this* device's window only). The old tap-to-reveal reaction bar is gone —
reactions now live in this menu.

## Clearing the window

Two independent ways to wipe the log:

- **Local** — the header's **Clear Chat** menu (shown when `config.allowClear` is true, the
  default) empties this device's window only. It does **not** notify peers.
- **Server-driven** — the channel/companion **authority** clears every member's window by
  emitting a `chat_clear` frame. In channel mode it rides the shared `broadcast` multiplexer
  like every other chat frame; in companion (`config.target`) mode it arrives as a broadcast:

  ```json
  // channel mode
  "broadcast_request": { "msg_type": "chat_clear", "chatId": "team-chat" }
  // companion mode
  "broadcast": { "event": "chat_clear" }
  ```

  An **absent `chatId`** clears every chat control on the channel; a present one targets just
  that control's `id`. `chat_clear` is **wire API** — never rename it.

## Examples

### Device-to-device chat
Chat with a hub peer, with typing dots, receipts, reactions and replies on, and a long history.
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

### Companion chat
Talk privately to one named peer, with no images and a short history.
```json
{
  "type": "chat",
  "id": "companion-chat",
  "position": [0, 0],
  "span": [4, 4],
  "label": "Assistant",
  "config": {
    "target": "companion",
    "allowImages": false,
    "allowReplies": false,
    "historyCount": 20
  }
}
```

### Quiet read-only log
Show channel messages without typing dots, receipts, reactions or a Clear Chat control.
```json
{
  "type": "chat",
  "id": "channel-log",
  "position": [4, 0],
  "span": [4, 4],
  "label": "Channel Log",
  "config": {
    "showTypingIndicators": false,
    "showReadReceipts": false,
    "allowReactions": false,
    "allowReplies": false,
    "allowClear": false,
    "tint": "#34C759"
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

