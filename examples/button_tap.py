"""Handle a button tap: each press adds one to a counter.  Run: python3 examples/button_tap.py"""
import asyncio
import sys

from carterkit import Layout
from _common import main

with Layout("Tap", id="tap", cols=4, rows=2) as ui:
    count = ui.gauge("count", label="Taps", min=0, max=100, listen="count")
    button = ui.button("tap", label="Tap me", send="tap")
taps = 0


async def run(hub, forever=True):
    @button.on
    async def tapped(frame):
        global taps
        taps += 1
        await count.push(taps)
        return {"ok": True}

    async with hub:
        await hub.push_layout()
        await count.push(0)
        print("Tap the button on the phone; Ctrl-C stops.")
        while forever:
            await asyncio.sleep(1)


if __name__ == "__main__":
    sys.exit(main(run, ui))
