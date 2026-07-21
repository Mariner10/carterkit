# carterkit ↔ CAR-TER app parity audit (0.7.0 prep)

## 0.7.0 outcome (what landed)

**Acceptance: all 25 SampleLayouts + all 10 templates validate with ZERO errors** (was
8 samples failing). Suite 219→**230 passed**. Highlights:
- Validator made app-faithful: `bad_enum`→warning (+ `:param` strip), mqtt/http/sensor
  bindings validated by their own shape (no forced `event`), `mode:"flow"` grids skip 2-D
  bounds, shared `ControlDefinition` display fields recognized, `source:` refs + unused
  sources checked, light top-level validation for sources/alerts/publishers/glance/state.
- Builder/bind sugar added: `source_mqtt`/`source_http`, `bind.mqtt`/`mqtt_publish`/`http`/
  `http_request`/`sensor` (+ `sensor=` kwarg), `publisher`, `alert`, `glance`, `poll_group`,
  `appearance`, `dynamic_tab`.
- Codegen + contract mark mqtt/http/sensor as **app-direct** (new `contract.appDirect`;
  stubs never fake-serve them); the `carterkit explore` page shows them.
- Parity acceptance pytest (`test_parity_acceptance.py`) + round-trip authoring tests
  (`test_parity_authoring.py`) with a soft warning-inventory drift guard.

**Intents/Siri**: needs no new kit API — the app derives App Intents from **labeled
actionable controls**, so a control built with a `label=` and a `send=`/`action` already
carries everything Siri surfaces. Documented as the mechanic (no code change).

**Notif v2**: a **runtime** feature, already complete on `main` — `CarterClient.notify(
actions=…, sender=…, image=…)` sends, `on_notif_action` / `Hub.on_notif_action` receive the
flat `notif_action` frame (room-cipher E2EE automatic). Nothing to author in a layout.

Two benign warning classes remain over the app's own corpus (reviewed, expected): `bad_enum`
×3 (`three_quarter`×3 — app renders it as half) and `bad_action` ×9 (ilogger uses
`mode:"request"` on broadcasts — fires fine, just awaits a reply that never comes). (The
earlier `outline`×2 was an app-doc self-inconsistency — `button.md` `values:` now includes
`outline`, re-vendored, so those warnings are gone.)

---


Source of truth is the **app**: `CAR-TER/CAR-TER/ControlDocs/*.md` (62 docs, incl the new
`sources.md`) + `CAR-TER/CAR-TER/Models/*.swift`. When kit and app disagree, the app wins.
Docs re-vendored via `scripts/sync-controldocs.sh` (62 docs; `sources.md` added, plus
`actions/index/layout-config/sync` refreshed from the sources work).

`sources.md` is a **system doc** (`category: system`) — it parses (fields available to the
validator via `catalog.parse_all`) but is correctly excluded from the placeable catalog by
`PLACEABLE_CATEGORIES`, so it never appears as a control. No parser change needed; verified.

Columns: **B**uilder (`ui.*`/`build.*`/`bind.*`) · **V**alidator/linter · **C**odegen ·
**X** contract/explore · **R** client/hub runtime. Cell = `ok` / `ADD` (added in 0.7.0) /
`n-a` (with reason). "app-side" = an app/relay runtime the kit only authors + validates +
explains, never speaks itself.

## Acceptance debt (the 8 SampleLayouts the kit wrongly rejects today)

The app renders all 25 SampleLayouts + all 10 templates; templates already pass (0 errors).
Only these 8 samples error, in 3 root-cause classes — all **validator over-strictness vs the
app's real tolerance**, not authoring bugs:

