"""Paged cards: a card list the hub pages and searches; each card expands into a page.

Run:  python hub.py   then scan the QR it prints with the CAR-TER app.
Edit hub.py or layout.json while it runs: every save reaches the phone.

The list asks for 20 rows at a time as it scrolls (`paging` in layout.json) and
@hub.pages answers from ITEMS. Typing in the search field starts the list over with
the text as `query`; the matching happens here, on the hub. Tapping a card opens it
into a detail page (the template's `expand`) and sends the card's id to `card_open`.
"""
from pathlib import Path

from carterkit import Layout

ui = Layout.load(Path(__file__).with_name("layout.json"))

ICONS = ["shippingbox", "doc.text", "folder", "tag"]

#: Placeholder data: swap in your own rows (a database query, an API, files on disk).
#: Every row needs an "id"; the other fields are what the template reads as {{item.<field>}}.
ITEMS = [{"id": f"item-{n}", "name": f"Item {n}", "detail": f"Example detail {n}",
          "icon": ICONS[n % len(ICONS)],
          "notes": f"Placeholder notes for item {n}. Put the long description here."}
         for n in range(1, 201)]

starred: set[str] = set()


def search(query: str) -> list[dict]:
    """The rows matching `query` (case-insensitive, name or detail)."""
    q = query.strip().lower()
    return [r for r in ITEMS if q in r["name"].lower() or q in r["detail"].lower()]


def name_of(item_id) -> str:
    return next((r["name"] for r in ITEMS if r["id"] == item_id), str(item_id))


async def run(hub):
    """Handlers; restarted on every save."""

    @hub.pages("cards")
    def cards_page(offset, limit, cursor, query):
        rows = search(query)
        page = [dict(r, detail=("Starred - " if r["id"] in starred else "") + r["detail"])
                for r in rows[offset:offset + limit]]
        return page, None, len(rows)          # (items, next cursor, total)

    @hub.on("cards")
    async def card_open(frame):
        await hub.push("status", f"Opened {name_of(frame.get('id'))}")

    @hub.on("card_star")
    async def card_star(frame):
        item = frame.get("id")
        starred.symmetric_difference_update({item})
        state = "Starred" if item in starred else "Unstarred"
        await hub.push("status", f"{state} {name_of(item)}")


if __name__ == "__main__":
    from carterkit import livefile
    raise SystemExit(livefile.main(__file__))
