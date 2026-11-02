---
type: glance-lock-screen
label: Lock Screen
icon: lock.iphone
category: system
fields:
  - name: lockScreen
    type: object
    description: Glance field. The lock-screen Live Activity banner, a scene (rows of tiles). Defaults to island.expanded.bottom. A bare tile is accepted and becomes one row
  - name: columns
    type: number
    description: Scene field. Columns the banner lays out against; defaults to the widest row, capped at 12
    min: 1
    max: 12
    step: 1
  - name: rows
    type: object[]
    description: Scene field. Rows of tiles; each row is an array of tile objects (see [[glance]])
constraints: {"surface":"lock-screen","requires":"liveActivity true, or live.activity.start other than never","banner":{"field":"lockScreen","accepts":"scene","default":"island.expanded.bottom","sceneColumnsMax":12,"interactive":true,"interactiveNeedsAuthorDeclaredControl":true,"limits":{"stateBytesPerUpdate":4096,"maxSessionHours":8},"allowedTiles":["value","gauge","ring","bar","light","sparkline","text","icon","spacer","timer","freshness","toggle","button","step","open"]},"accessoryFamilies":{"widgetField":"widgets[].families","accessoryCircular":{"maxTiles":1,"allowedTiles":["gauge","ring","value"]},"accessoryRectangular":{"maxRows":1,"allowedTiles":["value","text","icon","spacer","timer","freshness"]},"accessoryInline":{"maxTiles":1,"allowedTiles":["value"]},"monochrome":true,"interactive":false},"corners":{"via":"glance.controls","kinds":["toggle","button","cycle","step","set"],"placedBy":"the user"}}
---

Three things live on the Lock Screen, and they are configured in three places:

| What | Declared in | Notes |
|---|---|---|
| The **banner** of a running Live Activity | `lockScreen` (this page) | a scene; defaults to `expanded.bottom` of the island |
| **Accessory widgets** (circular, rectangular, inline) | `widgets[]` with those `families`, see [[widgets]] | monochrome, not interactive |
| **Corner controls** | `controls[]`, see [[control-center]] | toggle and button only to iOS; the user places them |

The banner needs a running Live Activity, so it follows the rules in
[[live-activity]]: `"liveActivity": true` (or `live.activity.start`), 4 KB of state per
update, 8 hours per session. Its scene is drawn with the same tiles as everywhere
else ([[glance]]), in the app's Glass look.

## Banner

The banner is wider and taller than the island's bottom region, so a scene of two or
three rows fits. Interactive tiles (`toggle`, `button`, `step`) show only for
controls the author declared in `glance.controls[]`, so declare the ones you want to
press from the banner; auto-derived controls stay pick-list-only.

If you leave `lockScreen` out, the banner repeats `island.expanded.bottom`. Write it
when the banner should show more than the island can.

## Accessory widgets

Accessory families are small and drawn in the system's monochrome, so a gauge arc
reads as a smudge where a number reads as a number. The re-flow rules, applied when
you give no override:

- `accessoryRectangular`: the first row, non-interactive tiles drawn as values.
- `accessoryCircular`: the first `gauge` or `ring`, else the first bound `value`.
- `accessoryInline`: "label value" of the first bound tile.

Give an override (`"accessoryCircular": { "rows": [[ … ]] }` inside the widget) to
choose the tile yourself.

## Constraints

The frontmatter `constraints` block lists, as JSON, the banner's limits, the three
accessory families with their tile limits and allowed tiles, and the corner-control
kinds. Interactive tiles are not offered on accessories: iOS shows no controls in
those slots.

## Examples

### Banner with two rows

A status row and a control row, with the controls declared so the buttons show.

```json
{
  "liveActivity": true,
  "controls": [
    { "id": "pause", "kind": "button", "label": "Pause", "control": "pause" },
    { "id": "lights", "kind": "toggle", "label": "Lights", "control": "lights-toggle" }
  ],
  "lockScreen": {
    "rows": [
      [ { "tile": "gauge", "control": "nozzle" }, { "tile": "ring", "control": "progress" }, { "tile": "timer", "control": "eta" } ],
      [ { "tile": "button", "control": "pause" }, { "tile": "toggle", "control": "lights-toggle" } ]
    ]
  }
}
```

### Banner as a single tile

A bare tile is accepted where a scene is expected and becomes one row.

```json
{
  "liveActivity": true,
  "lockScreen": { "tile": "bar", "control": "progress" }
}
```

### Circular accessory with a status row

A circular lock-screen widget that shows the print progress ring, beside a rectangular one.

```json
{
  "widgets": [
    { "id": "lock", "title": "Print progress",
      "families": ["accessoryCircular", "accessoryRectangular"],
      "scene": { "rows": [ [ { "tile": "ring", "control": "progress" }, { "tile": "value", "control": "nozzle" } ] ] } }
  ]
}
```