| Class | Files | Root cause | Fix |
|---|---|---|---|
| enum too strict | cider-music, demo-layout, demo-offline, feature-demo | app **defaults gracefully** on an unknown enum (CARGauge: anything ≠ `full` ⇒ half; button style falls back) — it never rejects | `bad_enum` → **warning** (app-faithful) |
| parameterized enum | companion-chat, companion-room | `formatValue: "decimal:2"` is a real parameterized format (`CARValueFormatter` parses `decimal:N`/`suffix:`/`prefix:`) | strip `:param` before enum check ⇒ not even a warning |
| mqtt/http action | sources-demo | validator requires `event` on every action, but `method:"mqtt"/"http"` actions have `topic`/`path`, no `event` | action validation branches on `method` |
| flow-grid bounds | deep-nest-test (14×) | grid `mode:"flow"` stacks children and ignores 2-D position/span; validator bounds-checks anyway | skip placement checks when `mode == "flow"` |

`button.style: "outline"` (cider) is documented as accepted in the app doc's own prose but
omitted from its `values:` list — an **app-doc self-inconsistency** (flagged; downgraded to a
benign warning by the `bad_enum` change; app doc should add `outline` to the enum list).

Pre-existing red: `tests/test_connection.py::test_parse_account_block_cannot_serve` fails only
because the uncommitted `connection.py` edit renamed the error string "Add Device"→"Add Hub";
the test's `match=` must follow (fix-forward, done in Step 2).

## Layout-surface parity table

| Feature (from LayoutConfig / sync-action) | B | V | C | X | R | Notes |
|---|---|---|---|---|---|---|
| name / headerTitle / version / accentColor | ok | ok | n-a | n-a | n-a | validator requires name+version |
| tabs / grid / groups (+ nested) | ok | ok | ok | ok | ok | flow-mode bounds fix (V) |
| connection block (url/identity/mode/e2eeKey) | ok | ok | ok | ok | ok | `bind.connection`, `Connection.parse` |
| appearance | **ADD** | ADD | n-a | n-a | n-a | app-side render; add `ui.appearance()` + light validation |
| theme | ok | ok | n-a | n-a | n-a | `theming.theme_for`; themeFields validated |
| state (sync/authority/acks/ackTimeoutMs) | ok | **ADD** | n-a | n-a | ok | `ui.state()`; Hub authority+acks; add light validation |
| id (portable layout id) | ok | n-a | n-a | n-a | ok | auto/keeps |
| pollGroups | **ADD** | **ADD** | ok | ADD | ok | add `ui.poll_group()`; server answers the poll event |
| dynamicTabs (top-level) | **ADD** | ADD | n-a | ADD | ok | dynamic *groups* exist (`dynamic=`); add top-level dynamicTabs authoring; `Hub.fill` |
| **sources** (mqtt/http source defs) | **ADD** | **ADD** | ADD | **ADD** | n-a(app-side) | `ui.source_mqtt/http`; validate declared-source refs; explore feed = app-direct |
| **sensors** (`method:"sensor"` sync) | **ADD** | **ADD** | n-a | ok | n-a(app-side) | `bind.sensor()`; validate sensor name vs `sensors.md`; contract already lists |
| **publishers** (SensorPublisherDefinition) | **ADD** | **ADD** | n-a | ok | n-a(app-side) | `ui.publisher()`; contract already surfaces publishers |
| **alerts** (relay-watcher rules) | **ADD** | **ADD** | n-a | ADD | ok | `ui.alert()`; validate broadcast+msg_type+valuePath+cmp; watcher payload |
| **glance** (GlanceConfig) | **ADD** | **ADD** | n-a | ADD | n-a(app+relay) | `ui.glance()`; validate control ids/candidates; LA push doc |
| meshsocket sync (listen/when/event/valuePath/filter) | ok | ok | ok | ok | ok | |
| meshsocket action (send/command/broadcast_request) | ok | ok | ok | ok | ok | dead_action lint |
| **mqtt sync/action** (topic/retain) | **ADD** | **ADD** | ok(app-direct) | **ADD** | n-a | `bind.mqtt()`; validate topic + source; codegen marks app-direct |
| **http sync/action** (path/url/interval/httpMethod) | **ADD** | **ADD** | ok(app-direct) | **ADD** | n-a | `bind.http()`; validate path/url + source |
| acks / ackTimeoutMs | ok | ADD | n-a | n-a | ok | via `state()`; Hub `enable_command_acks` |
| `{{value}}` typed passthrough | ok | n-a | ok | ok | ok | |
| **notif v2** (`notif_action`, flat, room-cipher E2EE) | **ADD** | **ADD** | n-a | ADD | ok | `bind.notif_action`/`ui`; validate shape; `hub.on_notif_action` (committed) |
| E2EE room cipher | ok | n-a | n-a | n-a | ok | `e2ee.E2EESession.group` |
| Intents/Siri (labeled actions) | **ADD** | n-a | n-a | ADD | n-a(app-derived) | ensure builder attaches `label`/action-name metadata; document mechanic |
| per-control configs (canvasConfig, drag-pack frame/spatial, chat, popover/markdown) | ok | ok | ok | ok | ok | umbrella `fooConfig` synth; validated after re-sync |
| dynamic groups / slots | ok | ok | n-a | ok | ok | `dynamic=`, `Hub.fill` |

