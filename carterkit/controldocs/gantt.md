---
type: gantt
depth: complete
label: Gantt
icon: chart.bar.doc.horizontal
category: controls
defaultSpan: [3, 4]
addIntent: show
pickerCategory: Charts
friendlyName: Timeline
oneLiner: Tasks laid out over time
aliases: [schedule, timeline, project, tasks, plan, bars]
starterPreset: {"label": "Timeline"}
io:
  - emits: task
    when: tap
    title: When you tap a task
    field: taskAction
    fallback: action
    type: json
    says: the task as its name, its place in the list and its progress from 0 to 1
    example: {"name": "Item 1", "index": 0, "progress": 0.5}
    also: With Editable on it also sends when you let go after dragging a bar to set progress
    since: next
  - receives: rows
    role: show
    type: json
    shape: {"tasks": [{"name": "text", "start": "date or number", "end": "date or number?", "progress": "number?", "color": "hex?", "milestone": "true?"}]}
    from: [hub, mqtt, http, store, default]
    says: tasks with a name, a start and an end (dates or plain numbers, not mixed) and optional progress, color or milestone flag
    reacts: the bars are redrawn on the new time axis; a milestone shows as a single point
    example: {"tasks": [{"name": "Item 1", "start": 0, "end": 3, "progress": 0.5}]}
    since: next
  - sample: {"tasks": [{"name": "Item 1", "start": 0, "end": 3, "progress": 1}, {"name": "Item 2", "start": 2, "end": 6, "progress": 0.4}, {"name": "Item 3", "start": 5, "end": 8, "progress": 0}]}
    next: {"tasks": [{"name": "Item 1", "start": 0, "end": 3, "progress": 1}, {"name": "Item 2", "start": 2, "end": 6, "progress": 0.8}, {"name": "Item 3", "start": 5, "end": 8, "progress": 0.2}]}
fields:
  - name: haptic
    tab: action
    type: enum
    values: [none, light, medium, heavy, soft, rigid, selection, success, warning, error]
    description: Touch feedback on interaction (supported hardware)
    summary: "The buzz you feel on a touch"
    does: "Plays this haptic on the phone when you tap or drag on the timeline."
    valueHelp: {"none": "no vibration", "light": "a small soft tap", "medium": "a medium tap", "heavy": "a strong thud", "soft": "a muted cushioned tap", "rigid": "a firm sharp click", "selection": "the faint tick of picking an item", "success": "the double tap of a success", "warning": "a two-pulse warning", "error": "a sharp triple buzz of an error"}
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label above the timeline
    summary: "The title above the chart"
    does: "Shows this text as the header over the timeline; the selected task's name and percent appear beside it."
  - name: ganttConfig
    type: object
    description: Full configuration object (see GanttConfig section)
    summary: "All the timeline settings"
    does: "Groups the options that change how the bars, axis and dragging behave; every setting inside is optional."
  - name: tint
    edit: color
    depth: surface
    title: Color
    tab: style
    type: color
    default: "#667eea"
    description: First-task color and palette seed
    summary: "The main color"
    does: "Colors the first task's bar and seeds the colors of the rest."
  - name: barCornerRadius
    edit: scrub
    depth: hold
    under: rowHeight
    title: Bar roundness
    unit: pt
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    default: 5
    description: Bar corner rounding
    summary: "How round the bar ends are"
    does: "Rounds the corners of every bar; 0 is square and higher is pill-like."
    group: ganttConfig
  - name: colors
    edit: list
    depth: surface
    title: Bar colors
    tab: style
    type: string[]
    description: Per-task color cycle (task color wins)
    summary: "A color for each task"
    does: "Cycles through these colors down the rows; a task's own color overrides it."
    group: ganttConfig
  - name: editable
    chip: Touch
    type: bool
    default: false
    description: Drag along a bar to set its progress
    summary: "Let people drag progress"
    does: "Dragging along a bar sets that task's progress, saves it and fires the task action when you let go."
    group: ganttConfig
  - name: rowHeight
    edit: scrub
    depth: surface
    title: Row height
    unit: pt
    min: 12
    max: 100
    step: 1
    type: number
    default: 30
    description: Points per task row
    summary: "How tall each row is"
    does: "Sets the height of every task row, so the whole chart grows or shrinks with the task count."
    group: ganttConfig
  - name: scrub
    type: bool
    default: false
    description: "When not editable: drag sweeps the row selection with haptic ticks (the action still fires on tap)"
    summary: "Slide to browse rows"
    does: "When the chart is not editable, dragging sweeps the selected row with a haptic tick; the action still fires on tap."
    group: ganttConfig
  - name: showAxis
    edit: part
    depth: hold
    title: Time axis
    type: bool
    default: true
    description: Time labels along the top
    summary: "Show the time labels"
    does: "Draws the time labels along the top of the chart when on, hides them when off."
    group: ganttConfig
  - name: showGrid
    edit: part
    depth: hold
    title: Grid lines
    type: bool
    default: true
    description: Vertical gridlines at the axis ticks
    summary: "Show the grid lines"
    does: "Draws faint vertical lines at each axis label when on."
    group: ganttConfig
  - name: showProgress
    edit: part
    depth: hold
    title: Progress fill
    type: bool
    default: true
    description: Progress fill inside bars + % readout
    summary: "Show how far along"
    does: "Fills each bar to its progress and shows the percent readout when on."
    group: ganttConfig
  - name: showToday
    edit: part
    depth: hold
    title: Today line
    type: bool
    default: true
    description: Dashed 'now' line (date timelines only)
    summary: "Show a line for now"
    does: "Draws a dashed line at the current time on date-based timelines; number timelines never show it."
    group: ganttConfig
  - name: step
    min: 0
    max: 1
    step: 0.05
    type: number
    default: 0.05
    description: Progress snap while dragging
    summary: "How coarse dragging is"
    does: "Rounds dragged progress to multiples of this size (0.05 is 5 percent steps), with a tick at each notch."
    group: ganttConfig
  - name: taskAction
    tab: action
    type: object
    description: taskAction
    summary: "What a tap or drag sends"
    does: "The action fired when a task is tapped or a progress drag ends; {{value}} carries the task as JSON."
    group: ganttConfig
