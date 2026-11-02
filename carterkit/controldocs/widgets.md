---
type: glance-widgets
label: Glance Widgets
icon: rectangle.grid.2x2
category: system
fields:
  - name: id
    type: string
    description: Stable id within the layout; the widget gallery offers "<title> · <layout>" per id. An entry with no id cannot be offered
  - name: title
    type: string
    description: Gallery name (defaults to the id)
  - name: icon
    type: string
    description: SF Symbol glyph shown in the gallery
  - name: families
    type: string[]
    description: Any of systemSmall systemMedium systemLarge systemExtraLarge accessoryCircular accessoryRectangular accessoryInline. Absent or empty means every family
  - name: scene
    type: object
    description: The base scene (rows of tiles), re-flowed per family unless that family has an override
  - name: columns
    type: number
    description: Scene field. Columns the scene lays out against; defaults to the widest row, capped at 12
    min: 1
    max: 12
    step: 1
  - name: rows
    type: object[]
    description: Scene field. Rows of tiles; each row is an array of tile objects (see [[glance]] for the tile table)
  - name: systemSmall
    type: object
    description: Optional scene override for that family, same shape as scene. The same applies to systemMedium, systemLarge, systemExtraLarge, accessoryCircular, accessoryRectangular and accessoryInline
constraints: {"surface":"widgets","sceneColumnsMax":12,"familyNames":["systemSmall","systemMedium","systemLarge","systemExtraLarge","accessoryCircular","accessoryRectangular","accessoryInline"],"familyDefault":"all","overrideKeys":"any family name","families":{"systemSmall":{"maxRows":1,"reflow":"first row only","interactive":true,"allowedTiles":["value","gauge","ring","bar","light","sparkline","text","icon","spacer","timer","freshness","toggle","button","step","open"]},"systemMedium":{"maxRows":null,"reflow":"as authored","interactive":true,"allowedTiles":["value","gauge","ring","bar","light","sparkline","text","icon","spacer","timer","freshness","toggle","button","step","open"]},"systemLarge":{"maxRows":null,"reflow":"as authored","interactive":true,"allowedTiles":["value","gauge","ring","bar","light","sparkline","text","icon","spacer","timer","freshness","toggle","button","step","open"]},"systemExtraLarge":{"maxRows":null,"reflow":"as authored","interactive":true,"allowedTiles":["value","gauge","ring","bar","light","sparkline","text","icon","spacer","timer","freshness","toggle","button","step","open"]},"accessoryCircular":{"maxRows":1,"maxTiles":1,"reflow":"first gauge or ring, else first bound value","interactive":false,"allowedTiles":["gauge","ring","value"]},"accessoryRectangular":{"maxRows":1,"reflow":"first row; non-interactive tiles drawn as values, monochrome","interactive":false,"allowedTiles":["value","text","icon","spacer","timer","freshness"]},"accessoryInline":{"maxRows":1,"maxTiles":1,"reflow":"first bound tile as label and value","interactive":false,"allowedTiles":["value"]}}}
---

A **widget** is a scene (rows of tiles) the user places on the Home Screen, Lock
Screen, StandBy or CarPlay through the **CAR-TER Scene** widget. Declare them in
`glance.widgets[]`. This page is the reference for the widget block; the tile
vocabulary lives in [[glance]], the other surfaces in [[live-activity]],
[[lock-screen]] and [[control-center]].

A layout that declares no `widgets` still offers the zero-config **Layout Glance**
(hero + slots) and **Control Value** (any single control) widgets.

## How a scene fits each family

One `scene` serves every family; the app re-flows it to what the family can show.
An entry under the family's own name always wins over the re-flow.

| Family | What renders from the base `scene` | Interactive tiles |
|---|---|---|
| `systemSmall` | the first row only | yes |
| `systemMedium` `systemLarge` `systemExtraLarge` | the scene as authored (columns capped at 12) | yes |
| `accessoryRectangular` | the first row, non-interactive tiles drawn as values, monochrome | no |
| `accessoryCircular` | one tile: the first `gauge` or `ring`, else the first bound `value`, else the first bound tile | no |
| `accessoryInline` | one tile as "label value": the first bound tile | no |

So design for the smallest family you list: put the tiles that matter most in the
**first row**, and add per-family overrides where the re-flow is not what you want.
A widget lists its `families`; leave `families` out to offer every one.

## Constraints

The `constraints` block in this page's frontmatter carries the same limits as JSON
for tools: per family the `maxRows`, `maxTiles` (where the family takes one), the
`reflow` rule and the `allowedTiles`. `maxRows: null` means the code sets no limit
(iOS does: widgets do not scroll, so keep to what fits). Rules enforced when a layout loads
(`SurfaceSceneValidator`, shown in the connection console):

- A row wider than the scene's columns is clipped; a tile may not span more columns than the scene has.
- A tile that needs a number (`gauge` `ring` `bar` `sparkline` `timer` `step`) must bind a numeric control.
- `toggle` binds a toggle control; `step` binds a slider or stepper.
- A pressed tile needs an action to send, and from a widget only MeshSocket and `open` actions can fire.
- An unknown control id drops that tile and nothing else; an unknown tile kind renders as `value`.

## Examples

### Temperature widget

One scene for medium, with a one-gauge override for small and a ring for the lock screen.

```json
{
  "widgets": [
    { "id": "temps", "title": "Temps", "icon": "thermometer.medium",
      "families": ["systemSmall", "systemMedium", "accessoryCircular"],
      "scene": { "rows": [
        [ { "tile": "gauge", "control": "nozzle" }, { "tile": "gauge", "control": "bed" } ],
        [ { "tile": "sparkline", "control": "nozzle", "span": 2 } ]
      ] },
      "systemSmall": { "rows": [ [ { "tile": "gauge", "control": "nozzle" } ] ] },
      "accessoryCircular": { "rows": [ [ { "tile": "ring", "control": "progress" } ] ] } }
  ]
}
```

### Control widget

Interactive tiles on a medium widget: a toggle and a step button under a status row.

```json
{
  "widgets": [
    { "id": "console", "title": "Console", "families": ["systemMedium"],
      "scene": { "rows": [
        [ { "tile": "light", "control": "state" }, { "tile": "timer", "control": "eta" }, { "tile": "freshness" } ],
        [ { "tile": "toggle", "control": "lights-toggle" }, { "tile": "step", "control": "fan-speed", "delta": 10 } ]
      ] } }
  ]
}
```

### Lock screen readout

A rectangular accessory: one row, values only, tiles drawn monochrome.

```json
{
  "widgets": [
    { "id": "print", "title": "Print", "families": ["accessoryRectangular", "accessoryInline"],
      "scene": { "rows": [
        [ { "tile": "value", "control": "progress", "label": "Done" }, { "tile": "value", "control": "nozzle" } ]
      ] } }
  ]
}
```
