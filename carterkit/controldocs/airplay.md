---
type: airplay
label: AirPlay
icon: airplayaudio
category: controls
since: next
defaultSpan: [1, 1]
addIntent: change
pickerCategory: Media
friendlyName: AirPlay
oneLiner: Pick where the sound plays
aliases: [route, speaker, cast, homepod, output]
depth: complete
starterPreset: {}
io:
  - emits: none
  - receives: none
fields:
  - name: tint
    since: next
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    description: Icon color (unset = the theme's text color)
    summary: The icon color
    does: Colors the AirPlay icon while the sound plays on this phone; if unset it is the theme's text color.
  - name: activeTint
    since: next
    edit: color
    depth: surface
    title: Active color
    tab: style
    type: color
    description: Icon color while playing to an AirPlay device (unset = the theme's accent color)
    summary: The icon color while playing to AirPlay
    does: Colors the AirPlay icon while the sound is going to an AirPlay device; if unset it is the theme's accent color.
colorSlots:
  - slot: icon
    default: neutral
    alias: tint
    since: next
    summary: The color of the AirPlay icon
    does: Colors the icon while the sound plays on this phone; until set it follows the neutral role, the text color.
  - slot: active
    default: primary
    alias: activeTint
    since: next
    summary: The icon color while playing to AirPlay
    does: Colors the icon while the sound goes to an AirPlay device; until set it follows the primary role, the accent.
---

# AirPlay

The `airplay` control is Apple's route picker, themed with the layout's colors and nothing
else. Tap it and the system AirPlay sheet opens: HomePods, Apple TV, speakers, several rooms
at once. It has no action and no data of its own; pair it with the [[audio]] block, whose
`route` and `airplay` player readings show where the sound is going.

## Type
`"airplay"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tint` | color | — (the theme's text color) | Icon color while the sound plays on this phone |
| `activeTint` | color | — (the theme's accent color) | Icon color while playing to an AirPlay device |

## Examples

### Speaker picker
The icon in the theme's colors, next to the play controls of a music layout.
```json
{
  "type": "airplay",
  "id": "route",
  "position": [5, 3]
}
```

### Green when playing elsewhere
A gray icon that turns green while the sound goes to a HomePod or Apple TV.
```json
{
  "type": "airplay",
  "id": "speaker",
  "position": [4, 0],
  "tint": "#8E8E93",
  "activeTint": "#34C759"
}
```

### Wide output button
A wider cell for the picker under a now-playing card, in the layout's accent color.
```json
{
  "type": "airplay",
  "id": "output",
  "position": [6, 0],
  "span": [1, 2],
  "tint": "#667eea"
}
```

## Notes

- The picker is the system's: the sheet itself cannot be restyled.
- The icon grows with its cell like a [[symbol]]'s glyph, and the Background padding insets it.
- With an AirPlay receiver, pause, seek and skip flush its buffer instead of fading.

## Related
- [[audio]] — The audio block and its player readings
- [[shared-properties]] — Base fields
