# __NAME__: paged cards

**What it shows.** A search field over a list of cards. The list asks the hub for 20 rows
at a time as it scrolls (`paging` in `layout.json`), and `@hub.pages("cards")` in `hub.py`
answers from placeholder rows. Typing searches on the hub: the list starts over with the
text as `query`. Each card is drawn from the list's `itemTemplate` (an icon, a name with a
detail line, a Star button); tapping a card grows it into a detail page (the template's
`expand`: the same icon and name, bigger, plus notes only the page shows) and sends its id
to the hub, which answers on the status line.

**Run it.**

```bash
python hub.py              # prints a QR: in CAR-TER open the layout list, tap Scan
carterkit validate layout.json
```

The pairing is kept in `.carterkit/session.json`, so the next run reconnects without a
scan. Every save of `hub.py` or `layout.json` is pushed to the phone. Have a Connect+ hub
credential? Save it as `secrets/hub.json` to use the managed relay instead of your LAN.

**Change first.**

1. `ITEMS` in `hub.py`: your own rows. Each needs an `id`; the template reads the other
   fields as `{{item.<field>}}`.
2. `search()`: match the way your data wants (a database `LIKE`, an API call). Return
   `(rows, None, total)` from the page handler so the list knows where it ends.
3. The card: `itemTemplate.children` in `layout.json`; the detail page: its `expand`
   (`ref` moves a card control to a new cell, entries with a `type` exist only on the page).
