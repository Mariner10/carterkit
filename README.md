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

Use **typed builders** (`build.<control>`) and **binding helpers** (`bind`) — both
generated from / shaped by the bundled docs, so unknown control types and bad enum
values raise instead of silently shipping a broken layout:

```python
import carterkit
from carterkit import LayoutBuffer, build, bind, validate_layout

b = LayoutBuffer.blank(name="Dashboard", columns=4, rows=4)
b.add_control(build.gauge(id="cpu", label="CPU", min=0, max=100,
                          sync=[bind.listen("cpu", filter={"msg_type": "metrics"})]),
              default_span=[2, 2])
b.add_control(build.button(id="refresh", label="Refresh",
                           action=bind.action("refresh")))

print(carterkit.format_findings(validate_layout(b.layout)))   # schema + grid lint
help(build.gauge)        # ← prints the gauge documentation, straight from the docs
```

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
    c = CarterClient(gateway_url="ws://localhost:18080", token="<mesh token>",
                     channel="home", role="device", name="my-hub")
    c.on("toggle", lambda d: {"ok": True, **d})
    await c.connect()
    await c.broadcast("reading", {"temp_c": 21.4})
    await asyncio.sleep(60)
    await c.close()

asyncio.run(main())
```

End-to-end encryption (ChaCha20-Poly1305 + per-session salt) is transparent when you
pass an `e2ee_key`. Send a push to every device on a Connect+ account with
`CarterClient.notify(...)` or the stdlib-only `carterkit.notify_http(...)`.

## Built on

[`meshsocket`](https://pypi.org/project/meshsocket/) — the WebSocket mesh transport.

The ControlDocs are vendored from the CAR-TER app repo; refresh them with
`scripts/sync-controldocs.sh`.
