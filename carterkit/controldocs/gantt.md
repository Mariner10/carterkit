---
type: gantt
label: Gantt
icon: chart.bar.doc.horizontal
category: controls
defaultSpan: [3, 4]
fields:
  - name: label
    type: string
    description: Header label above the timeline
  - name: ganttConfig
    type: object
    description: Full configuration object (see GanttConfig section)
  - name: tint
    type: color
    default: "#667eea"
    description: First-task color and palette seed
  - name: barCornerRadius
    type: number
    default: 5
    description: Bar corner rounding
    group: ganttConfig
  - name: colors
    type: string[]
    description: Per-task color cycle (task color wins)
    group: ganttConfig
  - name: editable
    type: bool
    default: false
    description: Drag along a bar to set its progress
    group: ganttConfig
  - name: rowHeight
    type: number
    default: 30
    description: Points per task row
    group: ganttConfig
  - name: scrub
    type: bool
    default: false
    description: When not editable: drag sweeps the row selection with haptic ticks (the action still fires on tap)
    group: ganttConfig
  - name: showAxis
    type: bool
    default: true
    description: Time labels along the top
    group: ganttConfig
  - name: showGrid
    type: bool
    default: true
    description: Vertical gridlines at the axis ticks
    group: ganttConfig
  - name: showProgress
    type: bool
    default: true
    description: Progress fill inside bars + % readout
    group: ganttConfig
  - name: showToday
    type: bool
    default: true
    description: Dashed 'now' line (date timelines only)
    group: ganttConfig
  - name: step
    type: number
    default: 0.05
    description: Progress snap while dragging
    group: ganttConfig
  - name: taskAction
    type: object
    description: taskAction
    group: ganttConfig
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
    description: Task name color
---

# Gantt

A project timeline: one horizontal bar per task from `start` to `end`, with an
optional progress fill, milestone diamonds, and a dashed **today** marker when
the timeline is date-based. The hidden edge: with `editable: true`, dragging
along a bar **sets that task's progress** — the chart becomes a bank of
per-task progress sliders that write back into the dataset and fire
`taskAction` on release.

## Type
`"gantt"`

## Recommended Size
Full-width: `[3, 4]` and up. The control sizes its own height from the task
count (`rowHeight` × tasks), so in a flow grid no `controlHeight` is needed.

## Relevant Fields
Inherits all [[control-def|shared fields]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | — | Header label (selection/drag readout appears beside it) |
| `ganttConfig` | [[#GanttConfig]] | — | Full configuration object (all optional) |
| `tint` | string | `"#667eea"` | First-task color / palette seed |
| `action` | [[actions\|ActionDefinition]] | — | Fallback for `taskAction` |

## GanttConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `showAxis` | bool | `true` | Time labels along the top |
| `showGrid` | bool | `true` | Vertical gridlines at the axis ticks |
| `showToday` | bool | `true` | Dashed "now" line (date timelines only) |
| `showProgress` | bool | `true` | Progress fill inside bars + % readout |
| `rowHeight` | number | `30` | Points per task row |
| `barCornerRadius` | number | `5` | Bar corner rounding |
| `colors` | string[] | built-in palette | Per-task color cycle (task `color` wins) |
| `taskAction` | [[actions\|ActionDefinition]] | — | Fired on tap / drag release; `{{value}}` = the task as JSON |
| `editable` | bool | `false` | Drag along a bar to set its progress |
| `step` | number | `0.05` | Progress snap while dragging |
| `scrub` | bool | `false` | When not `editable`: drag sweeps the row selection with haptic ticks (the action still fires on tap) |

## Sync Payload Structure

A task list — natural JSON or an encoded string. A bare array is shorthand for
`{"tasks": …}`:

```json
{
  "tasks": [
    { "name": "Design",  "start": "2026-07-01", "end": "2026-07-05", "progress": 1.0 },
    { "name": "Build",   "start": "2026-07-04", "end": "2026-07-12", "progress": 0.4, "color": "#FF9500" },
    { "name": "Ship",    "start": "2026-07-14", "milestone": true }
  ]
}
```

### Task Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Row label in the leading gutter |
| `start` | string \| number | yes | `"yyyy-MM-dd"`, ISO 8601 datetime, or a plain number (any unit) |
| `end` | string \| number | yes* | Same forms as `start` (*not needed for milestones) |
| `progress` | number | no | 0–1 fill inside the bar |
| `color` | string | no | Bar color (hex) |
| `milestone` | bool | no | Draw a diamond at `start` instead of a bar |

Dates and numbers share one axis — don't mix them in one payload.

## Examples

### Sprint board (server-pushed)
```json
{
  "type": "gantt",
  "id": "sprint",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Sprint 12",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "sprint_plan" }, "valuePath": "gantt" }]
}
```

### Editable progress tracker
```json
{
  "type": "gantt",
  "id": "tracker",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Drag to update",
  "ganttConfig": {
    "editable": true,
    "taskAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast", "payload": { "msg_type": "task_progress", "task": "{{value}}" } }
  },
  "defaultValue": "[{\"name\":\"Prep\",\"start\":0,\"end\":3,\"progress\":0.5},{\"name\":\"Run\",\"start\":2,\"end\":8,\"progress\":0.1}]"
}
```

## Behavior
- Tap a bar to select it (header shows `name %`); tap empty space to clear
- Dragging (when `editable`) snaps to `step` with a selection tick per notch, updates the stored dataset on release so state [[sync|readback]] round-trips, then fires the action with `{"name", "index", "progress"}`
- Axis labels adapt to the span: hours under 2 days, day/month under ~10 months, month/year beyond
- Milestones ignore `end` and can't be progress-dragged
- Without `editable`, `scrub: true` lets a drag sweep the row selection fluidly instead

## Notes
- Keep names short — the leading gutter is ~25% of the width, capped at 110 pt
- ~10 tasks fit comfortably; the control grows taller with more
- Dependencies/arrows are out of scope v1 — encode ordering with dates

## Related
- [[chart]] — cartesian series (incl. `waterfall` for cumulative effects)
- [[list]] — tabular task data
- [[progress-ring]] — single-task progress
- [[sync]] — how schedules arrive
- [[actions]] — how `taskAction` fires
