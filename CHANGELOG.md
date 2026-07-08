# Changelog

All notable changes to **carterkit** are documented here. This project follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- `Layout(cols=…, rows=…)` now sets the **default grid for every tab**. Previously the
  layout-level `rows` was ignored and tabs fell back to a fixed 6-row grid, so a sized
  layout could fail auto-placement with a confusing "no free slot". Override per tab with
  `ui.tab("Name", rows=…)`. The declarative veneer inherits the same way: a `Tab` class
  without its own `cols=`/`rows=` uses the `Screen`'s grid.
- `LayoutBuffer.add_group(...)` now **normalizes nested children** — each child gets a
  unique `id` and an auto-placed `position` within the group's own grid (recursing into
  nested groups), instead of producing a group that immediately fails validation for
  missing `id`/`position`. Raises a clear error if the group grid has no room.

## [0.5.2] — 2026-06-30

Docs-only re-sync.

### Changed
- Re-vendored `index.md`: corrected the stale "28 control types" count to **27**
  (the catalog excludes the `divider`/`spacer` layout primitives). No API changes.

## [0.5.1] — 2026-06-30

Docs-only re-sync so the bundled catalog matches the published website catalog.

### Changed
- Re-vendored ControlDocs from the app repo (`label`, `log-console`, `text-input`),
  re-aligning carterkit's bundled control definitions with
  `carterbeaudoin.net/CAR-TER/catalog.json` (clears the `check_sources` drift
  warning). No API changes.

## [0.5.0] — 2026-06-24

Grid authoring now expresses the app's 2-D grid model. Backward compatible.

### Added
- `tab()`, `group()`, and `LayoutBuffer.add_tab()` accept **`mode`** (`"grid"` /
  `"flow"`) and **`row_height`**, emitted into the grid dict. The app renders a true
  2-D grid by default (controls span `row × col`); `mode="flow"` opts a tab/group
  into the legacy row-banded layout for forms and full-page content.

### Changed
- Re-vendored ControlDocs: new **grid-dimensions** doc (the grid model), `hideValue`
  on ring/gauge, and the `carterbeaudoin.net` domain fix.

## [0.4.0] — 2026-06-22

Reworked layout authoring around a flat builder with live handles, added a declarative
class veneer, and shipped a dynamic-group traffic lint. Fully backward compatible — the
old `.add(build.<control>(...), default_span=…)` fluent chain still works.

### Added
- **Flat builder with handles** (`Layout`). Controls are methods on the layout
  (`ui.gauge("cpu", …)`), ids are positional, and tabs/groups are context managers:

  ```python
  with Layout("Bench", cols=4, rows=4) as ui:
      ui.connect("ws://host:8765", channel="lab")
      with ui.tab("Main", icon="gauge"):
          cpu = ui.gauge("cpu", label="CPU", min=0, max=100, span=(2, 2),
                         listen="cpu", when={"msg_type": "metrics"})
          ui.status_light("warn", visible=cpu > 90)
          ui.button("refresh", label="Refresh", send="refresh", request=True)
  ui.save("bench.json")
  ```
- **Control handles** (`Control`). Every control method returns a handle usable as a
  binding target (`visible=cpu > 90` builds a real visibility condition) or to patch the
  control later (`cpu.update(max=200)`). Handle ops `<,<=,>,>=` and `.eq()`/`.neq()`
  build `Condition`s; `==`/`!=` keep normal Python semantics.
- **Binding sugar** folded into control kwargs: `listen=`/`when=`/`event=` build a `sync`;
  `send=`/`request=`/`payload=` build an `action`. Full `sync=[...]`/`action={...}` still
  accepted for advanced cases.
- **Dynamic groups, author-time**: `_GridScope` does sub-grid auto-placement, so controls
  can be generated *inside* a group in `for`/`if` loops (previously `LayoutBuffer` could
  not add children into a group at all).
- **`Fragment`** — a detached grid whose `.children` / `.payload(event)` is the broadcast
  body that fills a runtime `dynamic="event"` group.
- **Declarative-class veneer** (`carterkit.declare`): `Screen`, `Tab`, `Group`, `Connect`,
  `Ref`, and PascalCase control specs (`Gauge`, `Button`, `StatusLight`, …) generated from
  the catalog. id = attribute name; compiles to the same `Layout`/`LayoutBuffer`.
- **`lint_dynamic_traffic(layout, observed)`** (`carterkit.dynamic`): the dynamic-content
  counterpart to `live_data_lint` — flags `dynamic=` groups whose event never arrives,
  payloads missing a `children` array, off-grid/invalid injected children, and orphan
  children-bearing broadcasts. Also exposed as the `lint_dynamic_traffic` MCP tool.

### Changed
- `Layout` accepts `cols=` (alias of `columns=`) and is usable as a context manager.
- `Layout.group()` / `_GridScope.group()` accept an explicit `id=` (used by the
  declarative veneer to take the group id from its class/attribute name).
- New exports: `Layout`, `Fragment`, `Control`, `Condition`, `dynamic`,
  `lint_dynamic_traffic`.

## [0.3.1]

Previous release.
