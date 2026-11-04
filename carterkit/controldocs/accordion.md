---
type: accordion
depth: complete
label: Accordion
icon: list.bullet.below.rectangle
category: controls
defaultSpan: [3, 2]
addIntent: organize
pickerCategory: Layout
friendlyName: Sections
oneLiner: Headings that open and close
aliases: [collapse, expand, section, fold, disclosure, faq]
addRank: 5
starterPreset: {}
fields:
  - name: accordionMode
    effect: behavior
    edit: look
    depth: surface
    title: Open mode
    type: enum
    values: [single, multi]
    default: single
    description: Whether one or many sections can be open
    summary: Whether opening one section closes the others
    does: Single keeps one section open at a time; multi lets any number stay open together.
    valueHelp: {"single": "opening a section closes the one that was open", "multi": "every section opens and closes on its own"}
  - name: expandedIndex
    bounds: none
    type: number
    default: 0
    description: Section open on load (-1 = all collapsed)
    summary: Which section is open when the layout appears
    does: Opens the section at this position on load, counting from 0; -1 starts with every section closed.
  - name: showChevron
    edit: part
    depth: hold
    title: Chevron
    type: bool
    default: true
    description: Show the disclosure chevron
    summary: The small arrow beside each heading
    does: Shows or hides the arrow at the end of each heading; hidden leaves just the heading text.
  - name: panels
    type: object
    description: The panel groups this container pages through (group defs with children)
    summary: The headings and the content under each
    does: Each entry becomes one heading row that expands to show its own controls.
  - name: containerAnimation
    tab: style
    type: object
    description: Transition tuning, e.g. { profile, duration }
    summary: How the sections animate when opening or closing
    does: Tunes the spring and speed of expanding and collapsing, e.g. profile smooth or duration 0.3 seconds.
  - name: defaultValue
    min: -1
    step: 1
    bounds: none
    type: number
    description: Initial open index (overrides expandedIndex; -1 = all collapsed)
    summary: The section that starts open
    does: Opens the section at this position on load (from 0) and wins over the open-on-load index; -1 starts all closed.
themeFields:
  - name: surfacePrimary
    type: color
    default: "#FFFFFF0F"
    description: Section card background
    summary: The fill behind each section card
    does: Paints every section card in this color, including its transparency.
  - name: accentColor
    type: color
    default: "#667eea"
    description: Chevron color
    summary: The color of the arrows
    does: Tints the chevron on every heading in this color.
  - name: blurEnabled
    title: Frosted glass
    type: bool
    default: true
    description: Blur the card background
    summary: A see-through blurred look for the cards
    does: Blurs whatever sits behind each section card when on; off leaves a plain flat fill.
  - name: borderColor
    title: Border color
    type: color
    default: #FFFFFF1A
    description: Border color
    summary: The outline around each card
    does: Draws the card outline in this color, including transparency.
  - name: borderWidth
    title: Border thickness
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
    summary: How heavy the outline is
    does: Sets the outline thickness from 0 (none) to 5 points.
  - name: cardPadding
    title: Card spacing
    min: 0
    max: 32
    step: 1
    type: number
    default: 12
    description: Padding inside each panel card
    summary: Breathing room inside each section
    does: Adds 0 to 32 points between a section card edge and its content.
  - name: cornerRadius
    title: Corner roundness
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
    summary: How rounded the corners are
    does: Rounds the section cards from square (0) to 30 points.
  - name: foregroundColor
    title: Text color
    type: color
    default: #FFFFFF
    description: Primary text color
    summary: The color of the heading words
    does: Paints the section headings and default text in this color.
---

# Accordion

A vertical stack of collapsible **sections**. Each section is a [[group-def|group]] whose
`label` is the header and whose grid of children is the expandable body. In `single` mode the
open section index is the control value (so it **syncs** and fires **actions**); in `multi`
mode sections open independently.

## Type
`"accordion"`

## Relevant Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `panels` | [[group-def]][] | — | The sections, each a group definition |
| `accordionMode` | string | `"single"` | `"single"` (one open) or `"multi"` (many) |
| `expandedIndex` | number | `0` | Section open on load; `-1` = all collapsed |
| `showChevron` | bool | `true` | Show the disclosure chevron |
| `defaultValue` | number | — | Initial open index (overrides `expandedIndex` if set) |
| `containerAnimation` | object | — | Motion customization (see below) |

