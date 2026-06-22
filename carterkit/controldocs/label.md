---
type: label
label: Label
icon: textformat
category: controls
defaultSpan: [1, 2]
fields:
  - name: text
    type: string
    description: Static display text (overridden by sync)
  - name: label
    type: string
    description: Alternative to text
  - name: icon
    type: string
    description: SF Symbol before text
  - name: style
    type: enum
    values: [default, headline, title, caption, mono, large-mono]
    default: default
    description: Text style variant
  - name: tint
    type: color
    default: "#FFFFFF"
    description: Text and icon color
  - name: align
    type: enum
    values: [leading, center, trailing]
    default: leading
    description: Text alignment
  - name: formatValue
    type: string
    description: Value display format (see formatValue table)
themeFields:
  - name: controlPadding
    type: number
    default: 8
    description: Internal padding
  - name: foregroundColor
    type: color
    default: #FFFFFF
    description: Primary text color
---

# Label

A read-only text display. Shows static text or synced dynamic text. Stores a `.string` value when synced.

## Type
`"label"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `text` | string | — | Static display text (overridden by sync) |
| `label` | string | — | Alternative to `text` |
| `icon` | string | — | SF Symbol before text |
| `style` | string | `"default"` | See [[style-properties#Label Styles]] |
| `tint` | string | white | Text and icon color |
| `align` | string | `"leading"` | `"leading"`, `"center"`, `"trailing"` |
| `formatValue` | string | — | Value display format (see formatValue table below) |

## Format Values

| Value | Output | Example |
|-------|--------|---------|
| `"decimal"` | `"72"` or `"3.5"` | Rounds to integer |
| `"decimal:N"` | `"3.14"` | Fixed N decimal places (e.g., `"decimal:2"`) |
| `"percent"` | `"80%"` | Integer percentage |
| `"time"` | `"3:45"` | Minutes:seconds from total seconds |
| `"duration"` | `"1h 23m"` | Human-readable duration from seconds |
| `"bytes"` | `"1.2 GB"` | Auto-scaled byte units |
| `"bps"` | `"54 Mbps"` | Auto-scaled bits-per-second |
| `"suffix:X"` | `"72°F"` | Append custom suffix (e.g., `"suffix:°F"`) |
| `"none"` | (hidden) | No value display |

## Styles

| Value | Font |
|-------|------|
| `"default"` | `.subheadline` |
| `"headline"` | `.headline.bold` |
| `"title"` | `.title2.bold` |
| `"caption"` | `.caption` |
| `"mono"` | `.subheadline` monospaced |
| `"large-mono"` | `.title3` monospaced medium |

## Examples

### Static info label
```json
{
  "type": "label",
  "id": "temp-display",
  "position": [0, 0],
  "span": [1, 2],
  "text": "Current: 72°F"
}
```

### Synced label with icon
```json
{
  "type": "label",
  "id": "track-artist",
  "position": [1, 2],
  "span": [1, 2],
  "text": "—",
  "icon": "person.fill",
  "tint": "#AAAAAA",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "player_state" }, "valuePath": "artist" }]
}
```

### Headline style
```json
{
  "type": "label",
  "id": "track-title",
  "position": [0, 2],
  "span": [1, 2],
  "text": "No Track",
  "style": "headline",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "player_state" }, "valuePath": "title" }]
}
```

## Behavior
- When synced, the `text` field serves as a placeholder until the first sync value arrives
- Text updates animate with a smooth numeric content transition
- Labels have no action — they are display-only

## Related
- [[shared-properties]] — Base fields
- [[style-properties#Label Styles]] — Style variants
- [[sync]] — Live value updates
