# Hub surfaces: progress, toast, haptic and log

A hub can ask the app to draw four more things, on the same terms as `hub.confirm()` and
`hub.open_sheet()`: a **progress** task (pill, sheet, Dynamic Island and Lock Screen), a **toast**,
a **haptic** and a live **log** console. Frames follow the CAR-TER spec
`docs/superpowers/specs/2026-11-06-hub-surfaces.md`; carterkit builds them in
`carterkit/hub_surfaces.py`, mixed into `Hub`. All data below is placeholder.

```python
async with hub.progress("Installing Example package", total=48_000_000, unit="bytes",
                        cancellable=True, ask="Stop installing Example package?",
                        show="sheet", log="task-7-log") as task:
    task.on_cancel(lambda t: print("cancel asked"))
    while task.done < 48_000_000 and not task.cancelled:
        await task.update(done=task.done + 1_000_000, detail="Downloading")
    if task.cancelled:
        await task.cancelled_ok()             # state "cancelled"
    else:
        await task.finish("Installed 1.2.0")  # state "done"; task.fail("...") for "failed"

await hub.toast("Example package installed", message="Version 1.2.0", style="success",
                haptic="success", action=("Show log", {"log": "task-7-log"}))
played = await hub.haptic("success")          # True when played

log = hub.log("task-7-log", title="Install log", progress="task-7")
await log.info("Unpacking Example package (1.2.0)")
await log.warn("Example warning")
await log.open()                              # the console sheet; False on busy
logging.getLogger("job").addHandler(log.handler())
await log.close()
```

## API

| Call | Sends | Notes |
|---|---|---|
| `hub.progress(title, *, value, done, total, unit, detail, step, cancellable, ask, cancel_label, show, island, eta_s, stale_s, log, id)` | `progress` | Returns a `Progress`; `async with` or `await` opens it. `step=(index, count, label)` |
| `Progress.update(**fields)`, `.pause()`, `.resume()`, `.finish(message, haptic)`, `.fail(message, haptic)`, `.cancelled_ok()` | `progress` | Leaving the block unended sends `done` (or `failed` on an exception) |
| `Progress.done` (count), `.cancelled`, `.dismissed`, `.refused`, `.on_cancel(fn)` | | Set by `progress_reply` |
| `hub.toast(title, message, *, style, duration_s, haptic, icon, action, on_action, id)` | `toast` | Returns the reply (`queued`, `updated`, `merged`, or `ok: False` with `busy` / `background`) |
| `hub.haptic(pattern)` | `haptic` | `selection light medium heavy success warning error`; `False` when dropped |
| `hub.log(id, *, title, progress)` -> `LogStream`; `.write/.debug/.info/.notice/.warn/.error`, `.open()`, `.clear()`, `.close()`, `.flush()`, `.handler()` | `log` | Python `logging` handler is thread-safe |
| `toast_sync`, `haptic_sync`, `Progress.update_sync` | | For code on another thread, like `confirm_sync` |
| `hub.resend_surfaces()` | | What a reconnect runs; callable by hand |

`HubError` is raised when the app refuses outright (`not-hub`, `invalid`, `off`), when no device
is on the channel, or for a bad argument before anything is sent. `busy`, `ended` and
`played: false` are returns, not errors.

## What carterkit does for you

- **Coalescing.** Progress updates inside `hub.progress_min_interval` (0.25 s, 4 frames/s) fold into
  one trailing frame, so the newest state is always the last sent. A state change (`pause`, `finish`,
  `fail`, `cancelled_ok`) is sent at once. While nothing changes, a heartbeat resends the full frame
  every `stale_s / 2` (default 15 s) so the app never calls the task stale.
- **Log pacing.** Lines are batched per 100 ms and capped at 200 lines/s; the excess queues on the
  hub (20,000 lines at most, oldest dropped with a marker line), never into the app's flood limit.
- **Reconnect.** On every socket reconnect carterkit resends each running task's full frame and each
  open log stream's title (not its lines), so the app resumes without re-opening the sheet.
- **Replies.** `progress_reply` sets `task.cancelled` (`cancel`), `task.dismissed` (`dismissed`) or
  `task.refused` (`busy`). A `toast_reply` reaches `@hub.on("toast_reply")` or the toast's `on_action`.
  The app never cancels by itself: after Cancel, end the task with `cancelled_ok()`.
- **Caps.** Texts are cut to the spec's lengths (toast title 60, message 120, ...); numbers are
  checked (NaN and negatives are refused; `value` above 1 is clamped).

## Dynamic Island while the app sleeps

For a hub that pushes Live Activity updates itself (Connect+ relay push):

```python
from carterkit import ambient
state = ambient.content_state(
    updated_at=ambient.apple_date(time.time()),
    tasks=[ambient.task("task-7", "Installing Example package", hub="hub-a",
                        detail="Downloading", fraction=0.42,
                        eta_at=ambient.apple_date(time.time() + 90), cancel=True)])
```

`content_state` carries up to three `tasks`; the rest are only counted in `tasksMore`. A hub with no
Connect+ credential moves the Island only while the app runs (about 30 s in the background).

## Starter kit

`carterkit new demo --template progress` scaffolds a layout with a Start button that runs an
example task with a Cancel, steps and a log, and Toast and Haptic buttons.
