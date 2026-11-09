---
type: map
depth: complete
label: Map
icon: map.fill
category: controls
defaultSpan: [4, 4]
addIntent: show
pickerCategory: Media
friendlyName: Map
oneLiner: A place on a map
aliases: [location, gps, pin, geo, route, places]
starterPreset: {"label": "Map","mapStyle": "standard"}
io:
  - emits: none
  - receives: pins
    role: show
    type: json
    shape: {"markers": [{"coordinate": "[lat, lng]", "label": "text?", "color": "hex?", "ripple": "true?"}], "paths": [{"points": "[[lat, lng]]", "color": "hex?"}], "center": "[lat, lng]?"}
    from: [hub, mqtt, http, store]
    says: pins, each a coordinate with an optional label and color, paths through several points, and an optional center
    reacts: the pins and paths are redrawn and the camera refits to show them, until you pan or zoom yourself; a pin marked ripple pulses to ask for attention
    example: {"markers": [{"coordinate": [0, 0], "label": "Pin 1"}]}
    since: next
  - sample: {"markers": [{"coordinate": [0, 0], "label": "Pin 1"}, {"coordinate": [0.02, 0.03], "label": "Pin 2"}, {"coordinate": [-0.01, 0.05], "label": "Pin 3"}]}
    next: {"markers": [{"coordinate": [0, 0], "label": "Pin 1"}, {"coordinate": [0.04, 0.03], "label": "Pin 2"}, {"coordinate": [-0.01, 0.05], "label": "Pin 3"}]}