## Controls catalog (post-resync)
43 placeable controls exposed with correct categories/fields; `canvas`/`pinboard`/`sortboard`
(cat `input`) + `divider`/`spacer` (cat `layout`) placeable; drag-pack umbrella configs synthesize.
No control gaps.

## Implementation plan (Step 2)

**Validator (unblocks acceptance — do first):**
1. `bad_enum` → `warn`; strip `:param` (value before first `:`) before membership test.
2. `_validate_bindings`: branch on `method` — `mqtt`/`http`/`sensor` actions don't need `event`;
   validate their shape instead (mqtt→`topic`; http→`path`|`url`). Sync: `valuePath` optional for
   mqtt/http/sensor (bare payloads); mqtt sync→`topic`; http sync→`path`|`url`.
3. Thread declared `sources` into validation: a `source:` ref must name a declared source; mqtt
   binding with 0 or >1 mqtt sources without `source` → error/warn per sources.md rules.
4. `_grid_findings`/`validate_placement`: skip bounds+overlap when grid `mode == "flow"` (tab+group).
5. Light top-level validation for `sources`, `alerts`, `glance`, `publishers`, `state` shapes
   (never reject unknown top-level keys the app tolerates).

**Builder sugar (parity):**
6. `bind.mqtt(topic=…, value_path=…, retain=…)`, `bind.http(path=…/url=…, interval=…, http_method=…)`,
   `bind.sensor("heading")`, `bind.notif_action(...)`; wire `listen=`/`send=` to accept a `method=`.
7. `Layout` top-level setters: `source_mqtt(name, url, …)`/`source_http(name, base_url, …)`,
   `publisher(sensor, …)`, `alert(...)`, `glance(...)`, `poll_group(...)`, `appearance(...)`,
   `dynamic_tabs(...)` — following existing naming idioms (snake methods, camel JSON).

**Codegen/contract/explore:** mqtt/http/sensor feeds surfaced as **app-direct** (stubs don't
fake-serve them); notif_action + alert feeds noted; explore/contract strings for new feed types.

**Acceptance test (Step 3):** pytest globbing all `SampleLayouts/*.json` + `templates/*.json`,
`validate_layout` → **zero errors** (warnings reviewed); skip when app repo not adjacent.
Round-trip: kit-built layouts using each new feature validate + decode-parity (no unknown-field
warnings vs vendored docs).

**Docs/0.7.0 (Step 4):** README/API for new sugar; CHANGELOG + `pyproject` → 0.7.0; `carterkit lint`
picks up new rules. No publish.

### Deliberately n-a (justified)
- MQTT/HTTP wire + sensor hardware + glance/LiveActivity presentation + Siri intent surfacing are
  **app/relay runtimes**; kit's role is author + validate + explain, never speak them (per brief).
- No request/reply sugar for named commands (relay only routes `route_msg` replies) — unchanged.
