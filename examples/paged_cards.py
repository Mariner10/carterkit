"""Paged cards with a separate search box.  Run: python3 examples/paged_cards.py

A text input with role "search" filters the card list as you type; the hub answers each page
request (`cards_page`) with the matching rows."""
import asyncio
import sys

from carterkit import Layout
from _common import main

CATALOG = [{"title": f"Item {n:02d}", "subtitle": "Tap for details"} for n in range(1, 61)]
PAGE = 12

with Layout("Cards", id="cards", cols=4, rows=8) as ui:
    search = ui.text_input("find", position=(0, 0), span=(1, 4), placeholder="Search", role="search")
    ui.list("cards", position=(1, 0), span=(7, 4), layout="grid", search="find",
            paging={"request": "cards_page", "pageSize": PAGE, "queryFrom": "find",
                    "replyType": "cards_rows", "replyPath": "rows"},
            itemTemplate={"type": "group", "grid": {"columns": 2, "rows": 2}, "children": [
                {"type": "label", "id": "t", "position": [0, 0], "span": [1, 2], "text": "{{item.title}}"},
                {"type": "label", "id": "s", "position": [1, 0], "span": [1, 2], "text": "{{item.subtitle}}"}]})


def page(frame):
    q = (frame.get("query") or "").lower()
    rows = [r for r in CATALOG if q in r["title"].lower()]
    start = int(frame.get("offset") or frame.get("position") or 0)
    # echo req / query / offset: a paged list matches the reply on them
    return {"msg_type": "cards_rows", "rows": rows[start:start + PAGE], "total": len(rows),
            "offset": start, "query": frame.get("query"), "req": frame.get("req")}


async def run(hub, forever=True):
    @hub.on("cards_page")
    async def asked(frame):
        await hub.broadcast("cards_rows", page(frame))
        return {"ok": True}

    async with hub:
        await hub.push_layout()
        print("Search and scroll on the phone; Ctrl-C stops.")
        while forever:
            await asyncio.sleep(1)


if __name__ == "__main__":
    sys.exit(main(run, ui))
