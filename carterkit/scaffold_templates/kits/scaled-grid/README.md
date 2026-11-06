# __NAME__: scaled card grid

**What it shows.** Three rows, each one group spanning 1 row x 5 columns of the page. Each
group's own grid is 3 rows x 15 columns with `"scale": "auto"`, which draws it at the
smaller of span rows / grid rows (1/3) and span columns / grid columns (5/15): five tiny
cards per row (a name, an On toggle, an Open button), each control a 1 x 1 at a third of
the size. Taps stay full size. Hold a row and it expands (its `expand` block) onto a
3 x 5 grid at full size; the same controls move there, they are not copies. Open on a
card asks the hub, which opens a sheet of its own with `hub.open_sheet(group=...)`; its
Done button asks the hub to close it with `hub.close_sheet(id)`, and the app reports every
close as `sheet_closed`.

**Run it.**

```bash
python hub.py              # prints a QR: in CAR-TER open the layout list, tap Scan
carterkit validate layout.json
```

The pairing is kept in `.carterkit/session.json`, so the next run reconnects without a
scan. Every save of `hub.py` or `layout.json` is pushed to the phone. Have a Connect+ hub
credential? Save it as `secrets/hub.json` to use the managed relay instead of your LAN.

**Change first.**

1. The scale: a group's `grid.scale` takes `"auto"` or a number from 0.3 to 1.5. Try a
   1 x 5 group with a 2 x 10 grid (`auto` = 1/2).
2. The expanded layout: each `{"ref": ..., "position": ...}` in a row's `expand.children`
   moves one control while it is open. In Python the same block is
   `carterkit.expand_block(trigger="hold", style="sheet", grid=..., children=[bind.place("a1-name", [0, 0]), ...])`
   passed to `ui.group(..., expand=...)`.
3. `sheet_for()` in `hub.py`: what the hub's sheet shows for a card.
