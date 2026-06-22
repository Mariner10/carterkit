---
type: map
label: Map
icon: map.fill
category: controls
defaultSpan: [3, 4]
fields:
  - name: mapStyle
    type: enum
    values: [standard, satellite, hybrid]
    default: standard
    description: Map rendering style
  - name: mapInteractive
    type: bool
    default: true
    description: Allow user pan/zoom
  - name: mapZoom
    type: number
    default: 0.01
    description: Default coordinate span in degrees
  - name: label
    type: string
    description: Header label above the map
  - name: tint
    type: color
    default: "#667eea"
    description: Center point marker color
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

# Map

A MapKit view showing a coordinate center point and polyline paths. Optionally interactive.

## Type
`"map"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `mapStyle` | string | `"standard"` | `"standard"`, `"satellite"`, `"hybrid"` |
| `mapInteractive` | bool | `true` | Allow user pan/zoom |
| `mapZoom` | number | `0.01` | Default coordinate span in degrees |
| `controlHeight` | number | `120` (min) | Rendered height in points. The map is only ~120pt tall by default; set this (e.g. `300`) for a full-screen-feel map. See [[control-def]]. |
| `label` | string | — | Header label above the map |
| `tint` | string | `"#667eea"` | Center point marker color |

## Sync Payload Structure

The map receives its data as a JSON string via [[sync]]. The expected structure:

```json
{
  "center": [42.3601, -71.0589],
  "paths": [
    {
      "points": [[42.36, -71.05], [42.37, -71.06], [42.38, -71.04]],
      "color": "#FF0000"
    },
    {
      "points": [[42.35, -71.04], [42.36, -71.03]],
      "color": "#00FF00"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `center` | [lat, lng] | Map center coordinate |
| `paths` | array | Optional array of polyline paths |
| `paths[].points` | [[lat, lng], ...] | Array of coordinate pairs |
| `paths[].color` | string | Hex color for this path line |

## Examples

### Vehicle tracker
```json
{
  "type": "map",
  "id": "vehicle-location",
  "position": [0, 0],
  "span": [3, 4],
  "mapStyle": "standard",
  "mapInteractive": true,
  "mapZoom": 0.005,
  "label": "Vehicle",
  "tint": "#FF3B30",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "gps_update" }, "valuePath": "map_data" }]
}
```

### Static satellite view (non-interactive)
```json
{
  "type": "map",
  "id": "property-view",
  "position": [0, 0],
  "span": [2, 4],
  "mapStyle": "satellite",
  "mapInteractive": false,
  "mapZoom": 0.002,
  "label": "Property"
}
```

### Route history with multiple paths
```json
{
  "type": "map",
  "id": "route-map",
  "position": [0, 0],
  "span": [4, 4],
  "mapStyle": "standard",
  "mapZoom": 0.02,
  "label": "Today's Routes",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "route_history" }, "valuePath": "map_data" }]
}
```

## Behavior
- Shows a marker dot at the center coordinate with the control's `tint` color
- Paths render as polylines with their individual colors
- When no data is synced, shows a placeholder with a map icon
- Map interactions (pan/zoom) don't fire any actions — display only
- Center and paths update as new sync data arrives

## Notes
- The sync value must be a JSON string. The map control parses it internally.
- Multiple paths with different colors can show different routes, zones, etc.
- `mapZoom` is a coordinate span — smaller values = more zoomed in

## Related
- [[shared-properties]] — Base fields
- [[sync]] — How map data is received
