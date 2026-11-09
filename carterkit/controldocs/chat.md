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
io:
  - emits: message
    when: submit
    title: When you send a message
    field: config.target
    type: string
    says: the message text
    example: "Sample A"
    also: It goes to the MeshSocket peer named in Target, or to the whole channel when Target is empty
    since: next
  - receives: lines
    role: show
    type: json
    shape: {"event": "chat_response", "text": "text", "name": "text?"}
    from: [hub]
    says: a reply broadcast with its text and an optional sender name
    reacts: the reply is added to the bottom of the conversation, shown under the sender name or the Target name
    example: {"text": "Sample A"}
    since: next
  - sample: {"lines": [{"name": "Sample A", "text": "Sample A"}, {"name": "Sample B", "text": "Sample B"}]}
card: {"draws": "card", "padding": "0", "says": "The messages run to the card's edge: the header and the composer carry their own padding, so the card adds none until you set one.", "since": "next"}
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
    type: bool
    description: "No effect yet: the app has no image attachments."
    group: config
    summary: Not wired up yet
    does: Does nothing yet; the chat has no image attachments whichever way this is set.
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
    chip: Chat
    edit: part
    depth: hold
    title: Replies
    type: bool
    description: allowReplies
    group: config
    summary: Lets people reply to a message
    does: Adds a Reply choice to the long-press menu and shows replies in threads when on.
  - name: historyCount
    effect: behavior
    edit: scrub
    depth: hold
    under: label
    title: History
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
    description: "No effect yet: the app does not read it."
    group: config
    summary: Events that show as notices
    does: Does nothing yet; event names listed here are not shown as system notes.
  - name: target
    edit: inline
    depth: surface
    title: Target
    type: string
    description: target
    group: config
    summary: Who to chat with
    does: Sends your messages to the named MeshSocket peer as a private companion chat; leave it empty to chat with the whole channel.
  - name: tint
    type: color
    changes: [{in: next, note: "Fills your bubbles and colors the highlights (the bubble color slot)"}]
    description: "Color of your bubbles and highlights; unset they follow the theme accent."
    group: config
    summary: The color of your messages
    does: Fills your message bubbles and colors names, reply marks and the send arrow; unset, the bubbles keep the theme's accent gradient.
themeFields:
  - use: controlPadding
    since: next
    does: Pads the chat inside its card (default 0, so messages run to the card edge).
  - use: cornerRadius
    summary: How round the card corners are
    does: Rounds the chat card's corners from 0 to 30 pt (default 12).
  - use: surfacePrimary
    does: Fills the card behind the chat with this color, default a faint white wash.
  - use: accentColor
    summary: The main highlight color
    does: Sets the accent color the chat uses for highlights, default a soft indigo.
  - use: secondaryColor
    summary: The softer text color
    does: Colors secondary text such as names and timestamps, default a dimmed white.
  - use: borderColor
    summary: The card's outline color
    does: Colors the outline drawn around the card.
  - use: borderWidth
    does: Sets the card outline from 0 to 5 pt (default 1); 0 hides it.
  - use: labelFontSize
    does: Sets the header label size from 8 to 24 pt (default 12).
  - use: foregroundColor
    does: Colors the main message and label text, default white.
  - use: tertiaryColor
    does: Colors the faintest text and ink, default a very dim white.
colorSlots:
  - slot: bubble
    default: primary
    alias: config.tint
    since: next
    summary: The color of your messages
    does: Fills your message bubbles and colors names, reply marks, read ticks and the send arrow; until the layout picks a color the bubbles keep the theme's accent gradient and the marks follow the primary role.
  - slot: text
    default: neutral
    since: next
    summary: The color of the message text
    does: Colors the words of incoming messages and the message box, the typing dots and the faint bar washes; until set it follows the neutral role, the text color.
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
| `config.allowImages` | bool | `false` | Allow image attachments (no effect yet) |
| `config.allowClear` | bool | `true` | Show the local **Clear Chat** control in the header. Server-driven `chat_clear` frames are honored regardless of this flag |
| `config.historyCount` | number | `50` | Number of messages to keep in history |
| `config.tint` | color | theme accent | Your bubbles and highlights (the `bubble` colour slot) |

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

