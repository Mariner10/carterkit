"""AgentPager — approve or deny agent tool requests from the phone (phase 0).

A small daemon core built on a carterkit ``Hub``: a local hook (Claude Code
``PermissionRequest``/``PreToolUse``) connects to a Unix socket, sends one JSON line
``{"agent", "tool", "summary"}`` and blocks until it reads ``{"decision", "reason"}``
back. The pager pages the phone with an Approve/Deny notification whose
``notif_id`` is a per-request nonce, and resolves the request from:

- a notification tap (``on_notif_action``: ``notifId`` = nonce, ``actionId``
  ``approve``/``deny``), or
- an in-app button frame ``{"msg_type": "action", "op": "pager_decide",
  "decision": "approve"|"deny", "req": <nonce>}``, or
- the deadline, which always denies.

It FAILS CLOSED: only an explicit approve carrying the live nonce of the active
request, before its deadline, ever yields ``allow``. A missing / non-string /
unknown nonce, an unknown action or decision, a late tap, a restart, a client
disconnect, or a notify failure never allows anything.

Use a personal, non-room channel: in an E2EE room ``strict_e2ee`` drops the app's
plaintext tap frames (they would fail closed, i.e. deny on the deadline).
"""
from __future__ import annotations

import asyncio
import collections
import json
import logging
import os
import tempfile
import time
import uuid
from pathlib import Path

log = logging.getLogger("carterkit.pager")

ALLOW, DENY = "allow", "deny"
DEFAULT_DIR = Path("~/.carter/pager")
DEFAULT_TIMEOUT = 90.0
SUMMARY_MAX = 120          # body text rides APNs in plaintext: keep it short
AUDIT_MAX = 500            # audit entries kept in memory for the logConsole
CLOSED_MAX = 1000          # resolved nonces remembered to answer late taps
LINE_MAX = 64 * 1024       # one request line from the hook

# The ONLY accepted decision / actionId spellings. Anything else is ignored.
_DECISIONS = {"approve": ALLOW, "deny": DENY}


class PendingStore:
    """Pending requests on disk, keyed by nonce: ``{agent, tool, summary, created,
    deadline, state}``. The file is mode 0600 inside a 0700 directory and every
    write is atomic (temp file + ``os.replace``), so a crash never leaves a torn
    file. Its only job is restart safety: whatever is in it at startup was pending
    when the daemon died and is denied."""

    def __init__(self, path=None):
        self.path = Path(path).expanduser() if path else (DEFAULT_DIR / "pending.json").expanduser()
        self._data: dict[str, dict] = {}

    def load(self) -> dict:
        try:
            raw = json.loads(self.path.read_text())
        except FileNotFoundError:
            raw = {}
        except (OSError, ValueError) as e:
            log.warning("pager: unreadable pending store %s (%s); starting empty", self.path, e)
            raw = {}
        self._data = {k: v for k, v in raw.items()
                      if isinstance(k, str) and isinstance(v, dict)} if isinstance(raw, dict) else {}
        return dict(self._data)

    def items(self) -> dict:
        return dict(self._data)

    def put(self, nonce, record) -> None:
        self._data[nonce] = dict(record)
        self._write()

    def update(self, nonce, **fields) -> None:
        if nonce in self._data:
            self._data[nonce].update(fields)
            self._write()

    def remove(self, nonce) -> None:
        if self._data.pop(nonce, None) is not None:
            self._write()

    def clear(self) -> None:
        self._data = {}
        self._write()

    def _write(self) -> None:
        parent = self.path.parent
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".pending-", suffix=".tmp", dir=parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w") as fh:
                json.dump(self._data, fh, indent=1)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self.path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise


class _Request:
    __slots__ = ("nonce", "agent", "tool", "summary", "created", "deadline",
                 "state", "future", "timer")

    def __init__(self, agent, tool, summary, loop):
        self.nonce = "pg" + uuid.uuid4().hex
        self.agent, self.tool, self.summary = agent, tool, summary
        self.created = time.time()
        self.deadline = None
        self.state = "queued"
        self.future = loop.create_future()
        self.timer = None

    def record(self) -> dict:
        return {"agent": self.agent, "tool": self.tool, "summary": self.summary,
                "created": self.created, "deadline": self.deadline, "state": self.state}


def _clip(text, n) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "…"

