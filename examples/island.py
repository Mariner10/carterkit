"""Drive the Dynamic Island / Live Activity from Python.  Run: python3 examples/island.py"""
import asyncio
import sys

from carterkit import Layout, island, scene, tile
from _common import main

with Layout("Island", id="island", cols=4, rows=2) as ui:
    temp = ui.gauge("temp", label="Temp", min=0, max=100, listen="temp",
                    formatValue="suffix:°C")
    ui.glance(hero=temp, live_activity=True, island=island(
        compact_leading=tile("gauge", temp), minimal=tile("gauge", temp),
        expanded={"bottom": scene([tile("gauge", temp)])}))


async def run(hub, pause=2.0):
    async with hub:
        await hub.push_layout()
        await temp.push(20)
        await hub.surfaces.start_activity(alert_title="Island demo")
        for t in (35, 60, 85):
            await temp.push(t)
            await hub.surfaces.update_activity()
            await asyncio.sleep(pause)
        await hub.surfaces.end_activity()


if __name__ == "__main__":
    sys.exit(main(run, ui))