fields:
  - name: mapStyle
    category: look
    edit: look
    depth: surface
    title: Map style
    tab: style
    type: enum
    values: [standard, satellite, hybrid, globe]
    default: standard
    description: Map rendering style (globe frames the whole Earth)
    summary: Which kind of map to draw
    does: Draws the map as a street map, satellite photos, photos with labels, or a whole-Earth globe.
    valueHelp: {"standard": "a normal street map", "satellite": "satellite photos with no labels", "hybrid": "satellite photos with street and place labels", "globe": "the whole Earth seen from space, ignoring Zoom"}
    valueTitles: {"standard": "Standard", "satellite": "Satellite", "hybrid": "Hybrid", "globe": "Globe"}
    valueSymbols: {"standard": "map.fill", "satellite": "globe.americas.fill", "hybrid": "map", "globe": "globe"}
  - name: mapInteractive
    effect: behavior
    edit: switch
    depth: hold
    title: Pan and zoom
    type: bool
    default: true
    description: Allow user pan/zoom
    summary: Let people drag and zoom
    does: When on you can pan and zoom the map with your fingers; off locks the view.
  - name: mapZoom
    edit: scrub
    depth: surface
    title: Zoom
    bounds: none
    step: 0.01
    type: number
    default: 0.01
    description: Default coordinate span in degrees
    summary: How close the map starts
    does: Sets how much ground a single-point view shows, as a span in degrees; smaller zooms in closer.
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label above the map
    summary: A title above the map
    does: Shows this text as a header above the map.
  - name: tint
    edit: color
    depth: surface
    title: Pin color
    tab: style
    type: color
    default: "#667eea"
    description: Default marker color (used when a marker carries none)
    summary: Color of the pins
    does: Colors every pin that does not bring its own color.
  - name: mapConfig
    chip: Map
    type: object
    description: Property→style mapping for GeoJSON feeds (marker size/color/label/ripple)
    summary: Teach the map a feed
    does: Tells the map which properties of your data set pin size, color, label and ripple.
  - name: markerStyle
    since: next
    group: mapConfig
    edit: look
    depth: hold
    under: mapStyle
    title: Pin style
    type: enum
    values: [dot, symbol, puck]
    default: dot
    description: How each pin is drawn (mapConfig.markerStyle)
    summary: Dots, bare symbols or symbols in a circle
    does: Draws each pin as a plain dot, a bare SF Symbol (named by mapConfig.markerSymbol), or a symbol inside a filled circle.
    valueHelp: {"dot": "a plain round dot", "symbol": "a bare symbol such as an airplane", "puck": "a symbol inside a filled circle"}
    valueTitles: {"dot": "Dot", "symbol": "Symbol", "puck": "Puck"}
    valueSymbols: {"dot": "circle.fill", "symbol": "airplane", "puck": "mappin.circle.fill"}
  - name: recenter
    since: next
    group: mapConfig
    edit: look
    depth: hold
    under: mapStyle
    title: Camera follows
    type: enum
    values: [auto, always, initial, "off"]
    default: auto
    description: How the camera reacts to new data (mapConfig.recenter)
    summary: Whether the map keeps re-framing the pins
    does: Chooses when the camera refits to the pins as new data arrives.
    valueHelp: {"auto": "frames and follows the pins, but stops once you pan or zoom yourself", "always": "refits to the pins on every update", "initial": "frames the pins once and then stays put", "off": "never moves the camera"}
    valueTitles: {"auto": "Auto", "always": "Always", "initial": "Once", "off": "Off"}
    valueSymbols: {"auto": "location.fill", "always": "arrow.triangle.2.circlepath", "initial": "scope", "off": "location.slash.fill"}
  - name: markerSizeProperty
    edit: key
    depth: hold
    title: Pin size
    since: next
    group: mapConfig
    type: string
    description: Numeric feed property that drives pin size (mapConfig.markerSizeProperty), scaled from markerSizeDomain into markerSizeRange
    summary: Which number in your feed sets each pin's size
    does: Sizes each pin from this number in your data, so bigger readings draw bigger pins.
  - name: markerSizeDomain
    since: next
    group: mapConfig
    type: number[]
    default: [0, 10]
    description: Input range [low, high] of markerSizeProperty (mapConfig.markerSizeDomain)
    summary: The lowest and highest reading to expect
    does: Treats readings at the low end as the smallest pin and at the high end as the largest.
  - name: markerSizeRange
    since: next
    group: mapConfig
    type: number[]
    default: [8, 30]
    description: Output pin diameter range [smallest, largest] in points (mapConfig.markerSizeRange)
    summary: How small and how large pins can get
    does: Sets the smallest and largest pin size in points.
  - name: markerColorProperty
    edit: key
    depth: hold
    title: Pin colour
    since: next
    group: mapConfig
    type: string
    description: Feed property holding a hex color for each pin (mapConfig.markerColorProperty)
    summary: Which value in your feed colors each pin
    does: Colors each pin with the hex color found under this name in your data.
  - name: markerLabelProperty
    edit: key
    depth: hold
    title: Pin label
    since: next
    group: mapConfig
    type: string
    description: Feed property used as each pin's label (mapConfig.markerLabelProperty)
    summary: Which value in your feed names each pin
    does: Writes this value from your data beside each pin.
  - name: rippleProperty
    edit: key
    depth: hold
    title: Ripple on
    since: next
    group: mapConfig
    type: string
    description: Numeric feed property that decides which pins ripple (mapConfig.rippleProperty)
    summary: Which number in your feed makes a pin pulse
    does: Pulses a ring around every pin whose reading here reaches the ripple threshold.
  - name: rippleThreshold
    since: next
    group: mapConfig
    type: number
    bounds: none
    default: 0
    description: rippleProperty >= rippleThreshold makes that pin ripple (mapConfig.rippleThreshold)
    summary: How high a reading must be to pulse
    does: Pulses only the pins whose reading is at least this number.
  - name: ripple
    since: next
    group: mapConfig
    type: object
    description: "Ring styling for rippling pins: color, period (s, default 1.6), radius (pt, default 44) (mapConfig.ripple)"
    summary: How the pulsing ring looks
    does: Sets the ring's color, how long one pulse takes, and how wide it grows.
  - name: maxMarkers
    since: next
    group: mapConfig
    type: number
    min: 1
    max: 5000
    default: 400
    description: Cap on drawn pins; a public feed can be unbounded (mapConfig.maxMarkers)
    summary: The most pins the map draws
    does: Draws at most this many pins, so a huge feed stays smooth.
  - name: center
    since: next
    group: mapConfig
    type: number[]
    description: Fixed camera centre [lat, lng] instead of fitting the data; combines with recenter (mapConfig.center)
    summary: A fixed spot the map always looks at
    does: Points the map at this latitude and longitude instead of framing the pins.
  - name: markersPath
    edit: key
    depth: hold
    title: Places list
    since: next
    group: mapConfig
    type: string
    description: Dot-path to the array of point objects in a non-GeoJSON payload, e.g. "ac" (mapConfig.markersPath)
    summary: Where the list of places sits in your feed
    does: Reads the pins from the list found under this name in your data.
  - name: markerLatProperty
    edit: key
    depth: hold
    title: Latitude
    since: next
    group: mapConfig
    type: string
    description: Property holding latitude on each point object, e.g. "lat"; switches to object-array mode (mapConfig.markerLatProperty)
    summary: Which value in your feed is the latitude
    does: Places each pin at the latitude found under this name.
  - name: markerLngProperty
    edit: key
    depth: hold
    title: Longitude
    since: next
    group: mapConfig
    type: string
    description: Property holding longitude on each point object, e.g. "lon" (mapConfig.markerLngProperty)
    summary: Which value in your feed is the longitude
    does: Places each pin at the longitude found under this name.
  - name: markerIdProperty
    edit: key
    depth: hold
    title: Pin identity
    since: next
    group: mapConfig
    type: string
    description: Property giving each pin a stable identity across updates; needed for smooth motion (mapConfig.markerIdProperty)
    summary: Which value tells pins apart between updates
    does: Keeps each pin the same pin across updates, so it glides instead of jumping.
  - name: coordinateOrder
    since: next
    group: mapConfig
    type: enum
    values: [lnglat, latlng]
    default: lnglat
    description: Order of raw [a, b, weight] number triples, GeoJSON-style lnglat or latlng (mapConfig.coordinateOrder)
    summary: Whether your numbers list longitude or latitude first
    does: Reads each number pair as longitude then latitude, or latitude then longitude.
    valueHelp: {"lnglat": "each pair is longitude then latitude, the GeoJSON order", "latlng": "each pair is latitude then longitude"}
    valueTitles: {"lnglat": "Lng, Lat", "latlng": "Lat, Lng"}
    valueSymbols: {"lnglat": "arrow.right", "latlng": "arrow.down"}
  - name: minWeight
    since: next
    group: mapConfig
    type: number
    bounds: none
    description: In number-triple mode, drop points whose weight is below this before capping (mapConfig.minWeight)
    summary: The weakest reading still worth a pin
    does: Leaves out points whose weight is below this number, keeping the strongest ones.
  - name: markerSymbol
    since: next
    group: mapConfig
    type: string
    description: Default SF Symbol name for the symbol and puck pin styles, e.g. "airplane" (mapConfig.markerSymbol)
    summary: The symbol every pin uses
    does: Draws this symbol for each pin when the pin style is symbol or puck.
  - name: markerSymbolProperty
    edit: key
    depth: hold
    title: Pin symbol
    since: next
    group: mapConfig
    type: string
    description: Per-object property naming an SF Symbol, overriding markerSymbol (mapConfig.markerSymbolProperty)
    summary: Which value in your feed picks each pin's symbol
    does: Gives each pin the symbol named under this value in your data.
  - name: motion
    since: next
    group: mapConfig
    type: bool
    default: false
    description: Glide pins between updates instead of snapping; needs markerIdProperty with more than one pin (mapConfig.motion)
    summary: Pins glide to their new spot
    does: Moves each pin smoothly to its new position when fresh data arrives.
  - name: motionDuration
    since: next
    group: mapConfig
    type: number
    min: 0
    max: 60
    default: 1.2
    description: Seconds one position glide takes; set near the poll interval (mapConfig.motionDuration)
    summary: How long each glide takes
    does: Takes this many seconds to move a pin to its new spot.
  - name: hideLabel
    since: next
    edit: part
    depth: hold
    title: Hide title
    type: bool
    default: false
    description: Hide the header label above the map
    summary: Show the map without its title row
    does: On hides the title row above the map even when a label is set; off shows it.
  - name: controlHeight
    effect: behavior
    edit: scrub
    depth: hold
    under: mapStyle
    title: Height
    min: 120
    max: 1200
    step: 10
    type: number
    description: Map height in points in a flow-mode grid (2-D grids size it by rowSpan)
    summary: How tall the map is
    does: Sets the map height from 120 to 1200 points when the grid flows; 2-D grids use row span instead.
