---
type: video
label: Video
icon: video
category: controls
since: next
defaultSpan: [4, 3]
addIntent: show
pickerCategory: Media
friendlyName: Live video
oneLiner: A live camera from your hub
aliases: [camera feed, webcam, live view, stream]
depth: complete
starterPreset: {"label": "Camera"}
io:
  - emits: none
  - receives: none
fields:
  - name: label
    since: next
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label
    summary: The name shown above the picture
    does: Shows this text above the video in the label font size (8-24 pt, default 12); with no label no header row appears.
  - name: source
    since: next
    chip: Camera
    edit: inline
    depth: surface
    title: Camera
    type: string
    description: The hub's camera id to show (its direct_hello video id)
    summary: Which of the hub's cameras this shows
    does: Names the hub camera to play, by the id the hub advertises. Left empty it shows the hub's first camera. While the phone connects it says Connecting; a camera that is off or unknown shows Camera unavailable.
  - name: fit
    since: next
    edit: part
    depth: hold
    title: Fit
    type: string
    values: [{ value: fill, since: next }, { value: fit, since: next }]
    default: fill
    valueTitles: {"fill": "Fill", "fit": "Fit"}
    valueHelp: {"fill": "the picture covers the whole cell, cropping the edges", "fit": "the whole picture shows, with bars where the shapes differ"}
    description: "How the picture fills its cell: fill or fit"
    summary: Crop to fill, or show the whole picture
    does: Fill scales the picture to cover the cell and crops what overflows; fit keeps the whole picture visible with empty bars.
  - name: hideLabel
    since: next
    edit: part
    depth: hold
    title: Hide title
    type: bool
    default: false
    description: Hide the header label
    summary: Show the video without its title row
    does: On hides the title row above the video even when a label is set; off shows it.
themeFields:
  - use: cornerRadius
    summary: How round the card corners are
    does: Rounds the control's card corners from 0 to 30 pt (default 12).
  - use: surfacePrimary
    does: Fills the card behind the video with this color, default a faint white wash.
  - use: borderColor
    summary: The card's outline color
    does: Draws the card's outline in this color, default a faint white.
  - use: borderWidth
    does: Sets the outline thickness from 0 to 5 pt (default 1).
---

# Video

A live camera on the hub, played over the direct link: a peer-to-peer connection from the phone to the hub, set up through the hub's connection. Video flows only while the control is on screen, and the link closes 30 seconds after the last video control leaves.

## Type
`"video"`

## Relevant Fields
Inherits all [[shared-fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Header label |
| `source` | string | first camera | The hub's camera id |
| `fit` | string | `"fill"` | `fill` crops to cover, `fit` shows the whole picture |
| `hideLabel` | bool | `false` | Hide the header label |

## States
- **Connecting…** while the link is being made.
- **Can't connect from this network** with the line "This network blocks direct connections. It works on home Wi-Fi and most mobile networks. Support for networks like this is coming." when the network blocks direct connections.
- **Camera unavailable** when the hub has no direct link, the camera is unknown, or its status is not ok, idle or starting.
- The hub-offline notice when the hub is offline.

## Examples

### Front door
```json
{
  "type": "video",
  "id": "door",
  "position": [0, 0],
  "span": [4, 3],
  "label": "Front door",
  "source": "door"
}
```

### Whole picture, no title
```json
{
  "type": "video",
  "id": "printer",
  "position": [0, 0],
  "span": [4, 3],
  "source": "printer",
  "fit": "fit",
  "hideLabel": true
}
```

## Related
- [[shared-fields]] — Base fields
- [[web-view]] — A web page inside the layout
