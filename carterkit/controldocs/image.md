---
type: image
label: Image
icon: photo
category: controls
defaultSpan: [2, 2]
addIntent: show
pickerCategory: Media
friendlyName: Picture
oneLiner: A photo or an icon
aliases: [picture, photo, icon, logo, thumbnail, img]
addRank: 7
depth: complete
starterPreset: {"systemName": "photo"}
io:
  - emits: none
  - receives: value
    role: show
    type: string
    from: [hub, mqtt, http, sensor, store, derive, default]
    says: a picture address, or a code (a number, state word or true/false) that the icon, picture and color maps turn into a symbol
    reacts: the picture changes to the one that matches; a code with no match uses the default entry, then the control's own symbol; a bare code is never read as an address
    example: "1"
    since: next
fields:
  - name: systemName
    edit: symbol
    depth: surface
    title: Symbol
    type: string
    description: SF Symbol name (fallback/placeholder)
    summary: The symbol shown when there is no picture
    does: Draws this SF Symbol when no image loads or none is given, scaled to fill the cell (never below about 28 pt) and tinted.
  - name: url
    chip: Picture
    edit: inline
    depth: surface
    title: Picture address
    type: string
    description: Static remote image URL (an asset:// address is reserved, not loaded yet)
    summary: The picture to load from the web
    does: Loads and shows the image at this absolute web address; a failed or missing address falls back to the symbol. Addresses starting asset:// are reserved for pictures bundled with a layout and are not loaded yet.
  - name: style
    edit: look
    depth: surface
    title: Shape
    tab: style
    type: enum
    values: [rounded, circle]
    description: Visual style variant
    summary: Square-ish or round corners
    does: Clips the picture to rounded corners (12 pt) or a full circle; an image roundness value overrides it.
    valueHelp: {"rounded": "softly rounded corners", "circle": "clipped to a circle or pill"}
  - name: imageCornerRadius
    edit: scrub
    depth: hold
    under: style
    title: Image roundness
    tab: style
    min: 0
    max: 60
    step: 1
    type: number
    description: Custom corner radius
    summary: How round the picture corners are
    does: Rounds the picture's corners from 0 to 60 pt, overriding the Shape choice.
  - name: imageShadow
    edit: scrub
    depth: hold
    under: style
    unit: pt
    title: Shadow
    tab: style
    type: number
    min: 0
    max: 30
    step: 1
    default: 0
    description: Soft shadow blur under the image (0 = none)
    summary: A soft shadow under the picture
    does: Blurs a dark shadow under the picture from 0 (none) to 30 pt, with room added around it so it is not cut off.
  - name: aspectRatio
    edit: look
    depth: surface
    title: Fit
    type: enum
    values: [fit, fill]
    description: "fit (scale to fit) or fill (scale to fill, may crop)"
    summary: Whether the picture fills the box or fits inside
    does: Scales the picture to sit fully inside its cell, or to cover the cell and crop the overflow.
    valueHelp: {"fit": "the whole picture shows, with empty space if the shapes differ", "fill": "the picture covers the whole cell and the edges are cropped"}
  - name: hideBackground
    edit: part
    depth: hold
    title: Background
    tab: style
    type: bool
    default: false
    description: Remove glass background
    summary: Whether the card behind it is drawn
    does: Removes the glass card, fill and border so only the picture or symbol sits on the page.
  - use: iconMap
    does: Swaps in the SF Symbol listed for the incoming value, with "default" as the catch-all; it wins over the static symbol and url.
  - name: valueMap
    tab: data
    type: object
    edit: map
    columns: [{"name": "value", "title": "Value", "type": "string", "edit": "inline", "required": true, "values": ["default"], "default": "value{n}"}, {"name": "url", "title": "Image URL", "type": "string", "edit": "inline", "required": true, "default": ""}]
    description: Incoming value → image URL
    summary: Show different pictures for different values
    does: Loads the image at the web address listed for the incoming value; it wins over every other source.
    summary: Show different pictures for different values
  - name: colorMap
    tab: data
    type: object
    edit: map
    columns: [{"name": "value", "title": "Value", "type": "string", "edit": "inline", "required": true, "values": ["default"], "default": "value{n}"}, {"name": "color", "title": "Color", "type": "color", "edit": "color", "required": true, "default": "#8E8E93"}]
    description: Incoming value → hex tint for the mapped symbol
    summary: Show different colors for different values
    does: Tints the symbol with the hex color listed for the incoming value; photos are not tinted.
    summary: Show different colors for different values
themeFields:
  - use: cornerRadius
    summary: How round the card corners are
    does: Rounds the control's card corners from 0 to 30 pt (default 12).
  - use: controlPadding
    summary: The gap between card edge and picture
    does: Sets the space inside the card around the picture from 0 to 24 pt (default 8).
  - use: surfacePrimary
    does: Fills the card behind the picture with this color, default a faint white wash.
  - use: foregroundColor
    summary: The color of the symbol
    does: Colors the fallback symbol when no tint or color map applies, default white.
  - use: borderColor
    summary: The card's outline color
    does: Draws the card's outline in this color, default a faint white.
  - use: borderWidth
    does: Sets the outline thickness from 0 to 5 pt (default 1).
colorSlots:
  - slot: symbol
    default: neutral
    alias: tint
    since: next
    summary: The color of the symbol
    does: Colors the fallback or mapped symbol when no color map matches; until set it follows the neutral role, the text color. Photos are not tinted.
---

# Image

A static or synced image display. Can show SF Symbols, remote URLs, or synced image URLs.

## Type
`"image"`

## Relevant Fields
Inherits all [[shared-fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `systemName` | string | — | SF Symbol name (fallback/placeholder) |
| `url` | string | — | Static remote image URL; `asset://` is reserved and not loaded yet |
| `style` | string | — | `"rounded"` for rounded corners, `"circle"` for circular clipping |
| `imageCornerRadius` | number | — | Custom corner radius |
| `imageShadow` | number | `0` | Soft shadow blur under the image (0–30) |
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
A static symbol standing in for a feed.
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
Shows the picture whose address arrives over a live feed.
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
Turns a weather code from a web request into a colored symbol.
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
A big tinted symbol that fills its cell.
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
Changes symbol and color as a printer's state changes.
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
- **In a `rowHeight: "auto"` row an image never sets the row's height**: it takes
  the height its row's other content gives it, so a fallback symbol cannot balloon a
  compact templated row.
- Supports long-press groups for detail views

## Related
- [[shared-fields]] — Base fields
- [[sync]] — Receiving image URLs
- [[label]] — the same value maps, mapping to text
