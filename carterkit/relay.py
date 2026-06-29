"""Run a tiny embedded MeshSocket relay for local / LAN testing of a layout.

The relay is the WebSocket hub both the app and your server connect to. For real
self-hosting you point at the Connect+ relay (``wss://relay…``); for a quick local
test this spins one up in-process so there's nothing else to run.

It refuses to start on a port that's already in use — the usual cause of a confusing
"connects then immediately drops" loop: a second relay silently fails to bind, its
hub lands on the *first* one, and two same-named hubs evict each other every couple
of seconds. Failing fast with a clear message beats debugging that.

    from carterkit import LocalRelay, CarterClient

    async with LocalRelay(port=8765, key="dev-key") as relay:
        hub = CarterClient("ws://127.0.0.1:8765", token="dev-key",
                           channel="home", role="device")
        await hub.connect()
        ...                       # push values; the app connects to the same relay
"""
from __future__ import annotations

import asyncio
import socket as _socket

try:                                  # ships with the meshsocket dependency
    from socket_server import MeshServer
except ImportError:                   # pragma: no cover - environment guard
    MeshServer = None


def lan_ip(override: str | None = None) -> str:
    """This machine's LAN IP — the address to bake into a layout so a phone can reach
    the relay. Returns `override` if given, or falls back to 127.0.0.1 when offline."""
    if override:
        return override
    s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))        # no packets sent; just picks the egress interface
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """True if something is already accepting connections on ``(host, port)``.

    A 0.0.0.0 listener also answers on 127.0.0.1, so the default probe catches the
    common "another relay is already running" case."""
    probe = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
    probe.settimeout(0.3)
    try:
        return probe.connect_ex((host if host not in ("", "0.0.0.0") else "127.0.0.1", port)) == 0
    finally:
        probe.close()


class LocalRelay:
    """An in-process MeshSocket relay with shared-key auth, for local testing.

    ``key`` is the shared key clients must present (``""`` runs open, no auth).
    ``on_join(name, ip)`` fires when a client authenticates — handy for pushing a
    fresh snapshot to a device the moment it connects. Use it as an async context
    manager, or call :meth:`start` / :meth:`stop` yourself. Raises ``RuntimeError``
    if the port is already in use and ``ImportError`` if the server isn't installed.
    """

    def __init__(self, port: int = 8765, key: str = "", host: str = "0.0.0.0", on_join=None):
        if MeshServer is None:
            raise ImportError("LocalRelay needs the MeshSocket server; run `pip install meshsocket`.")
        self.port, self.key, self.host, self.on_join = port, key, host, on_join
        self._server = None
        self._task: asyncio.Task | None = None

    async def start(self) -> "LocalRelay":
        if port_in_use(self.port, self.host):
            raise RuntimeError(
                f"port {self.port} is already in use — another relay or tester is probably "
                f"running. Stop it (e.g. `pkill -f tester.py`) or pass a different port.")
        auth = (lambda tok, ip: tok == self.key) if self.key else (lambda tok, ip: True)
        on_auth = None
        if self.on_join:
            on_auth = lambda client, ip, tok: self.on_join(getattr(client, "name", "?"), ip)
        self._server = MeshServer(host=self.host, port=self.port,
                                  auth_handler=auth, on_authenticated=on_auth)
        self._task = asyncio.create_task(self._server.start())
        await asyncio.sleep(0.5)      # let the listener bind before clients dial in
        return self

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def __aenter__(self) -> "LocalRelay":
        return await self.start()

    async def __aexit__(self, *exc) -> bool:
        await self.stop()
        return False
