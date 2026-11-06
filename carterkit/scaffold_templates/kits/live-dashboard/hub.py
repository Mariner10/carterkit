"""Live dashboard: a gauge, a sparkline and a readout fed live by the hub.

Run:  python hub.py   then scan the QR it prints with the CAR-TER app.
Edit hub.py or layout.json while it runs: every save reaches the phone.

Every INTERVAL seconds the hub sends one `metrics` broadcast. The gauge and the
sparkline both listen for it (same filter, same valuePath), so one push moves the
needle and adds a point to the trend. The readout listens for its own `readout` frame.
"""
# tutorial: load
import asyncio
import random
from pathlib import Path

from carterkit import Layout

ui = Layout.load(Path(__file__).with_name("layout.json"))
# end: load

# tutorial: sensor
INTERVAL = 1.0          # seconds between readings
state = {"level": 50.0}


def read_level() -> float:
    """Placeholder sensor: a random walk between 0 and 100. Read your real value here."""
    state["level"] = min(100.0, max(0.0, state["level"] + random.uniform(-6, 6)))
    return round(state["level"], 1)
# end: sensor


# tutorial: publish
async def publish(hub, level: float, previous: float | None = None) -> None:
    await hub.push("level", level)          # the gauge, and the sparkline on the same frame
    trend = "" if previous is None else (" rising" if level > previous else " falling")
    await hub.push("readout", f"{level:.1f} %{trend}")
# end: publish


# tutorial: reset
async def reset(hub, frame) -> None:
    state["level"] = 50.0
    await publish(hub, 50.0)
# end: reset


# tutorial: loop
async def run(hub):
    """Handlers and the live loop; restarted on every save."""
    hub.on("reset", lambda frame: reset(hub, frame))

    previous = None
    while True:
        level = read_level()
        await publish(hub, level, previous)
        previous = level
        await asyncio.sleep(INTERVAL)
# end: loop


if __name__ == "__main__":
    from carterkit import livefile
    raise SystemExit(livefile.main(__file__))
