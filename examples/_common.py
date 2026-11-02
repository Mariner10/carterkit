"""Shared by the examples: find the Add Hub credential or print how to get one."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HINT = ("No hub credential found. On the phone open Hubs -> Add Hub and save the JSON as "
        "secrets/hub.json (or set CARTER_HUB=/path/to/hub.json), then run this again.")


def credential():
    """Path of the Add Hub JSON, or None."""
    for path in (os.environ.get("CARTER_HUB"), "secrets/hub.json",
                 os.path.join(HERE, "..", "secrets", "hub.json")):
        if path and os.path.isfile(path):
            return path
    return None


def hub_for(ui):
    """A Hub for `ui` on the saved credential; prints the Add Hub hint and returns None without one."""
    path = credential()
    if path is None:
        print(HINT)
        return None
    return ui.serve(path)


def main(run, ui):
    import asyncio
    hub = hub_for(ui)
    if hub is None:
        return 1
    try:
        asyncio.run(run(hub))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(0)