themeFields:
  - use: cornerRadius
    does: Rounds the map corners from square (0) to 30 points.
  - use: controlPadding
    summary: The room inside the control
    does: Sets the padding inside the map frame, 0 to 24 points.
  - use: surfacePrimary
    summary: The colour behind the control
    does: Fills the map card background with this color.
  - use: secondaryColor
    summary: Quieter text color
    does: Colors the secondary text on the map.
  - use: borderColor
    summary: Outline color
    does: Colors the line around the map.
  - use: borderWidth
    summary: Outline thickness
    does: Sets how thick the outline is, 0 to 5 points.
  - use: labelFontSize
    summary: Label text size
    does: Sets the size of the header label text, 8 to 24 points.
  - use: accentColor
    summary: Highlight color
    does: Sets the accent tint used on the map.
  - use: surfaceSecondary
    summary: Backdrop color
    does: Fills the secondary surface behind map details with this color.
colorSlots:
  - slot: main
    default: primary
    alias: tint
    since: next
    summary: The color of the pins
    does: Colors the markers and the center dot, unless a marker has its own color; until a palette sets primary it keeps the map's own blue (667EEA).
  - slot: route
    default: "#FF0000"
    since: next
    summary: The color of the routes
    does: Draws every path that has no color of its own; until set it is red.
---

# Map

A MapKit view showing markers and polyline paths. Feed it the native payload or a
GeoJSON `FeatureCollection`; the camera auto-fits everything it's given. Optionally
interactive.

## Type
`"map"`

