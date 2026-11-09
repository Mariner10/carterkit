---
type: qrCode
depth: complete
label: QR Code
icon: qrcode
category: controls
defaultSpan: [2, 2]
addIntent: show
pickerCategory: Readouts
friendlyName: QR code
oneLiner: A code a phone camera can scan
aliases: [qr, barcode, scan, code, link, share]
starterPreset: {"label": "QR code","text": "https://example.com"}
io:
  - emits: none
  - receives: value
    role: show
    type: string
    from: [hub, mqtt, http, store, derive]
    says: the text to turn into a code
    reacts: the code is redrawn to encode the new text, replacing the configured text
    example: "Sample A"
    since: next
  - sample: "Sample A"
    next: "Sample B"
fields:
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Label below the QR code
    summary: The words under the code
    does: Shows this text in a small line below the QR code.
  - name: text
    chip: Code
    edit: inline
    depth: surface
    title: Code text
    type: string
    description: Static content to encode (overridden by sync)
    does: Sets the content the code encodes; a synced value replaces it as soon as one arrives.
    summary: Content to encode until a connected value is available
  - name: tint
    edit: color
    depth: surface
    title: Code color
    tab: style
    type: color
    default: "#FFFFFF"
    description: QR code foreground color
    summary: The color of the code squares
    does: Recolors the dark squares of the code; keep it strongly different from the background so cameras can read it.
  - name: qrBackground
    edit: color
    depth: surface
    title: Code background
    tab: style
    type: color
    description: "Fill behind the code (default: none, the card shows through)"
    summary: The patch behind the code
    does: Fills a solid color behind the squares; left empty, the card shows through.
  - name: correctionLevel
    edit: look
    depth: hold
    under: tint
    title: Error correction
    type: enum
    values: [L, M, Q, H]
    default: M
    description: Error correction level
    summary: How much damage the code can survive
    does: "Changes how dense the code looks: higher levels add more squares so a scratched or covered code still scans."
    valueHelp: {"L": "lowest correction, simplest code, for clean screens", "M": "medium correction, a good everyday balance", "Q": "higher correction, survives some smudging", "H": "highest correction, densest code, survives scratches or a logo over it"}
  - name: hideLabel
    since: next
    edit: part
    depth: hold
    title: Hide title
    type: bool
    default: false
    description: Hide the caption below the code
    summary: Show the code without its caption
    does: On hides the title line under the code; off shows it when a title is set.
  - name: hideBackground
    edit: part
    depth: hold
    title: Background
    tab: style
    type: bool
    default: false
    description: Remove glass card background
    summary: The frosted card behind the code
    does: On removes the glass card so the code sits straight on the page; off keeps the card.
themeFields:
  - use: cornerRadius
    summary: How round the card corners are
    does: Rounds the card corners by 0 to 30 points.
  - use: controlPadding
    summary: The space around the code inside the card
    does: Pushes the code in from the card edge by 0 to 24 points.
  - use: surfacePrimary
    summary: The card fill
    does: Sets the color of the card behind the code, usually a faint tint.
  - use: secondaryColor
    does: Recolors the secondary text around the code.
  - use: borderColor
    summary: The color of the card outline
    does: Recolors the outline drawn around the card.
  - use: borderWidth
    summary: How thick the card outline is
    does: Sets the card outline thickness from 0 to 5 points; 0 hides it.
  - use: labelFontSize
    summary: How big the caption is
    does: Sizes the caption below the code from 8 to 24 points.
  - use: foregroundColor
    does: Recolors the caption text below the code.
colorSlots:
  - slot: code
    default: neutral
    alias: tint
    since: next
    summary: The color of the code
    does: Colors the code's squares; until set it follows the neutral role, the text color.
  - slot: background
    default: "#00000000"
    alias: qrBackground
    since: next
    summary: The color behind the code
    does: Fills a rounded card behind the code; clear until set.
---

# QR Code (display)

A **display** control that renders a QR code image from static text or a dynamically synced value — useful for sharing URLs, connection strings, or codes on screen. (This is unrelated to *pairing this device* to a live editing session, which uses the camera scanner, not this control.)

## Type
`"qrCode"`

## Relevant Fields
Inherits all [[shared-fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | falls back to `id` | Label below the QR code |
| `text` | string | — | Static content to encode (overridden by sync) |
| `tint` | color | `"#FFFFFF"` | QR code foreground color |
| `qrBackground` | color | — | Fill behind the code |
| `correctionLevel` | string | `"M"` | Error correction level: `"L"`, `"M"`, `"Q"`, `"H"` |
| `hideLabel` | bool | `false` | Hide the caption below the code |
| `hideBackground` | bool | `false` | Remove glass card background |

## Examples

### Wi-Fi sharing QR code
Shows a static Wi-Fi join code with the highest error correction, so guests can scan it to connect.

```json
{
  "type": "qrCode",
  "id": "wifi-qr",
  "position": [0, 0],
  "span": [2, 2],
  "label": "Guest Wi-Fi",
  "text": "WIFI:T:WPA;S:GuestNetwork;P:welcome123;;",
  "tint": "#FFFFFF",
  "correctionLevel": "H"
}
```

### Code on a solid background
Fills a white patch behind a dark code, the most reliable look for cameras in dark mode.

```json
{ "type": "qrCode", "id": "link-qr", "position": [0, 0], "span": [2, 2], "label": "Open the guide",
  "text": "https://example.com/guide", "tint": "#000000", "qrBackground": "#FFFFFF" }
```

### Every error-correction level
Shows the lowest level, a sparse code for short text on a clean screen; the other levels (M, Q, H) use the same field and add more squares each step.

```json
{ "type": "qrCode", "id": "short-qr", "position": [0, 0], "span": [2, 2], "label": "Short link",
  "text": "https://example.com", "correctionLevel": "L" }
```

### Code without the card
Removes the glass card so the code sits straight on the page.

```json
{ "type": "qrCode", "id": "bare-qr", "position": [0, 0], "span": [2, 2], "label": "Bare code",
  "text": "https://example.com", "hideBackground": true }
```

### Live code from a synced value
Encodes whatever value arrives over MeshSocket, such as a rotating pairing code; the static text shows until the first value comes in.

```json
{ "type": "qrCode", "id": "pair-qr", "position": [0, 0], "span": [2, 2], "label": "Pairing code",
  "text": "waiting",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "device": "server" }, "valuePath": "pair_url" }] }
```

## Notes
The QR code is read-only: it has no tap, long-press or detail view, so there is nothing to bind besides the synced value.

## Related
- [[shared-fields]] — Base fields
- [[sync]] — Real-time data sync
