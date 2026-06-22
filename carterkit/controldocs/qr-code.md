---
type: qrCode
label: QR Code
icon: qrcode
category: controls
defaultSpan: [2, 2]
fields:
  - name: label
    type: string
    description: Label below the QR code
  - name: text
    type: string
    description: Static content to encode (overridden by sync)
  - name: tint
    type: color
    default: "#FFFFFF"
    description: QR code foreground color
  - name: style
    type: enum
    values: [default, rounded]
    default: default
    description: "default (square modules) or rounded"
  - name: correctionLevel
    type: enum
    values: [L, M, Q, H]
    default: M
    description: Error correction level
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

# QR Code (display)

A **display** control that renders a QR code image from static text or a dynamically synced value — useful for sharing URLs, connection strings, or codes on screen. (This is unrelated to *pairing this device* to a live editing session, which uses the camera scanner, not this control.)

## Type
`"qrCode"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | falls back to `id` | Label below the QR code |
| `text` | string | — | Static content to encode (overridden by sync) |
| `tint` | color | `"#FFFFFF"` | QR code foreground color |
| `style` | string | `"default"` | `"default"` (square modules) or `"rounded"` |
| `correctionLevel` | string | `"M"` | Error correction level: `"L"`, `"M"`, `"Q"`, `"H"` |
| `hideBackground` | bool | `false` | Remove glass card background |

## Examples

### Wi-Fi sharing QR code
```json
{
  "type": "qrCode",
  "id": "wifi-qr",
  "position": [0, 0],
  "span": [2, 2],
  "label": "Guest Wi-Fi",
  "text": "WIFI:T:WPA;S:GuestNetwork;P:welcome123;;",
  "tint": "#FFFFFF",
  "style": "rounded",
  "correctionLevel": "H"
}
```

## Related
- [[shared-properties]] — Base fields
- [[sync]] — Real-time data sync
