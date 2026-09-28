---
type: logConsole
label: Log Console
icon: terminal.fill
category: controls
defaultSpan: [3, 4]
addIntent: show
friendlyName: Log
oneLiner: Lines of messages as they arrive
starterPreset: {"label": "Log"}
fields:
  - name: label
    type: string
    description: Header label
  - name: style
    tab: style
    type: enum
    values: [default, transparent]
    default: default
    description: "default (dark bg) or transparent"
  - name: maxLines
    min: 10
    max: 1000
    step: 10
    type: number
    default: 200
    description: Maximum buffered lines
  - name: showTimestamps
    type: bool
    default: true
    description: Prefix each line with timestamp
  - name: fontSize
    tab: style
    min: 8
    max: 28
    step: 1
    type: number
    default: 11
    description: Monospace font size
  - name: autoScroll
    type: bool
    default: true
    description: Auto-scroll to latest line
  - name: controlHeight
    min: 80
    max: 800
    step: 10
    type: number
    description: "Console area height in points (default: compact, capped at 200). Set it when the console should fill a tall grid span."
  - name: logColors
    tab: style
    type: object
    description: "Map log levels to colors: {\"error\": \"#FF3B30\", \"warn\": \"#FF9500\"}"
  - name: tint
    tab: style
    type: color
    default: "#667eea"
    description: Accent color
  - name: defaultValue
    type: array
    description: Seed lines shown before the first sync (strings, or objects with text and level)
themeFields:
  - name: cornerRadius
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
  - name: controlPadding
    min: 0
    max: 24
    step: 1
    type: number
    default: 8
    description: Internal padding
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
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
  - name: labelFontSize
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
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

## Related
- [[shared-properties]] — Base fields
- [[sync]] — Real-time data sync
