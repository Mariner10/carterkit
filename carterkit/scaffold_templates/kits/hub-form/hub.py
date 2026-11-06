"""Hub form: a form whose Send reaches the hub, which checks it and answers.

Run:  python hub.py   then scan the QR it prints with the CAR-TER app.
Edit hub.py or layout.json while it runs: every save reaches the phone.

The group's `form` block (layout.json) keeps the typed values on the phone as a draft
and checks its rules there (name required, count 1 to 10). Send submits the whole draft
once, as `{"msg_type": "form_submit", "form": {...}}`; nothing reaches the hub before.
The hub checks again (the phone's rules are a convenience, the hub decides), keeps the
entry and answers with a status line and the list of entries.
"""
from pathlib import Path

from carterkit import Layout

ui = Layout.load(Path(__file__).with_name("layout.json"))

entries: list[dict] = []


def check(form: dict) -> str | None:
    """The hub's own rules; a reason to refuse, or None. Put yours here."""
    name = str(form.get("name") or "").strip()
    if not name:
        return "A name is needed"
    if any(e["name"].lower() == name.lower() for e in entries):
        return f"{name} is already in the list"
    try:
        count = int(form.get("count") or 0)
    except (TypeError, ValueError):
        return "Count must be a number"
    if not 1 <= count <= 10:
        return "Count must be 1 to 10"
    return None


async def run(hub):
    """Handlers; restarted on every save."""

    @hub.on("form_submit")
    async def submitted(frame):
        form = frame.get("form") if isinstance(frame.get("form"), dict) else {}
        reason = check(form)
        if reason:
            await hub.push("status", f"Not saved: {reason}")
            return
        entry = {"name": str(form["name"]).strip(), "count": int(form["count"]),
                 "choice": form.get("choice") or "Option A",
                 "urgent": "Yes" if form.get("urgent") else "No"}
        entries.append(entry)
        await hub.push("entries", entries)
        await hub.push("status", f"Saved {entry['name']} ({len(entries)} so far)")

    await hub.push("entries", entries)


if __name__ == "__main__":
    from carterkit import livefile
    raise SystemExit(livefile.main(__file__))
