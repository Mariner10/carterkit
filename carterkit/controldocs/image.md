---
type: image
label: Image
icon: photo
category: controls
defaultSpan: [2, 2]
fields:
  - name: systemName
    type: string
    description: SF Symbol name (fallback/placeholder)
  - name: url
    type: string
    description: Static remote image URL
  - name: style
    type: enum
    values: [rounded, circle]
    description: Visual style variant
  - name: imageCornerRadius
    type: number
    description: Custom corner radius
  - name: aspectRatio
    type: enum
    values: [fit, fill]
    description: "fit (scale to fit) or fill (scale to fill, may crop)"
  - name: hideBackground
    type: bool
    default: false
    description: Remove glass background
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
  - name: borderColor
    type: color
    default: #FFFFFF1A
    description: Border color
  - name: borderWidth
    type: number
    default: 1
    description: Border width
---

# Image

A static or synced image display. Can show SF Symbols, remote URLs, or synced image URLs.

## Type
`"image"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `systemName` | string | — | SF Symbol name (fallback/placeholder) |
| `url` | string | — | Static remote image URL |
| `style` | string | — | `"rounded"` for rounded corners, `"circle"` for circular clipping |
| `imageCornerRadius` | number | — | Custom corner radius |
| `aspectRatio` | string | — | `"fit"` (scale to fit) or `"fill"` (scale to fill, may crop) |
| `hideBackground` | bool | `false` | Remove glass background |

## Examples

### SF Symbol placeholder (e.g., for camera feed)
```json
{
  "type": "image",
  "id": "cam-front",
  "position": [0, 0],
  "span": [1, 2],
  "systemName": "video.fill"
}
```

### Synced album artwork
```json
{
  "type": "image",
  "id": "album-art",
  "position": [0, 0],
  "span": [3, 2],
  "systemName": "music.note.list",
  "style": "rounded",
  "imageCornerRadius": 8,
  "hideBackground": true,
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "player_state" }, "valuePath": "artwork_url" }]
}
```

## Behavior
- When synced, receives a URL string and loads the image from that URL
- `systemName` renders as SF Symbol when no URL is available
- Supports long-press groups for detail views

## Related
- [[shared-properties]] — Base fields
- [[sync]] — Receiving image URLs
