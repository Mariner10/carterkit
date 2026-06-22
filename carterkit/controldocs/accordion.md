---
type: accordion
label: Accordion
icon: list.bullet.below.rectangle
category: controls
defaultSpan: [3, 2]
fields:
  - name: accordionMode
    type: enum
    values: [single, multi]
    default: single
    description: Whether one or many sections can be open
  - name: expandedIndex
    type: number
    default: 0
    description: Section open on load (-1 = all collapsed)
  - name: showChevron
    type: bool
    default: true
    description: Show the disclosure chevron
themeFields:
  - name: surfacePrimary
    type: color
    default: "#FFFFFF0F"
    description: Section card background
  - name: accentColor
    type: color
    default: "#667eea"
    description: Chevron color
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

## Theming
Sections are glass cards from the active [[theming|theme]]; the chevron uses `accentColor`.

## Related
- [[group-def]] — each section is a group
- [[carousel]] — horizontal paging
- [[flip-card]] — flip between faces
- [[actions]] — `{{value}}` section index
- [[sync]] — drive the open section from the server
- [[animations]] — base animation profiles
