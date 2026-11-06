"""Confirm delete: a Delete that asks first, on the phone, before the hub removes anything.

Run:  python hub.py   then scan the QR it prints with the CAR-TER app.
Edit hub.py or layout.json while it runs: every save reaches the phone.

Each row's Delete (and Delete all) sends a command; the hub calls hub.confirm(), which
shows the app's own confirm frame naming this hub, and acts only on 'confirm'. The
other answers are 'cancel', 'timeout' (nobody answered) and 'busy' (another prompt was up).
"""
from pathlib import Path

from carterkit import Layout

ui = Layout.load(Path(__file__).with_name("layout.json"))


def placeholder_rows() -> list[dict]:
    """Placeholder data: swap in your own (files, records, devices)."""
    return [{"id": f"thing-{n}", "name": f"Thing {n}", "detail": f"Example detail {n}"}
            for n in range(1, 7)]


things = placeholder_rows()


def name_of(thing_id) -> str:
    return next((t["name"] for t in things if t["id"] == thing_id), str(thing_id))


async def show(hub, status: str) -> None:
    """Send the rows and a status line (the hub's copy is the truth)."""
    await hub.push("things", things)
    await hub.push("status", status)


async def run(hub):
    """Handlers; restarted on every save."""

    @hub.on("thing_delete")
    async def delete_one(frame):
        thing_id = frame.get("id")
        if not any(t["id"] == thing_id for t in things):
            return
        name = name_of(thing_id)
        choice = await hub.confirm(f"Delete {name}?", "It leaves the list until you tap Restore.",
                                   confirm_label="Delete", destructive=True, timeout_s=30)
        if choice == "confirm":
            things[:] = [t for t in things if t["id"] != thing_id]
            await show(hub, f"Deleted {name}")
        else:
            await hub.push("status", f"Kept {name} ({choice})")

    @hub.on("delete-all")
    async def delete_all(frame):
        if not things:
            return
        choice = await hub.confirm(f"Delete all {len(things)}?", confirm_label="Delete all",
                                   destructive=True, timeout_s=30)
        if choice == "confirm":
            things.clear()
            await show(hub, "Deleted everything")
        else:
            await hub.push("status", f"Kept everything ({choice})")

    @hub.on("restore")
    async def restore(frame):
        things[:] = placeholder_rows()
        await show(hub, "Restored the placeholder rows")

    await show(hub, "Delete asks on the phone first")


if __name__ == "__main__":
    from carterkit import livefile
    raise SystemExit(livefile.main(__file__))
