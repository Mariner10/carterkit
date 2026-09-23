# carterkit

[![PyPI](https://img.shields.io/pypi/v/carterkit.svg)](https://pypi.org/project/carterkit/)
[![Downloads](https://static.pepy.tech/badge/carterkit)](https://pepy.tech/project/carterkit)
[![Python versions](https://img.shields.io/pypi/pyversions/carterkit.svg)](https://pypi.org/project/carterkit/)

Build and drive [CAR-TER](https://carterbeaudoin.net/CAR-TER) layouts from Python.

**The control docs are the library.** Every control's schema, fields, and examples
are parsed at runtime from the ControlDocs markdown bundled inside the package — the
exact same docs the CAR-TER app renders — so the catalog never drifts from the
definitions.

```bash
pip install carterkit
```

## iOS surfaces from your backend

Use `hub.surfaces` to refresh widgets and Control Center state, send notifications
with buttons and inline replies, and start/update/end Live Activities. It derives
payloads from your layout and uses the hub's renewed Add Hub credential. Existing
`@control.on` handlers receive actions from widgets, Control Center and Shortcuts.

```python
await hub.surfaces.publish({temperature: 25}, activity=True)  # widgets + Control Center + island
await hub.surfaces.notify("Workshop", "Job complete", include_glance=True)
print(await hub.surfaces.state())     # what a widget pulls when iOS wakes it
```

`publish` is one request to the relay, which **retains** the values: a widget iOS
wakes hours later still renders something, and the relay's own floors coalesce a
chatty publisher rather than burning the app's push budget (a skipped push comes
back as `suppressed`, with the state merged either way).

Design the surfaces in the layout, in the same vocabulary as the controls:

```python
from carterkit import tile, scene, widget, island, live, cc_toggle, cc_step

ui.glance(hero=nozzle, live=live(tier="fresh"),
          widgets=[widget("temps", title="Temps", families=["systemMedium"],
                          scene=scene([tile("gauge", nozzle), tile("gauge", bed)],
                                      [tile("sparkline", nozzle, span=2)]))],
          island=island(compact_trailing=tile("ring", progress),
                        expanded=dict(bottom=scene([tile("gauge", nozzle)]))),
          controls=[cc_toggle("lights", "Lights", lights),
                    cc_step("fan-up", "Fan +10", fan_speed, delta=10)])
```

Control Center has toggles and buttons only, so a slider becomes `cc_step`/`cc_set`
and a picker becomes `cc_cycle`; `carterkit.doc("glance")` has the full reference.

See the [connector guide](docs/ios-surfaces.md) for setup, notification actions,
delivery semantics, payload limits and lower-level APIs. The
[example](examples/ios_surfaces.py) previews offline by default. These additions
are in this checkout; installing the existing PyPI release does not include them.

## Explore the controls (zero config)

```python
import carterkit

carterkit.controls()            # {type: schema} for every placeable control
carterkit.doc("gauge")          # full parsed doc: fields, themeFields, examples
print(carterkit.doc_markdown("gauge"))   # the rendered documentation prose
carterkit.examples("button")    # documented example snippets
```

## Build a layout

Controls are **methods on the layout**, ids are positional, tabs and groups are context
managers, and bindings fold into kwargs. Each control method returns a **handle** you can
use as a binding target or patch later. Unknown control types and bad enum values raise
instead of silently shipping a broken layout:

```python
from carterkit import Layout

with Layout("Dashboard", cols=4, rows=4) as ui:
    ui.connect("ws://192.168.1.50:8765", channel="home")
    with ui.tab("Main", icon="gauge"):
        cpu = ui.gauge("cpu", label="CPU", min=0, max=100, span=(2, 2),
                       listen="cpu", when={"msg_type": "metrics"})
        ui.status_light("warn", visible=cpu > 90)      # handle → visibility condition
        ui.button("refresh", label="Refresh", send="refresh")

print(ui.findings())        # schema + grid + binding lint against the bundled catalog
ui.save("dashboard.json")   # the composed layout, ready to push/load
```

Binding sugar: `listen=`/`when=`/`event=` build a `sync`, and `send=`/`payload=` build
an `action` — `send="refresh"` compiles to the one shape the relay actually forwards
(`broadcast_request` tagged `msg_type: "refresh"`; `Hub.on` demuxes it back for you).
Pass `sync=[...]`/`action={...}` (via `carterkit.bind`) for anything fancier. A handle
comparison (`cpu > 90`) becomes a real visibility condition; `==`/`!=` stay normal
Python, so use `.eq()`/`.neq()`. `help(carterkit.build.gauge)` prints any control's
documentation, straight from the bundled docs.

> **Naming:** multi-word controls are **`snake_case` as `Layout` methods**
> (`ui.status_light(...)`, `ui.log_console(...)`, `ui.progress_ring(...)`) but
> **`camelCase` as the JSON `type`** and as `carterkit.build.*` functions
> (`"statusLight"`, `build.logConsole`). Single-word controls (`gauge`, `button`) look
> the same either way. Grid size (`cols`/`rows`) set on `Layout(...)` is the default for
> every tab; override it per tab with `ui.tab("Name", rows=…)`.

### Beyond MeshSocket — sources, sensors, and app-side features

A layout can drive itself off protocols you already run, or the phone's own hardware, with
**no server code** — the app speaks them directly:

```python
ui.source_mqtt("broker", "mqtt://192.168.1.10:1883")   # declare a broker
ui.source_http("api", "http://192.168.1.5:8080", interval=5)
with ui.tab("Home", icon="house"):
    ui.gauge("temp", label="Temp", min=0, max=40, sync=[bind.mqtt("home/temp")])
    ui.toggle("fan", label="Fan", sync=[bind.mqtt("home/fan/state")],
              action=bind.mqtt_publish("home/fan/set"))
    ui.gauge("cpu", label="CPU", sync=[bind.http("/status", interval=5, valuePath="cpu")])
    ui.compass("hdg", label="Heading", sensor="heading")   # device sensor, no backend
```

`bind.mqtt` / `bind.mqtt_publish` / `bind.http` / `bind.http_request` / `bind.sensor` build
the sync/action dicts; the validator checks a `source:` names a declared source and that
mqtt/http bindings carry a topic/path. These are marked **app-direct** in the contract, so a
generated `bridge.py` never tries to serve them.

Author the rest of the app's surface from Python too:

```python
ui.publisher("heading", interval=0.25)                     # stream a sensor to a hub/server
ui.alert(event="broadcast", value_path="temp", operator="gt", value=30,
         title="Too hot", body="Greenhouse over 30°C")     # relay-watcher push rule
ui.glance(hero="temp", slots=["fan"], live_activity=True)  # widgets / island / Control Center
ui.poll_group("tick", event="broadcast_request", interval=10, payload={"msg_type": "poll"})
ui.appearance(color_scheme="dark", show_header=True)
ui.dynamic_tab("inject_tab")                               # runtime-injected tab
ui.state(sync=True, authority="hub", acks=True)           # device-held shared state + acks
```

**Prefer a declarative style?** A class veneer compiles to the *same* layout — ids come
from attribute names, tabs/groups are nested classes (great for fixed dashboards; the flat
builder reads better for generated ones):

```python
from carterkit.declare import Screen, Tab, Connect, Gauge, Button, StatusLight

class Dashboard(Screen, cols=4, rows=4):
    relay = Connect("ws://192.168.1.50:8765", channel="home")
    class Main(Tab, icon="gauge"):
        cpu  = Gauge(label="CPU", min=0, max=100, span=(2, 2), listen="cpu")
        warn = StatusLight(visible=cpu > 90)
        refresh = Button(label="Refresh", send="refresh")

Dashboard.save("dashboard.json")
```

### Dynamic groups

Generate controls in `for`/`if` loops (auto-placed in the group's own grid), or mark a
group `dynamic="event"` and replace its children live at runtime. Build that replacement
payload with `Fragment`, then lint it against the broadcasts your server actually emits —
catching events that never arrive, missing `children` arrays, and off-grid/invalid
injected controls before they ship:

```python
import carterkit
from carterkit import Fragment

ui.group("Now Playing", span=(3, 4), cols=4, rows=3, dynamic="player_state")

frag = Fragment(cols=4, rows=3)
frag.label("title", text="Song", span=(1, 4))
frag.button("play", label="Play", send="play")
# your server broadcasts frag.payload("player_state") == {"msg_type": ..., "children": [...]}

print(carterkit.format_findings(
    carterkit.lint_dynamic_traffic(ui.layout, [frag.payload("player_state")])))
```

Prefer surgical edits? `LayoutBuffer` gives `add_control` / `update_control` / `move_control`
over a held draft; `lay.buffer` exposes it.

`infer.build_layout(payload)` generates a wired layout from a sample telemetry dict;
`codegen.generate_service_stub(layout)` emits a runnable `Hub`-based server skeleton;
`theming.theme_for(...)` and `tune.tune_gauge(...)` round out the authoring tools.

## CLI

```bash
carterkit catalog                 # list every control type
carterkit doc gauge               # print a control's documentation
carterkit examples button         # list a control's examples (--name to print one)
carterkit validate layout.json    # lint a layout (exit 1 on errors)
carterkit gen layout.json         # generate a runnable Hub server stub
carterkit relay --port 8765       # run the bundled MeshSocket relay (keyed, loopback)
carterkit relay --lan --key s3cret  # let phones on the LAN join with that shared key
```

`carterkit relay` generates and prints a shared key when you don't pass `--key`, and
binds `127.0.0.1` unless you pass `--lan`. Running it open (no key) requires
`--insecure` and means anyone who can reach the port joins every channel.

## Drive the layout you just built

The layout already declares every control's wire contract, so the same object that
authored the UI also drives it — `ctrl.push(value)` derives the broadcast from the
control's `sync` binding, and `@ctrl.on` derives the demux from its `action`:

```python
import asyncio
from carterkit import Layout

with Layout("Thermostat") as ui:
    with ui.tab("Main"):
        temp   = ui.gauge("temp", label="Temp", min=0, max=40,
                          listen="temp", when={"msg_type": "climate"})
        target = ui.slider("target", min=10, max=30, send="set_target")

async def main():
    async with ui.serve() as hub:        # zero config: embedded LocalRelay
        print("pair the app with:", hub.qr_json())
        await hub.wait_for_device()
        await hub.push_layout()          # routed apply-layout; echoes what rendered

        @target.on
        async def _(data):
            heater.set(data["value"])

        while True:
            await temp.push(read_temp())
            await asyncio.sleep(2)

asyncio.run(main())
```

The same surface works cross-process off the saved JSON — the layout file is the
contract: `Hub("dashboard.json").push("temp", 21.5)`. Dynamic groups fill with
`hub.fill(group, fragment)`; the hub answers late joiners with the last pushed values
(control-state authority) by default.

## One connection story

`Connection.parse(...)` accepts every connection artifact in the ecosystem, and
`ui.connect(...)` / `ui.serve(...)` / `Hub(...)` all take it:

| You have | Pass | Works |
|---|---|---|
| nothing (LAN dev) | `ui.serve()` | embedded `LocalRelay`, QR pairing |
| a self-hosted relay | `"ws://192.168.1.50:8765"` (+ `token=`) | symmetric: same config for app & hub |
| Connect+ | the **Add Device** JSON from the app (Members → Add Device) | token self-refresh + room E2EE automatic |

The asymmetry to know: self-hosted is symmetric (one URL + shared key both sides);
on Connect+ the app joins with its own account while the hub holds the per-device
credential — which is the hub's identity, so it is never embedded into a layout.

`CarterClient` remains the lower-level client (`on`/`broadcast`/`request`).
End-to-end encryption (ChaCha20-Poly1305 + per-session salt) is applied to every frame
the client sends when an `e2ee_key` is present, and every sealed frame it receives is
opened, replay-checked and freshness-checked (±120 s) before a handler sees it. Keys
must be exactly 32 bytes (base64). What E2EE does **not** do: room mode is one
symmetric key per room, so it does not tell members apart — any member can send as
any other. And in 0.12 a *plaintext* frame arriving in an E2EE session is still passed
through (with a one-time warning per `msg_type`) because the current app answers
routed requests in the clear; pass `CarterClient(strict_e2ee=True)` to drop them, which
becomes the default in 0.13. Relay control frames are always plaintext.

Send a push to every device on a Connect+ account with `CarterClient.notify(...)` or
the stdlib-only `carterkit.notify_http(...)`.

### Security defaults (0.12)

- The embedded `LocalRelay` (and `Hub()` / `ui.serve()` with no connection) gets a
  random shared key and binds `127.0.0.1`. Pass `host="0.0.0.0"` for LAN pairing (the
  QR carries the LAN address and the key); a keyless relay needs `insecure=True`.
- A device credential's `validator` must be `https`. Plain `http` is accepted only for
  `127.0.0.1`/`localhost` with `allow_insecure_validator=True`.
- `carterkit explore` serves loopback only, refuses foreign `Host`/`Origin`, requires a
  per-run token on every write, and redacts `connection.token`, `e2eeKey` and source
  passwords/auth headers from `/api/layout` and `/api/status`. The QR on the page still
  encodes the full pairing payload — that is what the phone scans.
- `validate_layout` never raises on hostile input and flags `non_finite`, `too_deep`,
  `too_many_controls`, `bad_url`, `embedded_secret` and `long_string`.
- `Layout.save` writes `0600` (a layout may carry a relay or room key).
- Inbound frames are dispatched under a semaphore (32) and a per-`msg_type` token
  bucket (20/s, burst 40); excess frames are dropped and counted in `client.dropped`.

## Built on

[`meshsocket`](https://pypi.org/project/meshsocket/) — the WebSocket mesh transport.

The ControlDocs are vendored from the CAR-TER app repo; refresh them with
`scripts/sync-controldocs.sh`.
