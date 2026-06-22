"""Helpers that build the (verbose, easy-to-get-wrong) sync / action / connection
dicts controls use. Shapes mirror the bundled ControlDocs (sync.md, actions.md).

    from carterkit import bind
    bind.listen("cpu", filter={"msg_type": "telemetry"})
    bind.action("set_power", payload={"state": "{{value}}"}, mode="request")
    bind.connection("ws://192.168.1.50:8765", channel="home")
"""
from __future__ import annotations


def listen(value_path: str, *, event: str = "broadcast", filter: dict | None = None,
           method: str = "meshsocket") -> dict:
    """A `sync` entry: subscribe to `event`, match `filter`, extract `value_path`
    (dot-notation). Returns one sync dict — controls take a list of them."""
    s: dict = {"method": method, "type": "listen", "event": event, "valuePath": value_path}
    if filter is not None:
        s["filter"] = filter
    return s


def action(event: str, *, payload: dict | None = None, mode: str = "broadcast",
           method: str = "meshsocket") -> dict:
    """An `action` dict: fire `event` on tap/change. `mode` is "broadcast" (fire and
    forget) or "request" (await reply). `payload` strings support `{{value}}`."""
    if mode not in ("broadcast", "request"):
        raise ValueError(f"mode must be 'broadcast' or 'request', got {mode!r}")
    a: dict = {"method": method, "mode": mode, "event": event}
    if payload is not None:
        a["payload"] = payload
    return a


def connection(url: str, *, channel: str = "home", name: str = "CAR-TER",
               role: str = "controller", token: str | None = None) -> dict:
    """A layout `connection` block (relay URL + identity)."""
    conn: dict = {"url": url, "identity": {"name": name, "channel": channel, "role": role}}
    if token is not None:
        conn["token"] = token
    return conn
