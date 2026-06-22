---
type: statusLight
label: Status Light
icon: circle.fill
category: controls
defaultSpan: [1, 1]
fields:
  - name: label
    type: string
    description: Text beside the indicator
  - name: tint
    type: color
    default: "#34C759"
    description: Default indicator color
  - name: statusColors
    type: object
    description: "Map state strings to hex colors: {\"online\": \"#34C759\", \"offline\": \"#FF3B30\"}"
  - name: size
    type: enum
    values: [small, default, large]
    default: default
    description: "Indicator size: small (8pt), default (12pt), large (18pt)"
  - name: style
    type: enum
    values: [dot, badge]
    default: dot
    description: "dot (circle) or badge (pill with state text)"
  - name: pulse
    type: bool
    default: false
    description: Pulse animation when active
  - name: defaultValue
    type: string
    description: Initial state key
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
  - name: foregroundColor
    type: color
    default: #FFFFFF
    description: Primary text color
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

# Status Light

A compact indicator that displays state as a colored dot or badge. The color changes based on synced state values mapped through `statusColors`.

## Type
`"statusLight"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | falls back to `id` | Text beside the indicator |
| `tint` | color | `"#34C759"` | Default indicator color |
| `statusColors` | object | — | Map state strings to hex colors |
| `size` | string | `"default"` | `"small"` (8pt), `"default"` (12pt), `"large"` (18pt) |
| `style` | string | `"dot"` | `"dot"` (circle) or `"badge"` (pill with state text) |
| `pulse` | bool | `false` | Pulse animation when active |
| `defaultValue` | string | — | Initial state key |

## Examples

### Server status indicator
```json
{
  "type": "statusLight",
  "id": "server-status",
  "position": [0, 0],
  "label": "API Server",
  "statusColors": {
    "online": "#34C759",
    "degraded": "#FF9500",
    "offline": "#FF3B30"
  },
  "size": "large",
  "style": "badge",
  "pulse": true,
  "defaultValue": "offline",
  "sync": { "method": "meshsocket", "event": "server_health" }
}
```

## Related
- [[shared-properties]] — Base fields
- [[sync]] — Real-time data sync
