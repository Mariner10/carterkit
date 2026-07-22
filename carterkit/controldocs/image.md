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
  - name: iconMap
    type: object
    description: Incoming value → SF Symbol name ("default" catches the rest)
  - name: valueMap
    type: object
    description: Incoming value → image URL
  - name: colorMap
    type: object
    description: Incoming value → hex tint for the mapped symbol
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
| `iconMap` | object | — | Incoming value → SF Symbol name — see [[#Value maps]] |
| `valueMap` | object | — | Incoming value → image URL |
| `colorMap` | object | — | Incoming value → hex tint for the mapped symbol |

## Value maps

An image doesn't have to be fed a URL: point it at a code — a WMO weather code, a
device state, an alarm level — and let the layout say what that code looks like.

```json
"iconMap": { "0": "sun.max.fill", "3": "cloud.fill", "61": "cloud.rain.fill", "default": "questionmark.circle" },
"colorMap": { "0": "#FFD60A", "61": "#0A84FF" }
```

- **Keys match the stringified value**, so `0`, `"0"`, `true`, and `"rain"` all work
  from the same map. `true`/`false` also match `yes`/`no`/`on`/`off`/`1`/`0`, and a
  number matches whether it arrives as `61` or `61.00`. Key lookup falls back to a
  case-insensitive match.
- **`"default"`** is the catch-all for any value with no entry; with no `"default"`
  either, the image falls back to its own `systemName` rather than rendering blank.
- **Precedence**: a `valueMap` URL wins, then an `iconMap` symbol, then the synced
  value as a URL, then the static `url`, then `systemName`.
- Only **absolute** URLs load (a synced bare code is never mistaken for an address).
- `colorMap` tints the mapped symbol; a photo is unaffected.

[[label]] takes the same three fields, where `valueMap` supplies display text.

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

### Live weather icon (WMO code → SF Symbol, no server)
```json
{
  "type": "image",
  "id": "wx-icon",
  "position": [0, 0],
  "span": [2, 2],
  "systemName": "cloud",
  "hideBackground": true,
  "iconMap": { "0": "sun.max.fill", "1": "sun.max.fill", "2": "cloud.sun.fill", "3": "cloud.fill", "45": "cloud.fog.fill", "51": "cloud.drizzle.fill", "61": "cloud.rain.fill", "71": "cloud.snow.fill", "80": "cloud.heavyrain.fill", "95": "cloud.bolt.rain.fill", "default": "questionmark.circle" },
  "colorMap": { "0": "#FFD60A", "1": "#FFD60A", "2": "#FFD60A", "61": "#0A84FF", "80": "#0A84FF", "95": "#FF9F0A" },
  "sync": [{ "method": "http", "url": "https://api.open-meteo.com/v1/forecast?latitude=42.36&longitude=-71.06&current=weather_code", "interval": 900, "valuePath": "current.weather_code" }]
}
```

### Hero symbol tile
```json
{
  "type": "image",
  "id": "wx-hero",
  "position": [0, 0],
  "span": [3, 2],
  "systemName": "sun.max.fill",
  "tint": "#FFD60A",
  "hideBackground": true
}
```

The symbol fills the cell, so the span alone controls how big it reads.

### Device state → symbol
```json
{
  "type": "image",
  "id": "printer-state",
  "position": [0, 2],
  "span": [2, 2],
  "systemName": "printer",
  "iconMap": { "idle": "printer", "printing": "printer.fill", "error": "exclamationmark.triangle.fill", "default": "questionmark.circle" },
  "colorMap": { "printing": "#30D158", "error": "#FF453A" },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "printer" }, "valuePath": "state" }]
}
```

## Behavior
- When synced, receives a URL string and loads the image from that URL
- `systemName` renders as SF Symbol when no URL is available
- **A symbol scales to its cell**, exactly as a photo does: give the control a
  `[3, 2]` span and it renders as a hero tile, not a small glyph in a large box. It
  never shrinks below a legible ~28pt, which is also the size it settles at in a
  `flow` grid (where the cell has no fixed height) — set `controlHeight` there to
  make it larger. See [[grid-dimensions]]
- `iconMap`/`valueMap`/`colorMap` turn a synced **code** into a symbol, an image URL,
  and a tint — see [[#Value maps]]
- Supports long-press groups for detail views

## Related
- [[shared-properties]] — Base fields
- [[sync]] — Receiving image URLs
- [[label]] — the same value maps, mapping to text
