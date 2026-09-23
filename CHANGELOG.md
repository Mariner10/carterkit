# Changelog

All notable changes to **carterkit** are documented here. This project follows
[Semantic Versioning](https://semver.org/).

## [0.12.0] — unreleased

Security hardening from the 2026-09-22 audit, plus the Ambient Surfaces v2 work that
was staged as 0.11.0 and never published (folded in below).

### Security
- **E2EE `open()` is a validated parser.** Any malformed envelope — a negative, float,
  string or ≥2^64 counter, a salt that is not 16 bytes, a ciphertext shorter than the
  tag, loose base64, a missing field, a bad tag — raises one `ValueError`. Derived keys
  are cached per salt (bounded LRU of 256) so HKDF no longer runs per frame.
- **Replay and freshness inside the frozen v2 envelope.** `seal()` stamps `_ts` (unix
  ms), `_ch` (channel) and `_from` (sender) into the plaintext; `open()` rejects a
  duplicate `(salt, counter)` (high-water mark + 64-frame reorder window, LRU of 256
  salts), a `_ts` more than ±120 s from local time, and a `_ch` for another channel.
  The wire bytes are unchanged and old receivers ignore the extra keys. `_ts`/`_ch`
  are consumed on open; `_from` is kept for handlers, and `CarterClient` overwrites it
  with the relay-stamped sender when one is present. `seal(..., stamp=False)` seals a
  payload verbatim (test vectors; notification `enc` content uses it).
- **32-byte keys only.** `E2EESession`, `CarterClient(e2ee_key=)`, `Connection` (layout
  `e2eeKey`, QR/credential `k`) and `bind.connection()` reject keys that are not
  strict base64 of exactly 32 bytes.
- **Fail-closed receive path.** `CarterClient._open` never raises into a handler: an
  undecryptable envelope is dropped and counted (`client.dropped`). A plaintext frame
  in an E2EE session is dropped by default (`strict_e2ee=True`); `strict_e2ee=False`
  passes it through with one warning per `msg_type` as a debugging aid only. Relay
  control frames (`welcome`, `node_status`, `roster`, …) are always allowed. No
  compatibility path: peers that do not seal every frame must be upgraded together.
- **Inbound backpressure.** Dispatch runs under `asyncio.Semaphore(32)`
  (`max_inflight=`) and a per-`msg_type` token bucket (`rate_per_type=20`, burst 2x);
  excess frames are dropped with a counter and a rate-limited warning.
- **`LocalRelay` is keyed and loopback by default.** `key=None` generates
  `secrets.token_urlsafe(24)` (read it back from `relay.key`; `Connection.parse(None)`
  does the same); `host` defaults to `127.0.0.1`. A keyless relay, or a keyless bind on
  a non-loopback host, requires `insecure=True`. `Hub(..., host=, insecure=)` passes
  through. `carterkit relay` gained `--key` (generated and printed once when omitted),
  `--lan` and `--insecure`; it refuses to run open without `--insecure`.
- **Validator URL must be https.** `device_refresh_http`, `CarterClient(validator_url=)`
  and `Connection` reject an `http://` validator unless the host is loopback and
  `allow_insecure_validator=True`; the refresh POST has a 10 s timeout.
- **`carterkit explore`** refuses foreign `Host` (421) and cross-site writes (403),
  requires a per-run token (`X-Explorer-Token` header / `?token=` on `/events`) on every
  POST, and redacts `connection.token`/`e2eeKey`, `sources.*.password` and auth-like
  headers from `/api/layout` and the generated stub. `/api/status.qr` no longer carries
  the relay key or room key; the full pairing payload is at `/api/pairing` (token
  required) for the page's copy button. POST bodies are capped at 1 MB.
- **`validate_layout` never raises.** New findings: `bad_span`, `bad_grid`,
  `bad_position` (non-integer geometry), `non_finite` (NaN/Infinity), `too_deep`
  (groups past 16 levels), `too_many_controls` (over 2000), `bad_url` (schemes outside
  https/http/mqtt/mqtts/ws/wss; http warns), `embedded_secret` (connection token/key,
  source passwords/auth headers) and `long_string` (> 4 KB). Cell enumeration is capped
  so a `span: [1500, 1500]` is reported, not built.
- **Generated servers are secure by default.** `carterkit gen` emits a hub keyed from
  `CARTER_RELAY_KEY` (or a fresh key), bound to `CARTER_RELAY_HOST` (default loopback),
  with `logging.basicConfig`, an exception-safe telemetry loop, typed value guards
  derived from each control's spec, and the pairing payload rendered as an ASCII QR
  instead of printed JSON.
- **`Layout.save` writes 0600.**
- **Packaging:** `meshsocket>=0.2.0,<0.3`, `cryptography>=42,<50`; `MANIFEST.in`
  excludes `tests/`; the publish workflow pins actions by SHA, runs the test suite
  first, checks the tag against `pyproject.toml`, and publishes from the protected
  `pypi` environment.

### Changed
- `E2EESession.seal()` output for a given plaintext differs from 0.11 because of the
  stamped fields; the construction itself (HKDF labels, nonce, cipher) is unchanged
  and the frozen test vectors still hold with `stamp=False`.
- `Connection.parse(None).key` is a fresh random key instead of `""`; `qr_json()` and
  `layout_block()` therefore carry a `token` for local relays.
- `Connection.app_url()` returns `ws://127.0.0.1:<port>` for a loopback-bound embedded
  relay instead of the LAN ip a phone could not reach anyway; `Hub`, `carterkit relay`
  and `carterkit explore` log/print a one-line hint that `host="0.0.0.0"` / `--lan` is
  needed for a phone on the LAN. `carterkit explore --lan` added.
- `Hub(strict_e2ee=, max_inflight=, rate_per_type=)` pass through to `CarterClient`.
- The explorer's `/api/status.qr` is the pairing JSON minus `token`/`k`.
- Docs (README, `relay.py`, `client.py`) now state what the code guarantees: room mode
  does not authenticate senders; plaintext in an E2EE session is dropped; the
  explorer's redaction covers layout and status, not the QR.
- **Requires `meshsocket>=0.2.0`** (identify-after-auth closes, identity validation,
  fail-closed server defaults).

### Ambient Surfaces v2 (staged as 0.11.0, unpublished)

The layout reaches iOS *outside* the app as widgets, a Dynamic Island, a lock-screen
banner and Control Center buttons — and one call keeps all of them live.

### Added
- **`hub.surfaces.publish(...)`** — ONE request (`POST /surfaces/publish`) that
  merges this layout's values into the relay's retained state and pokes every
  surface: widget push tokens, Control Center control tokens and the registered
  Live Activities. Values are keyed by control handle or id, `controls=` mirrors
  Control Center tile state, and `activity=True` lets the relay synthesize the
  content state from the merged values (`"end"` finishes the session, a dict says
  exactly what to send). Publishing at telemetry rate is safe: inside the relay's
  floors the state still merges and the surface is reported `suppressed`.
- **`hub.surfaces.state()`** — what a widget pulls when iOS wakes it
  (`GET /surfaces/state/<layoutId>`), or `None` before the first publish.
- **`hub.surfaces.register_token()` / `.deregister_token()`** — register a widget
  or Control Center push token for the layout, for provisioning and tests.
- **`carterkit.ambient.surfaces_*`** — the stdlib-only request builders behind
  those: `surfaces_register_token`, `surfaces_deregister_token`,
  `surfaces_get_state` (404 → `None`), `surfaces_put_state` (merge without
  spending a push) and `surfaces_publish`. They validate what the relay would
  otherwise reject in silence: scalars only, layout ids ≤ 128 bytes and free of
  the `#`/`|` the relay's storage keys are delimited by, an 8 KB body, and the
  five documented `activity` keys (`contentState`, `staleSeconds`, `priority`,
  `relevanceScore`, `event`).
- **`carterkit.glance`** — builders for the v2 `glance` block, exported at the top
  level: `tile`, `scene`, `widget`, `island`, `live`, `state`, and the Control
  Center set `cc_toggle` / `cc_button` / `cc_cycle` / `cc_step` / `cc_set`. Every
  `control=` takes a `Layout` control handle as well as an id, and the kind's
  required fields are checked at build time — a `cycle` with one state or a `step`
  with nothing to step raises here instead of rendering as a dead button.
- **`Layout.glance(...)` takes the v2 fields** — `controls` entries of kind
  `toggle`/`button`/`cycle`/`step`/`set` (with `on`/`off` styling, `valueControl`,
  `valueLabel`, `states`, `delta`, `value`), plus `live`, `widgets`, `island` and
  `lock_screen`. The v1 signature is unchanged and v1 layouts emit exactly what
  they did before. Control handles are resolved to ids anywhere in the block,
  including inside hand-written dicts.
- **`validate_layout` lints the v2 block** — `bad_glance` for a tile, control,
  `valueControl`, hero or slot naming a control that isn't in the layout;
  `bad_glance_tile` for an unknown tile kind; `bad_glance_control` (error) for a
  `step`/`cycle`/`set` with no `control`, a `cycle` with fewer than two states, or
  a non-numeric `delta`; `bad_glance_family`, `bad_glance_live`,
  `bad_glance_island` (a single-tile island region handed a scene) and
  `bad_glance_span` (a tile or row wider than its scene).
- **ControlDocs**: the new `glance.md` — the full surface reference, from what iOS
  allows per surface to the tile table and the liveness tiers — and the
  `layout-config.md` that points at it. `carterkit.doc("glance")` resolves it.

## [0.10.0]

### Added
- **`Layout.batch_publishers()`** — emits the top-level `batchPublishers: true`: the
  phone sends one `sensor_batch` frame per tick of its fastest publisher interval,
  each sensor riding the ticks where its own interval is due. `CarterClient`
  unbatches transparently (`on_broadcast` / Hub handlers see plain `sensor`
  frames); `validate_layout` checks the flag is a bare bool and notes when there is
  no `publishers` block. Docs re-vendored (publishers, layout-config, sources).
- **`Layout.keep_awake()`** — emits the new top-level `keepAwake: true`, asking the
  app to suppress the iOS auto screen lock while the layout is on screen (a
  request the user can veto in Permissions → Data Pipe). `validate_layout` warns
  when the field isn't a bare bool. Docs re-vendored (layout-config, publishers).

## [0.9.1]

### Added
- **`carterkit.ambient`** — the surfaces that reach a device when the app is not
  running: the Live Activity / Dynamic Island push pipeline
  (`live_activity_register` / `live_activity_deregister` / `live_activity_push`,
  with the `apple_date` / `content_state` / `activity_attributes` helpers and the
  wire constants they guard) and `mesh_broadcast`, the relay's HTTP bridge that
  carries a press with no socket held open. Stdlib-only, like `notify_http`.
  Includes the silent-push vs NSE-alert delivery-guarantee table — a silent
  refresh stops at force-quit; an alerting one always works.

### Fixed
- **`DEFAULT_VALIDATOR` pointed at the relay, not the validator.** The fallback
  used when a device credential carries no `validator` key was the WebSocket
  relay host (`connect.carterbeaudoin.net`), which serves no HTTP API — so a
  credential without an embedded validator could never refresh its token or send
  alerts. It is now the Connect+ validator base
  (`https://zzko0nn851.execute-api.us-east-1.amazonaws.com`), matching the app's
  Release config.
- **Ambient HTTP calls send an explicit User-Agent** — Cloudflare 403s urllib's
  default.
- **Re-vendored `map.md`**: object-array feeds, SF-symbol/puck markers, motion,
  recenter.

## [0.9.0]

Control docs for the live-data feature set: vendors the ControlDocs that let a
layout render real public-API data with no server (map markers/GeoJSON/globe,
label/image value→text/symbol/tint maps, list dot-path columns, bare-array
sparkline) and teaches `contract.py` about them. Also stops a single validator
HTTP 403 from being treated as permanent device revocation (3 consecutive 403s
now required), which silently killed a Connect+ hub's phone link.

## [0.8.0]

**Studio Mirror** — `carterkit explore` now mirrors the phone live, and can drive any
control on it, not just the wire-bound ones.

Previously a Studio Session pinned the phone to a blank layout and the explorer pulled
that blank layout, so both screens sat dead. The app now treats the studio connection as
authoritative (navigate anywhere; every layout registers on the studio socket) and
narrates what the user is doing; this release is the listening half.

### Added
- **Studio Mirror demux.** Broadcasts carrying `msg_type: "studio.event"` are demuxed
  out of the generic wire log into typed SSE events (`{kind: "studio", event, data}`)
  for the seven-event vocabulary: `hello`, `layout`, `layout-closed`, `tab`, `action`,
  `value`, `bye`. Full contract in the app repo's `carter-mcp/PROTOCOL.md`.
- **`Explorer.mirror`** — live device state (device, app version, layout, tabs, active
  tab, alive flag, last event), surfaced as `"mirror"` in `/api/status`.
- **Auto-follow.** A `layout` event re-pulls `get-current-layout`, so the rendered
  contract follows the phone wherever the user navigates.
- **`Explorer.prime_mirror`** — a late or restarted explorer derives the same facts from
  the routed pull (`get-current-layout` + `get-device-info` + the roster) instead of
  showing an empty panel. Inferred fields always yield to a real `studio.event`.
- **`Explorer.set_control_values`** and `POST /api/set` — the routed `set-control-state`
  verb (new in the app), which is the only wire path to a control with **no `sync`
  binding**. Returns the device's truthful `{ok, applied, skipped}`.
- **`carterkit.explore.extract_controls`** and `GET /api/controls` — the *device* view:
  every control in the layout, wired or not, with a typed input inferred per control
  kind. Triggers/Data-feeds remain the *wire contract* view.
- **Device Mirror + Controls panels** on the Layout Link page: device/layout/tab pills, a
  live `action`/`value` ticker whose control ids jump to the matching feed input, and a
  Controls column that drives any control by id.
- **`carterkit.contract.is_group`** — the group test, exported.

### Fixed
- **Nested controls vanished from a pulled layout.** The app's layout echo re-encodes its
  own model, and older builds emit group nodes with **no `type`** (the Swift
  `GroupDefinition` has no such field). Every walker keyed on `type == "group"`, so it
  stopped at the group: nested controls disappeared and the group itself leaked through
  as a `type: "?"` row (Feature Demo listed 24 controls instead of ~60). `is_group` now
  also accepts the implicit shape (children, no `type`), and it is used by
  `walk_with_location`, `extract_controls`, the dynamic-group detection in
  `extract_contract`, and `Hub`'s control index — that last one meant a nested control
  could appear in Data feeds while `hub.push()` couldn't find it.

No layout-JSON changes. The wire gains one broadcast vocabulary (`studio.event`) and one
routed verb (`set-control-state`), both additive.

## [0.7.1]

A real, scannable pairing QR — `carterkit explore`'s web page shows one now instead of
just the raw JSON.

### Added
- **`carterkit.qr`** — a compact, dependency-free QR Code encoder (ISO/IEC 18004, byte
  mode, ECC L/M, auto version, standard mask selection). Vendored so `explore` and the
  CLI never need a runtime dependency.
- **Layout Link's pairing card.** The "Scan with CAR-TER to pair" card renders an inline
  SVG QR (white-backed for a dark page) plus the payload text and a copy button, for
  local/self-hosted connections; hidden when there's nothing to pair (a production
  Connect+ device never shows one). Updates through the page's existing status flow.
- **`carterkit explore`'s terminal output** now prints a half-block ASCII QR above the
  pairing JSON, so the phone can scan straight from the terminal.

No layout-JSON or wire-format changes.

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
