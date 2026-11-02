"""A temporary tab: added while this runs, removed on exit.  Run: python3 examples/live_tab.py"""
import asyncio
import sys

from carterkit import Layout
from _common import main

with Layout("Lab", id="lab", cols=4, rows=2) as ui:
    with ui.tab("Home"):
        ui.label("hi", text="The Lab tab appears while the script runs")

TEMP = {"id": "lab_temp", "type": "gauge", "label": "Temp", "min": 0, "max": 40,
        "position": [0, 0], "span": [2, 2],
        "sync": [{"event": "broadcast", "filter": {"msg_type": "lab"}, "valuePath": "temp"}]}


async def run(hub, seconds=10):
    async with hub:
        await hub.push_layout()
        async with hub.live_tab("lab", "Lab") as tab:
            await tab.add(TEMP)
            for t in (18, 21, 24):
                await tab.push("lab_temp", t)
                await asyncio.sleep(seconds / 3)
        print("Tab removed.")


if __name__ == "__main__":
    sys.exit(main(run, ui))
