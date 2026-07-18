---
type: logConsole
label: Log Console
icon: terminal.fill
category: controls
defaultSpan: [3, 4]
fields:
  - name: label
    type: string
    description: Header label
  - name: style
    type: enum
    values: [default, transparent]
    default: default
    description: "default (dark bg) or transparent"
  - name: maxLines
    type: number
    default: 200
    description: Maximum buffered lines
  - name: showTimestamps
    type: bool
    default: true
    description: Prefix each line with timestamp
  - name: fontSize
    type: number
    default: 11
    description: Monospace font size
  - name: autoScroll
    type: bool
    default: true
    description: Auto-scroll to latest line
  - name: controlHeight
    type: number
    description: "Console area height in points (default: compact, capped at 200). Set it when the console should fill a tall grid span."
  - name: logColors
    type: object
    description: "Map log levels to colors: {\"error\": \"#FF3B30\", \"warn\": \"#FF9500\"}"
  - name: tint
    type: color
    default: "#667eea"
    description: Accent color
themeFields:
  - name: cornerRadius
    type: number
    default: 12
    description: Control corner radius
  - name: controlPadding
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
    type: number
    default: 1
    description: Border width
  - name: labelFontSize
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
  "sync": { "method": "meshsocket", "event": "log_stream" }
}
```

## Related
- [[shared-properties]] — Base fields
- [[sync]] — Real-time data sync
