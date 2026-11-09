---
id: live-dashboard
kind: tutorial
level: beginner
audience: code
title: A live dashboard
time: 20
builds: A gauge, a sparkline and a text readout that the hub moves once a second, with a button that sends a command back.
prerequisites: [first-hub]
since: "2.2"
kit: ">=0.20"
uses:
  controls: [control.gauge, control.sparkline, control.label, control.button]
  fields: []
  docs: [doc.sync]
  carterkit: [kit.layout.load, kit.hub.on, kit.hub.push]
starterKit: live-dashboard
next: []
steps:
  - id: layout
    goal: Lay out the dashboard
    do:
      code: load
    check: "`carterkit validate layout.json` prints no errors, and `python hub.py` starts and prints a QR code."
  - id: sensor
    goal: Read a value
    do:
      code: sensor
    check: "`read_level()` returns a number from 0 to 100 that drifts a little each time you call it."
    expect: {calls: [{fn: read_level, between: [0, 100]}]}
  - id: publish
    goal: Publish a reading
    do:
      code: publish
    check: "`publish(hub, 42.0, 40.0)` broadcasts a metrics frame with level 42.0 and a readout frame saying 42.0 % rising."
    expect: {calls: [{fn: publish, args: ["@hub", 42.0, 40.0]}], sent: [{msg_type: metrics, level: 42.0}, {msg_type: readout, text: "42.0 % rising"}]}
  - id: reset
    goal: Answer the button
    do:
      code: reset
    check: "`reset(hub, {})` puts the level back to 50 and publishes it at once."
    expect: {calls: [{fn: reset, args: ["@hub", {}]}], sent: [{msg_type: metrics, level: 50.0}, {msg_type: readout, text: "50.0 %"}]}
  - id: loop
    goal: Keep it moving
    do:
      code: loop
    check: "With INTERVAL shortened, the hub broadcasts at least three readings by itself, and a Reset from the phone sends 50 straight away."
    expect: {set: {INTERVAL: 0.005}, when: [{msg_type: reset}], wait: 0.05, at_least: {metrics: 3, readout: 3}, sent: [{msg_type: metrics, level: 50.0}]}
  - id: run
    goal: Watch it on a phone
    do:
      code: launch
    check: "The needle and the trend line move every second, the readout says rising or falling, and Reset to 50 swings the needle back."
---

# A live dashboard

A dashboard is the other half of [[tutorial:first-hub]]: there the phone asked and the hub answered; here the hub
speaks first. Once a second it reads a value and broadcasts it, and every phone on the channel updates from the
same frame with no work per viewer.

By the end you have the **live-dashboard** starter kit: `carterkit new my-dashboard --template live-dashboard`
scaffolds the same finished project. Start from the skeleton with
`carterkit tutorial --start live-dashboard my-dashboard` and check each step with
`carterkit tutorial --check live-dashboard --step N`.

## Lay out the dashboard {#layout}

Every display control listens for a broadcast frame, picked out by its `msg_type`, and pulls its number out of
the frame with `valuePath` ([[doc.sync]]). A [[control.gauge]] and a [[control.sparkline]] here listen for the
**same** `metrics` frame, so one broadcast moves the needle and adds a point to the trend (the sparkline keeps the
last 60). The [[control.label]] listens for its own `readout` frame, and the [[control.button]] only sends.

```json layout layout
{
  "name": "Live dashboard",
  "id": "my-dashboard",
  "version": 1,
  "accentColor": "#667eea",
  "tabs": [
    {
      "id": "live-tab",
      "title": "Live",
      "icon": "gauge",
      "grid": { "columns": 4, "rows": 6 },
      "children": [
        { "type": "gauge", "id": "level", "position": [0, 0], "span": [2, 2],
          "label": "Level", "min": 0, "max": 100, "unit": "%",
          "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast",
                     "valuePath": "level", "filter": { "msg_type": "metrics" } }] },
        { "type": "sparkline", "id": "trend", "position": [0, 2], "span": [2, 2],
          "label": "Last minute", "sparklinePoints": 60, "sparklineFill": true,
          "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast",
                     "valuePath": "level", "filter": { "msg_type": "metrics" } }] },
        { "type": "label", "id": "readout", "position": [2, 0], "span": [1, 4],
          "label": "Reading", "text": "Waiting for the hub",
          "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast",
                     "valuePath": "text", "filter": { "msg_type": "readout" } }] },
        { "type": "button", "id": "reset", "position": [3, 0], "span": [1, 4],
          "label": "Reset to 50", "icon": "arrow.counterclockwise",
          "action": { "method": "meshsocket", "event": "broadcast_request",
                      "payload": { "msg_type": "reset" } } }
      ]
    }
  ]
}
```

Then the top of `hub.py`; [[kit.layout.load]] reads that file for the hub to serve.

```python run load
import asyncio
import random
from pathlib import Path

from carterkit import Layout

ui = Layout.load(Path(__file__).with_name("layout.json"))
```

## Read a value {#sensor}

`read_level` is a placeholder sensor, a random walk between 0 and 100. This is the line you replace with a real
reading: a sensor, a CPU load, an API. Send native numbers, `73` and never `"73"`; gauges and sparklines want
numbers ([[data-flow]]).

```python run sensor
INTERVAL = 1.0          # seconds between readings
state = {"level": 50.0}


def read_level() -> float:
    """Placeholder sensor: a random walk between 0 and 100. Read your real value here."""
    state["level"] = min(100.0, max(0.0, state["level"] + random.uniform(-6, 6)))
    return round(state["level"], 1)
```

## Publish a reading {#publish}

[[kit.hub.push]] takes a control and a value and sends the frame that control listens for. Pushing `level` moves
the gauge and the sparkline together, because both listen for it; the readout is a second push. A rate of about
one per second is smooth; the phone coalesces UI updates.

```python run publish
async def publish(hub, level: float, previous: float | None = None) -> None:
    await hub.push("level", level)          # the gauge, and the sparkline on the same frame
    trend = "" if previous is None else (" rising" if level > previous else " falling")
    await hub.push("readout", f"{level:.1f} %{trend}")
```

## Answer the button {#reset}

The dashboard is mostly one-way, but the button shows the way back: it sends `reset`, the hub sets its value and
publishes it at once, and the phone sees the answer in the same place it sees every reading.

```python run reset
async def reset(hub, frame) -> None:
    state["level"] = 50.0
    await publish(hub, 50.0)
```

## Keep it moving {#loop}

`run` restarts on every save. [[kit.hub.on]] attaches `reset` to the button, then the loop reads, publishes and
sleeps for ever. The hub is the state authority, so a phone that joins late is brought up to date by the next
reading, within a second.

```python run loop
async def run(hub):
    """Handlers and the live loop; restarted on every save."""
    hub.on("reset", lambda frame: reset(hub, frame))

    previous = None
    while True:
        level = read_level()
        await publish(hub, level, previous)
        previous = level
        await asyncio.sleep(INTERVAL)
```

## Watch it on a phone {#run}

```bash launch
python hub.py
```

In CAR-TER open the layout list and tap **Scan**. The pairing is kept in `.carterkit/session.json`, so the next
run reconnects without a scan, and every save reaches the phone while it runs.

> Things to get right: `statusLight` controls map strings such as `green` and `red`; a `logConsole` takes a bare
> string, `{text, level}` or a list of either.
