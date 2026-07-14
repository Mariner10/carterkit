"""Helpers that build the (verbose, easy-to-get-wrong) sync / action / connection
dicts controls use. Shapes mirror the bundled ControlDocs (sync.md, actions.md).

    from carterkit import bind
    bind.listen("cpu", filter={"msg_type": "telemetry"})
    bind.command("set_power", payload={"state": "{{value}}"})
    bind.connection("ws://192.168.1.50:8765", channel="home")

The one wire fact everything here encodes: the relay dispatches ONLY its own verbs
(`WIRE_VERBS` plus housekeeping like `ping`). An action whose `event` is any other
name is silently dropped at the relay — the control does nothing. Commands therefore
ride `broadcast_request` with the command name as the payload's `msg_type`, and the
server demuxes on that (`Hub.on` does it automatically).
"""
from __future__ import annotations

#: The only frame types the relay forwards between peers. An action's `event`
#: must be one of these (or be built by :func:`command`) to go anywhere.
WIRE_VERBS = ("broadcast_request", "route_msg", "route_msg_noreply")

#: Frame types the relay itself answers (housekeeping) — legal, but not data-plane.
#: `identify` re-identifies the sender (name/channel switching from a control).
RELAY_SERVICE_VERBS = ("ping", "handshake", "status_request", "get_nodes", "identify")


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
    """A raw `action` dict: fire the frame `event` on tap/change. `mode` is
    "broadcast" (fire and forget) or "request" (await reply). `payload` strings
    support `{{value}}`.

    This is the power-user escape hatch — `event` goes on the wire as the frame
    type verbatim, so it must be a relay verb (`WIRE_VERBS`) to be forwarded.
    For a named command, use :func:`command` instead."""
    if mode not in ("broadcast", "request"):
        raise ValueError(f"mode must be 'broadcast' or 'request', got {mode!r}")
    a: dict = {"method": method, "mode": mode, "event": event}
    if payload is not None:
        a["payload"] = payload
    return a


def command(name: str, *, payload: dict | None = None, method: str = "meshsocket") -> dict:
    """An `action` for a named command that actually crosses the relay.

    Compiles to `broadcast_request` with `name` as the payload's `msg_type` — the
    fan-out shape every server can demux on (`Hub.on(handle)` derives it back).
    Default payload adds `{"value": "{{value}}"}` so the control's value rides
    along; pass `payload=` to replace that (the `msg_type` key always stays the
    command name).

    There is deliberately no request/reply variant: the relay only routes replies
    for `route_msg`, which needs a live `target_id` no layout can know at author
    time. Use the round-trip idiom instead — fire the command, and `listen=` for
    the state broadcast the server sends back."""
    body = dict(payload) if payload is not None else {"value": "{{value}}"}
    body["msg_type"] = name
    return {"method": method, "mode": "broadcast", "event": "broadcast_request",
            "payload": body}


def connection(url: str | None, *, channel: str = "home", name: str = "CAR-TER",
               role: str = "controller", token: str | None = None,
               hub: str | None = None, mode: str | None = None,
               e2ee_key: str | None = None, can_broadcast: bool | None = None) -> dict:
    """A layout `connection` block (relay URL + identity). `hub` names the mesh
    identity of the server that will drive this layout (`Layout.serve` adopts it),
    so both sides of the contract live in one artifact.

    `mode="room"` + `e2ee_key` (base64 group key, emitted as `e2eeKey`) author the
    Connect+ room shape — see `carterkit.connection.Connection.layout_block`, whose
    output this mirrors. In a room, `url=None` omits the URL entirely: the app dials
    its own Connect+ relay with its own account session, and a raw url/token here
    would make it hand the wrong credential to the wrong host (reconnect loop)."""
    conn: dict = {"identity": {"name": name, "channel": channel, "role": role}}
    if url is not None:
        conn["url"] = url
    if token is not None:
        conn["token"] = token
    if hub is not None:
        conn["hub"] = hub
    if e2ee_key is not None:
        conn["mode"] = mode or "room"
        conn["e2eeKey"] = e2ee_key
    elif mode is not None:
        conn["mode"] = mode
    if can_broadcast is not None:
        conn["identity"]["can_broadcast"] = can_broadcast
    return conn
