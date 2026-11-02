"""__NAME__: a CAR-TER layout with one gauge and one button.

Run:  python hello.py
First time: on the phone open Hubs -> Add Hub, save the credential as secrets/hub.json.
"""
import asyncio
import os
import random
import sys

from carterkit import Connection, Layout

CREDENTIAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secrets", "hub.json")

with Layout("__NAME__", id="__ID__", cols=4, rows=3) as ui:
    gauge = ui.gauge("level", label="Level", min=0, max=100, listen="level")
    button = ui.button("reset", label="Reset", send="reset")


async def main():
    if not os.path.isfile(CREDENTIAL):
        print("No hub credential yet. On the phone open Hubs -> Add Hub, "
              f"then save the credential as {CREDENTIAL}")
        return 1
    hub = ui.serve(Connection.parse(CREDENTIAL))

    @button.on
    async def reset(frame):
        await gauge.push(0)
        return {"ok": True}

    async with hub:
        print("Connected. Pushing a value every 2 s; Ctrl-C stops.")
        while True:
            await gauge.push(random.randint(0, 100))
            await asyncio.sleep(2)


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        pass
