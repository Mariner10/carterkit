---
type: camera
label: Camera
icon: camera.viewfinder
category: controls
defaultSpan: [2, 2]
fields:
  - name: label
    type: string
    description: Header label
  - name: scan
    type: array
    default: [barcode]
    description: "What the live scanner detects: any of barcode, text"
  - name: symbologies
    type: array
    description: "Barcode filter (qr, ean13, code128, …). Omit for all supported"
  - name: sendMode
    type: enum
    values: [auto, tap]
    default: auto
    description: "auto sends every stabilized detection; tap sends only items the user taps"
  - name: debounce
    type: number
    default: 3
    description: Seconds before the same decoded value can fire again
  - name: torch
    type: bool
    default: true
    description: Show a torch toggle while scanning
  - name: snapshot
    type: bool
    default: false
    description: Show a shutter button (implied when snapshotAction is set)
  - name: snapshotQuality
    type: number
    default: 0.6
    description: JPEG quality 0–1 (auto-lowered to fit the mesh frame budget)
  - name: snapshotMaxDimension
    type: number
    default: 1280
    description: Longest snapshot edge in pixels
  - name: hideLabel
    type: bool
    default: false
    description: Hide the header label (the LIVE chip moves into the viewfinder)
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
    description: Idle-state icon tint
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
---

# Camera

A live camera cell **(Pro)** that scans QR codes, barcodes, and printed text the moment they enter the frame, and can capture snapshots on demand. Detections fire the control's [[actions|action]] over the mesh immediately — point the camera at a code and the data is already on your server.

## Type
`"camera"`

## Privacy model

The camera **never starts on its own**. It renders as a "Tap to Start" card; only a tap on the control opens the viewfinder, a red **LIVE** chip shows the whole time it runs, and it stops automatically the moment the app leaves the foreground or the control scrolls off screen. A pushed or synced layout cannot turn the camera on remotely.

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `scan` | string[] | `["barcode"]` | What to detect live: `"barcode"`, `"text"` (OCR), or both |
| `symbologies` | string[] | all | Barcode filter: `qr`, `microQR`, `aztec`, `dataMatrix`, `ean13`, `ean8`, `upce`, `code128`, `code39`, `code93`, `pdf417`, `microPDF417`, `itf14`, `i2of5`, `codabar`, `gs1DataBar`, `gs1DataBarExpanded`, `gs1DataBarLimited` |
| `sendMode` | string | `"auto"` | `"auto"` fires `action` for every stabilized detection (debounced); `"tap"` fires only for the highlighted item the user taps |
| `debounce` | number | `3` | Seconds before the SAME decoded value can fire again (a code sitting in frame doesn't spam the mesh) |
| `torch` | bool | `true` | Torch toggle in the viewfinder |
| `snapshot` | bool | `false` | Shutter button; implied `true` when `snapshotAction` is set |
| `snapshotAction` | [[actions\|ActionDefinition]] | — | Fired on shutter with `{{image}}` substitution; falls back to `action` when omitted |
| `snapshotQuality` | number | `0.6` | JPEG quality; auto-lowered until the frame fits the mesh budget (~500 KB) |
| `snapshotMaxDimension` | number | `1280` | Longest snapshot edge in pixels |

## Substitution tokens

Scan detections fire `action` with:

- `{{value}}` — the decoded string (QR payload, barcode digits, or recognized text)
- `{{kind}}` — what was read: a symbology name (`qr`, `ean13`, …) or `text`

Snapshots fire `snapshotAction` with:

- `{{image}}` — the JPEG as base64 (no data-URL prefix)
- `{{width}}` / `{{height}}` — pixel dimensions

The control's stored value is the last scanned string, so [[visibility]] conditions and [[sync]] readback see it.

## Examples

### Live QR intake — the moment a code is seen, it's on the mesh
```json
{
  "type": "camera",
  "id": "intake-scanner",
  "position": [0, 0],
  "span": [2, 2],
  "label": "Scan Inventory",
  "scan": ["barcode"],
  "symbologies": ["qr", "ean13", "code128"],
  "debounce": 5,
  "action": {
    "method": "meshsocket",
    "mode": "broadcast",
    "event": "scan-result",
    "payload": { "msg_type": "inventory_scan", "code": "{{value}}", "kind": "{{kind}}" }
  }
}
```

### Live text capture (OCR), send only what the user taps
```json
{
  "type": "camera",
  "id": "serial-reader",
  "position": [0, 0],
  "span": [2, 2],
  "label": "Read Serial Number",
  "scan": ["text"],
  "sendMode": "tap",
  "action": {
    "method": "meshsocket",
    "mode": "broadcast",
    "event": "ocr-result",
    "payload": { "msg_type": "serial_read", "text": "{{value}}" }
  }
}
```

### Snapshot to a hub dashboard
```json
{
  "type": "camera",
  "id": "site-cam",
  "position": [0, 0],
  "span": [2, 2],
  "label": "Site Photo",
  "snapshotAction": {
    "method": "meshsocket",
    "mode": "broadcast",
    "event": "camera-photo",
    "payload": { "msg_type": "site_photo", "image_b64": "{{image}}", "w": "{{width}}", "h": "{{height}}" }
  }
}
```
A hub layout can render the photo with an [[image]] control listening for `site_photo` (decode the base64 server-side, or serve it back as a URL).

## Behavior
- Tap to start; **LIVE** chip while running; tap ✕ (or background the app) to stop
- Detections are highlighted in the viewfinder; `auto` mode sends them as they stabilize, `tap` mode waits for a tap
- The same value re-fires only after `debounce` seconds
- Requires camera permission (prompted on first start) and a device with a camera + A12 or later; the cell shows a friendly message otherwise
- Snapshots are size-capped (~500 KB JPEG) so they always fit a mesh frame; expect ~1 MB base64 on the wire

## Related
- [[shared-properties]] — Base fields
- [[actions]] — Action definition & `{{value}}` substitution
- [[qr-code]] — Displaying (rather than reading) QR codes
- [[image]] — Rendering received snapshots on another device
- Privacy Policy (Settings → About) — what leaves the device: nothing, except to *your* server
