"""Push one value into a gauge on your phone.  Run: python3 examples/push_value.py"""
import sys

from carterkit import Layout
from _common import main

with Layout("Push", id="push", cols=4, rows=2) as ui:
    level = ui.gauge("level", label="Level", min=0, max=100, listen="level")


async def run(hub):
    async with hub:
        await hub.push_layout()          # puts the gauge on the phone
        await level.push(42)             # the gauge moves to 42
        print("Pushed 42 to the gauge.")


if __name__ == "__main__":
    sys.exit(main(run, ui))
