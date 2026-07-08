---
type: chord
label: Chord
icon: circle.hexagonpath.fill
category: controls
defaultSpan: [3, 3]
fields:
  - name: label
    type: string
    description: Header label above the diagram
  - name: chordConfig
    type: object
    description: Full configuration object (see ChordConfig section)
  - name: tint
    type: color
    default: "#667eea"
    description: First-group color and palette seed
  - name: formatValue
    type: string
    description: Formatter for group totals
  - name: arcAction
    type: object
    description: arcAction
    group: chordConfig
  - name: colors
    type: string[]
    description: Group color cycle (payload colors wins)
    group: chordConfig
  - name: pad
    type: number
    default: 2.5
    description: Degrees of breathing room between arcs
    group: chordConfig
  - name: ribbonOpacity
    type: number
    default: 0.4
    description: Ribbon opacity (selection brightens involved ribbons)
    group: chordConfig
  - name: scrub
    type: bool
    default: false
    description: Drag around the ring sweeps the spotlight arc-to-arc like a dial, with haptic ticks (the action still fires on tap)
    group: chordConfig
  - name: showLabels
    type: bool
    default: true
    description: Group names around the rim
    group: chordConfig
themeFields:
  - name: cornerRadius
    type: number
    default: 12
    description: Control corner radius
  - name: surfacePrimary
    type: color
    default: #FFFFFF0F
    description: Background fill
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Group label color
---

# Chord

Who talks to whom: groups as arcs around a circle, relationships as ribbons
through the middle, ribbon width ∝ flow. Feed it a matrix — service-to-service
traffic, team hand-offs, trade between regions. Tapping an arc **spotlights
that group's ribbons** (the rest fade to a whisper) and fires `arcAction` with
the group's total, so the diagram doubles as a focus picker.

## Type
`"chord"`

## Recommended Size
Square — `[3, 3]`. The control keeps itself round and leaves a rim gutter for
labels.

## Relevant Fields
Inherits all [[control-def|shared fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Header label (selection readout appears beside it) |
| `chordConfig` | [[#ChordConfig]] | — | Full configuration object (all optional) |
| `tint` | string | `"#667eea"` | First-group color / palette seed |
| `formatValue` | string | — | Formatter for total readouts |
| `action` | [[actions\|ActionDefinition]] | — | Fallback for `arcAction` |

## ChordConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `showLabels` | bool | `true` | Group names around the rim |
| `pad` | number | `2.5` | Degrees of breathing room between arcs |
| `ribbonOpacity` | number | `0.4` | Ribbon opacity (selection brightens involved ribbons) |
| `colors` | string[] | built-in palette | Group color cycle (payload `colors` wins) |
| `arcAction` | [[actions\|ActionDefinition]] | — | Fired on arc tap; `{{value}}` = `{"label", "total"}` |
| `scrub` | bool | `false` | Drag around the ring sweeps the spotlight arc-to-arc like a dial, with haptic ticks (the action still fires on tap) |

## Sync Payload Structure

Labels plus a square matrix — `matrix[i][j]` is the flow from group `i` to
group `j`. A symmetric matrix reads as undirected relationship strength:

```json
{
  "labels": ["API", "Web", "DB", "Cache"],
  "colors": ["#667eea", "#34C759", "#FF9500", "#BF5AF2"],
  "matrix": [
    [0, 5, 3, 2],
    [5, 0, 1, 0],
    [3, 1, 0, 4],
    [2, 0, 4, 0]
  ]
}
```

Arc size ∝ the group's row sum (pure receivers use their incoming total so
they still show). Each ribbon end is sized by that direction's flow, so an
asymmetric matrix tapers honestly.

## Examples

### Service mesh traffic
```json
{
  "type": "chord",
  "id": "mesh-traffic",
  "position": [0, 0],
  "span": [3, 3],
  "label": "Calls/min",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "mesh_matrix" }, "valuePath": "chord" }]
}
```

### Tap-to-focus hand-off board
```json
{
  "type": "chord",
  "id": "handoffs",
  "position": [0, 0],
  "span": [3, 3],
  "label": "Hand-offs",
  "chordConfig": {
    "arcAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast", "payload": { "msg_type": "focus_team", "team": "{{value}}" } }
  },
  "defaultValue": "{\"labels\":[\"Design\",\"Build\",\"QA\"],\"matrix\":[[0,6,1],[2,0,5],[1,3,0]]}"
}
```

## Behavior
- Arcs start at 12 o'clock and run clockwise; labels stay horizontal, anchored away from the rim
- Tap an arc to spotlight its ribbons + fire `arcAction`; tap again or tap outside the ring to clear
- `scrub: true` turns the ring into a dial — dragging sweeps the spotlight with a tick at every arc boundary
- Ribbons blend a gradient between their two group colors
- Dataset pushes animate via the control's `animation` profile

## Notes
- 3–8 groups read best; the rim gets crowded past that
- Self-flows (`matrix[i][i]`) are ignored
- For staged/directional flow use [[sankey]]; for arbitrary topology use [[graph]]

## Related
- [[sankey]] — staged flow volumes
- [[graph]] — force-directed node-link
- [[pie-chart]] — one group's share of a whole
- [[sync]] — how matrices arrive
- [[actions]] — how `arcAction` fires
