"""One connection story — every way into the mesh, parsed from one place.

The ecosystem grew four shapes of "how do I connect":

  1. a layout's `connection` block (what the APP dials):
     ``{"url", "token"?, "mode"?, "e2eeKey"?, "identity": {"name","channel","role"}}``
  2. the QR pairing JSON (what the app scans): ``{"url","channel","role","token"?}``
  3. the *Add Hub* credential (what a HUB holds — the app's Layout hub (Hubs → Add Hub) emits
     it): ``{"url","channel","token","role","refresh","did","k"?,"validator"?}``
  4. `CarterClient` constructor kwargs.

:class:`Connection` parses any of the first three (or a bare ``ws://`` URL, a file
path, or nothing at all) and emits any of the others, so a layout, a QR code, and a
serving hub can all be driven off the same artifact:

    conn = Connection.parse("device.json")      # Add-Device credential from the app
    conn = Connection.parse("ws://192.168.1.50:8765", channel="lab", token="key")
    conn = Connection.parse(None)               # zero-config: embedded LocalRelay

    ui.connect(conn)                            # app-side connection block
    hub = ui.serve(conn)                        # hub-side CarterClient (see hub.py)

The asymmetry it encodes (and the reason "one config" was never trivially true):

  * **Self-hosted** is symmetric — the same ``url`` + shared-key ``token`` works for
    the app and the hub, so one Connection round-trips everywhere.
  * **Connect+** is asymmetric — the app joins with its own account session (its
    layout block carries no usable hub credential), while the hub joins with the
    per-device credential from *Add Device* (short-lived ``token`` + long-lived
    ``refresh`` secret + ``did``). A device token is that device's identity:
    :meth:`layout_block` deliberately never embeds it into a layout.
"""
from __future__ import annotations

import json
import os

#: Connect+ validator (token refresh / alerts) used when a device credential
#: doesn't carry its own ``validator`` key. Overridable via ``validator=``.
DEFAULT_VALIDATOR = "https://connect.carterbeaudoin.net"

_LOCAL_DEFAULT_PORT = 8765


