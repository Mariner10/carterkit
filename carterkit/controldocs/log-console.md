---
type: logConsole
label: Log Console
icon: terminal.fill
category: controls
defaultSpan: [3, 4]
addIntent: show
pickerCategory: Readouts
friendlyName: Log
oneLiner: Lines of messages as they arrive
aliases: [console, log, terminal, output, messages, tail]
depth: complete
starterPreset: {"label": "Log"}
io:
  - emits: none
  - receives: lines
    role: show
    type: json
    shape: {"text": "text", "level": "text?"}
    from: [hub, mqtt, http, store, default]
    says: one log line per message, a text and an optional level
    reacts: each message adds a line at the bottom, colored by its level; the oldest lines drop off past the line limit, and the view follows the newest line unless auto-scroll is off
    example: {"text": "Sample A"}
    since: next
  - sample: {"text": "Sample A"}
    next: {"text": "Sample B"}
fields:
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label
    summary: The name shown above the log
    does: Shows this text in the header above the console, next to a count of the lines kept.
  - name: style
    edit: look
    depth: surface
    title: Style
    tab: style
    type: enum
    values: [default, transparent]
    default: default
    description: "default (dark bg) or transparent"
    summary: Dark panel or see-through
    does: Picks whether the lines sit on the theme's second background fill or on a clear background.
    valueHelp: {"default": "the lines sit on a filled panel", "transparent": "no panel fill, so the card behind shows through"}
  - name: maxLines
    effect: behavior
    edit: scrub
    depth: hold
    under: fontSize
    title: Lines kept
    min: 10
    max: 1000
    step: 10
    type: number
    default: 200
    description: Maximum buffered lines
    summary: How many lines to remember
    does: Shows only this many of the newest lines; older ones scroll away.
  - name: showTimestamps
    edit: part
    depth: hold
    title: Timestamps
    type: bool
    default: true
    description: Prefix each line with timestamp
    summary: Show the time on each line
    does: Puts the time (hours, minutes, seconds) in front of every line when on.
  - name: fontSize
    edit: scrub
    depth: surface
    title: Text size
    tab: style
    min: 8
    max: 28
    step: 1
    type: number
    default: 11
    description: Monospace font size
    summary: How big the text is
    does: Sets the size of the monospace text on every line.
  - name: autoScroll
    chip: Lines
    effect: behavior
    edit: part
    depth: hold
    title: Auto-scroll
    type: bool
    default: true
    description: Auto-scroll to latest line
    summary: Follow the newest line
    does: Keeps the view pinned to the latest line as new ones arrive, until you drag up to read older ones.
  - name: controlHeight
    edit: scrub
    depth: hold
    under: fontSize
    title: Height
    min: 80
    max: 800
    step: 10
    type: number
    description: "Console area height in points (default: compact, capped at 200). Set it when the console should fill a tall grid span."
    summary: How tall the log is
    does: Sets the height of the console area in points; without it the area stays compact at no more than 200.
  - name: logColors
    tab: style
    type: object
    description: "Map log levels to colors: {\"error\": \"#FF3B30\", \"warn\": \"#FF9500\"}"
    summary: Colors for each kind of message
    does: Colors each line by its level name, for example error or warn, overriding the theme's built-in level colors.
  - name: tint
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: Accent color
    summary: The accent color
    does: Stores an accent color for the console; lines take their colors from the level colors and the theme, so it shows no change today.
  - name: defaultValue
    type: array
    description: Seed lines shown before the first sync (strings, or objects with text and level)
    summary: Starting messages shown until new ones arrive
    does: Fills the console with these lines before any synced line arrives.
themeFields:
  - use: cornerRadius
    summary: How round the corners are
    does: Rounds the corners of the console card.
  - use: controlPadding
    summary: Space inside the card
    does: Sets the gap between the card edge and the header and log.
  - use: surfacePrimary
    summary: The card background
    does: Fills the whole card behind the header and log in this color.
  - use: accentColor
    summary: The highlight color
    does: Sets the theme accent color the console uses when no tint is set.
  - use: secondaryColor
    summary: Softer text color
    does: Colors the header label and the timestamps.
  - use: borderColor
    summary: The outline color
    does: Draws the card outline in this color.
  - use: borderWidth
    does: Sets the thickness of the card outline in points.
  - use: labelFontSize
    does: Sets the size of the header label text.
  - use: foregroundColor
    summary: Main text color
    does: Colors lines that have no level or an unknown one.
  - use: surfaceSecondary
    summary: Log area color
    does: Fills the log area inside the card unless the style is transparent.
---

# Log Console

A scrolling terminal-style log viewer. Displays timestamped log lines pushed via sync, with color-coded severity levels and monospace rendering.

> For a full **ANSI terminal** — raw escape-code colour/bold, pane-width auto-scaling and
> pinch-to-zoom (e.g. mirroring a captured shell/tmux pane) — use a [[label]] with
> `style: "terminal"` instead. The log console is line-oriented (level colours), not an
> escape-code renderer.

## Type
`"logConsole"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | falls back to `id` | Header label |
| `style` | string | `"default"` | `"default"` (dark bg) or `"transparent"` |
| `maxLines` | number | `200` | Maximum buffered lines |
| `showTimestamps` | bool | `true` | Prefix each line with timestamp |
| `fontSize` | number | `11` | Monospace font size |
| `autoScroll` | bool | `true` | Auto-scroll to latest line |
| `controlHeight` | number | — | Console area height in points (default: compact, capped at 200). Set it to fill a tall grid span |
| `logColors` | object | — | Map log levels to colors |
| `tint` | color | `"#667eea"` | Accent color |
| `defaultValue` | array | — | Seed lines shown before the first sync: strings or `{text, level}` objects. See [[control-def#defaultValue per type]] |

## Examples

### Application log viewer
```json
{
  "type": "logConsole",
  "id": "app-logs",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Application Logs",
  "maxLines": 500,
  "showTimestamps": true,
  "fontSize": 12,
  "autoScroll": true,
  "logColors": {
    "error": "#FF3B30",
    "warn": "#FF9500",
    "info": "#34C759",
    "debug": "#8E8E93"
  },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "log_stream" } }]
}
```

Each server broadcast `{"msg_type": "log_stream", "text": "…", "level": "warn"}` appends one line. With no `valuePath` the whole frame is read, so `text` (or `line`/`message`) and `level` both land.

### Quiet transparent log
Small, see-through log that shows no times and the newest lines only.
```json
{
  "type": "logConsole",
  "id": "quiet-log",
  "position": [0, 0],
  "span": [3, 2],
  "label": "Events",
  "style": "transparent",
  "showTimestamps": false,
  "maxLines": 50,
  "fontSize": 10
}
```

### Seeded log with custom level colors
Starts with two lines and colors errors and successes your own way.
```json
{
  "type": "logConsole",
  "id": "seeded-log",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Deploy",
  "controlHeight": 300,
  "autoScroll": true,
  "logColors": { "error": "#FF453A", "success": "#30D158" },
  "defaultValue": ["Waiting for deploy...", { "text": "Last run failed", "level": "error" }]
}
```

## Related
- [[shared-properties]] — Base fields
- [[sync]] — Real-time data sync
