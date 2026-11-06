---
type: camera
depth: complete
label: Camera
icon: camera.viewfinder
category: controls
defaultSpan: [3, 4]
addIntent: change
pickerCategory: Media
friendlyName: Scanner
oneLiner: Scan a barcode or QR code
aliases: [photo, picture, scan, capture, video, webcam]
starterPreset: {"label": "Scan","scan": ["barcode"]}
fields:
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label
    summary: The name shown on top
    does: Shows this text as the header above the camera.
  - name: scan
    type: array
    default: [barcode]
    description: "What the live scanner detects: any of barcode, text"
    summary: What the camera looks for
    does: Chooses whether the live viewfinder reads barcodes, printed text, or both.
  - name: symbologies
    type: array
    description: "Barcode filter (qr, ean13, code128, …). Omit for all supported"
    summary: Which barcode types to read
    does: Limits scanning to the listed barcode types; leave empty to read every supported type.
  - name: sendMode
    tab: action
    type: enum
    values: [auto, tap]
    default: auto
    description: "auto sends every stabilized detection; tap sends only items the user taps"
    summary: Send on its own or on tap
    does: Decides whether detections send themselves or wait for you to tap one.
    valueHelp: {"auto": "every steady detection is sent on its own and is the default", "tap": "only the item you tap in the viewfinder is sent"}
  - name: debounce
    tab: action
    min: 0
    max: 30
    step: 1
    type: number
    default: 3
    description: Seconds before the same decoded value can fire again
    summary: Wait before a repeat scan
    does: Holds back the same scanned value from firing again for this many seconds (0 to 30).
  - name: torch
    edit: part
    depth: hold
    title: Torch
    type: bool
    default: true
    description: Show a torch toggle while scanning
    summary: Show the flashlight button
    does: Shows a torch toggle in the viewfinder while scanning.
  - name: snapshot
    edit: part
    depth: hold
    title: Snapshot
    type: bool
    default: false
    description: Show a shutter button (implied when snapshotAction is set)
    summary: Show a photo button
    does: Shows a shutter button that takes a photo while the camera is running.
  - name: snapshotQuality
    min: 0
    max: 1
    step: 0.05
    type: number
    default: 0.6
    description: JPEG quality 0–1 (auto-lowered to fit the mesh frame budget)
    summary: How sharp the photo is
    does: Sets the photo's JPEG quality from 0 to 1; it is lowered automatically if the photo is too big to send.
  - name: snapshotMaxDimension
    min: 240
    max: 4096
    step: 1
    type: number
    default: 1280
    description: Longest snapshot edge in pixels
    summary: Biggest photo size
    does: Caps the photo's longest side, 240 to 4096 pixels.
  - name: hideLabel
    edit: part
    depth: hold
    title: Title shown
    type: bool
    default: false
    description: Hide the header label (the LIVE chip moves into the viewfinder)
    summary: Hide the title
    does: Hides the header title, and the LIVE chip moves into the viewfinder.
themeFields:
  - use: cornerRadius
    summary: How round the corners are
    does: Rounds the control's corners, from 0 (square) to 30 pt.
  - name: controlPadding
    title: Inner spacing
    min: 0
    max: 24
    step: 1
    type: number
    default: 8
    description: Internal padding
    summary: Space inside the edges
    does: Sets the gap between the control's edge and its content, 0 to 24 pt.
  - name: surfacePrimary
    title: Background color
    type: color
    default: #FFFFFF0F
    description: Background fill
    summary: The background color
    does: Fills the control's background with this color.
  - name: accentColor
    type: color
    default: #667eea
    description: Idle-state icon tint
    summary: The idle icon color
    does: Tints the camera icon on the Tap to Start card.
  - name: secondaryColor
    title: Second text color
    type: color
    default: #FFFFFF99
    description: Secondary text color
    summary: The quieter text color
    does: Colors the smaller, secondary text.
  - name: borderColor
    title: Border color
    type: color
    default: #FFFFFF1A
    description: Border color
    summary: The outline color
    does: Colors the outline drawn around the control.
  - name: borderWidth
    title: Border thickness
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
    summary: How thick the outline is
    does: Sets the outline thickness from 0 (none) to 5 pt.
  - use: foregroundColor
  - use: labelFontSize
    summary: Size of the title text
    does: Sets the title text size from 8 to 24 pt.
  - name: valueFontSize
    title: Value text size
    min: 8
    max: 48
    step: 1
    type: number
    default: 14
    description: Value text size
    summary: Size of the value text
    does: Sets the value text size from 8 to 48 pt.
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
  "span": [3, 4],
  "label": "Scan Inventory",
  "scan": ["barcode"],
  "symbologies": ["qr", "ean13", "code128"],
  "debounce": 5,
  "action": {
    "method": "meshsocket",
    "mode": "broadcast",
    "event": "broadcast_request",
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
  "span": [3, 4],
  "label": "Read Serial Number",
  "scan": ["text"],
  "sendMode": "tap",
  "action": {
    "method": "meshsocket",
    "mode": "broadcast",
    "event": "broadcast_request",
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
  "span": [3, 4],
  "label": "Site Photo",
  "snapshotAction": {
    "method": "meshsocket",
    "mode": "broadcast",
    "event": "broadcast_request",
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
