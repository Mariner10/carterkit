# Changelog

All notable changes to **carterkit** are documented here. This project follows
[Semantic Versioning](https://semver.org/).

## [0.7.0]

Full parity with the app — every layout it renders, the kit now authors and accepts.
Plus notifications that feel like they're from *your* layout (see below).

### Added — app parity
- **Re-vendored ControlDocs (62)** including the new `sources.md`; the catalog treats
  it as a system doc (informs validation, never a placeable control). 43 placeable
  controls, canvas + drag pack included.
- **Data sources (MQTT / HTTP).** Declare them with `Layout.source_mqtt(name, url, …)`
  / `source_http(name, base_url, …)`, and bind controls with `bind.mqtt(topic=…)` /
  `bind.mqtt_publish(topic=…)` / `bind.http(path=…, interval=…)` / `bind.http_request(…)`.
  The app speaks MQTT/HTTP directly — no server code — so these are surfaced as
  **app-direct** in the contract and never fake-served by a generated stub.
- **Device sensors.** `bind.sensor("heading")` / a `sensor="motion.roll"` kwarg on any
  control build a sensor sync; the validator knows the pipeline names.
- **Publishers** — `Layout.publisher(sensor, interval=…)` streams this device's sensors
  over the connection (`publishers` array; validated against known pipelines).
- **Alerts** — `Layout.alert(event=…, value_path=…, operator=…, value=…, title=…, body=…)`
  authors relay-watcher push rules (operator validated to eq/neq/gt/lt/gte/lte).
- **Glance / Live Activities** — `Layout.glance(hero=…, slots=[…], live_activity=True, …)`;
  hero/slot ids are validated against the layout's controls.
- **Poll groups, appearance, dynamic tabs** — `Layout.poll_group(...)`,
  `Layout.appearance(...)`, `Layout.dynamic_tab(event)`.

### Changed — validator now matches the app's real tolerance
- **Unknown enum values are warnings, not errors** — the app never rejects a layout for
  one (it renders the field's default); parameterized formats (`formatValue: "decimal:2"`)
  match on their base token.
- **Non-MeshSocket bindings.** `method: "mqtt"/"http"/"sensor"` sync/action are validated
  by their own shape (topic / path|url / sensor name) instead of demanding a relay `event`;
  a binding's `source:` must name a declared source, and a declared-but-unreferenced source
  warns.
- **`mode:"flow"` grids** skip 2-D bounds/overlap lint (the app stacks them).
- **Shared display fields** (`min`/`max`/`step`/`formatValue`/`controlHeight`/`hideValue`/
  `pulse`, and group `hideBackground`/`pulse`) are recognized, matching `ControlDefinition`.
- Light top-level validation for `sources`/`alerts`/`publishers`/`glance`/`state` shapes
  (never rejects the tolerant top-level keys the app ignores).
- **Parity acceptance test**: validates every bundled SampleLayout + published template with
  zero errors (skipped when the app repo isn't adjacent), plus a soft warning-inventory drift
  guard.

### Added
- **Layout Link (`carterkit explore`).** A layout is secretly an API — this
  serves it. `carterkit explore` starts a local web explorer that shows every
  **trigger** a layout's controls fire and every **data feed** they listen for,
  *type-defined*: token types (`{{value}}` resolves to the control's native
  type, refined by its config — a 0–255 slider shows `number 0–255`), typed
  push inputs per feed, a live wire log of every frame both directions, and a
  one-click typed `bridge.py` stub download. Zero-config flow: run it bare,
  scan the printed pairing JSON from the phone (Live Edit → scan), and the
  explorer pulls the phone's current layout over the mesh (`get-current-layout`
  / `get-layout`) the moment it joins — the layout you just built in the
  on-device editor becomes a browsable, pokeable API in one step. Works
  offline on a layout file too (`carterkit explore my-layout.json`). Stdlib
  only; the mesh connection retries in the background so a slow relay never
  blocks the page.
- **`carterkit.contract`** — `extract_contract(layout)`: the typed wire
  contract behind the explorer, importable on its own (agents: read this
  instead of reverse-engineering layout JSON). Redacts connection secrets, so
  a contract is safe to share.
- **`Hub.adopt_layout(layout)`** — adopt a layout after construction (e.g. one
  pulled off a paired device) and reindex controls.
- **Nested controls are first-class in `Hub`**: the control index now recurses
  through container pages (carousel/flipCard/accordion `panels`) and
  canvas-hosted items, so `hub.push`/`hub.on` resolve controls the on-device
  editor nested — matching the app's own sync collection.
- **Rich notifications (notify v2).** `notify_http` / `CarterClient.notify` /
  `Hub.notify` grew the personalization fields the relay + app now support:
  `subtitle`, `interruption` (`passive` / `active` / `time-sensitive`;
  `criticality=` accepted as an alias, `"critical"` rejected until Apple
  approval), `relevance` (0–1 stack ranking), `thread_id` (lock-screen
  grouping), `image=` (URL the device downloads and attaches), and
  `sender=` — a persona (`"Monroe"`, `("Monroe", avatar_url)`, or dict) that
  renders the push as a Communication Notification with the sender's name and
  circular avatar. `sound` stays a bundled-name/default/none (APNs cannot play
  remote sound URLs).
- **Action buttons with callbacks.** `notify(actions={"ack": ("Acknowledge",
  fn), …})` (≤4) puts buttons on the push; a tap comes back over the mesh as a
  flat `notif_action` broadcast and fires the per-send callback (dispatch keyed
  by an auto-minted `notifId`). `CarterClient.on_notif_action` /
  `Hub.on_notif_action` is the catch-all. Best-effort: taps arrive only while
  the app holds a live connection on the channel.
- **`Layout.notify(...)` — pushes scoped to the layout.** Sends through the
  layout's serving hub with `thread_id` defaulting to the layout name and
  `channel` to the layout's connection (so tapping the push opens that layout,
  and its notifications stack together).
- **E2EE notifications by default in rooms.** In a room (`e2ee_key` +
  `room=True`) `notify()` seals the content fields — title, body, subtitle,
  image URL, sender — into the `enc` envelope the app's push extension decrypts
  on-device; APNs/relay carry only a placeholder. Delivery hints
  (interruption/relevance/thread/sound/badge/channel/actions) ride in the
  clear. `encrypt=False` opts out; `encrypt=True` fails loudly without a room
  cipher. `CarterClient.notify` also now defaults `channel` to the client's
  mesh channel (tap-routing), and a persona defaults `thread_id` to the sender
  name so avatar and thread grouping agree.

## [0.6.0] — 2026-07-11

Author it, then drive it — the layout is now the whole contract.

### Fixed
- **`send=` sugar now produces actions that actually work.** It used to emit
  `{"event": "<your name>"}` — a frame type the relay silently drops (only the
  relay's own verbs are forwarded), so every sugar-authored button/slider did
  nothing over any relay. `send="cmd"` now compiles to `broadcast_request` with
  `payload.msg_type="cmd"` (default payload `{"value": "{{value}}"}`); wire verbs
  and relay service verbs (`ping`, `identify`) still pass through raw.
  `request=True` on a named command now raises with guidance — replies only ride
  `route_msg` (which needs a live `target_id`), so use the round-trip idiom
  (send= the command, listen= for the state broadcast the server answers with).
- `validate_layout` gained the **`dead_action`** lint (error) for any action-ish
  binding (`action`, `longPressAction`, `datumAction`, `snapshotAction`,
  `nodeAction`) whose `event` is not a verb the relay forwards or answers, plus
  shape checks (`route_msg` needs `target_id`; `route_msg_noreply` needs
  `target_name`; `mode:"request"` on a broadcast warns).
- `codegen` stubs no longer register handlers that can never fire, or emit
  telemetry that omits the sync `filter` keys — generated servers are built on
  `Hub` and derive every frame from the layout itself.
- `Layout(cols=…, rows=…)` now sets the **default grid for every tab**. Previously the
  layout-level `rows` was ignored and tabs fell back to a fixed 6-row grid, so a sized
  layout could fail auto-placement with a confusing "no free slot". Override per tab with
  `ui.tab("Name", rows=…)`. The declarative veneer inherits the same way: a `Tab` class
  without its own `cols=`/`rows=` uses the `Screen`'s grid.
- `LayoutBuffer.add_group(...)` now **normalizes nested children** — each child gets a
  unique `id` and an auto-placed `position` within the group's own grid (recursing into
  nested groups), instead of producing a group that immediately fails validation for
  missing `id`/`position`. Raises a clear error if the group grid has no room.

### Added
- **`Hub` / `Layout.serve()` — drive the layout you built, through its own
  bindings.** `ctrl.push(value)` derives the broadcast frame from the control's
  `sync` (filter + valuePath); `@ctrl.on` derives the demux from its `action`;
  `hub.fill(group, fragment)` replaces a dynamic group's children;
  `hub.wait_for_device()`, `hub.push_layout()` (routed apply-layout with a rendered
  echo), and `hub.qr_json()` complete the zero-config loop. Works cross-process off
  the saved JSON: `Hub("layout.json").push("temp", 21.5)`. The hub is control-state
  authority by default (late joiners receive the last pushed values).
- **`Connection.parse(...)` — one parser for every connection artifact**: `None`
  (embedded LocalRelay), a `ws://` URL + shared key, the app's *Add Device*
  credential (`{url,channel,token,role,refresh,did,k,validator}` — token
  self-refresh and room E2EE automatic), a layout `connection` block, or a whole
  layout. Emits `layout_block()` / `qr_json()` / `client_kwargs()`, and encodes the
  Connect+ policy: a device token is the hub's identity, never embedded in a layout.
- `bind.command(name, payload=)` — the compiled-command helper; `bind.WIRE_VERBS`;
  `bind.RELAY_SERVICE_VERBS`; `bind.connection(hub=)` names the serving hub inside
  the layout so both sides share one artifact.
- `CarterClient`: `can_route=` / `can_monitor=` capabilities and
  `broadcast_frame()` (verbatim payload, no forced msg_type).
- **`CarterClient.on_sync_request(cb)` / `Hub.on_sync_request(cb)`** — the app's
  `control_sync_request` (fired on layout load AND every reconnect) surfaced as a
  deterministic "a replica just joined / came back" callback, so dynamic-deck
  servers re-push exactly when needed instead of node-watching or blind periodic
  rebroadcasts. The frame's `dynamic` field lists the layout's dynamic slot
  events, so a server can re-fill only the requested decks. (Named to stay
  distinct from `LocalRelay.on_join`, which is relay-auth, not replica state.)
- **`CarterClient.enable_command_acks()`** — acknowledge `_cmd`-stamped command
  broadcasts (the app's opt-in ack'd commands, layout `state.acks: true`) with
  `command_ack {cmd_id, to, ok}`. Handled-gated: the broadcast handler must
  return `True` for a frame it actually handled — an unmatched command gets NO
  ack (the app times out + reverts, and another hub on the channel may be the
  one that answers); a raised exception acks `ok:false` and still propagates.
  `Hub` reports handled-ness from its demux automatically and auto-enables acks
  when the served layout's `state.acks` is true. `command_ack` joined the
  protocol-frame intercept, so hubs never see each other's acks as data.
- **`Layout.state(sync=, authority=, acks=, ack_timeout_ms=)`** — the layout
  `state` block as a first-class builder call (join/rehydrate signal + snapshot
  adoption + ack'd-command opt-in; `ackTimeoutMs` tunes the app's revert window,
  default 2000, for slow links).
- `bind.connection(mode=, e2ee_key=, can_broadcast=)` — author the Connect+ room
  connection shape (`mode: "room"` + `e2eeKey`, mirroring
  `Connection.layout_block`); `url=None` now omits the URL for room blocks where
  the app dials its own relay.
- Catalog now includes the `layout`-category placeables (`divider`, `spacer`) —
  they get typed builders and pass validation, closing the last "real control
  the local catalog rejects" gap (heatmap/carousel/accordion/radar landed with
  the ControlDocs re-sync). NOTE for release: ripples into the website
  `catalog.json` and the MCP drift fingerprint — rebuild via the docs-site flow.
- `Fragment` docs now state the stable-id contract: the app diffs dynamic
  children by id and preserves live values for ids it already has, so servers
  must keep injected ids stable across re-pushes.
- `CarterClient.connect()` now **pre-refreshes an expired device token**: a hub
  holding a refresh credential re-mints its short-lived relay token before
  dialing, so a service that sat stopped past the token's expiry self-heals on
  restart instead of retry-looping on "identify not admitted" forever (bit the
  deployed CarterLights hub on 2026-07-12). Transient validator errors fall
  through to the stored token; revocation raises `CarterDeviceRevoked`.

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
