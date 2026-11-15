"""A 10-band equalizer: vertical sliders in a hub-fed side strip.  Run: python3 examples/eq_strip.py

Each band's value goes to the hub (`eq_band`, with the band number); the hub can move a band
back with `band(i).push(v)`. The phone may restyle or rearrange the strip and the hub keeps
that beside this script (`customize` with `save`)."""
import asyncio
import sys

from carterkit import Layout
from _common import main

BANDS = 10
FREQS = ["32", "64", "125", "250", "500", "1k", "2k", "4k", "8k", "16k"]
gains = [0.0] * BANDS

with Layout("EQ", id="eq", cols=4, rows=6) as ui:
    ui.customize("look", save=True)
    with ui.group("Equalizer", id="strip", span=(6, 4), cols=4, rows=6,
                  scroll="horizontal", snap="none", edge="fade") as strip:
        sliders = [
            ui.slider(f"band{i}", label=FREQS[i], position=(0, i), span=(6, 1),
                      orientation="vertical", track="hidden", min=-12, max=12, step=0.5,
                      defaultValue=0, send="eq_band", payload={"band": i}, listen=f"band{i}")
            for i in range(BANDS)
        ]


async def run(hub, forever=True):
    @hub.on("eq_band")
    async def moved(frame):
        gains[int(frame["band"])] = float(frame["value"])   # the hub holds the phone's value
        return {"ok": True}

    async with hub:
        await hub.push_layout()
        for i, s in enumerate(sliders):
            await s.push(gains[i])
        print("Drag a band on the phone; Ctrl-C stops.")
        while forever:
            await asyncio.sleep(1)


if __name__ == "__main__":
    sys.exit(main(run, ui))