themeFields:
  - use: cornerRadius
  - use: surfacePrimary
    summary: The colour behind the control
    does: Fills the Gantt chart background with this color.
  - name: secondaryColor
    type: color
    default: #FFFFFF99
    description: Task name color
    summary: Task name color
    does: Colors the task names.
  - use: accentColor
    summary: Highlight color
    does: Sets the accent color used to tint the Gantt chart when no tint is set.
  - use: borderColor
    summary: Outline color
    does: Colors the outline drawn around the Gantt chart.
  - use: borderWidth
    summary: Outline thickness
    does: Sets the outline width from 0 to 5 points.
  - use: controlPadding
    summary: Space inside the edges
    does: Adds padding between the Gantt chart edge and its content, 0 to 24 points.
  - use: foregroundColor
    summary: Main text color
    does: Colors the primary text on the Gantt chart.
  - use: labelFontSize
    summary: Label text size
    does: Sets the label text size from 8 to 24 points.
  - use: tertiaryColor
    summary: Dimmed text color
    does: Colors the faintest text and ink on the chart.
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
Shows a timeline whose tasks are pushed by your server as a `sprint_plan` broadcast.
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
Lets you drag along a bar to set progress, then broadcasts the task that changed.
```json
{
  "type": "gantt",
  "id": "tracker",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Drag to update",
  "ganttConfig": {
    "editable": true,
    "taskAction": { "method": "meshsocket", "mode": "broadcast", "event": "broadcast_request", "payload": { "msg_type": "task_progress", "task": "{{value}}" } }
  },
  "defaultValue": "[{\"name\":\"Prep\",\"start\":0,\"end\":3,\"progress\":0.5},{\"name\":\"Run\",\"start\":2,\"end\":8,\"progress\":0.1}]"
}
```

### Quiet timeline with milestones
Draws a compact, colored plan with no grid or axis fill, using the built-in task list.
```json
{
  "type": "gantt",
  "id": "launch-plan",
  "position": [0, 0],
  "span": [3, 4],
  "label": "Launch plan",
  "tint": "#34C759",
  "ganttConfig": {
    "showGrid": false,
    "showToday": false,
    "rowHeight": 36,
    "barCornerRadius": 12,
    "colors": ["#34C759", "#FF9500", "#5AC8FA"]
  },
  "defaultValue": "{\"tasks\":[{\"name\":\"Draft\",\"start\":\"2026-07-01\",\"end\":\"2026-07-06\",\"progress\":1},{\"name\":\"Review\",\"start\":\"2026-07-05\",\"end\":\"2026-07-10\",\"progress\":0.3},{\"name\":\"Launch\",\"start\":\"2026-07-12\",\"milestone\":true}]}"
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
