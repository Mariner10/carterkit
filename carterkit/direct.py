"""Direct link, hub side: signaling handlers + the `carter-direct` sidecar manager.

The phone signals over the sealed MeshSocket room (`direct_hello` / `direct_offer` /
`direct_close`); media and the `rpc` data channel then run peer to peer inside the Go sidecar
(`carter-direct`), which talks to this process over stdio with length-prefixed frames. An `rpc`
request is dispatched to the very same handler a MeshSocket request would reach
(`CarterClient.dispatch_request(..., sealed=False)`), with the session's bound peer as
`_relayFrom`/`_from`. Session identity is the offer's relay-stamped `_relayFrom`, never `_from`.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import shutil
import struct
from pathlib import Path

log = logging.getLogger(__name__)

RELAY_SENDER_KEY = "_relayFrom"
DEFAULT_ICE = [{"urls": ["stun:stun.cloudflare.com:3478"]},
               {"urls": ["stun:stun.l.google.com:19302"]}]
GATHER_TIMEOUT_MS = 1500
MAX_INFLIGHT = 32
MAX_MESSAGE = 262144
OFFER_TIMEOUT = 10.0
BACKOFF_MIN, BACKOFF_MAX = 1.0, 30.0


# ─── codecs ──────────────────────────────────────────────────────────────────
def encode_frame(header: dict, body: bytes = b"") -> bytes:
    h = json.dumps(header, separators=(",", ":")).encode()
    return struct.pack(">II", 4 + len(h) + len(body), len(h)) + h + body


def decode_frame(buf: bytes):
    """buf = the frame WITHOUT its leading length. Returns (header, body)."""
    (hl,) = struct.unpack(">I", buf[:4])
    return json.loads(buf[4:4 + hl]), bytes(buf[4 + hl:])


async def read_frame(reader):
    """Next (header, body) from an asyncio stream; None at EOF."""
    try:
        (n,) = struct.unpack(">I", await reader.readexactly(4))
        return decode_frame(await reader.readexactly(n))
    except (asyncio.IncompleteReadError, ConnectionError):
        return None


def encode_rpc(header: dict, body: bytes = b"") -> bytes:
    h = json.dumps(header, separators=(",", ":")).encode()
    return struct.pack(">I", len(h)) + h + body


def decode_rpc(buf: bytes):
    (hl,) = struct.unpack(">I", buf[:4])
    return json.loads(buf[4:4 + hl]), bytes(buf[4 + hl:])


def find_sidecar() -> Path | None:
    """The `carter-direct` binary: env CARTERKIT_DIRECT_BIN, else the packaged one, else PATH."""
    env = os.environ.get("CARTERKIT_DIRECT_BIN")
    if env:
        p = Path(env)
        return p if p.is_file() else None
    pkg = Path(__file__).parent / "bin" / "carter-direct"
    if pkg.is_file():
        return pkg
    w = shutil.which("carter-direct")
    return Path(w) if w else None


# ─── sidecar process ─────────────────────────────────────────────────────────
class Sidecar:
    """Supervises one `carter-direct` process: restarts with backoff (1 s → 30 s), resends
    `config` after each `ready`. `on_frame(header, body)` gets every sidecar frame;
    `on_restart()` fires when the process died."""

    def __init__(self, path, config_fn, on_frame, on_exit=None):
        self.path = str(path)
        self.config_fn = config_fn
        self.on_frame = on_frame
        self.on_exit = on_exit
        self.proc = None
        self._task = None
        self._stopping = False
        self._wlock = None

    async def start(self):
        self._stopping = False
        self._wlock = asyncio.Lock()
        self._task = asyncio.create_task(self._supervise())
        for _ in range(100):                 # first spawn, so an early offer finds a process
            if self.proc is not None or self._task.done():
                break
            await asyncio.sleep(0.02)

    async def stop(self):
        self._stopping = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None
        await self._kill()

    async def _kill(self):
        p, self.proc = self.proc, None
        if p and p.returncode is None:
            try:
                p.kill()
            except ProcessLookupError:
                pass
            await p.wait()

    async def send(self, header: dict, body: bytes = b"") -> bool:
        p = self.proc
        if p is None or p.returncode is not None or p.stdin is None:
            return False
        try:
            async with self._wlock:
                p.stdin.write(encode_frame(header, body))
                await p.stdin.drain()
            return True
        except (ConnectionError, BrokenPipeError):
            return False

    async def _supervise(self):
        backoff = BACKOFF_MIN
        while not self._stopping:
            loop = asyncio.get_running_loop()
            t0 = loop.time()
            try:
                self.proc = await asyncio.create_subprocess_exec(
                    self.path, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL)
                await self.send({"op": "config", **self.config_fn()})
                while True:
                    fr = await read_frame(self.proc.stdout)
                    if fr is None:
                        break
                    if fr[0].get("op") == "ready":
                        backoff = BACKOFF_MIN
                        await self.send({"op": "config", **self.config_fn()})
                    try:
                        await self.on_frame(*fr)
                    except Exception:
                        log.exception("direct: frame handler failed")
                await self.proc.wait()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log.warning("direct: sidecar error: %s", exc)
            self.proc = None
            if self._stopping:
                return
            log.warning("direct: sidecar exited; restarting in %.1fs", backoff)
            if self.on_exit:
                try:
                    await self.on_exit()
                except Exception:
                    log.exception("direct: on_exit failed")
            await asyncio.sleep(backoff)
            backoff = min(BACKOFF_MAX, backoff * 2) if loop.time() - t0 < 30 else BACKOFF_MIN


# ─── hub mixin ───────────────────────────────────────────────────────────────
class HubDirect:
    """Mixin for Hub: `camera()`, the direct_* handlers and the sidecar lifecycle."""

    def _dx(self):
        st = self.__dict__.get("_dx_state")
        if st is None:
            st = self._dx_state = {"cameras": {}, "status": {}, "sessions": {}, "pending": {},
                                   "sidecar": None, "ice": list(DEFAULT_ICE), "tasks": set()}
        return st

    @property
    def direct_sessions(self) -> dict:
        """session id -> {"peer", "state", "path"}."""
        return self._dx()["sessions"]

    def camera(self, id: str, url: str, name: str | None = None) -> None:
        """Offer a camera (an RTSP/HTTP stream URL) on the direct link. Sync; safe before run."""
        st = self._dx()
        st["cameras"][id] = {"id": id, "url": url, "name": name or id}
        st["status"].pop(id, None)
        sc = st["sidecar"]
        if sc is not None:
            self._dx_spawn(sc.send({"op": "camera_add", "id": id, "url": url,
                                    "name": st["cameras"][id]["name"]}))

    def direct_capabilities(self) -> dict | None:
        if find_sidecar() is None:
            return None
        st = self._dx()
        return {"v": 1, "data": True,
                "video": [{"id": c["id"], "name": c["name"],
                           "status": st["status"].get(c["id"], "idle")}
                          for c in st["cameras"].values()]}

    def _dx_spawn(self, coro):
        t = asyncio.ensure_future(coro)
        tasks = self._dx()["tasks"]
        tasks.add(t)
        t.add_done_callback(tasks.discard)

    def _dx_config(self) -> dict:
        st = self._dx()
        return {"ice_servers": st["ice"], "cameras": list(st["cameras"].values()),
                "gather_timeout_ms": GATHER_TIMEOUT_MS, "max_inflight": MAX_INFLIGHT}

    async def _direct_start(self):
        path = find_sidecar()
        if path is None:
            return
        st = self._dx()
        if st["sidecar"] is not None:
            return
        self.client.on("direct_hello", self._dx_hello)
        self.client.on("direct_offer", self._dx_offer)
        self.client.on("direct_close", self._dx_close)
        sc = st["sidecar"] = Sidecar(path, self._dx_config, self._dx_frame, self._dx_exited)
        await sc.start()

    async def _direct_stop(self):
        st = self._dx()
        sc, st["sidecar"] = st["sidecar"], None
        if sc is not None:
            await sc.stop()
        for t in list(st["tasks"]):
            t.cancel()
        self._dx_fail_all()

    def _dx_fail_all(self):
        st = self._dx()
        for s in st["sessions"].values():
            if s["state"] != "closed":
                s["state"] = "failed"
        for fut in st["pending"].values():
            if not fut.done():
                fut.set_result({"error": "failed"})
        st["pending"].clear()

    async def _dx_exited(self):
        self._dx_fail_all()

    # handlers (run through CarterClient.on, so MeshSocket path = sealed, routed)
    async def _dx_hello(self, data):
        return self.direct_capabilities()

    async def _dx_offer(self, data):
        st = self._dx()
        session = data.get("session")

        def err(code):
            return {"msg_type": "direct_answer", "session": session, "error": code}
        peer = data.get(RELAY_SENDER_KEY)
        if not isinstance(peer, str) or not peer:
            return err("denied")
        sc = st["sidecar"]
        if sc is None or find_sidecar() is None:
            return err("no_sidecar")
        if not isinstance(session, str) or not isinstance(data.get("sdp"), str):
            return err("unsupported")
        want = data.get("want") or {}
        for cid in want.get("video") or []:
            if cid not in st["cameras"]:
                return err("unknown_camera")
        bound = st["sessions"].get(session)
        if bound is not None and bound["peer"] != peer:
            return err("denied")
        fut = asyncio.get_running_loop().create_future()
        st["pending"][session] = fut
        st["sessions"][session] = {"peer": peer, "state": "offered", "path": None}
        if not await sc.send({"op": "offer", "session": session, "peer": peer,
                              "sdp": data["sdp"], "want": want}):
            st["pending"].pop(session, None)
            st["sessions"].pop(session, None)
            return err("no_sidecar")
        try:
            res = await asyncio.wait_for(fut, OFFER_TIMEOUT)
        except asyncio.TimeoutError:
            st["pending"].pop(session, None)
            st["sessions"].pop(session, None)
            return err("busy")
        if res.get("error"):
            st["sessions"].pop(session, None)
            return err(res["error"])
        return {"msg_type": "direct_answer", "session": session, "sdp": res["sdp"]}

    async def _dx_close(self, data):
        st = self._dx()
        session = data.get("session")
        s = st["sessions"].get(session)
        peer = data.get(RELAY_SENDER_KEY)
        if s is None or not isinstance(peer, str) or s["peer"] != peer:
            return {"error": "denied"} if s is not None else {"ok": True}
        s["state"] = "closed"
        if st["sidecar"] is not None:
            await st["sidecar"].send({"op": "close", "session": session})
        return {"ok": True}

    # sidecar → kit
    async def _dx_frame(self, h, body):
        st = self._dx()
        op = h.get("op")
        if op in ("answer", "error"):
            fut = st["pending"].pop(h.get("session"), None)
            if fut and not fut.done():
                fut.set_result({"sdp": h.get("sdp")} if op == "answer"
                               else {"error": h.get("code") or "unsupported"})
        elif op == "session":
            s = st["sessions"].get(h.get("session"))
            if s is not None:
                s["state"] = h.get("state", s["state"])
                s["path"] = h.get("path", s["path"])
        elif op == "camera_status":
            st["status"][h.get("id")] = h.get("status")
        elif op == "rpc_request":
            self._dx_spawn(self._dx_rpc(h, body))
        elif op == "log":
            log.log(logging.WARNING if h.get("level") == "warn" else logging.INFO,
                    "carter-direct: %s", h.get("msg"))

    async def _dx_rpc(self, h, body):
        st = self._dx()
        session = h.get("session")
        req = h.get("header") or {}

        def reply(payload, data=None, key=None):
            hdr = {"reply_to": req.get("id"), "type": req.get("type"), "payload": payload}
            if data is not None:
                hdr["body"] = key or "data"
            return st["sidecar"].send({"op": "rpc_reply", "session": session, "header": hdr},
                                      data or b"") if st["sidecar"] else None

        async def done(coro):
            if coro is not None:
                await coro
        s = st["sessions"].get(session)
        if s is None or s["state"] in ("closed", "failed"):
            return await done(reply({"error": "handler_error"}))
        if len(body) > MAX_MESSAGE:
            return await done(reply({"error": "too_large"}))
        mtype = req.get("type")
        if mtype not in self.client._handlers:
            return await done(reply({"error": "unknown_type"}))
        payload = req.get("payload") if isinstance(req.get("payload"), dict) else {}
        if body:
            payload = dict(payload, **{req.get("body") or "data": body})
        ctx = {RELAY_SENDER_KEY: s["peer"], "_from": s["peer"]}
        try:
            res = await self.client.dispatch_request(mtype, payload, ctx, sealed=False)
        except Exception:
            log.exception("direct: handler %r failed", mtype)
            return await done(reply({"error": "handler_error"}))
        res = dict(res) if isinstance(res, dict) else {}
        raw = res.get("data")
        if isinstance(raw, str):
            try:
                raw = base64.b64decode(raw, validate=True)
            except ValueError:
                raw = None
        if isinstance(raw, (bytes, bytearray)):
            res.pop("data", None)
            raw = bytes(raw)
            if len(raw) > MAX_MESSAGE - 4096:
                return await done(reply({"error": "too_large"}))
            return await done(reply(res, raw, "data"))
        await done(reply(res))
