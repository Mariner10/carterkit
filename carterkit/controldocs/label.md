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
    values: [default, headline, title, caption, mono, large-mono, terminal]
    default: default
    description: Text style variant (terminal = ANSI terminal renderer)
  - name: tint
    type: color
    default: "#FFFFFF"
    description: Text and icon color
  - name: align
    type: enum
    values: [leading, center, trailing]
    default: leading
    description: Text alignment
  - name: scrollable
    type: bool
    default: false
    description: Fixed-height scrolling terminal/log view that keeps the latest line in view (pair with controlHeight)
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
| `tint` | string | white | Text and icon color (terminal: default text colour over the dark backdrop) |
| `align` | string | `"leading"` | `"leading"`, `"center"`, `"trailing"` |
| `scrollable` | bool | `false` | Fixed-height scrolling terminal/log view (pair with `controlHeight`) |
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
| `"terminal"` | Monospaced **ANSI terminal** — see [Terminal style](#terminal-style) |

## Terminal style

`style: "terminal"` (and, as a shortcut, **`mono`/`large-mono` + `scrollable`**) renders the
text as a real terminal instead of a plain mono label — purpose-built for piping a captured
shell/tmux pane to the phone:

- **ANSI styling** — colour (16 / 256 / truecolor), **bold**, dim, *italic*, underline, and
  reverse are parsed from the escape codes and rendered. Plain text (no escapes) renders
  normally.
- **Pane-matched scaling** — the font auto-scales so the source's column width exactly fills
  the view, so box-drawing and ASCII line up like the real pane. If a server prepends a
  `CSI 8;rows;cols t` size report, that column count is used; otherwise the widest line is.
- **Dark backdrop** — drawn on its own dark background (independent of the app theme) so
  ANSI colours have the contrast they were designed for.
- **Pinch to zoom** — pinch to scale the text past the fitted size; **double-tap** snaps back
  to fit. Content wider/taller than the view scrolls both ways.
- **Sizing** — set `controlHeight` for the on-screen height; `fontSize` caps the fitted font
  before zoom. Keeps the latest line in view and auto-scrolls on update.

Feed it like any synced label (a `.string` value); see the
[tmux-bridge](https://carterbeaudoin.net/CAR-TER) server for a complete example.

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

### Terminal snapshot (live pane)
```json
{
  "type": "label",
  "id": "pane-snapshot",
  "position": [1, 0],
  "span": [5, 4],
  "style": "terminal",
  "scrollable": true,
  "controlHeight": 360,
  "text": "(waiting for pane…)",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "snapshot" }, "valuePath": "text" }]
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
