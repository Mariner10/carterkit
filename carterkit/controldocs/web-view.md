---
type: webView
label: Web View
icon: globe
category: controls
defaultSpan: [3, 4]
fields:
  - name: url
    type: string
    description: URL to load
  - name: label
    type: string
    description: Header label
  - name: webInteractive
    type: bool
    default: true
    description: Allow user interaction
  - name: webScrollEnabled
    type: bool
    default: true
    description: Allow scrolling
  - name: webRefreshInterval
    type: number
    description: Auto-refresh interval in seconds
  - name: hideBackground
    type: bool
    default: false
    description: Remove glass card background
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

# Web View

An embedded web browser that renders a URL inline within the layout grid. Supports interactive browsing, scroll control, and periodic auto-refresh.

## Type
`"webView"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | string | — | URL to load |
| `label` | string | falls back to `id` | Header label |
| `webInteractive` | bool | `true` | Allow user interaction |
| `webScrollEnabled` | bool | `true` | Allow scrolling |
| `webRefreshInterval` | number | — | Auto-refresh interval in seconds |
| `hideBackground` | bool | `false` | Remove glass card background |

## Examples

### Embedded dashboard
```json
{
  "type": "webView",
  "id": "grafana",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Metrics Dashboard",
  "url": "https://grafana.local/d/overview?kiosk",
  "webInteractive": true,
  "webScrollEnabled": false,
  "webRefreshInterval": 30
}
```

## Related
- [[shared-properties]] — Base fields