## Relevant Fields
Inherits all [[shared-fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `mapStyle` | string | `"standard"` | `"standard"`, `"satellite"`, `"hybrid"`, `"globe"` |
| `mapInteractive` | bool | `true` | Allow user pan/zoom |
| `mapZoom` | number | `0.01` | Default coordinate span in degrees (ignored by `"globe"`, which always frames the whole Earth) |
| `controlHeight` | number | `120` (min) | In a 2-D grid, give the map more `rowSpan` for a taller map (height = `rowSpan × rowHeight`). In a `flow` grid it is ~120pt by default — set this (e.g. `300`) for a full-screen-feel map. See [[grid-dimensions]]. |
| `label` | string | — | Header label above the map |
| `tint` | string | `"#667eea"` | Default marker color (a marker's own `color` wins) |
| `mapConfig` | object | — | Property→style mapping for GeoJSON feeds — see [[#GeoJSON payloads]] |
| `mapConfig.markerStyle` | enum | `"dot"` | `dot`, `symbol` or `puck` — see [[#Marker style & SF Symbols]] |
| `mapConfig.recenter` | enum | `"auto"` | `auto`, `always`, `initial` or `off` — see [[#Motion & camera]] |
| `hideLabel` | bool | `false` | Hide the header label |

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

### Object-array feeds (not GeoJSON)

Many public feeds are plain-JSON arrays of point objects, not GeoJSON — a flight feed
`{ "ac": [ { "lat": …, "lon": …, "flight": … } ] }`, a single-point tracker (the ISS:
`{ "latitude": …, "longitude": … }`), or a raw `[lng, lat, weight]` grid. Point the map
at those by naming the coordinate fields; all the styling keys above still apply (their
"property" is a key on each object). Declaring `markersPath` or `markerLatProperty`
switches the map into this mode — ordinary payloads are unaffected.

| `mapConfig` field | Type | Default | Description |
|-------|------|---------|-------------|
| `markersPath` | string | — | Dot-path to the array of objects (e.g. `"ac"`). Omit if the payload *is* the array, or a single point object. |
| `markerLatProperty` / `markerLngProperty` | string | — | Latitude/longitude keys on each object. `lat`/`lon`/`latitude`/`longitude` are auto-detected when omitted. |
| `markerIdProperty` | string | — | Stable identity per marker across polls — **required for smooth `motion`** with more than one marker (e.g. `"hex"`). |
| `coordinateOrder` | string | `"lnglat"` | For raw `[a, b, weight]` number triples (e.g. NOAA aurora): `"lnglat"` or `"latlng"`. The third element feeds size (`markerSizeDomain`) and ripple. |
| `minWeight` | number | `0` | Number-triple mode: drop points weaker than this before the `maxMarkers` cap keeps the strongest. |

### Marker style & SF Symbols

| `mapConfig` field | Type | Default | Description |
|-------|------|---------|-------------|
| `markerStyle` | enum | `"dot"` | `dot`, `symbol` (a bare SF Symbol), or `puck` (an SF Symbol inside a filled circle). |
| `markerSymbol` | string | — | Default SF Symbol name for `symbol`/`puck` (e.g. `"airplane"`). |
| `markerSymbolProperty` | string | — | Per-object property giving an SF Symbol name, overriding `markerSymbol`. A feed property named `symbol`/`sf-symbol` is honored without config. |

### Motion & camera

| `mapConfig` field | Type | Default | Description |
|-------|------|---------|-------------|
| `motion` | bool | `false` | Smoothly **interpolate** marker positions between polls so they glide instead of teleporting. Needs `markerIdProperty` for >1 marker. |
| `motionDuration` | number | `1.2` | Seconds a glide takes — set near your poll interval. |
| `recenter` | enum | `"auto"` | How the camera reacts to new data: `auto` (frame + follow, but **stop the moment the user pans/zooms**), `always` (refit every update), `initial` (frame once), `off` (never move). |
| `center` | [lat, lng] | — | Pin the camera to a fixed point (and the control's `mapZoom`) instead of fitting the data's bounds — e.g. frame a high-latitude feed. |

### Example — live flight radar, no server

```json
{
  "type": "map", "id": "flights", "position": [0, 0], "span": [8, 4],
  "mapStyle": "hybrid", "mapZoom": 3.2, "tint": "#30D158",
  "mapConfig": {
    "markersPath": "ac", "markerLatProperty": "lat", "markerLngProperty": "lon",
    "markerIdProperty": "hex", "markerLabelProperty": "flight",
    "markerStyle": "puck", "markerSymbol": "airplane",
    "motion": true, "motionDuration": 8, "recenter": "initial", "maxMarkers": 200
  },
  "sync": [{ "method": "http", "url": "https://api.adsb.lol/v2/lat/40.7/lon/-74/dist/100", "interval": 8 }]
}
```

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
- [[shared-fields]] — Base fields
- [[sync]] — How map data is received
