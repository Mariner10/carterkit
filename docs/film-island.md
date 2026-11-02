# Film kit: Python driving the Dynamic Island (30 s)

Everything except the recording itself. The script is `examples/island_demo.py`.

## Before you film

- A **real iPhone** with CAR-TER installed and Live Activities allowed (the simulator cannot receive Live Activity pushes).
- Add Hub credential saved as `secrets/hub.json` (phone: Hubs -> Add Hub, save the JSON), or `export CARTER_HUB=/path/to/hub.json`. Without it the script prints the Add Hub hint and exits.
- Phone on the same network, screen unlocked, Do Not Disturb off. Screen-record the phone, or film it, with the top of the screen (the Island) in frame.
- Dry run once: `python3 examples/island_demo.py`. You should see `layout pushed`, `Live Activity started`, six `update n/6` lines and `Live Activity ended`.

## Layout of the frame

Terminal on the **left** (large font, 14 pt+, dark theme, only the one command visible). Phone on the **right**, Island at the top. Keep the terminal clean: `clear` first.

## Title card (2 s, before the terminal)

> **Python drives your iPhone's Dynamic Island**
> `pip install carterkit` . 10 lines of Python

Optional voice-over: "This is a Python script. Watch the top of the phone."

## Shot list

| Time | Terminal (left) | Phone (right) |
|------|-----------------|---------------|
| 0-3 s | Type and run `python3 examples/island_demo.py`. Prints `layout pushed`. | Home screen; the CAR-TER layout appears. |
| 3 s | `Live Activity started` | The Island appears. |
| 6-26 s | One line every 4 s: `update 1/6: level = 15` ... `update 6/6: level = 90` | The Island gauge jumps up and down with each line. Long-press to expand it once (around 10 s). |
| ~15 s | Tap **Ping** on the phone: `button tapped on the phone` prints. | Finger taps Ping in the app (or the expanded Island). |
| 30 s | `Live Activity ended` | The Island disappears. |

End on the terminal and the empty Island for 1 s, then the closing card: `github.com/Mariner10/carterkit`.

## Exact commands

```
clear
python3 examples/island_demo.py
```

To retake: let it finish (or Ctrl-C), then run it again. It restarts the Live Activity from scratch.

## If the Island is not available

- **iPhone without an Island** (anything before 14 Pro): the Live Activity shows as a Lock Screen banner. Film with the phone locked and lit; same script, same timing.
- **No Live Activity at all** (permission off, simulator): run `python3 examples/live_tab.py` or `python3 examples/push_value.py`, same left/right framing, and let the value move in the app. Say "Live tab" instead of "Island" in the title card.
- **Credential error**: the script prints the Add Hub hint; fix it per "Before you film".
