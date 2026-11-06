---
type: group-def
depth: complete
label: Group Definition
icon: square.grid.3x3.square
category: models
fields:
  - name: type
    title: Type
    values: [group]
    type: enum
    description: Discriminator; always group (required)
    summary: Always group
    does: Marks this entry as a group card rather than a control.
    valueHelp: {"group": "the only value; a container card with its own grid"}
  - name: id
    title: ID
    type: string
    description: Unique identifier among the layout's controls and groups (required)
    summary: Its unique name
    does: Lets bindings, visibility and expand triggers point at this group; no two things in a layout share one.
  - name: name
    title: Name
    type: string
    description: Readable name the editor shows for this group; never used for identity
    summary: A friendly name for the editor
    does: Labels the group in the editor lists; nothing on the page shows it.
  - name: label
    edit: inline
    depth: surface
    title: Header
    type: string
    description: Header text shown above the group; absent or null for no header
    summary: The title at the top of the card
    does: Shows this text as a header above the group; leave it out for no header.
  - name: position
    title: Position
    type: array
    description: Zero-indexed [row, col] grid cell within the parent (required)
    summary: Which cell it starts in
    does: Puts the group's top-left corner at this row and column of the page.
  - name: span
    title: Size
    type: array
    description: "[rowSpan, colSpan] grid cells occupied (default [1, 1])"
    summary: How many cells it covers
    does: Makes the group this many rows and columns big on the page; default one cell.
  - name: landscape
    title: Landscape place
    type: object
    description: "This group's cell when an iPhone is on its side: {position, span} or {hidden: true}"
    summary: Its place when the phone is on its side
    does: Moves or hides the group when an iPhone is turned sideways.
  - name: regular
    title: Tablet place
    type: object
    description: "This group's cell on an iPad-width page: {position, span} or {hidden: true}"
    summary: Its place on an iPad
    does: Moves or hides the group on an iPad-width page.
  - name: grid
    title: Inner grid
    type: object
    description: Internal grid for the group's children (a grid-dimensions object; required)
    summary: The cells inside the card
    does: Sets the columns, rows, row height and scale the group's controls are laid out on.
  - name: columns
    group: grid
    title: Columns
    edit: scrub
    depth: surface
    min: 1
    max: 12
    step: 1
    type: number
    description: Columns of the group's inner grid (grid.columns; the editor offers 1 to 12, as for a tab)
    summary: How many columns the group's controls share
    does: "Splits the group's card into this many equal columns (1 to 12); its controls sit on them."
  - name: rows
    group: grid
    title: Rows
    edit: scrub
    depth: surface
    min: 1
    max: 50
    step: 1
    type: number
    description: Rows of the group's inner grid (grid.rows)
    summary: How many rows the group's card holds
    does: "Gives the group's card this many rows of cells (1 to 50); more rows fit more controls."
  - name: rowHeight
    group: grid
    title: Row height
    edit: scrub
    unit: pt
    depth: hold
    under: rows
    min: 12
    max: 200
    step: 1
    default: 56
    type: number
    description: Points per row of the group's inner grid (grid.rowHeight; default 56)
    summary: How tall each row of the group is
    does: "Makes every row of the group's card this many points tall (12 to 200); Default goes back to 56."
  - name: scale
    group: grid
    title: Scale
    edit: scrub
    depth: hold
    under: rows
    min: 0.3
    max: 1.5
    step: 0.05
    default: 1
    type: number
    description: "Size the group's controls draw at (grid.scale): a number from 0.3 to 1.5, or \"auto\" (rowHeight / 56); default 1. See Scale"
    summary: How big the group's controls are drawn
    does: "Draws every control in the group smaller or bigger, text, padding, corners and icons together, so a fine grid of short rows holds whole controls; taps still get a full-size target. Default goes back to 1."
  - name: children
    title: Contents
    type: object[]
    description: Controls and nested groups (required)
    summary: What is inside the group
    does: Lists the controls and smaller groups drawn in the card.
  - name: dynamic
    title: Live event
    tab: advanced
    type: string
    description: Event name whose broadcasts replace the children at runtime (see Dynamic Groups)
    summary: Contents that arrive live
    does: Replaces the children whenever a broadcast with this event name arrives.
  - name: visible
    title: Show when
    type: object
    description: Show/hide based on another control's value (a VisibilityCondition)
    summary: Show only when...
    does: Hides the whole group unless another control's value meets the condition.
  - name: enabled
    title: Enabled when
    type: object
    description: Enable/disable every child; false dims the group and ignores touches
    summary: Allow touches only when...
    does: Dims the group and ignores touches on all its controls while the condition is false.
  - name: form
    title: Form
    type: object
    description: Make the group a form whose inputs write a draft, written once by submit
    summary: Turn the card into a form
    does: Makes the inputs inside write to a draft that is saved once when submitted.
  - name: hideBackground
    edit: background
    depth: surface
    title: Background on/off
    type: bool
    default: false
    description: Remove the glass card behind the group
    summary: Drop the glass card
    does: Removes the card background so the controls sit directly on the page.
  - name: pulse
    title: Pulse
    type: object
    description: Flash a ring around the group when a live event lands
    summary: Flash when something arrives
    does: Flashes a ring around the group each time the chosen live event lands.
  - name: theme
    edit: theme
    title: Theme
    type: object
    description: Theme overrides for the group's header, card and every child (same keys as a control's theme)
    summary: Colours and style for the card
    does: Overrides the header, card and every child's theme; a child's own theme still wins.
  - name: expand
    title: Expand
    edit: pose
    tab: advanced
    type: object
    description: "Let the group grow into a foreground container with a corner close (X): {trigger: tap|hold|both, style: fullScreen|sheet, grid, children, title}. children are {ref, position, span} placements that move the group's own children, or controls that exist only when expanded. See Expand"
    summary: Let the group open up full screen
    does: "Tapping the card (a tap no child claims), holding it, or both: the group's card grows from where it sits into the whole screen (or a large sheet), its controls laid out bigger with more of them, and shrinks back when closed."
  - name: trigger
    group: expand
    title: Opens by
    edit: pick-control
    depth: surface
    values: [tap, hold, both, none]
    default: tap
    type: string
    description: "What opens the expanded group (expand.trigger): tap, hold, both, none, a control id, or an array like [\"hold\", \"more-button\"]"
    summary: How the group opens
    does: "Opens the group on a tap, a hold, either, or never from the card (none); or when a control you pick on the page is tapped. A keyword and controls can combine."
  - name: style
    group: expand
    title: Style
    edit: look
    depth: hold
    under: trigger
    values: [fullScreen, sheet]
    default: fullScreen
    type: string
    description: "Where the expanded group lands (expand.style): the whole screen, or a large sheet over a dimmed page"
    summary: Full screen or a sheet
    does: "Full screen takes the whole display; a sheet rises as a large card over the dimmed page. Both close with the corner X or a drag down."
  - name: title
    group: expand
    title: Title
    edit: inline
    depth: surface
    type: string
    description: "Heading shown on the expanded group (expand.title); empty uses the group's own title"
    summary: The expanded page's heading
    does: "Types the heading the expanded group shows at its top; leave it empty to use the group's own title."
  - name: action
    title: Action
    tab: advanced
    type: object
    description: "Fired by a tap on the group that no child claims (static text, images, gauges without an action, the card background and padding). Same shape as a control's action. A child's own taps and holds win. Ignored when `expand` also opens on tap"
    summary: Make the whole card tappable
    does: "Taps on the card's non-interactive parts send the action; buttons, toggles, sliders, inputs and rows with their own action keep their own taps. The card dips slightly while pressed."
  - name: extensions
    title: Extensions
    tab: advanced
    type: object
    description: Tool data keyed by reverse-DNS name; preserved, never interpreted
    summary: Notes for other tools
    does: Stores tool data under reverse-DNS names that the app keeps but never uses.
