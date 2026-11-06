# __NAME__: a remote with authoritative state

**What it shows.** Power and Mute toggles, Volume and Brightness sliders, a Reset button
and a status line. The controls only ask: each sends `set_<name>` with its value. The hub
owns the truth: it applies its rules (only Power works while the power is off, the volume
stops at 80), keeps the result in `STATE` and sends every value back, so a refused or
clamped change snaps the control back to what the hub says. A phone that joins late gets
the hub's values straight away (the hub is the state authority).

**Run it.**

```bash
python hub.py              # prints a QR: in CAR-TER open the layout list, tap Scan
carterkit validate layout.json
```

The pairing is kept in `.carterkit/session.json`, so the next run reconnects without a
scan. Every save of `hub.py` or `layout.json` is pushed to the phone. Have a Connect+ hub
credential? Save it as `secrets/hub.json` to use the managed relay instead of your LAN.

**Change first.**

1. `apply()` in `hub.py`: send the command to your real device and keep what it reports.
2. `DEFAULTS` and `VOLUME_LIMIT`: your device's starting state and limits.
3. A new control: add it to `layout.json` with an `action` sending `set_<name>` and a
   `sync` listening for `<name>_state`, then add its key to `DEFAULTS`.
