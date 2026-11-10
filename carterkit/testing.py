"""A fake hub for tests and tutorial checks: your hub.py against no relay and no phone.

``FakeHub`` serves a layout with the socket stubbed by a recording fake, so a hub's
handlers can be driven with ``await fake.dispatch({...})`` and what it broadcast read back
with ``fake.frames("metrics")``. It is the one fake the starter kits' tests, the
tutorial lint and ``carterkit tutorial --check`` share.

    from carterkit.testing import FakeHub, load_hub_module

    mod = load_hub_module("hub.py")               # imports it; mod.ui, mod.run
    fake = FakeHub(mod.ui)
    async with fake.running(mod.run):             # run(hub) as a task, cancelled after
        await fake.dispatch({"msg_type": "set_volume", "value": 95})
    assert fake.frames("volume_state")[-1]["value"] == 80
"""
from __future__ import annotations

import asyncio
import contextlib
import importlib.util
from typing import Any, Awaitable, Callable, Optional


def _supported(cap_id: str, version: Optional[str]) -> bool:
    """Does a phone on ``version`` support capability ``cap_id``? Unknown ids are
    supported (no pin); ``since: next`` is unreleased, so no version has it."""
    from .validate import _is_app_version, _version_newer, capabilities_manifest
    caps = capabilities_manifest().get("capabilities")
    entry = caps.get(cap_id) if isinstance(caps, dict) else None
    since = entry.get("since") if isinstance(entry, dict) else None
    if since is None:
        return True
    if not _is_app_version(since):
        return False
    return not _version_newer(since, version)


def filter_frame(frame: dict, version: Optional[str]) -> Optional[dict]:
    """What a phone on ``version`` would be sent: None when the frame's capability
    (``hub-surfaces.<msg_type>``) is newer than it, else the frame minus fields whose
    ``hub-surfaces.<msg_type>.<field>`` pin is newer. ``version`` None = no filtering."""
    if version is None or not isinstance(frame, dict):
        return frame
    mt = frame.get("msg_type")
    if not mt:
        return frame
    if not _supported(f"hub-surfaces.{mt}", version):
        return None
    return {k: v for k, v in frame.items() if _supported(f"hub-surfaces.{mt}.{k}", version)}


class FakeSock:
    """The relay socket: records everything the hub sends; ``reply`` answers requests."""

    def __init__(self):
        self.sent: list = []
        self.handlers: dict = {}
        self.reply: Any = None

    def on(self, t, f):
        self.handlers[t] = f

    async def send(self, t, payload=None, reply_to=None):
        self.sent.append((t, payload))

    async def request(self, t, payload=None, timeout=5.0):
        self.sent.append(("REQ:" + t, payload))
        return self.reply

    async def start(self):
        pass

    async def wait_until_ready(self):
        pass

    async def stop(self):
        pass


class PhoneSock(FakeSock):
    """A socket with one phone on the channel: it answers ``hub.confirm`` prompts with
    ``answer`` (a choice id, ``"confirm"`` or ``"cancel"``) and accepts routed sheets."""

    def __init__(self, fake: "FakeHub", answer: str = "confirm"):
        super().__init__()
        self.fake, self.answer = fake, answer

    async def request(self, t, payload=None, timeout=5.0):
        self.sent.append(("REQ:" + t, payload))
        if t == "get_nodes":
            return {"clients": [{"id": "dev1", "name": "phone"}]}
        if t == "route_msg" and payload["type"] == "prompt":
            reply = {"msg_type": "prompt_reply", "id": payload["payload"]["id"], "choice": self.answer}
            asyncio.get_running_loop().call_later(
                0.01, lambda: asyncio.ensure_future(self.fake.hub._dispatch(reply)))
            return {"ok": True, "queued": 0}
        if t == "route_msg":
            return {"ok": True}
        return self.reply


class FakeHub:
    """``layout.serve()`` with a recording socket. ``.hub`` is the real Hub."""

    def __init__(self, ui, *, answer: str = "confirm", **serve_kw):
        self.ui = ui
        self.hub = ui.serve(**serve_kw)
        self.sock = PhoneSock(self, answer)
        self.hub.client._sock = self.sock
        self.app_version: Optional[str] = None
        self.manifest_hash: Optional[str] = None

    @property
    def sent(self) -> list:
        return self.sock.sent

    async def hello(self, appVersion: Optional[str] = None, manifestHash: Optional[str] = None,
                    **extra) -> None:
        """Deliver the phone's hello: ``appVersion`` (and ``manifestHash``) are remembered
        so ``frames()`` only shows what that phone supports (capability ``since`` <= it)."""
        self.app_version, self.manifest_hash = appVersion, manifestHash
        frame = {"msg_type": "hello", **extra}
        if appVersion is not None:
            frame["appVersion"] = appVersion
        if manifestHash is not None:
            frame["manifestHash"] = manifestHash
        await self.hub._dispatch(frame)

    def frames(self, msg_type: Optional[str] = None) -> list:
        """Broadcast payloads the hub sent, optionally only one ``msg_type``. After a
        ``hello(appVersion=...)``, frames and fields newer than that app are dropped."""
        out = [f for f in (filter_frame(p, self.app_version)
                           for t, p in self.sock.sent if t == "broadcast_request")
               if f is not None]
        return [p for p in out if msg_type is None or p.get("msg_type") == msg_type]

    def routed(self, kind: str) -> list:
        """Payloads of routed messages of one inner ``type`` (``prompt``, ``sheet``...)."""
        return [p["payload"] for t, p in self.sock.sent if t == "REQ:route_msg" and p["type"] == kind]

    async def dispatch(self, frame: dict) -> None:
        """Deliver a frame as if the phone had broadcast it."""
        await self.hub._dispatch(frame)

    @contextlib.asynccontextmanager
    async def running(self, run: Callable[[Any], Awaitable], settle: float = 0.02):
        """Run ``run(hub)`` as a task (as the live runner does), yield once it has settled,
        cancel it on exit."""
        task = asyncio.create_task(run(self.hub))
        await asyncio.sleep(settle)
        try:
            yield self
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


def load_hub_module(path, name: str = "hub_under_test"):
    """Import a hub.py by path (not through the live runner) and return the module."""
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