class AgentPager:
    """Fail-closed approval pager on top of a carterkit ``Hub`` (or anything with
    ``notify``, ``on_notif_action``, ``on(name, fn)`` and ``broadcast``).

    ``await pager.start()`` restores the store (denying every leftover request),
    wires the decision handlers and opens the Unix socket; ``await pager.ask(agent,
    tool, summary)`` returns ``"allow"`` or ``"deny"``. One request per agent is
    active (paged, with a deadline); later requests from the same agent queue FIFO
    behind it."""

    def __init__(self, hub, *, timeout=DEFAULT_TIMEOUT, store_path=None, socket_path=None,
                 status_msg_type="pager"):
        if timeout is None or timeout <= 0:
            raise ValueError("timeout must be > 0 (the deadline is what makes it fail closed)")
        self.hub = hub
        self.timeout = float(timeout)
        self.store = PendingStore(store_path)
        self.socket_path = (Path(socket_path).expanduser() if socket_path
                            else (DEFAULT_DIR / "pager.sock").expanduser())
        self.status_msg_type = status_msg_type
        self._queues: dict[str, collections.deque] = {}
        self._active: dict[str, _Request] = {}           # nonce -> active request
        self._closed: collections.OrderedDict = collections.OrderedDict()  # nonce -> decision
        self._audit: collections.deque = collections.deque(maxlen=AUDIT_MAX)
        self._tasks: set = set()
        self._server = None
        self._wired = False

    # ─── lifecycle ──────────────────────────────────────────────────────────
    async def start(self, *, serve_socket=True):
        self.restore()
        self.wire()
        if serve_socket:
            await self.serve()
        await self._push_status("started")
        return self

    def wire(self):
        """Register the notification-tap catch-all and the in-app action demux."""
        if self._wired:
            return
        self.hub.on_notif_action(self.handle_notif_action)
        self.hub.on("action", self.handle_action)
        self._wired = True

    def restore(self) -> list:
        """Deny every request persisted by a previous run: its hook connection is
        gone, so nothing can be waiting for an answer. Late taps for those nonces
        are answered "expired"."""
        now = time.time()
        denied = []
        for nonce, rec in self.store.load().items():
            deadline = rec.get("deadline")
            expired = isinstance(deadline, (int, float)) and deadline <= now
            reason = "expired before restart" if expired else "orphaned by restart"
            self._remember(nonce, DENY)
            self._record(nonce, rec.get("agent"), rec.get("tool"), rec.get("summary"),
                         DENY, reason, "restart")
            denied.append(nonce)
        if denied or self.store.path.exists():
            self.store.clear()
        return denied

    async def stop(self):
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
            try:
                if self.socket_path.is_socket():
                    self.socket_path.unlink()
            except OSError:
                pass
        for queue in list(self._queues.values()):
            for req in reversed(list(queue)):   # tail first: nothing new activates
                self._resolve(req, DENY, "pager stopped", "shutdown")
        for task in list(self._tasks):
            task.cancel()

    # ─── asking ─────────────────────────────────────────────────────────────
    async def ask(self, agent, tool, summary="") -> str:
        decision, _reason = await self.ask_detailed(agent, tool, summary)
        return decision

    async def ask_detailed(self, agent, tool, summary=""):
        """``(decision, reason)``. Cancelling the awaiting task withdraws the request
        (a withdrawn request is denied, never allowed)."""
        req = self.submit(agent, tool, summary)
        try:
            return await asyncio.shield(req.future)
        except asyncio.CancelledError:
            self.withdraw(req)
            raise

    def submit(self, agent, tool, summary="") -> _Request:
        if not isinstance(agent, str) or not agent.strip():
            raise ValueError("agent must be a non-empty string")
        if not isinstance(tool, str) or not tool.strip():
            raise ValueError("tool must be a non-empty string")
        summary = "" if summary is None else str(summary)
        req = _Request(agent.strip(), tool.strip(), summary, asyncio.get_running_loop())
        queue = self._queues.setdefault(req.agent, collections.deque())
        queue.append(req)
        self.store.put(req.nonce, req.record())
        if len(queue) == 1:
            self._activate(req)
        else:
            self._spawn(self._push_status("queued", req))
        return req

    def withdraw(self, req) -> None:
        if not req.future.done():
            self._resolve(req, DENY, "withdrawn: requester disconnected", "withdraw")

    # ─── the active request ────────────────────────────────────────────────
    def _activate(self, req) -> None:
        loop = asyncio.get_running_loop()
        req.state = "waiting"
        req.deadline = time.time() + self.timeout
        req.timer = loop.call_later(self.timeout, self._on_deadline, req)
        self._active[req.nonce] = req
        self.store.update(req.nonce, state=req.state, deadline=req.deadline)
        self._spawn(self._page(req))

    def _on_deadline(self, req) -> None:
        if not req.future.done():
            self._resolve(req, DENY, f"timed out after {self.timeout:g}s", "deadline")

    def _resolve(self, req, decision, reason, source) -> None:
        """The single exit for a request. Idempotent; activates the agent's next."""
        if req.future.done():
            return
        if req.timer is not None:
            req.timer.cancel()
        req.state = "resolved"
        self._active.pop(req.nonce, None)
        self._remember(req.nonce, decision)
        queue = self._queues.get(req.agent)
        was_head = bool(queue) and queue[0] is req
        if queue is not None:
            try:
                queue.remove(req)
            except ValueError:
                pass
        self.store.remove(req.nonce)
        req.future.set_result((decision, reason))
        self._record(req.nonce, req.agent, req.tool, req.summary, decision, reason, source)
        log.info("pager: %s %s %s (%s via %s)", req.agent, req.tool, decision, reason, source)
        self._spawn(self._push_status("resolved", req, decision=decision, reason=reason))
        if queue is not None and not queue:
            self._queues.pop(req.agent, None)
        elif queue and was_head:
            self._activate(queue[0])

    # ─── decisions ──────────────────────────────────────────────────────────
    def decide(self, nonce, decision, source="api") -> str:
        """Apply a decision to the request with ``nonce``. Returns ``"allowed"``,
        ``"denied"``, ``"expired"`` (already resolved/timed out: nothing happens)
        or ``"ignored"`` (malformed / unknown). Only ``"allowed"`` ever allows."""
        if not isinstance(nonce, str) or not nonce:
            log.warning("pager: ignoring %s decision with bad nonce %r", source, nonce)
            return "ignored"
        if not isinstance(decision, str) or decision not in _DECISIONS:
            log.warning("pager: ignoring unknown %s decision %r for %s", source, decision, nonce)
            return "ignored"
        req = self._active.get(nonce)
        if req is None or req.future.done():
            if nonce in self._closed:
                log.warning("pager: late %s %r for %s: expired, not applied",
                            source, decision, nonce)
                self._record(nonce, None, None, None, self._closed[nonce],
                             f"late {decision} ignored (expired)", source)
                self._spawn(self._push_status("expired", nonce=nonce, decision=decision))
                return "expired"
            log.warning("pager: ignoring %s decision for unknown nonce %s", source, nonce)
            return "ignored"
        if time.time() >= req.deadline:     # timer not yet fired, deadline passed
            self._resolve(req, DENY, f"timed out after {self.timeout:g}s", "deadline")
            return "expired"
        verdict = _DECISIONS[decision]
        reason = "approved from CAR-TER" if verdict == ALLOW else "denied from CAR-TER"
        self._resolve(req, verdict, reason, source)
        return "allowed" if verdict == ALLOW else "denied"

    def handle_notif_action(self, data):
        """``on_notif_action`` catch-all: ``notifId`` is the nonce."""
        if not isinstance(data, dict):
            return "ignored"
        return self.decide(data.get("notifId"), data.get("actionId"), "notification")

    def handle_action(self, data):
        """``{msg_type: "action", op: "pager_decide", decision, req}`` from the app.
        Other ``action`` ops belong to other controls and are left alone."""
        if not isinstance(data, dict) or data.get("op") != "pager_decide":
            return None
        return self.decide(data.get("req"), data.get("decision"), "in-app")

    # ─── paging + status ────────────────────────────────────────────────────
    def notification(self, req) -> tuple:
        """``(title, body)`` for a request. The body rides APNs in plaintext on a
        non-room channel, so it carries the tool plus at most 120 summary chars."""
        title = _clip(f"{req.agent} wants to run {req.tool}", 200)
        summary = _clip(req.summary, SUMMARY_MAX)
        body = _clip(f"{req.tool}: {summary}" if summary else req.tool, 250)
        return title, body

    async def _page(self, req) -> None:
        """Send the Approve/Deny push. Any failure (no validator, local relay,
        network) only loses the push: the request stays answerable in-app and the
        deadline still denies it."""
        await self._push_status("waiting", req)
        title, body = self.notification(req)
        actions = {
            "approve": {"title": "Approve", "destructive": True,
                        "authentication_required": True},
            "deny": {"title": "Deny"},
        }
        for level in ("time-sensitive", "active"):
            if req.future.done():
                return
            try:
                await self.hub.notify(title, body, notif_id=req.nonce, actions=actions,
                                      interruption=level)
                return
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001 — any notify failure is non-fatal
                log.warning("pager: notify (%s) failed for %s: %s", level, req.nonce, e)
        log.warning("pager: no push for %s; answer in-app or it denies at the deadline",
                    req.nonce)

    def status(self) -> dict:
        """Snapshot for the layout: active requests and queue depth per agent."""
        agents = {}
        for agent, queue in self._queues.items():
            head = queue[0] if queue else None
            agents[agent] = {
                "tool": head.tool if head else None,
                "req": _clip(head.summary, 40) if head else None,
                "nonce": head.nonce if head and head.state == "waiting" else None,
                "deadline": head.deadline if head else None,
                "waiting": max(0, len(queue) - 1),
            }
        return {"status": "waiting" if self._active else "idle", "agents": agents}

    async def _push_status(self, event, req=None, **extra) -> None:
        frame = {"event": event, **self.status(), **extra}
        if req is not None:
            frame.update(agent=req.agent, tool=req.tool, nonce=req.nonce,
                         deadline=req.deadline)
        if self._audit:
            last = self._audit[-1]
            frame["log"] = {"text": last["text"],
                            "level": "info" if last["decision"] == ALLOW else "warning"}
        try:
            await self.hub.broadcast(self.status_msg_type, frame)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001 — status is best-effort
            log.debug("pager: status push failed: %s", e)

    # ─── audit ──────────────────────────────────────────────────────────────
    @property
    def audit(self) -> list:
        """Decisions, oldest first: ``{ts, nonce, agent, tool, summary, decision,
        reason, source, text}``; ``text`` is a ready logConsole line."""
        return [dict(e) for e in self._audit]

    def pending(self) -> list:
        return [req.record() | {"nonce": req.nonce}
                for queue in self._queues.values() for req in queue]

    def _record(self, nonce, agent, tool, summary, decision, reason, source) -> None:
        ts = time.time()
        who = f"{agent} {tool}" if agent else nonce
        self._audit.append({
            "ts": ts, "nonce": nonce, "agent": agent, "tool": tool, "summary": summary,
            "decision": decision, "reason": reason, "source": source,
            "text": f"{time.strftime('%H:%M:%S', time.localtime(ts))} {decision.upper()} "
                    f"{who}: {reason}"})

    def _remember(self, nonce, decision) -> None:
        self._closed[nonce] = decision
        while len(self._closed) > CLOSED_MAX:
            self._closed.popitem(last=False)

    def _spawn(self, coro):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:            # no loop (sync shutdown path): drop it
            coro.close()
            return None
        task = loop.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    # ─── Unix-socket ask API ────────────────────────────────────────────────
    async def serve(self):
        """Listen on ``socket_path`` (0600, parent dir 0700). One connection = one
        request: a JSON line ``{agent, tool, summary}`` in, ``{decision, reason}``
        out. Closing the connection early withdraws the request."""
        path = self.socket_path
        if len(os.fsencode(str(path))) > 100:
            raise ValueError(f"socket path too long for AF_UNIX (keep it < 100 bytes): {path}")
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if path.is_socket():
            try:        # a live daemon still answers: refuse to steal its socket
                _r, w = await asyncio.open_unix_connection(str(path))
            except OSError:
                path.unlink()               # stale socket from a dead daemon
            else:
                w.close()
                try:
                    await w.wait_closed()
                except OSError:
                    pass
                raise RuntimeError(f"another pager is already listening on {path}")
        elif path.exists() or path.is_symlink():
            raise FileExistsError(f"{path} exists and is not a socket")
        self._server = await asyncio.start_unix_server(self._handle_conn, path=str(path),
                                                       limit=LINE_MAX)
        os.chmod(path, 0o600)
        return self._server

    async def _handle_conn(self, reader, writer):
        req = None
        try:
            try:
                line = await asyncio.wait_for(reader.readline(), 10)
                msg = json.loads(line) if line.strip() else None
                if not isinstance(msg, dict):
                    raise ValueError("expected one JSON object line")
                req = self.submit(msg.get("agent"), msg.get("tool"), msg.get("summary", ""))
            except (ValueError, TypeError, asyncio.TimeoutError) as e:
                await self._reply(writer, DENY, f"bad request: {e}")
                return
            watcher = asyncio.ensure_future(_drain_until_eof(reader))
            try:
                await asyncio.wait({req.future, watcher},
                                   return_when=asyncio.FIRST_COMPLETED)
            finally:
                watcher.cancel()
            if not req.future.done():       # the requester hung up first
                self.withdraw(req)
                return
            decision, reason = req.future.result()
            await self._reply(writer, decision, reason)
        except asyncio.CancelledError:
            if req is not None:
                self.withdraw(req)
            raise
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except (OSError, asyncio.CancelledError):
                pass

    @staticmethod
    async def _reply(writer, decision, reason):
        try:
            writer.write(json.dumps({"decision": decision, "reason": reason}).encode() + b"\n")
            await writer.drain()
        except (OSError, RuntimeError):
            pass


