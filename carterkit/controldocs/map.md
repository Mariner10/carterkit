---
type: map
label: Map
icon: map.fill
category: controls
defaultSpan: [3, 4]
fields:
  - name: mapStyle
    type: enum
    values: [standard, satellite, hybrid, globe]
    default: standard
    description: Map rendering style (globe frames the whole Earth)
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
    description: Default marker color (used when a marker carries none)
  - name: mapConfig
    type: object
    description: Property→style mapping for GeoJSON feeds (marker size/color/label/ripple)
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

A MapKit view showing markers and polyline paths. Feed it the native payload or a
GeoJSON `FeatureCollection`; the camera auto-fits everything it's given. Optionally
interactive.

## Type
`"map"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `mapStyle` | string | `"standard"` | `"standard"`, `"satellite"`, `"hybrid"`, `"globe"` |
| `mapInteractive` | bool | `true` | Allow user pan/zoom |
| `mapZoom` | number | `0.01` | Default coordinate span in degrees (ignored by `"globe"`, which always frames the whole Earth) |
| `controlHeight` | number | `120` (min) | In a 2-D grid, give the map more `rowSpan` for a taller map (height = `rowSpan × rowHeight`). In a `flow` grid it is ~120pt by default — set this (e.g. `300`) for a full-screen-feel map. See [[grid-dimensions]]. |
| `label` | string | — | Header label above the map |
| `tint` | string | `"#667eea"` | Default marker color (a marker's own `color` wins) |
| `mapConfig` | object | — | Property→style mapping for GeoJSON feeds — see [[#GeoJSON payloads]] |

## Sync Payload Structure

The map receives its data as a JSON string via [[sync]] — or, since it is a
JSON-document control, as a plain JSON object/array, which the app encodes for it.
That means an [[sources|HTTP source]] can point straight at a GeoJSON endpoint with
no server in between.

### Native payload

```json
{
  "center": [42.3601, -71.0589],
  "markers": [
    { "coordinate": [42.3601, -71.0589], "color": "#FF9F0A", "size": 16, "label": "Depot" },
    { "coordinate": [42.3875, -71.0995], "color": "#FF453A", "size": 20, "label": "Stalled",
      "ripple": { "color": "#FF453A", "period": 1.4, "radius": 56 } }
  ],
  "paths": [
    {
      "points": [[42.36, -71.05], [42.37, -71.06], [42.38, -71.04]],
      "color": "#FF0000"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `center` | [lat, lng] | Optional. Drawn as a single pin only when there are no markers and no paths |
| `markers` | array | Optional array of pins |
| `markers[].coordinate` | [lat, lng] | Required. `lat` + `lng` (or `lon`/`longitude`) keys are also accepted |
| `markers[].color` | string | Hex fill; falls back to the control's `tint` |
| `markers[].size` | number | Dot diameter in points (default 12, clamped 4–60) |
| `markers[].label` | string | Text under the dot (`title` is used when absent) |
| `markers[].ripple` | bool \| object | An expanding ring animated at this marker |
| `markers[].ripple.color` | string | Ring color (default: the marker's color) |
| `markers[].ripple.period` | number | Seconds per expansion (default 1.6) |
| `markers[].ripple.radius` | number | Widest ring radius in points (default 44) |
| `paths` | array | Optional array of polyline paths |
| `paths[].points` | [[lat, lng], ...] | Array of coordinate pairs |
| `paths[].color` | string | Hex color for this path line |

`ripple` is **data**, not a wire event: it rides in the payload, so an HTTP poll can
raise it. That's different from [[pulse]], which flashes the whole control when a
MeshSocket frame arrives.

### GeoJSON payloads

A payload whose `type` is `FeatureCollection`, `Feature`, or a bare geometry is read
as GeoJSON:

- `Point` / `MultiPoint` → markers
- `LineString` / `MultiLineString` / `Polygon` rings / `MultiPolygon` → paths
- `GeometryCollection` → walked recursively

> **GeoJSON positions are `[longitude, latitude]`** — the reverse of the native
> payload's `[lat, lng]`. The app flips them for you; don't pre-flip your feed.
> A third element (elevation/depth) is ignored.

Feature `properties` style each marker. Recognized without configuration:
`color` or `marker-color`, `size` or `marker-size`, `label` or `name`, `title`,
`ripple: true`; paths read `color` or `stroke`.

For a feed you don't control, `mapConfig` points at whatever properties it *does*
have:

| `mapConfig` field | Type | Default | Description |
|-------|------|---------|-------------|
| `markerSizeProperty` | string | — | Numeric property that drives marker diameter |
| `markerSizeDomain` | [number, number] | `[0, 10]` | Input range of that property |
| `markerSizeRange` | [number, number] | `[8, 30]` | Output diameter in points (clamped at the ends) |
| `markerColorProperty` | string | — | Property holding a hex color |
| `markerLabelProperty` | string | — | Property used as the marker label |
| `rippleProperty` | string | — | Numeric property that decides which markers ripple |
| `rippleThreshold` | number | `0` | `rippleProperty >= threshold` ⇒ that marker ripples |
| `ripple` | object | — | Ring styling (`color`/`period`/`radius`) for those markers |
| `maxMarkers` | number | `400` | Cap on rendered markers — public feeds can be unbounded |

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

### Fleet map with multiple markers and a ripple
```json
{
  "type": "map",
  "id": "fleet-map",
  "position": [0, 0],
  "span": [6, 4],
  "label": "Fleet",
  "mapZoom": 0.05,
  "tint": "#FF9F0A",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "fleet_positions" }, "valuePath": "map" }]
}
```

The server broadcasts `{"msg_type":"fleet_positions","map":{"markers":[…],"paths":[…]}}` —
see [[#Native payload]] for the marker shape.

### Live USGS earthquake feed (GeoJSON over HTTP, no server)
```json
{
  "type": "map",
  "id": "quake-map",
  "position": [0, 0],
  "span": [6, 4],
  "label": "USGS — last hour",
  "mapStyle": "hybrid",
  "mapZoom": 20,
  "mapConfig": {
    "markerSizeProperty": "mag",
    "markerSizeDomain": [0, 7],
    "markerSizeRange": [6, 30],
    "markerLabelProperty": "place",
    "rippleProperty": "mag",
    "rippleThreshold": 4.0,
    "ripple": { "color": "#FF453A", "period": 1.8, "radius": 60 }
  },
  "sync": [{ "method": "http", "url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson", "interval": 300 }]
}
```

The endpoint's raw response is consumed as-is: each quake's `[lng, lat, depth]`
position becomes a marker, `properties.mag` scales it, `properties.place` labels it,
and M4.0+ quakes ripple. No `valuePath` is needed — the whole document is the payload.

### Worldwide feed on the globe
```json
{
  "type": "map",
  "id": "quake-globe",
  "position": [0, 0],
  "span": [6, 4],
  "label": "Worldwide seismicity",
  "mapStyle": "globe",
  "mapConfig": {
    "markerSizeProperty": "mag",
    "markerSizeDomain": [0, 8],
    "markerSizeRange": [5, 26],
    "markerLabelProperty": "place"
  },
  "sync": [{ "method": "http", "url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson", "interval": 300 }]
}
```

`"globe"` is the style to reach for whenever the data is global. A fitted region
can't express "the whole planet" — MapKit's Mercator projection crops a 180°
latitude span to roughly 120° of longitude in a portrait cell, so a worldwide feed
opened on a partial world you had to pinch out of. The globe style instead points
the camera at the data's centroid from ~42,000 km, which keeps every marker and
both poles in frame at any spread.

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
- Every marker renders as a colored dot with a white ring; `label`/`title` shows beneath it
- A `center` with no markers and no paths draws one pin in the control's `tint` color
- Paths render as polylines with their individual colors
- The camera auto-fits the bounding box of **all** markers and path points (padded);
  with a single point it centers there at `mapZoom`
- `mapStyle: "globe"` overrides that fit: satellite imagery with realistic
  elevation, viewed from ~42,000 km at the data's centroid, so the whole Earth is
  in frame. Use it for any worldwide feed; `mapZoom` has no effect on it
- Rippling markers animate an expanding ring at their coordinate; ripples are
  suppressed under Reduce Motion
- When no data is synced, shows a placeholder with a map icon
- Map interactions (pan/zoom) don't fire any actions — display only
- A re-broadcast that resolves to the same center is ignored, so a live feed
  doesn't fight the user's panning

## Notes
- The sync value may be a JSON string or a JSON object/array — both work
- Multiple paths with different colors can show different routes, zones, etc.
- `mapZoom` is a coordinate span — smaller values = more zoomed in. It only applies
  when there's a single point to show; multi-marker data is auto-fitted
- Legacy `{ "center": …, "paths": … }` payloads are unchanged — `markers` is additive

## Related
- [[shared-properties]] — Base fields
- [[sync]] — How map data is received
