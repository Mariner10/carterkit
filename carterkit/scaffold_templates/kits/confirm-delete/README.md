# __NAME__: confirm before delete

**What it shows.** A list of placeholder rows, each with a Delete button, plus Delete all
and Restore. Delete never removes anything by itself: the button sends a command, and the
hub asks first with `hub.confirm(...)`, which shows the app's own confirm frame (it names
this hub, with a red Delete because `destructive=True`). Only `'confirm'` deletes; `'cancel'`,
`'timeout'` and `'busy'` keep the row and say so on the status line. The hub keeps the
rows and sends them back after every change, so the phone always shows the hub's truth.

**Run it.**

```bash
python hub.py              # prints a QR: in CAR-TER open the layout list, tap Scan
carterkit validate layout.json
```

The pairing is kept in `.carterkit/session.json`, so the next run reconnects without a
scan. Every save of `hub.py` or `layout.json` is pushed to the phone. Have a Connect+ hub
credential? Save it as `secrets/hub.json` to use the managed relay instead of your LAN.

**Change first.**

1. `placeholder_rows()` in `hub.py`: your own rows (each needs an `id`).
2. The `if choice == "confirm":` branch of `delete_one`: the real delete goes there.
3. The wording: `hub.confirm(title, message, confirm_label=..., destructive=...)`.
   Code on another thread than the hub's loop uses `hub.confirm_sync(...)`.