async def _drain_until_eof(reader):
    try:
        while await reader.read(4096):
            pass
    except OSError:
        pass

def ask_via_socket(agent, tool, summary="", *, socket_path=None, timeout=None):
    """Blocking stdlib client for the ask API: ``(decision, reason)``. Raises on
    any transport or protocol error — callers (the hook) must treat an exception
    as "no answer" and never as allow."""
    import socket as _socket
    path = str(Path(socket_path).expanduser() if socket_path
               else (DEFAULT_DIR / "pager.sock").expanduser())
    with _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect(path)
        s.sendall(json.dumps({"agent": agent, "tool": tool, "summary": summary}).encode()
                  + b"\n")
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
    reply = json.loads(buf)
    decision = reply.get("decision") if isinstance(reply, dict) else None
    if decision not in (ALLOW, DENY):
        raise ValueError(f"bad pager reply: {reply!r}")
    return decision, reply.get("reason", "")


# ─── layout ─────────────────────────────────────────────────────────────────
PAGER_LAYOUT_ID = "agent-pager"


def build_pager_layout(connection=None, *, msg_type="pager") -> dict:
    """A minimal one-tab "Agents" layout (plain JSON, no code) that shows the
    pager's status frames: overall status, the waiting agent + tool, and the
    decision log. Approvals come from the notification's Approve/Deny buttons in
    phase 0 (an in-app button can't carry the nonce yet — K4/phase 2 add that).

    ``connection``: a :class:`~carterkit.connection.Connection` (or anything
    ``Connection.parse`` takes); when given, its app-side ``connection`` block is
    embedded (a Connect+ device token never is — see ``layout_block``)."""
    def listen(path):
        return [{"method": "meshsocket", "type": "listen", "event": "broadcast",
                 "filter": {"msg_type": msg_type}, "valuePath": path}]

    children = [
        {"id": "pg-status", "type": "statusLight", "label": "Pager",
         "position": [0, 0], "span": [1, 2], "sync": listen("status")},
        {"id": "pg-agent", "type": "label", "label": "Agent", "text": "—",
         "position": [0, 2], "span": [1, 2], "sync": listen("agent")},
        {"id": "pg-tool", "type": "label", "label": "Request", "text": "—",
         "position": [1, 0], "span": [1, 4], "sync": listen("tool")},
        {"id": "pg-log", "type": "logConsole", "label": "Decisions",
         "position": [2, 0], "span": [3, 4], "maxLines": 200,
         "logColors": {"info": "#34C759", "warning": "#FF9500"},
         "sync": listen("log")},
    ]
    layout = {
        "id": PAGER_LAYOUT_ID,
        "name": "Agents",
        "version": 1,
        "state": {"acks": True},
        "tabs": [{"id": "agents", "title": "Agents", "icon": "hand.raised",
                  "grid": {"columns": 4, "rows": 5}, "children": children}],
    }
    if connection is not None:
        from .connection import Connection
        conn = connection if isinstance(connection, Connection) else Connection.parse(connection)
        if conn.kind != "local":
            layout["connection"] = conn.layout_block(name="Agents")
    return layout
