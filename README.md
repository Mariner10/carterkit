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

## Quickstart

```bash
pip install carterkit
carterkit start
```

`carterkit start` prints a QR. On the phone open CAR-TER, open the layout list (tap the
title) and tap **Scan** (or Settings -> Studio Session -> Open Scanner), and point it at
the QR. The Playground layout lands on the phone and you are at a live prompt with its
controls bound by id:

```
>>> await level.push(42)        # the gauge moves
>>> await hello.push("hi there") # the label changes
>>> @tap.on
... async def tapped(frame): print("tapped!")
```

Tab completes names, `help(level)` says what a control can do, Ctrl-D disconnects. The
pairing is kept in `.carterkit/session.json`, so the next `carterkit start` in the same
folder reconnects without a scan (`--fresh` starts over). No account and no credential:
the hub runs on your LAN and the QR carries its address and a random key.

**Linked, or kept.** A pushed layout is *linked* on the phone: it is the layout on screen,
every push updates it in place, its taps and slider moves come back to Python, and it is
not written into the phone's layouts (it waits for your laptop when the hub is away).
`await hub.install()` at the prompt, or `carterkit start --install`, keeps it as a real
layout; from then on pushes update that file. (An app older than the linked loop shows
the push in its Studio session; `carterkit` says which happened.)

**Make it yours, live.** Scaffold a project and edit `hello.py` while it runs:

```bash
carterkit new demo
cd demo
carterkit repl hello.py   # QR once, then a live prompt on that layout
```

Every save of `hello.py` is pushed to the phone: the layout (a new label, a moved
gauge) and the behaviour (`async def run(hub)` holds the handlers and loops; it is
restarted on each save). `python hello.py` does the same without the prompt. An import
error prints one line and keeps the last good version running.

**Connect+ instead of the LAN** (a managed relay, works away from home): in CAR-TER open
**Hubs -> Add Hub** and save the JSON it shows as `secrets/hub.json`; `hello.py` and
`carterkit repl` pick it up.

## Starter kits

Seven small, complete projects to start from: each is a `layout.json` (clean under
`carterkit validate`), a `hub.py` that serves it, and a README saying what it shows and
what to change first. The data is placeholder (`Item 1`, `Thing 2`, `Option A`).

```bash
carterkit new --list                          # the kits, one line each
carterkit new cards --template paged-cards    # scaffold one
cd cards && python hub.py                     # QR once, then it is live on the phone
```

| Kit | What it shows |
|-----|---------------|
| `paged-cards` | A card list the hub pages 20 rows at a time (`@hub.pages`), searched on the hub; each card expands into a detail page (`itemTemplate.expand`) |
| `confirm-delete` | A Delete that asks first: the hub calls `hub.confirm(..., destructive=True)` and acts only on `'confirm'` |
| `live-dashboard` | A gauge and a sparkline fed by one broadcast (`hub.push`), plus a readout and a Reset command |
| `hub-form` | A form group whose Send submits the whole draft (`{{form}}`) to the hub, which checks it again and answers |
| `scaled-grid` | 1 x 5 cards with a 3 x 15 grid drawn at 1/3 (`grid.scale: "auto"`), that expand to full size on a hold, and a sheet the hub opens (`hub.open_sheet`) |
| `progress` | A task the app draws as a pill, a sheet and on the Island (`hub.progress`), with Cancel, a live log (`hub.log`) and a toast (`hub.toast`) |
| `remote` | Toggles and sliders that only ask; the hub applies its rules and sends its state back (`hub.push(..., force=True)`) |

`hub.py` loads its layout with `Layout.load("layout.json")` and keeps the behaviour in
`async def run(hub)`, the same contract as `hello.py`: pairing by QR (kept in
`.carterkit/session.json`), `secrets/hub.json` for Connect+, and every save of `hub.py`
or `layout.json` pushed to the phone. `carterkit repl hub.py` adds a live prompt.

### Generate the hub side of any layout

