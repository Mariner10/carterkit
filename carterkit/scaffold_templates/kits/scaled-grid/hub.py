"""Scaled grid: 1 x 5 cards that draw a 3 x 15 grid at 1/3, and a sheet the hub opens.

Run:  python hub.py   then scan the QR it prints with the CAR-TER app.
Edit hub.py or layout.json while it runs: every save reaches the phone.

Each row of the page is a group spanning 1 row x 5 columns whose own grid is 3 rows x 15
columns with "scale": "auto": the smaller of 1/3 and 5/15, so every 1 x 3 control inside
looks like a 1 x 1 control at a third of the size. Holding a row expands it (its
`expand` block) onto a 3 x 5 grid at full size: the same controls, moved, not copied.
Open on a card asks the hub, which opens a sheet of its own with hub.open_sheet().
"""
from pathlib import Path

from carterkit import HubError, Layout

ui = Layout.load(Path(__file__).with_name("layout.json"))

power: dict[str, bool] = {}          # card -> on/off, as the toggles last said


def truthy(value) -> bool:
    return value in (True, 1, "1", "true", "on")


def sheet_for(card: str) -> dict:
    """The hub's own group for a card's sheet: a grid and children, like a group."""
    state = "On" if power.get(card) else "Off"
    return {"grid": {"columns": 4, "rows": 3}, "children": [
        {"type": "label", "id": "sheet-card", "position": [0, 0], "span": [1, 4],
         "label": "Card", "text": card.upper()},
        {"type": "label", "id": "sheet-state", "position": [1, 0], "span": [1, 4],
         "label": "Power", "text": state},
        {"type": "button", "id": "sheet-done", "position": [2, 0], "span": [1, 4],
         "label": "Done", "action": {"method": "meshsocket", "event": "broadcast_request",
                                     "payload": {"msg_type": "sheet_done", "sheet": f"card-{card}"}}},
    ]}


async def run(hub):
    """Handlers; restarted on every save."""

    @hub.on("slot_power")
    async def slot_power(frame):
        card = str(frame.get("slot"))
        power[card] = truthy(frame.get("value"))
        await hub.push("status", f"{card.upper()} is {'on' if power[card] else 'off'}")

    @hub.on("slot_open")
    async def slot_open(frame):
        card = str(frame.get("slot"))
        try:            # the same id again replaces an open sheet in place
            await hub.open_sheet(group=sheet_for(card), title=f"Card {card.upper()}",
                                 style="sheet", id=f"card-{card}")
        except HubError as e:
            await hub.push("status", f"No sheet: {e}")
            return
        await hub.push("status", f"Opened card {card.upper()}")

    @hub.on("sheet_done")
    async def sheet_done(frame):
        try:
            await hub.close_sheet(str(frame.get("sheet")))
        except HubError:
            pass                         # already closed

    @hub.on("sheet_closed")
    async def sheet_closed(frame):       # {"id", "reason": "user"|"hub"|"replaced"|"busy"}
        await hub.push("status", f"Closed {frame.get('id')} ({frame.get('reason')})")


if __name__ == "__main__":
    from carterkit import livefile
    raise SystemExit(livefile.main(__file__))
