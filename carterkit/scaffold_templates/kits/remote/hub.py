"""Remote: toggles and sliders whose state the hub owns and sends back.

Run:  python hub.py   then scan the QR it prints with the CAR-TER app.
Edit hub.py or layout.json while it runs: every save reaches the phone.

A toggle or slider on the phone only asks: it sends `set_<name>` with its value. The hub
applies its rules (nothing but Power works while the power is off; the volume stops at
VOLUME_LIMIT), keeps the result in STATE and sends every value back, so a refused or
clamped change snaps the control back to the hub's value. push(..., force=True) resends
a value even when it equals the hub's last push: the phone moved it, the hub corrects it.
"""
from pathlib import Path

from carterkit import Layout

ui = Layout.load(Path(__file__).with_name("layout.json"))

DEFAULTS = {"power": True, "mute": False, "volume": 30, "brightness": 70}
VOLUME_LIMIT = 80
STATE = dict(DEFAULTS)


def truthy(value) -> bool:
    return value in (True, 1, "1", "true", "on")


def level(value, top: int = 100) -> int:
    try:
        return max(0, min(top, round(float(value))))
    except (TypeError, ValueError):
        return 0


def apply(key: str, value) -> str:
    """The hub's rules: change STATE[key] (or refuse) and say what happened.
    Your device goes here: send the command, then keep what it reports."""
    if key == "power":
        STATE["power"] = truthy(value)
        return f"Power {'on' if STATE['power'] else 'off'}"
    if not STATE["power"]:
        return f"Power is off: {key} stays as it was"
    if key == "mute":
        STATE["mute"] = truthy(value)
        return "Muted" if STATE["mute"] else "Sound on"
    if key == "volume":
        wanted = level(value)
        STATE["volume"] = min(wanted, VOLUME_LIMIT)
        if wanted > VOLUME_LIMIT:
            return f"Volume stops at {VOLUME_LIMIT}"
        return f"Volume {STATE['volume']}"
    STATE["brightness"] = level(value)
    return f"Brightness {STATE['brightness']}"


async def send_state(hub, status: str) -> None:
    """Every control gets the hub's value, even one the phone just moved."""
    for key, value in STATE.items():
        await hub.push(key, value, force=True)
    await hub.push("status", status)


async def run(hub):
    """Handlers; restarted on every save."""
    for key in DEFAULTS:
        def handler(frame, key=key):
            return send_state(hub, apply(key, frame.get("value")))
        hub.on(key, handler)              # the control's action: set_power, set_volume, ...

    @hub.on("reset")
    async def reset(frame):
        STATE.update(DEFAULTS)
        await send_state(hub, "Back to the defaults")

    await send_state(hub, "Ready")


if __name__ == "__main__":
    from carterkit import livefile
    raise SystemExit(livefile.main(__file__))
