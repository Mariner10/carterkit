# __NAME__: live dashboard

**What it shows.** A gauge, a sparkline of the last 60 readings and a text readout, all
fed by the hub. Once a second `hub.py` reads a placeholder value (a random walk) and
pushes it: `hub.push("level", v)` broadcasts the `metrics` frame the gauge listens for,
and the sparkline listens for the very same frame, so one push moves both. Reset to 50
sends a command back; the hub sets the value and pushes it at once. The hub is the state
authority: a phone that joins late gets the last values straight away.

**Run it.**

```bash
python hub.py              # prints a QR: in CAR-TER open the layout list, tap Scan
carterkit validate layout.json
```

The pairing is kept in `.carterkit/session.json`, so the next run reconnects without a
scan. Every save of `hub.py` or `layout.json` is pushed to the phone. Have a Connect+ hub
credential? Save it as `secrets/hub.json` to use the managed relay instead of your LAN.

**Change first.**

1. `read_level()` in `hub.py`: read a real value (a sensor, a CPU load, an API).
2. `INTERVAL`: how often it is sent.
3. The gauge's `min`, `max` and `unit` in `layout.json`; more controls follow the same
   pattern: give each a `sync` on a `msg_type` and `hub.push("<id>", value)` it.
