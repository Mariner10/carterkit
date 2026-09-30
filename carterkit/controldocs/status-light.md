---
type: statusLight
label: Status Light
icon: circle.fill
category: controls
defaultSpan: [1, 1]
addIntent: show
friendlyName: Status dot
oneLiner: "A colored dot: OK, busy, or off"
addRank: 6
starterPreset: {"label": "Status"}
lookPresets: [{"id": "dot","name": "Dot","symbol": "circle.fill","set": {"style": "dot","pulse": null}},{"id": "badge","name": "Badge","symbol": "capsule.fill","set": {"style": "badge","pulse": null}},{"id": "pulsing","name": "Pulsing","symbol": "dot.radiowaves.left.and.right","set": {"style": "dot","pulse": true}}]
fields:
  - name: label
    type: string
    description: Text beside the indicator
  - name: tint
    tab: style
    type: color
    default: "#34C759"
    description: Default indicator color
  - name: statusColors
    tab: style
    type: object
    description: "Map state strings to hex colors: {\"online\": \"#34C759\", \"offline\": \"#FF3B30\"}"
    summary: Colors for each status
  - name: size
    tab: style
    type: enum
    values: [small, default, large]
    default: default
    description: "Indicator size: small (8pt), default (12pt), large (18pt)"
  - name: style
    tab: style
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
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "server_health" }, "valuePath": "state" }]
}
```

The server broadcasts `{"msg_type": "server_health", "state": "degraded"}`; `state` picks the `statusColors` key.

## Related
- [[shared-properties]] — Base fields
- [[sync]] — Real-time data sync