---

A visual container that clusters controls into a glass card with its own internal grid.

## Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `"group"` | yes | Discriminator — must be `"group"` |
| `id` | string | yes | Unique identifier (among the layout's controls and groups; see [[layout-config#Identity]]) |
| `name` | string | no | Readable name the editor shows for this group. Never used for identity |
| `label` | string | no | Header text shown above the group. Set to `null` for no header |
| `position` | [row, col] | yes | Grid cell position within parent |
| `span` | [rows, cols] | no | Grid cells occupied. Default: `[1, 1]` |
| `landscape` | `{position, span}` or `{hidden: true}` | no | This group's cell when an iPhone is on its side; ignored in portrait. See [[grid-dimensions#Landscape and iPad]] |
| `regular` | `{position, span}` or `{hidden: true}` | no | This group's cell on an iPad-width page |
| `grid` | [[grid-dimensions]] | yes | Internal grid dimensions for this group's children; its `scale` draws them as miniatures (see [[#Scale]]) |
| `children` | [[child-definition]][] | yes | Controls and nested groups |
| `dynamic` | string | no | Event name for [[dynamic-content\|runtime-injected children]] |
| `visible` | [[visibility\|VisibilityCondition]] | no | Show/hide based on another control's value |
| `enabled` | [[visibility\|VisibilityCondition]] | no | Enable/disable every child; false dims the group and ignores touches |
| `form` | [[form]] object | no | Make the group a form: its inputs write a draft, validated, written once by `submit` |
| `hideBackground` | bool | no | Remove glass card background (default: `false`) |
| `pulse` | [[pulse]] object | no | Flash a ring around the group when a live event lands |
| `theme` | object | no | Theme overrides for the group's label, card and every child (same keys as a control's `theme`; `$name` palette refs work). A child's own `theme` and `tint` still win. See [[theming#Cascade]] |
| `action` | object | no | Fired by a tap no child claims (non-interactive content, the card background and padding); a child's own tap or hold wins. Same shape as a control's `action`. Ignored when `expand` opens on tap (expand wins) |
| `expand` | object | no | Grow the group into a foreground container with a corner close, laid out again with more controls. See [[#Expand]] |
| `extensions` | object | no | Tool data keyed by reverse-DNS name; preserved, never interpreted, 64 KB cap. See [[document-contract#Extensions]] |

## Editing a group

Tapping a group in the editor opens its Group pane. It edits the group's scalar fields above (name, header, background), its inner grid (the [[grid-dimensions]] fields: columns, rows, row height and scale under a hold on Rows, arrangement, landscape policy), and three keys of its `theme` that shape the card: `accentColor` (Tint), `cardPadding` (Padding) and `cornerRadius` (Corners). **Edit controls** opens the group so its children can be tapped and edited; **Ungroup** moves the children up into the parent where they sat; **Delete** removes the group and everything in it (undo brings it back).

**Collapsed | Expanded** (the `expand` field's `edit: pose`) flips the pane to the group's expanded layout: the grown card's grid (`expand.grid`), with each child the expand does not place yet as a ghost at its collapsed cell. Dragging a child into cells writes its `{ref, position, span}` entry in `expand.children` (the first one creates `expand`: `trigger: "tap"`, `style: "fullScreen"`, the group's columns on a taller grid); the corner handle resizes it (its `span`); dragging it off the card removes the ref, and once the expand places any child the unplaced ones fade while expanded (the pose then shows them on a faded shelf below the card, to drag in from there). Columns and Rows on the bar size `expand.grid`; **Don't expand** removes `expand`. Each drag is one undo step. Controls that exist only while expanded show with an Only here mark.

## Examples

### Bedroom card
A titled card with two switches and a brightness slider on a two-column grid.

```json
{
  "type": "group",
  "id": "bedroom",
  "label": "Bedroom",
  "position": [2, 0],
  "span": [2, 2],
  "grid": { "columns": 2, "rows": 2 },
  "children": [
    { "type": "toggle", "id": "br-light", "position": [0, 0], "label": "Light" },
    { "type": "toggle", "id": "br-fan", "position": [0, 1], "label": "Fan" },
    { "type": "slider", "id": "br-dim", "position": [1, 0], "span": [1, 2], "min": 0, "max": 100, "label": "Brightness" }
  ]
}
```

### Hold to expand
A card that opens as a large sheet when held, with the same toggle placed larger inside.

```json
{
  "type": "group",
  "id": "lamp",
  "label": "Lamp",
  "position": [0, 0],
  "span": [1, 2],
  "grid": { "columns": 2, "rows": 1 },
  "expand": {
    "trigger": "hold",
    "style": "sheet",
    "grid": { "columns": 2, "rows": 3 },
    "children": [
      { "ref": "lamp-power", "position": [0, 0], "span": [1, 2] }
    ]
  },
  "children": [
    { "type": "toggle", "id": "lamp-power", "position": [0, 0], "span": [1, 2], "label": "Power" }
  ]
}
```

### Quiet background-free group
A group with no glass card and a pulse ring that flashes when a live event lands.

```json
{
  "type": "group",
  "id": "status",
  "position": [1, 0],
  "span": [1, 2],
  "hideBackground": true,
  "grid": { "columns": 2, "rows": 1 },
  "pulse": { "event": "broadcast", "direction": "inward", "color": "34C759" },
  "children": [
    { "type": "label", "id": "status-text", "position": [0, 0], "span": [1, 2], "text": "Waiting for data" }
  ]
}
```

## Scale

`grid.scale` draws the group's controls as proportional miniatures (or enlargements): text,
padding, spacing, corner radii, icons and control sizes (toggle tracks, slider thumbs, stepper
buttons) all scale together through the theme, so they stay crisp instead of being shrunk as a
picture. It is what makes a fine grid work: a compact list card on 3 rows × 15 columns holds
whole controls at a size that fits its short rows.

| Value | Draws at |
|-------|----------|
| absent | 1 (as today) |
| a number | that factor, clamped to 0.3 to 1.5 (0.5 = half size) |
| `"auto"` | the row height over the default: `rowHeight / 56`, clamped (rows of 28 pt draw at 0.5). With `rowHeight: "auto"` it draws at 1 |

- Taps stay full size: a button, toggle or stepper drawn smaller than 44 pt still takes a 44-pt
  touch around its centre.
- It scales what is inside the group, not the group's own card and header (those follow the
  grid the group sits in). A group nested inside a scaled group is scaled with it (its rows
  too), times its own `scale`.
- Visual controls (rings, gauges, charts) already scale their insides to their cell, so they
  look the same at any scale; the factor matters most for labels, buttons and inputs.
- A list's `itemTemplate` grid takes `scale` too, so every row draws at it. An `expand` page
  draws at its own `grid.scale`, and at 1 when it has no grid of its own.

A compact card: 3 short rows on 15 columns, drawn at `auto` (40 / 56 ≈ 0.71):

```json
{
  "type": "group",
  "id": "compact-card",
  "position": [0, 0],
  "span": [3, 4],
  "grid": { "columns": 15, "rows": 3, "rowHeight": 40, "scale": "auto" },
  "children": [
    { "type": "image", "id": "cc-icon", "position": [0, 0], "span": [3, 3], "systemName": "shippingbox" },
    { "type": "label", "id": "cc-name", "position": [0, 3], "span": [1, 8], "text": "Example package", "subtitle": "1.2.0" },
    { "type": "toggle", "id": "cc-auto", "position": [1, 3], "span": [1, 8], "label": "Auto update" },
    { "type": "label", "id": "cc-size", "position": [2, 3], "span": [1, 8], "text": "Size: 1.1 MB", "style": "caption" },
    { "type": "button", "id": "cc-go", "position": [0, 11], "span": [3, 4], "label": "Install" }
  ]
}
```

## Dynamic Groups

When `dynamic` is set, the group's `children` are replaced at runtime by content arriving over MeshSocket. The incoming broadcast must have `msg_type` matching the `dynamic` value and a `children` array.

```json
{
  "type": "group",
  "id": "now-playing",
  "label": "Now Playing",
  "position": [0, 0],
  "span": [3, 4],
  "grid": { "columns": 4, "rows": 3 },
  "children": [],
  "dynamic": "player_state"
}
```

### Chunked decks (`rev`, `part`, `parts`)

The relay drops any websocket frame over its read limit (256 KiB on Connect+,
and an E2EE room seals and base64-encodes the frame, so it grows by about a
third on the wire). A server whose deck may come near that size splits it into
several broadcasts. Each one carries the same `msg_type` plus three extra keys:

| Key | Type | Rule |
|-----|------|------|
| `rev` | string | Identifies one deck. Every part of the deck carries the same `rev`; use a new `rev` (a counter, a timestamp, a content hash) for each new deck. At most 256 UTF-8 bytes. |
| `parts` | integer | Total number of parts, `2`...`64`. A frame whose `parts` is missing, not a number (for example a string), or a number of `1` or less is a normal single-frame deck. |
| `part` | integer | This frame's index. **Number parts `1`...`parts` (1-based).** CAR-TER 1.2.6 and later also accept 0-based `0`...`parts-1`. |
| `children` | array | This part's slice of the deck: whole child objects. Split between children, never inside one. |

```json
{ "msg_type": "player_state", "rev": "42", "part": 1, "parts": 2, "children": [ { "type": "label", "id": "dyn-title", "position": [0, 0], "span": [1, 4], "text": "Song" } ] }
{ "msg_type": "player_state", "rev": "42", "part": 2, "parts": 2, "children": [ { "type": "slider", "id": "dyn-volume", "position": [1, 0], "span": [1, 4], "min": 0, "max": 100 } ] }
```

How the app puts a deck back together:

- It buffers parts per group. Once it holds `parts` distinct `part` indices for
  one `rev`, it concatenates the `children` slices in ascending `part` order and
  applies the result as one deck. Parts can arrive in any order.
- A frame with a different `rev` or `parts` than the buffered deck throws away
  the unfinished deck and starts a new one. Only one deck is in flight per group.
  The newest deck wins, and an abandoned one never renders half-built.
- The app drops a frame, without logging it, if `parts` is not a whole number
  from `2` to `64`, if `part` is missing or outside `0`...`parts`, if `rev` is
  missing, not a string or longer than 256 bytes, or if `children` is not an array.
- Use one numbering convention for the whole deck. If a sender mixes them (say,
  `0`, `1` and `2` with `parts: 2`), the deck completes as soon as it has two
  distinct indices, so it can apply only part of the deck.
- The app rebuilds the deck as `msg_type` set to the group id, plus the joined
  `children`. Other top-level keys on the parts are ignored.
- Use 1-based numbering. Before 1.2.6, the app reassembled `1`...`parts` only:
  1.2.5 drops part `0`, so a 0-based deck never completes on it. Send 0-based
  parts only to 1.2.6 and later.
- Chunking applies to dynamic **groups** only. A [[dynamic-content|dynamic tab]]
  always arrives as one frame.

A carterkit helper builds these frames for you once a release ships it:
`carterkit.dynamic.chunk_deck(event, children)` returns the frame list (1-based),
and `Hub.fill(group, children, max_bytes=...)` sends a deck in parts when it is
larger than `max_bytes`. Check the installed carterkit for `chunk_deck` before
relying on it; otherwise split the deck by hand.

## Pulse

Set `pulse` to make the group flash a ring whenever a server event arrives —
a lightweight way to visualise live data landing in a group without wiring a
control. The ring expands `outward` (e.g. data collected/leaving) or contracts
`inward` (e.g. data arriving/stored), then fades. An optional `filter` narrows
which payloads trigger it, matching keys the same way a [[sync]] filter does.

| Field | Type | Description |
|-------|------|-------------|
| `event` | string | Server event that fires the pulse |
| `color` | hex string | Ring colour (default: green `34C759`) |
| `direction` | `"outward"` \| `"inward"` | Pulse direction (default: `outward`) |
| `filter` | object | Optional payload match, e.g. `{ "device": "thunk-app" }` |

```json
{
  "type": "group",
  "id": "gps-collector",
  "label": "Live GPS",
  "position": [0, 0],
  "grid": { "columns": 2, "rows": 2 },
  "children": [],
  "pulse": { "event": "broadcast", "filter": { "msg_type": "iCloudListen" }, "direction": "outward", "color": "34C759" }
}
```

## Theming

A group renders as a glass card whose surface, corner radius, border, and padding come from the active [[theming|theme]] (`surfacePrimary`, `cornerRadius`, `borderColor`, `borderWidth`, `cardPadding`). Set `hideBackground: true` for a transparent group (no card), e.g. a hero row of status lights. A group's own `theme` overrides those keys for the card, its label and everything inside it, e.g. `"theme": {"accentColor": "$leaf", "surfacePrimary": "#1B2A1F"}`; per-control `theme` overrides on the children still apply on top. See [[theming#Cascade]].

## Expand

`expand` lets a person open a group up: tapping the card (a tap no child claims), or holding
it, grows the card from where it sits, in one continuous motion, into a foreground
container with a close (X) in its corner. As it grows, the group's own controls move from their
cells to new ones on the expand `grid`: the same controls, not copies, so their live values,
bindings and actions carry straight through. Controls that only make sense with room fade and
scale in once it has grown. The X, a drag down on the container's top edge, or a tap on the
dimmed page (sheet style) plays it backwards to where the group sits.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `trigger` | `"tap"`, `"hold"`, `"both"`, `"none"`, a control id, or an array mixing them | `"tap"` | What opens it. `tap`: a tap on the card; `hold`: a hold on the card; `both`: either; `none`: only buttons, actions or the hub. A control id (a child of the group or any control in the layout; inside a list's `itemTemplate` the id resolves in the same row) expands the group when that control is tapped, and the control's own `action` still fires. Examples: `"hold"`, `"more"`, `["hold", "more"]`. A child's own tap or hold always wins over the card's; only a tap on non-interactive content, the background or the padding opens it. An id that matches no control never fires. An old `"icon"` reads as `"tap"`. Edits take effect live |
| `style` | `"fullScreen"` or `"sheet"` | `"fullScreen"` | The whole screen, or a large card up from the bottom over the dimmed page |
| `grid` | [[grid-dimensions]] | the group's `grid` | The grid the expanded layout is placed on |
| `children` | object[] | — | Placements and expanded-only controls, below |
| `title` | string | the group's `label` | Text beside the close button |

Each entry of `children` is one of two things:

- **A placement** of one of the group's children: `{"ref": "<child id>", "position": [row, col],
  "span": [rows, cols]}`. Other fields in it are laid over that child while expanded (a bigger
  `size`, another `style`); `id` and `type` are ignored. A `ref` that names no child of this
  group is skipped.
- **A control or group** of its own (it needs a `type`; the `id` may be left out). It exists only
  while expanded.

A child that no entry refers to fades out while expanded and comes back on collapse. An
`expand` with no `children` keeps every child where it is, on the expand `grid`. While a group
expands its controls are laid out on grid cells (the expand grid's rows), even when the group's
own grid is a `flow` grid.

A one-row card (an image, a label with two lines of text, two buttons) that opens into a page:
the image large at the top left, the text beside it, the buttons below, and a description only
the page has.

```json
{ "type": "group", "id": "pkg", "position": [0, 0], "span": [2, 4],
  "grid": { "columns": 4, "rows": 2 },
  "expand": {
    "trigger": ["tap", "more"], "style": "fullScreen", "title": "Example package",
    "grid": { "columns": 4, "rows": 6 },
    "children": [
      { "ref": "icon", "position": [0, 0], "span": [2, 2] },
      { "ref": "name", "position": [0, 2], "span": [2, 2] },
      { "ref": "install", "position": [2, 0], "span": [1, 2] },
      { "ref": "share", "position": [2, 2], "span": [1, 2] },
      { "type": "label", "id": "about", "position": [3, 0], "span": [3, 4],
        "text": "A longer description that only the expanded page shows." }
    ]
  },
  "children": [
    { "type": "image", "id": "icon", "position": [0, 0], "systemName": "shippingbox" },
    { "type": "label", "id": "name", "position": [0, 1], "label": "Version 1.2.0", "text": "Example package" },
    { "type": "button", "id": "more", "position": [1, 0], "span": [1, 4], "label": "More" },
    { "type": "button", "id": "install", "position": [0, 2], "label": "Install",
      "action": { "method": "meshsocket", "event": "install", "payload": { "id": "pkg" } } },
    { "type": "button", "id": "share", "position": [0, 3], "label": "Share",
      "action": { "method": "meshsocket", "event": "share", "payload": { "id": "pkg" } } }
  ] }
```

A [[list]]'s `itemTemplate` is a group too: give it an `expand` and every row grows the same
way. Its refs are the template's child ids (each row's own controls move), and its placements
and new controls are filled in from the row (`{{item.<field>}}`). Nothing inside an
expanded group offers to expand again, except a templated row of a list in it, which opens on
top with a back button.

## Hub sheets

The hub of the layout on screen can expand a group itself, with the routed `sheet` verb on the
layout's own socket: `{id, groupId}` expands that group of the layout (live, from where it sits
when it is on screen); `{id, group}` opens a group definition of the hub's own, drawn from its
fields like a list's [[list#Item templates|item template]] and replaced in place when a frame
with the same `id` arrives again. `title` and `style` are optional and `{id, close: true}`
closes it. A hub's own group sends only to the hub: actions of any other method are dropped, as
are `sync` and `form`, and `{{secret:…}}` never resolves in it. When it closes the app
broadcasts `sheet_closed {id, reason}`. Wire contract: `docs/HUB-SHEET.md` in the app
repository.

## Rendering
- Groups render as a glass card (frosted material + subtle border)
- The internal grid is independent of the parent grid
- Groups can be nested (a group's children can include other groups)

## Related
- [[control-def]] — controls within groups
- [[layout-config]] — the top-level structure
- [[grid-dimensions]] — Grid sizing
- [[visibility]] — The `visible` and `enabled` fields
- [[form]] — Draft, validate, submit
- [[dynamic-content]] — Runtime injection
- [[theming]] — Theme & appearance system
