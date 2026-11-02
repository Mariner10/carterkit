"""30-second film script: Python drives the Dynamic Island on a real phone.

Run: python3 examples/island_demo.py     (needs a real iPhone: the simulator gets no Live Activity pushes)

Timeline (seconds from the first keypress of the recording):
  0-3    layout pushed, terminal prints the plan
  3      Live Activity starts, Island appears
  6-26   six value updates, one every 4 s, each a visible jump
  ~15    tap the "Ping" button on the phone; the terminal prints it
  30     Live Activity ends
"""
import asyncio
import sys
import time

from carterkit import Layout, island, scene, tile
from _common import main

STEP = 4.0                         # seconds between updates
VALUES = (15, 40, 25, 70, 55, 90)  # six updates with obvious motion up and down

with Layout("Island demo", id="island-demo", cols=4, rows=2) as ui:
    level = ui.gauge("level", label="Level", min=0, max=100, listen="level")
    ping = ui.button("ping", label="Ping", send="ping")
    ui.glance(hero=level, live_activity=True, island=island(
        compact_leading=tile("gauge", level), minimal=tile("gauge", level),
        expanded={"bottom": scene([tile("gauge", level)])}))


async def run(hub):
    t0 = time.monotonic()

    def say(text):
        print(f"[{time.monotonic() - t0:4.1f}s] {text}", flush=True)

    @ping.on
    async def pinged(frame):
        say("button tapped on the phone")      # the on-camera moment
        return {"ok": True}

    async with hub:
        await hub.push_layout()                # t=0
        await level.push(0)
        say("layout pushed")
        await asyncio.sleep(3)                 # t=3
        await hub.surfaces.start_activity(alert_title="Island demo")
        say("Live Activity started")
        await asyncio.sleep(3)                 # t=6
        for i, v in enumerate(VALUES, 1):
            await level.push(v)
            await hub.surfaces.update_activity()
            say(f"update {i}/6: level = {v}")
            await asyncio.sleep(STEP)          # last sleep lands at t=30
        await hub.surfaces.end_activity()
        say("Live Activity ended")


if __name__ == "__main__":
    sys.exit(main(run, ui))
