"""__NAME__: a CAR-TER layout with one gauge and one button, live.

Run:  python hello.py
Scan the QR it prints with the CAR-TER app (layout list -> Scan, or
Settings -> Studio Session -> Open Scanner). The layout lands on the phone, the
gauge starts moving, and every save of this file is pushed to the phone: change a
label, add a control, edit run() below.

`carterkit repl hello.py` does the same with a live prompt (`await gauge.push(7)`).
Have a Connect+ hub credential? Save it as secrets/hub.json to use the managed relay.
"""
import asyncio
import random

from carterkit import Layout

with Layout("__NAME__", id="__ID__", cols=4, rows=3) as ui:
    gauge = ui.gauge("level", label="Level", min=0, max=100, listen="level")
    button = ui.button("reset", label="Reset", send="reset")


async def run(hub):
    """Behaviour: handlers and loops. Restarted on every save."""
    @button.on
    async def reset(frame):
        await gauge.push(0)
        return {"ok": True}

    while True:
        await gauge.push(random.randint(0, 100))
        await asyncio.sleep(2)


if __name__ == "__main__":
    from carterkit import livefile
    raise SystemExit(livefile.main(__file__))