In `single` mode, an incoming [[sync]] opens a section (cascading through intermediate
sections on a multi-step jump); toggling fires the [[actions|action]] with the index (`-1`
when collapsing). In `multi` mode the open set is local UI state and the value reflects only
the last-toggled index.

## Animation Customization

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `profile` | string | `bouncy` | Base spring profile |
| `duration` | number | — | Override expand/collapse seconds |
| `bounce` | number | — | Spring bounce 0–1 |
| `multiStep` | bool | `true` | Cascade through sections on a multi-step jump (single mode) |
| `stepInterval` | number | `0.12` | Seconds per intermediate step |
| `chevronRotation` | number | `90` | Chevron rotation° when expanded |

## Examples

### Single-open settings, synced
Shows single mode with a spring animation: only one section stays open and the open index is the control value. Intended effect: tapping Network closes Display and opens Network.
```json
{
  "type": "accordion",
  "id": "settings",
  "position": [0, 0],
  "span": [4, 2],
  "accordionMode": "single",
  "expandedIndex": 0,
  "containerAnimation": { "profile": "smooth", "chevronRotation": 90 },
  "panels": [
    { "type": "group", "id": "display", "label": "Display", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "slider", "id": "bright", "position": [0,0], "label": "Brightness", "min": 0, "max": 100 } ] },
    { "type": "group", "id": "network", "label": "Network", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "toggle", "id": "wifi", "position": [0,0], "label": "Wi-Fi" } ] }
  ]
}
```

### Multi-open FAQ
Shows multi mode, no chevron and all sections starting closed. Intended effect: each question opens on its own and several answers can stay open at once, with plain headings.
```json
{
  "type": "accordion",
  "id": "faq",
  "position": [0, 0],
  "span": [4, 3],
  "accordionMode": "multi",
  "expandedIndex": -1,
  "showChevron": false,
  "panels": [
    { "type": "group", "id": "q1", "label": "How do I reset it?", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "label", "id": "a1", "position": [0,0], "text": "Hold the button for five seconds." } ] },
    { "type": "group", "id": "q2", "label": "Where is the log?", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "label", "id": "a2", "position": [0,0], "text": "Open the Logs page." } ] }
  ]
}
```

### Action and sync on the open section
Shows the action fired on every toggle and a sync that opens a section from the server. Intended effect: tapping a heading sends its index (-1 when collapsing) and a broadcast scene message opens the matching section on the phone.
```json
{
  "type": "accordion",
  "id": "scenes",
  "position": [0, 0],
  "span": [4, 2],
  "accordionMode": "single",
  "defaultValue": 0,
  "containerAnimation": { "profile": "bouncy", "multiStep": true, "stepInterval": 0.12 },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "scene" }, "valuePath": "index" }],
  "action": { "method": "meshsocket", "mode": "send", "event": "route_msg_noreply", "payload": { "target_name": "hub", "type": "scene", "payload": { "index": "{{value}}" } } },
  "panels": [
    { "type": "group", "id": "home", "label": "Home", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "label", "id": "home-l", "position": [0,0], "text": "Home scene" } ] },
    { "type": "group", "id": "away", "label": "Away", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "label", "id": "away-l", "position": [0,0], "text": "Away scene" } ] }
  ]
}
```

### Themed frosted cards
Shows the theme fields: frosted glass, a thick border and larger spacing. Intended effect: roomy, rounded section cards with a visible outline.
```json
{
  "type": "accordion",
  "id": "themed",
  "position": [0, 0],
  "span": [4, 2],
  "blurEnabled": true,
  "borderWidth": 2,
  "cardPadding": 20,
  "cornerRadius": 24,
  "panels": [
    { "type": "group", "id": "t1", "label": "Details", "position": [0,0], "grid": { "columns": 1, "rows": 1 },
      "children": [ { "type": "label", "id": "t1l", "position": [0,0], "text": "More here" } ] }
  ]
}
```

> Note: `expandedIndex` and `defaultValue` do the same job; use only one.

## Theming
Sections are glass cards from the active [[theming|theme]]; the chevron uses `accentColor`.

## Related
- [[group-def]] — each section is a group
- [[carousel]] — horizontal paging
- [[flip-card]] — flip between faces
- [[actions]] — `{{value}}` section index
- [[sync]] — drive the open section from the server
- [[animations]] — base animation profiles
