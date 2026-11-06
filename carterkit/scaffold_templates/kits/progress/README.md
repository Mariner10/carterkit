# __NAME__: progress, toast, haptic and log

**What it shows.** One button starts an example task that the app draws as a pill under the
status bar, a progress sheet (ring, "20 of 48 MB", a three-step strip, **Cancel** that asks
first) and, with the app away, on the Dynamic Island and Lock Screen. The hub updates the
task with `hub.progress(...)` and `task.update(...)`, writes a live log with `hub.log(...)`
(the sheet's **Show log**), and ends with a toast whose action opens that log. Cancel sets
`task.cancelled`; the hub stops and reports it with `task.cancelled_ok()`. The Toast and
Haptic buttons play `hub.toast(...)` and `hub.haptic(...)` on their own.

**Run it.**

```bash
python hub.py              # prints a QR: in CAR-TER open the layout list, tap Scan
carterkit validate layout.json
```

The pairing is kept in `.carterkit/session.json`, so the next run reconnects without a
scan. If the phone drops off, carterkit resends the running task and the log's title when
it reconnects. Have a Connect+ hub credential? Save it as `secrets/hub.json`.

**Change first.**

1. `run_task()` in `hub.py`: the real work goes where the chunks are counted (`TOTAL`, `CHUNK`).
2. The wording: `hub.progress(title, unit=..., cancellable=..., ask=...)`.
3. `show="pill"` keeps it out of the way; `island=False` keeps it off the Island.
   Code on another thread uses `task.update_sync(...)`, `hub.toast_sync(...)`.
