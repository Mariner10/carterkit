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
        ui.button("refresh", label="Refresh", send="refresh", request=True)

print(ui.findings())        # schema + grid + binding lint against the bundled catalog
ui.save("dashboard.json")   # the composed layout, ready to push/load
```

Binding sugar: `listen=`/`when=`/`event=` build a `sync`, and `send=`/`request=`/`payload=`
build an `action`; pass `sync=[...]`/`action={...}` (via `carterkit.bind`) for anything
fancier. A handle comparison (`cpu > 90`) becomes a real visibility condition; `==`/`!=`
stay normal Python, so use `.eq()`/`.neq()`. `help(carterkit.build.gauge)` prints any
control's documentation, straight from the bundled docs.

> **Naming:** multi-word controls are **`snake_case` as `Layout` methods**
> (`ui.status_light(...)`, `ui.log_console(...)`, `ui.progress_ring(...)`) but
> **`camelCase` as the JSON `type`** and as `carterkit.build.*` functions
> (`"statusLight"`, `build.logConsole`). Single-word controls (`gauge`, `button`) look
> the same either way. Grid size (`cols`/`rows`) set on `Layout(...)` is the default for
> every tab; override it per tab with `ui.tab("Name", rows=…)`.

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
        refresh = Button(label="Refresh", send="refresh", request=True)

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
`codegen.generate_service_stub(layout)` emits a runnable MeshSocket server skeleton;
`theming.theme_for(...)` and `tune.tune_gauge(...)` round out the authoring tools.

## CLI

```bash
carterkit catalog                 # list every control type
carterkit doc gauge               # print a control's documentation
carterkit examples button         # list a control's examples (--name to print one)
carterkit validate layout.json    # lint a layout (exit 1 on errors)
carterkit gen layout.json         # generate a MeshSocket service stub
carterkit relay --port 8765       # run the bundled MeshSocket relay
```

## Drive a device

```python
import asyncio
from carterkit import CarterClient

async def main():
    async with CarterClient(gateway_url="ws://localhost:18080", token="<mesh token>",
                            channel="home", role="device", name="my-hub") as c:
        c.on("toggle", lambda d: {"ok": True, **d})
        await c.broadcast("reading", {"temp_c": 21.4})
        await asyncio.sleep(60)
    # leaving the `async with` disconnects automatically

asyncio.run(main())
```

End-to-end encryption (ChaCha20-Poly1305 + per-session salt) is transparent when you
pass an `e2ee_key`. Send a push to every device on a Connect+ account with
`CarterClient.notify(...)` or the stdlib-only `carterkit.notify_http(...)`.

## Built on

[`meshsocket`](https://pypi.org/project/meshsocket/) — the WebSocket mesh transport.

The ControlDocs are vendored from the CAR-TER app repo; refresh them with
`scripts/sync-controldocs.sh`.