class Connection:
    """A parsed mesh connection: where to dial, as whom, with which secrets.

    ``kind`` is one of:
      * ``"local"`` — no source given; serve with an embedded :class:`LocalRelay`.
      * ``"selfhosted"`` — a plain relay URL (+ optional shared-key token). Symmetric:
        the same config works app-side and hub-side.
      * ``"device"`` — a Connect+ *Add Device* credential (token/refresh/did[/k]).
        Hub-side only; the app joins with its own account.
      * ``"account"`` — a Connect+ layout block with no hub credential (e.g. a room
        layout). Enough to emit app-side blocks, but it cannot serve a hub.
    """

    def __init__(self, kind: str, *, url: str | None = None, channel: str = "home",
                 role: str | None = None, token: str | None = None,
                 e2ee_key: str | None = None, room: bool = True,
                 device_id: str | None = None, refresh_token: str | None = None,
                 validator: str | None = None, hub: str | None = None,
                 port: int = _LOCAL_DEFAULT_PORT, key: str = ""):
        self.kind = kind
        self.url = url
        self.channel = channel
        self.role = role
        self.token = token
        self.e2ee_key = e2ee_key
        self.room = room                      # group cipher (the app's mode:"room")
        self.device_id = device_id
        self.refresh_token = refresh_token
        self.validator = validator
        self.hub = hub                        # preferred mesh name for a serving hub
        self.port = port                      # local-relay bind (kind == "local")
        self.key = key                        # local-relay shared key

    # ─── parsing ─────────────────────────────────────────────────────────────
    @classmethod
    def parse(cls, source=None, **overrides) -> "Connection":
        """Build a Connection from anything the ecosystem hands you.

        ``source`` may be: ``None`` (embedded LocalRelay), a ``ws://``/``wss://``
        URL, a path to a JSON file (Add-Device credential, pairing JSON, layout
        block, or a whole layout), such a dict directly, or an existing
        Connection (returned as-is unless overridden). Keyword overrides
        (``channel=``, ``token=``, ``validator=``, ``hub=``, …) win over parsed
        values."""
        if isinstance(source, Connection):
            conn = source
        elif source is None:
            conn = cls("local")
        elif isinstance(source, str):
            if source.startswith(("ws://", "wss://")):
                conn = cls("selfhosted", url=source)
            elif os.path.exists(source):
                with open(source) as f:
                    return cls.parse(json.load(f), **overrides)
            else:
                raise ValueError(
                    f"can't parse connection source {source!r}: not a ws:// URL and "
                    f"not a file that exists")
        elif isinstance(source, dict):
            conn = cls._parse_dict(source)
        else:
            raise TypeError(f"can't parse a {type(source).__name__} as a connection")
        for k, v in overrides.items():
            if not hasattr(conn, k):
                raise TypeError(f"unknown connection field {k!r}")
            setattr(conn, k, v)
        return conn

    @classmethod
    def _parse_dict(cls, d: dict) -> "Connection":
        if "tabs" in d:                      # a whole layout — use its connection block
            block = d.get("connection")
            if not block:
                raise ValueError(
                    "this layout has no 'connection' block — pass a URL or a device "
                    "credential instead")
            return cls._parse_dict(block)
        if "identity" in d:                  # a layout connection block
            ident = d.get("identity") or {}
            return cls(
                "selfhosted" if d.get("url") else "account",
                url=d.get("url"), token=d.get("token"),
                channel=ident.get("channel", "home"), role=ident.get("role"),
                e2ee_key=d.get("e2eeKey"), room=(d.get("mode") == "room" or "e2eeKey" in d),
                hub=d.get("hub"))
        if "did" in d or "refresh" in d:     # Add-Device credential (hub-side)
            return cls(
                "device", url=d.get("url"), token=d.get("token"),
                channel=d.get("channel", "home"), role=d.get("role", "hub"),
                e2ee_key=d.get("k") or d.get("e2eeKey"),
                device_id=d.get("did"), refresh_token=d.get("refresh"),
                validator=d.get("validator"))
        if "url" in d:                       # QR pairing JSON / bare dict
            return cls(
                "selfhosted", url=d["url"], token=d.get("token"),
                channel=d.get("channel", "home"), role=d.get("role"),
                e2ee_key=d.get("k") or d.get("e2eeKey"), hub=d.get("hub"))
        raise ValueError(
            f"can't recognize this dict as a connection (keys: {sorted(d)}) — expected "
            f"a layout connection block, a pairing JSON, or an Add-Device credential")

    # ─── emissions ───────────────────────────────────────────────────────────
    def app_url(self) -> str:
        """The URL the APP should dial. For kind 'local' that's this machine's LAN
        address (the phone can't reach 127.0.0.1)."""
        if self.url:
            return self.url
        from .relay import lan_ip
        return f"ws://{lan_ip()}:{self.port}"

    def layout_block(self, *, name: str = "CAR-TER", role: str | None = None) -> dict:
        """The layout `connection` block for the APP side.

        Policy: a Connect+ device token is the HUB's per-device identity, never the
        phone's — so for kind 'device' the block carries url/channel only and the
        phone joins with its own account session. Self-hosted shared-key tokens DO
        embed (both sides present the same key)."""
        block: dict = {
            "url": self.app_url(),
            "identity": {"name": name, "channel": self.channel,
                         "role": role or "controller"},
        }
        if self.kind in ("selfhosted", "local"):
            token = self.token if self.kind == "selfhosted" else (self.key or None)
            if token:
                block["token"] = token
        if self.e2ee_key:
            block["mode"] = "room"
            block["e2eeKey"] = self.e2ee_key
        if self.hub:
            block["hub"] = self.hub
        return block

    def qr_json(self, *, role: str = "controller") -> str:
        """The pairing JSON the app scans (Settings → scan)."""
        obj: dict = {"url": self.app_url(), "channel": self.channel, "role": role}
        token = self.token if self.kind == "selfhosted" else (self.key or None)
        if self.kind in ("selfhosted", "local") and token:
            obj["token"] = token
        if self.e2ee_key:
            obj["k"] = self.e2ee_key
        return json.dumps(obj)

    def client_kwargs(self, *, name: str | None = None) -> dict:
        """Constructor kwargs for a hub-side :class:`CarterClient`."""
        if self.kind == "account":
            raise ValueError(
                "this connection is a Connect+ account-side block — it has no hub "
                "credential. Mint one on the phone (Layout hub → Hubs → Add Hub) and pass "
                "that JSON instead.")
        url = self.url if self.kind != "local" else f"ws://127.0.0.1:{self.port}"
        kw: dict = {
            "gateway_url": url,
            "token": self.token or (self.key if self.kind == "local" else "") or "",
            "channel": self.channel,
            "role": self.role or ("hub" if self.kind == "device" else "device"),
            "name": name or self.hub or "hub",
        }
        if self.e2ee_key:
            kw["e2ee_key"] = self.e2ee_key
            kw["room"] = self.room
        if self.device_id and self.refresh_token:
            kw["device_id"] = self.device_id
            kw["refresh_token"] = self.refresh_token
            kw["validator_url"] = self.validator or DEFAULT_VALIDATOR
        return kw

    def __repr__(self) -> str:
        bits = [self.kind, self.url or f"port={self.port}", f"channel={self.channel!r}"]
        if self.device_id:
            bits.append(f"did={self.device_id}")
        if self.e2ee_key:
            bits.append("e2ee")
        return f"<Connection {' '.join(bits)}>"