`carterkit codegen layout.json -o hub.py` writes the same kind of `hub.py` for a layout of
your own (a phone export, one a connector built, a kit you changed), so `python hub.py`
pairs and serves it at once:

- one `@hub.on` handler per command the layout sends (control actions, row buttons in an
  `itemTemplate`, a form's submit), reading the payload fields and guarding `{{value}}` by
  the control's type and range;
- `@hub.pages` for every list with `paging`, serving placeholder rows (`Item 1`, `Example
  detail 1`) with exactly the fields its rows read as `{{item.<field>}}`, searched on the hub;
- `hub.confirm` before a command that deletes, removes or clears (a note instead where the
  action already has `confirm: "dialog"`: the app asked, asking twice is worse);
- the form's own rules (`form.fields`) checked again on the hub;
- an `open_<group>()` helper (`hub.open_sheet`) for each group with `expand`, and a
  `sheet_closed` handler;
- `hub.push` for what the hub feeds: the state of toggles and sliders it owns (sent back
  with `force=True`), list rows, a status label, and live readouts (gauges, sparklines,
  labels) from a periodic task.

Everything it cannot know is a commented `TODO`. Without `-o` it prints the script (for a
file beside the layout); `--force` replaces an existing file; `--stub` prints the older
`Hub(...)` service stub. In Python: `codegen.generate_hub(layout)` and, as plain data,
`codegen.analyze_hub(layout)`.

## Tutorials in the terminal

Step-by-step tutorials with a check per step, vendored from the CAR-TER docs
(`dev-guide/tutorials/`). A code tutorial ends exactly at a starter kit above.

```bash
carterkit tutorial                                  # the list: id, length, what you build
carterkit tutorial steps first-hub                  # read it: each step's code and what you should see
carterkit tutorial --start first-hub my-remote      # the kit as it stands before step 1
carterkit tutorial --check first-hub --step 3 --dir my-remote   # steps 1 to 3's checks
```

`--check` loads your `hub.py` and `layout.json`, validates the layout and runs each step's check against
`carterkit.testing.FakeHub`: the same hub on a recording socket, with no relay and no phone, that you can use
in your own tests (`FakeHub(ui).dispatch(frame)`, `.frames("msg_type")`, `async with fake.running(run)`).
`carterkit/scripts/sync_controldocs.py --dest carterkit/tutorials` refreshes the vendored files at the commit
pinned in `carterkit/tutorials/SOURCE`.

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

Credentials stay out of the JSON: `ui.secret(...)` declares a `{{secret:name}}` the
phone fills in from its Keychain at request time, only for a host the declaration
allows (the layout's source hosts by default; `hosts=[...]` replaces that, `mesh=True`
allows MeshSocket action payloads). `validate_layout` warns (`secret_host`,
`secret_mesh`, `secret_in_url`, `secret_not_filled`) when a request would be refused.

```python
token = ui.secret("ha_token", label="Home Assistant token", kind="token")
ui.source_http("ha", "https://ha.local:8123", headers={"Authorization": f"Bearer {token}"})
```

`bind.mqtt` / `bind.mqtt_publish` / `bind.http` / `bind.http_request` / `bind.sensor` build
the sync/action dicts; the validator checks a `source:` names a declared source and that
mqtt/http bindings carry a topic/path. These are marked **app-direct** in the contract, so a
generated `bridge.py` never tries to serve them.

The phone can also own the data outright: a **local store** (`local-store.md`) is typed
collections that live in the app and survive the layout, queried with plain JSON stages —
no server, no SQL:

```python
ui.source_local("db", {"books": {"title": "string", "pages": "integer", "finished": "date"}},
                namespace="reading-log",
                views={"thisYear": {"from": "books", "where": {"finished": {"gte": "{{startOfYear}}"}}}})
with ui.tab("Shelf", icon="books.vertical"):
    ui.label("n", label="Books", sync=[bind.local("books", aggregate="count")])
    ui.chart("m", label="Per month",
             sync=[bind.local("thisYear", group_by={"field": "finished", "bucket": "month"})])
    ui.button("add", label="Add", action=bind.local_op("insert", "books",
              set={"title": "{{value}}", "finished": "{{today}}"}))
```

`bind.local` / `bind.local_op` build the sync/action; the validator checks every stage
against the declared fields (unknown field, bad operator or op, `limit` outside 1…1000,
reserved `set` keys, view cycles, the `shared` namespace) so the phone never sees a stage
it would refuse.

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

**Ack'd commands.** With `ui.state(acks=True)` the app stamps each command with a
`_cmd` id and waits ~2 s for `command_ack`; a `Hub` serving that layout acks
automatically (`CarterClient.enable_command_acks()` by hand). Return `True` from a handler
that handled the frame; anything else stays silent so the control reverts. Every hub
also dedupes `_cmd` ids — a re-delivered or replayed command never runs twice and gets
the first ack again. The seen-set is saved beside the device.json credential (or
`cmd_dedupe_path=`), so it survives a restart; token-only hubs keep it in memory.

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
`codegen.generate_hub(layout)` writes the hub script for a layout (see [Generate the hub
side of any layout](#generate-the-hub-side-of-any-layout));
`theming.theme_for(...)` and `tune.tune_gauge(...)` round out the authoring tools.

## Drive the layout you just built

The layout already declares every control's wire contract, so the same object that
authored the UI also drives it — `ctrl.push(value)` derives the broadcast from the
control's `sync` binding, and `@ctrl.on` derives the demux from its `action`:

```python
import asyncio
import random
from carterkit import Layout

with Layout("Thermostat") as ui:
    with ui.tab("Main"):
        temp   = ui.gauge("temp", label="Temp", min=0, max=40,
                          listen="temp", when={"msg_type": "climate"})
        target = ui.slider("target", min=10, max=30, send="set_target")

setpoint = 20.0
reading = 18.0

async def main():
    global setpoint, reading
    # host="0.0.0.0": the phone on your LAN must be able to reach the QR address
    async with ui.serve(host="0.0.0.0") as hub:   # embedded LocalRelay
        print("pair the app with:", hub.qr_json())
        await hub.wait_for_device()
        await hub.push_layout()          # routed apply-layout; echoes what rendered

        @target.on
        async def _(data):
            global setpoint
            setpoint = data["value"]     # your heater control goes here

        while True:
            reading += (setpoint - reading) * 0.1 + random.uniform(-0.2, 0.2)
            await temp.push(round(reading, 1))
            await asyncio.sleep(2)

asyncio.run(main())
```

The same surface works cross-process off the saved JSON — the layout file is the
contract: `Hub("dashboard.json").push("temp", 21.5)`. Dynamic groups fill with
`hub.fill(group, fragment)`; the hub answers late joiners with the last pushed values
(control-state authority) by default.

### Progress, toasts, haptics and a live log

`hub.progress(...)` shows a task in the app (pill, sheet, Dynamic Island) with an optional Cancel
that sets `task.cancelled`; `hub.toast(...)`, `hub.haptic(...)` and `hub.log(...)` draw the rest.
Updates coalesce to 4 frames/s and a running task is resent when the hub reconnects;
`ambient.task(...)` plus `content_state(tasks=)` feeds the Island while the app sleeps. See
[docs/hub-surfaces.md](docs/hub-surfaces.md).

```python
async with hub.progress("Installing Example package", total=48, unit="items", cancellable=True) as task:
    await task.update(done=12, detail="Downloading")
await hub.toast("Example package installed", style="success", haptic="success")
```

### Ask the user to confirm, and page long lists

`hub.confirm()` shows the app's own confirm frame (it names this hub) and returns
`'confirm'`, `'cancel'`, `'timeout'` or `'busy'`. `hub.confirm_sync()` is the blocking form
for code on another thread than the hub's loop.

```python
choice = await hub.confirm("Remove the package?", "You can add it again later.",
                           confirm_label="Remove", destructive=True, timeout_s=60)
if choice == "confirm":
    remove_package()
```

A list with `paging` asks for rows a page at a time. `@hub.pages` answers it: the handler
gets `(offset, limit, cursor, query)` and returns the items, or `(items, next_cursor, total)`.
The reply is broadcast as the list's `replyType` with `req` and `query` echoed.

```python
@hub.pages("my-list")            # the list's id, or its paging.replyType
async def _(offset, limit, cursor, query):
    rows = search(query)         # your data source
    return rows[offset:offset + limit], None, len(rows)
```

`hub.open_sheet()` opens a group in the app's foreground container (full screen or a
sheet; app doc `HUB-SHEET.md`) and returns the sheet id; `hub.close_sheet(id)` closes it.
Open a group of the layout (laid out by its `expand` block) or one of your own, and listen
for the close:

```python
from carterkit import Layout, expand_block, bind

with Layout("Packages") as ui:
    with ui.tab("Main"):
        ui.button("more", label="More", action=bind.expand("pkg"))
        with ui.group("Example package", id="pkg", cols=4, rows=1,
                      expand=expand_block(trigger=["tap", "more"], style="sheet",
                                          grid={"columns": 4, "rows": 3},
                                          children=[bind.place("name", [0, 0], [1, 4]),
                                                    {"type": "label", "position": [1, 0],
                                                     "span": [2, 4], "text": "Only when expanded"}])) as g:
            g.label("name", position=[0, 0], span=[1, 4])
hub = ui.serve()

@hub.on("sheet_closed")
def closed(data):                      # {"id": ..., "reason": "user"|"hub"|"replaced"|"busy"}
    print(data["id"], data["reason"])

# inside an async handler:
sid = await hub.open_sheet(group_id="pkg", title="Example package", style="sheet")
sid = await hub.open_sheet(group={"grid": {"columns": 4, "rows": 1},
                                  "children": [{"type": "label", "position": [0, 0],
                                                "span": [1, 4], "text": "Hello"}]})
await hub.close_sheet(sid)
```

`bind.expand(id)`, `bind.collapse(id)` and `bind.toggle_expand(id)` are the matching action
kinds (a control inside a list row names the list's id). A refused sheet (`not-hub`,
`invalid`, `not-found`, `busy`) raises `HubError`; sending `open_sheet(..., id=sid)` again
replaces an open sheet in place.

## Explore the controls (zero config)

```python
import carterkit

carterkit.controls()            # {type: schema} for every placeable control
carterkit.doc("gauge")          # full parsed doc: fields, themeFields, examples
print(carterkit.doc_markdown("gauge"))   # the rendered documentation prose
carterkit.examples("button")    # documented example snippets
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
back as `suppressed`, with the state merged either way). If the phone never opened
CAR-TER no token is registered: the reply then carries `no_tokens: True` (and one
warning is logged per layout).

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


## One connection story

`Connection.parse(...)` accepts every connection artifact in the ecosystem, and
`ui.connect(...)` / `ui.serve(...)` / `Hub(...)` all take it:

| You have | Pass | Works |
|---|---|---|
| nothing (LAN dev) | `ui.serve()` | embedded `LocalRelay`, QR pairing |
| a self-hosted relay | `"ws://192.168.1.50:8765"` (+ `token=`) | symmetric: same config for app & hub |
| Connect+ | the **Add Hub** JSON from the app (Hubs -> Add Hub) | token self-refresh + room E2EE automatic |

The asymmetry to know: self-hosted is symmetric (one URL + shared key both sides);
on Connect+ the app joins with its own account while the hub holds the per-device
credential — which is the hub's identity, so it is never embedded into a layout.

`CarterClient` remains the lower-level client (`on`/`broadcast`/`request`).
End-to-end encryption (ChaCha20-Poly1305 + per-session salt) is applied to every frame
the client sends when an `e2ee_key` is present, and every sealed frame it receives is
opened, replay-checked and freshness-checked (±120 s) before a handler sees it. Keys
must be exactly 32 bytes (base64). A *plaintext* frame arriving in an E2EE session is
dropped and counted (`client.dropped["plaintext"]`); relay control frames are always
plaintext and always pass. `CarterClient(strict_e2ee=False)` passes plaintext through
with a one-time warning per `msg_type` — a debugging aid for a peer that is not sealing
yet, not a supported mode. What E2EE does **not** do: room mode is one symmetric key
per room, so it does not tell members apart — any member can send as any other.

Send a push to every device on a Connect+ account with `CarterClient.notify(...)` or
the stdlib-only `carterkit.notify_http(...)`.

### Security defaults

- The embedded `LocalRelay` (and `Hub()` / `ui.serve()` with no connection) gets a
  random shared key and binds `127.0.0.1`; the pairing QR then honestly says
  `ws://127.0.0.1:…`, which only this machine can reach. Pass `host="0.0.0.0"` (or
  `carterkit explore --lan` / `carterkit relay --lan`) for a phone on the LAN — the QR
  then carries the LAN address and the key. A keyless relay needs `insecure=True`.
- `Hub(strict_e2ee=, max_inflight=, rate_per_type=)` pass through to its `CarterClient`.
- A device credential's `validator` must be `https`. Plain `http` is accepted only for
  `127.0.0.1`/`localhost` with `allow_insecure_validator=True`.
- `carterkit explore` serves loopback only, refuses foreign `Host`/`Origin`, requires a
  per-run token on every write, and redacts `connection.token`, `e2eeKey` and source
  passwords/auth headers from `/api/layout` and `/api/status`. The QR on the page still
  encodes the full pairing payload — that is what the phone scans.
- `validate_layout` never raises on hostile input and flags `non_finite`, `too_deep`,
  `too_many_controls`, `bad_url`, `embedded_secret` and `long_string`.
- `Layout.save` writes `0600` (a layout may carry a relay or room key).
- A device credential loaded from a `device.json` path is rewritten (atomically, `0600`)
  when the validator rotates its refresh secret; load credentials by path, not inline,
  so a rotation survives a restart.
- Inbound frames are dispatched under a semaphore (32) and a per-`msg_type` token
  bucket (20/s, burst 40); excess frames are dropped and counted in `client.dropped`.

## CLI

```bash
carterkit new demo                # scaffold a starter project (hello.py, secrets/, VS Code settings)
carterkit new demo -t remote      # scaffold a starter kit (layout.json + hub.py; --list names them)
carterkit repl hello.py           # live prompt with the hub connected, controls bound by id
carterkit catalog                 # list every control type
carterkit doc gauge               # print a control's documentation
carterkit examples button         # list a control's examples (--name to print one)
carterkit tutorial [steps ID | --start ID DIR | --check ID --step N]   # tutorials with checks
carterkit validate layout.json    # lint a layout (exit 1 on errors)
carterkit codegen layout.json -o hub.py  # write the hub script for a layout (`gen` too)
carterkit explore layout.json     # live, typed endpoint explorer (--device, --lan, --port)
carterkit share layout.json       # serve a layout for 10 minutes + QR to import it
carterkit local describe ws://HOST:PORT   # read/seed the paired phone's local store (describe|query|seed)
carterkit relay --port 8765       # run the bundled MeshSocket relay (keyed, loopback)
carterkit relay --lan --key s3cret  # let phones on the LAN join with that shared key
carterkit pager install|uninstall|run   # approve Claude Code tool calls from the phone
carterkit version                 # print the installed version
carterkit --version               # same, as "carterkit <version>"
```

`carterkit relay` generates and prints a shared key when you don't pass `--key`, and
binds `127.0.0.1` unless you pass `--lan`. Running it open (no key) requires
`--insecure` and means anyone who can reach the port joins every channel.

## Agent pager

`carterkit pager` pages your phone to approve Claude Code tool calls (fails closed).
Setup, the Agents layout and metrics: [docs/pager.md](docs/pager.md).

## Built on

[`meshsocket`](https://pypi.org/project/meshsocket/) — the WebSocket mesh transport.

The ControlDocs are vendored from the CAR-TER app repo; refresh them with
`scripts/sync-controldocs.sh`.
