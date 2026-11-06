"""Hub surfaces: progress, toast, haptic and a live log, drawn by the app.

Mixed into :class:`carterkit.hub.Hub` like ``HubExtras``. Each verb is a routed frame to the
device (``progress``, ``toast``, ``haptic``, ``log``); the app's replies come back as
``progress_reply`` / ``toast_reply`` broadcasts. See docs/hub-surfaces.md.

    async with hub.progress("Installing Example package", total=48_000_000, unit="bytes",
                            cancellable=True) as task:
        await task.update(done=1_000_000, detail="Downloading")
        if task.cancelled:
            await task.cancelled_ok()
"""
from __future__ import annotations

import asyncio
import inspect
import logging
import math
import time
import uuid

log = logging.getLogger("carterkit.hub")

UNITS = ("bytes", "items", "none")
SHOWS = ("sheet", "pill", "none")
STATES = ("running", "paused", "done", "failed", "cancelled")
TERMINAL = ("done", "failed", "cancelled")
STYLES = ("info", "success", "warning", "error")
HAPTICS = ("selection", "light", "medium", "heavy", "success", "warning", "error")
LEVELS = ("debug", "info", "notice", "warn", "error")

#: Hub-side coalescing: at most one progress frame per this many seconds per task (4/s).
PROGRESS_MIN_INTERVAL = 0.25
#: Log lines are batched per interval and capped per second (the app's own limit is 200/s).
LOG_BATCH_S = 0.1
LOG_LINES_PER_S = 200
LOG_QUEUE_MAX = 20000


def _err(msg):
    from .hub import HubError
    return HubError(msg)


def _num(v, name, *, lo=0.0, hi=None):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v):
        raise _err(f"{name} must be a finite number, got {v!r}")
    if v < lo or (hi is not None and v > hi):
        raise _err(f"{name} must be {lo}..{hi if hi is not None else 'up'}, got {v!r}")
    return v


def _text(v, name, cap):
    if not isinstance(v, str):
        raise _err(f"{name} must be a string")
    return v[:cap]


def _enum(v, name, allowed):
    if v not in allowed:
        raise _err(f"{name} must be one of {', '.join(allowed)}, got {v!r}")
    return v


def _id(v) -> str:
    if not isinstance(v, str) or not 1 <= len(v) <= 64:
        raise _err("id must be a string of 1-64 characters")
    return v


async def _maybe(fn, *a):
    r = fn(*a)
    if inspect.isawaitable(r):
        r = await r
    return r


class Progress:
    """A running task shown by the app (pill, sheet, Island). Async context manager."""

    def __init__(self, hub, id: str, fields: dict):
        self.hub, self.id = hub, id
        self.frame: dict = {"id": id}
        self.cancelled = False            # set by progress_reply choice "cancel"
        self.dismissed = False            # set by choice "dismissed"
        self.refused: str | None = None   # "busy" when the app turned it away
        self.ended = False
        self.reply: dict | None = None
        self._cancel_cbs: list = []
        self._started = False
        self._last_sent = 0.0
        self._flush_handle = None
        self._beat: asyncio.Task | None = None
        self._merge(fields)

    @property
    def done(self):
        """The count done so far (0 until you send ``done=``)."""
        return self.frame.get("done", 0)

    @property
    def state(self) -> str:
        return self.frame.get("state", "running")

    def on_cancel(self, fn):
        """Call ``fn(task)`` (sync or async) when the person cancels."""
        self._cancel_cbs.append(fn)
        return fn

    # ─── frame building ──────────────────────────────────────────────────────
    def _merge(self, fields: dict) -> None:
        f = self.frame
        for k, v in fields.items():
            if v is None and k != "value":
                continue
            if k == "cancellable":
                if v is False:
                    f["cancel"] = False
                elif not isinstance(f.get("cancel"), dict):
                    f["cancel"] = {}
            elif k in ("ask", "cancel_label"):
                c = f.get("cancel")
                c = dict(c) if isinstance(c, dict) else {}
                c["ask" if k == "ask" else "label"] = _text(v, k, 80 if k == "ask" else 24)
                f["cancel"] = c
            elif k == "value":
                if v is None:
                    f["value"] = None
                else:
                    f["value"] = min(1.0, _num(v, "value"))
                f.pop("done", None)
            elif k in ("done", "total"):
                f[k] = _num(v, k)
                if k == "done":
                    f.pop("value", None)
            elif k == "unit":
                f["unit"] = _enum(v, "unit", UNITS)
            elif k == "state":
                f["state"] = _enum(v, "state", STATES)
            elif k == "show":
                f["show"] = _enum(v, "show", SHOWS)
            elif k == "title":
                f["title"] = _text(v, k, 80)
            elif k == "detail":
                f["detail"] = _text(v, k, 120)
            elif k == "island":
                f["island"] = bool(v)
            elif k == "eta_s":
                f["etaS"] = _num(v, "eta_s", hi=86400)
            elif k == "stale_s":
                f["staleS"] = _num(v, "stale_s", lo=5, hi=300)
            elif k == "step":
                if isinstance(v, (tuple, list)):
                    v = dict(zip(("index", "count", "label"), v))
                if not isinstance(v, dict) or "index" not in v or "count" not in v:
                    raise _err("step needs index and count")
                s = {"index": int(_num(v["index"], "step.index", lo=1)),
                     "count": int(_num(v["count"], "step.count", lo=1, hi=99))}
                if v.get("label"):
                    s["label"] = _text(v["label"], "step.label", 40)
                f["step"] = s
            elif k == "log":
                f["log"] = _id(getattr(v, "id", v))
            elif k == "hub":
                f["hub"] = _text(v, k, 40)
            else:
                raise _err(f"unknown progress field {k!r}")

    # ─── sending ─────────────────────────────────────────────────────────────
    async def start(self) -> "Progress":
        """Open the task (the first frame). ``async with`` and ``await hub.progress(...)``
        both do this."""
        if not self._started:
            self._started = True
            self.hub._surface_register(self)
            await self._send()
        return self

    def __await__(self):
        return self.start().__await__()

    async def _send(self) -> dict:
        if self._flush_handle is not None:
            self._flush_handle.cancel()
            self._flush_handle = None
        self._last_sent = time.monotonic()
        res = await self.hub._route_surface("progress", dict(self.frame))
        self.reply = res
        if res.get("ok") is False:
            if res.get("reason") == "ended":
                self._finish_local()
            elif res.get("reason") == "busy":
                self.refused = "busy"
        if not self.ended and self.frame.get("state", "running") not in TERMINAL:
            self._ensure_beat()
        return res

    def _ensure_beat(self) -> None:
        if self._beat is None:
            try:
                self._beat = asyncio.get_running_loop().create_task(self._heartbeat())
            except RuntimeError:
                pass

    async def _heartbeat(self) -> None:
        # The app marks a task stale after staleS: resend the frame at half that while idle.
        try:
            while not self.ended:
                every = float(self.frame.get("staleS", 30)) / 2
                await asyncio.sleep(max(0.01, every - (time.monotonic() - self._last_sent)))
                if not self.ended and time.monotonic() - self._last_sent >= every - 0.005:
                    try:
                        await self._send()
                    except Exception as e:
                        log.warning("progress %s heartbeat failed: %s", self.id, e)
        except asyncio.CancelledError:
            pass

    def _finish_local(self) -> None:
        self.ended = True
        if self._beat is not None:
            self._beat.cancel()
            self._beat = None
        if self._flush_handle is not None:
            self._flush_handle.cancel()
            self._flush_handle = None
        self.hub._surface_forget(self)

    async def update(self, **fields) -> dict | None:
        """Merge fields (``value``/``done``/``total``/``detail``/``step``/``state``/...) and
        send. Coalesced to ``hub.progress_min_interval`` (4 frames/s): frames inside the gap
        fold into one trailing send, so the newest state is always the last one sent.
        Returns the app's reply, or ``None`` when the send was deferred."""
        if self.ended:
            return None
        self._merge(fields)
        if self.frame.get("state", "running") in TERMINAL:
            self._started = True
            self.hub._surface_register(self)
            res = await self._send()
            self._finish_local()
            return res
        if not self._started:
            await self.start()
            return self.reply
        wait = self.hub.progress_min_interval - (time.monotonic() - self._last_sent)
        if wait <= 0 or "state" in fields:       # a state change is never held back
            return await self._send()
        if self._flush_handle is None:
            loop = asyncio.get_running_loop()
            self._flush_handle = loop.call_later(wait, lambda: loop.create_task(self._flush()))
        return None

    async def _flush(self) -> None:
        self._flush_handle = None
        if not self.ended:
            try:
                await self._send()
            except Exception as e:
                log.warning("progress %s send failed: %s", self.id, e)

    def update_sync(self, **fields):
        """:meth:`update` for code on another thread than the hub's loop."""
        return self.hub._run_sync(self.update(**fields))

    async def pause(self):
        return await self.update(state="paused")

    async def resume(self):
        return await self.update(state="running")

    async def _end(self, state, message, haptic):
        if message or haptic:
            result = {}
            if message:
                result["message"] = _text(message, "message", 120)
            if haptic:
                result["haptic"] = _enum(haptic, "haptic", HAPTICS + ("none",))
            self.frame["result"] = result
        return await self.update(state=state)

    async def finish(self, message: str | None = None, haptic: str | None = None):
        """End as ``done`` with an optional final line and haptic (default ``success``)."""
        return await self._end("done", message, haptic)

    async def fail(self, message: str | None = None, haptic: str | None = None):
        """End as ``failed`` (default haptic ``error``)."""
        return await self._end("failed", message, haptic)

    async def cancelled_ok(self, message: str | None = None):
        """Say the task stopped after the person's Cancel: state ``cancelled``."""
        return await self._end("cancelled", message, None)

    async def __aenter__(self) -> "Progress":
        return await self.start()

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        if not self.ended:
            try:
                await (self.fail() if exc_type else self.finish())
            except Exception as e:
                log.warning("progress %s could not send its end: %s", self.id, e)
                self._finish_local()
        return False

    async def _on_cancel(self) -> None:
        self.cancelled = True
        for fn in list(self._cancel_cbs):
            await _maybe(fn, self)

class LogStream:
    """A live log console the hub appends to. Lines are batched per 100 ms and capped at
    200 lines/s on the hub side; the overflow waits in a queue, never in the app's limit."""

    def __init__(self, hub, id: str, title: str | None, progress: str | None):
        self.hub, self.id = hub, id
        self.title = _text(title, "title", 60) if title else None
        self.progress = _id(getattr(progress, "id", progress)) if progress else None
        self.closed = False
        self.skipped = 0                 # lines the app reported skipping
        self._queue: list[dict] = []
        self._lost = 0
        self._titled = False
        self._pending_clear = False
        self._task: asyncio.Task | None = None

    def _frame(self, **extra) -> dict:
        f: dict = {"id": self.id}
        if self.title and not self._titled:
            f["title"] = self.title
        if self.progress:
            f["progress"] = self.progress
        f.update(extra)
        return f

    def _enqueue(self, text: str, level: str = "info") -> None:
        if self.closed:
            return
        _enum(level, "level", LEVELS)
        if len(self._queue) >= LOG_QUEUE_MAX:
            self._queue.pop(0)
            self._lost += 1
        self._queue.append({"text": str(text), "level": level, "at": round(time.time(), 3)})
        self._ensure_task()

    def _ensure_task(self) -> None:
        if self._task is None or self._task.done():
            try:
                self._task = asyncio.get_running_loop().create_task(self._pump())
            except RuntimeError:
                pass

    async def _pump(self) -> None:
        try:
            while self._queue and not self.closed:
                await asyncio.sleep(LOG_BATCH_S)
                await self._send_batch(int(LOG_LINES_PER_S * LOG_BATCH_S))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.warning("log %s send failed: %s", self.id, e)

    async def _send_batch(self, limit: int | None, **extra) -> dict | None:
        lines, self._queue = (self._queue[:limit], self._queue[limit:]) if limit \
            else (self._queue, [])
        if self._lost and lines:
            lines.insert(0, {"text": f"{self._lost} lines dropped on the hub (queue full)",
                             "level": "warn"})
            self._lost = 0
        if not lines and not extra:
            return None
        frame = self._frame(**extra)
        if lines:
            frame["lines"] = lines
        res = await self.hub._route_surface("log", frame)
        self._titled = True
        if res.get("skipped"):
            self.skipped += int(res["skipped"])
        return res

    async def write(self, text: str, level: str = "info") -> None:
        """Queue one line (the shorthand for a single ``info`` line is the default level)."""
        self._enqueue(text, level)

    async def debug(self, text): await self.write(text, "debug")
    async def info(self, text): await self.write(text, "info")
    async def notice(self, text): await self.write(text, "notice")
    async def warn(self, text): await self.write(text, "warn")
    async def error(self, text): await self.write(text, "error")

    async def flush(self) -> None:
        """Send everything queued now, ignoring the pace (still in frames of 200 lines)."""
        while self._queue:
            await self._send_batch(LOG_LINES_PER_S)

    async def send_title(self) -> dict:
        """The frame that (re)announces the stream with no lines (used on reconnect)."""
        self._titled = False
        res = await self.hub._route_surface("log", self._frame())
        self._titled = True
        return res

    async def open(self) -> bool:
        """Open the console sheet now. Returns True when the app opened it (``busy``
        while the person has a container up is a return, not an error)."""
        await self.flush()
        res = await self._send_batch(None, open=True)
        return bool(res and res.get("opened"))

    async def clear(self) -> None:
        self._queue.clear()
        await self._send_batch(None, clear=True)

    async def close(self) -> None:
        """Flush, then end the stream (kept for reading, marked Ended)."""
        if self.closed:
            return
        await self.flush()
        await self._send_batch(None, close=True)
        self.closed = True
        if self._task is not None:
            self._task.cancel()
        self.hub._surface_forget(self)

    def handler(self, level: int = logging.INFO) -> logging.Handler:
        """A :class:`logging.Handler` that writes records to this stream (thread-safe)."""
        return _LogStreamHandler(self, level)

    async def __aenter__(self) -> "LogStream":
        return self

    async def __aexit__(self, *exc) -> bool:
        await self.close()
        return False


class _LogStreamHandler(logging.Handler):
    _MAP = ((logging.ERROR, "error"), (logging.WARNING, "warn"),
            (logging.INFO, "info"), (0, "debug"))

    def __init__(self, stream: LogStream, level: int):
        super().__init__(level)
        self.stream = stream

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = next(n for t, n in self._MAP if record.levelno >= t)
            msg = self.format(record)
            loop = self.stream.hub.__dict__.get("_loop")
            try:
                here = asyncio.get_running_loop()
            except RuntimeError:
                here = None
            if loop is not None and loop.is_running() and here is not loop:
                loop.call_soon_threadsafe(self.stream._enqueue, msg, level)   # another thread
            else:
                self.stream._enqueue(msg, level)
        except Exception:
            self.handleError(record)


class HubSurfaces:
    """Mixin: progress(), toast(), haptic(), log() and the reconnect resend."""

    #: Seconds between progress frames per task (4/s); the newest state always goes out.
    progress_min_interval = PROGRESS_MIN_INTERVAL

    # ─── plumbing ────────────────────────────────────────────────────────────
    async def _route_surface(self, verb: str, payload: dict) -> dict:
        """Route one surface frame to the device; returns the app's reply. Raises
        :class:`HubError` for ``not-hub`` / ``invalid`` / ``off`` and a missing device;
        ``busy``, ``ended`` and ``played: false`` come back as ordinary replies."""
        peer = await self._first_peer()
        if not peer:
            raise _err("no device on the channel — have the phone connect first")
        payload.setdefault("hub", self.name)
        payload.setdefault("from", self.name)
        res = await self.client._sock.request(
            "route_msg", {"target_id": peer.get("id"), "type": verb, "payload": payload},
            timeout=10.0)
        res = res if isinstance(res, dict) else {}
        if res.get("ok") is False and res.get("reason") in ("not-hub", "invalid", "off"):
            raise _err(f"the app refused the {verb}: {res['reason']}")
        return res

    def _run_sync(self, coro):
        loop = self.__dict__.get("_loop")
        if loop is None or not loop.is_running():
            coro.close()
            raise _err("the *_sync calls need a started hub whose event loop is running")
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is loop:
            coro.close()
            raise _err("a *_sync call would block the hub's own loop; await the async form")
        return asyncio.run_coroutine_threadsafe(coro, loop).result()

    def _surface_state(self) -> dict:
        st = self.__dict__.get("_surfaces_live")
        if st is None:
            st = self.__dict__["_surfaces_live"] = {"progress": {}, "log": {}}
            # progress_reply / toast_reply arrive as broadcasts, like prompt_reply
            for mt, fn in (("progress_reply", self._on_progress_reply),
                           ("toast_reply", self._on_toast_reply)):
                handlers = self._demux.setdefault(mt, [])
                if fn not in handlers:
                    handlers.append(fn)
            self._install_surface_resend()
        return st

    def _surface_register(self, obj) -> None:
        kind = "progress" if isinstance(obj, Progress) else "log"
        self._surface_state()[kind][obj.id] = obj

    def _surface_forget(self, obj) -> None:
        kind = "progress" if isinstance(obj, Progress) else "log"
        self._surface_state()[kind].pop(obj.id, None)

    # ─── reconnect: resend what is live ──────────────────────────────────────
    def _install_surface_resend(self) -> None:
        sock = self.client._sock
        previous = getattr(sock, "on_reconnect_callback", None)

        async def on_reconnect():
            if previous is not None:
                await _maybe(previous)
            await self.resend_surfaces()

        sock.on_reconnect_callback = on_reconnect

        # The phone coming back: the app broadcasts control_sync_request when a layout
        # (re)joins. Resend what is running so a resumed task is not "unmentioned".
        async def on_phone_back(_frame):
            await self.resend_surfaces()

        hooks = self.client._join_hooks
        if on_phone_back not in hooks:
            hooks.append(on_phone_back)

    async def resend_surfaces(self) -> int:
        """Resend every running task's full frame and every open log stream's title (not
        its lines): the app's resume rule. Called on every socket reconnect; callable by
        hand (e.g. when the phone reopens the layout). Returns how many were sent."""
        st = self.__dict__.get("_surfaces_live")
        if not st:
            return 0
        sent = 0
        for obj in list(st["progress"].values()):
            if obj.ended or obj.dismissed:
                continue
            try:
                await obj._send()
                sent += 1
            except Exception as e:
                log.warning("could not resend progress %s: %s", obj.id, e)
        for s in list(st["log"].values()):
            if s.closed:
                continue
            try:
                await s.send_title()
                sent += 1
            except Exception as e:
                log.warning("could not resend log %s: %s", s.id, e)
        return sent

    # ─── replies from the app ────────────────────────────────────────────────
    async def _on_progress_reply(self, data) -> None:
        data = data or {}
        task = self._surface_state()["progress"].get(data.get("id"))
        if task is None:
            return
        to = data.get("to")
        if to is not None and to != self.name:
            return              # another hub's task with the same id; older apps send no `to`
        choice = data.get("choice")
        if choice == "cancel":
            await task._on_cancel()
        elif choice == "dismissed":
            task.dismissed = True
            task._finish_local()
        elif choice == "busy":
            task.refused = "busy"

    async def _on_toast_reply(self, data) -> None:
        data = data or {}
        cbs = self.__dict__.get("_toast_actions", {})
        fn = cbs.get(data.get("id"))
        if fn is not None and data.get("choice") == "action":
            await _maybe(fn, data)

    # ─── progress ────────────────────────────────────────────────────────────
    def progress(self, title: str, *, value: float | None = None, done=None, total=None,
                 unit: str = "none", detail: str | None = None, step=None,
                 cancellable: bool = False, ask: str | None = None,
                 cancel_label: str | None = None, show: str = "pill", island: bool = True,
                 eta_s=None, stale_s=30, log=None, id: str | None = None) -> Progress:
        """A task the app shows (pill, sheet, Dynamic Island). Use ``async with`` (or
        ``await``) to open it; see :class:`Progress`. ``cancellable`` shows Cancel
        (``ask`` makes the app confirm first); the person's cancel sets ``task.cancelled``
        and calls :meth:`Progress.on_cancel` handlers. Updates coalesce to 4 frames/s and a
        running task is resent on reconnect."""
        tid = _id(id) if id is not None else "task-" + uuid.uuid4().hex[:10]
        fields = dict(title=title, unit=unit, show=show, island=island, detail=detail,
                      step=step, eta_s=eta_s, stale_s=stale_s, log=log)
        if value is not None:
            fields["value"] = value
        if done is not None:
            fields["done"] = done
        if total is not None:
            fields["total"] = total
        if cancellable or ask or cancel_label:
            fields["cancellable"] = True
            fields["ask"], fields["cancel_label"] = ask, cancel_label
        fields = {k: v for k, v in fields.items() if v is not None}
        for key, default in (("unit", "none"), ("show", "pill"), ("island", True),
                             ("stale_s", 30)):
            if fields.get(key) == default:       # the app's defaults; keep the frame small
                del fields[key]
        return Progress(self, tid, fields)

    # ─── toast ───────────────────────────────────────────────────────────────
    async def toast(self, title: str, message: str | None = None, *, style: str = "info",
                    duration_s=None, haptic: str | None = None, icon: str | None = None,
                    action=None, on_action=None, id: str | None = None) -> dict:
        """A short message in the app. ``action`` is ``(label, {"log": id})``,
        ``(label, {"progress": id})`` or ``(label, "reply")`` (the app then broadcasts
        ``toast_reply``, which ``on_action(frame)`` or ``@hub.on("toast_reply")`` handles).
        Returns the app's reply (``queued``, ``updated`` or ``merged``; or
        ``{"ok": False, "reason": "busy" | "background"}``)."""
        p: dict = {}
        if id:
            p["id"] = _id(id)
        p["title"] = _text(title, "title", 60)
        if message:
            p["message"] = _text(message, "message", 120)
        if style != "info":
            p["style"] = _enum(style, "style", STYLES)
        if icon:
            p["icon"] = icon
        if duration_s is not None:
            p["durationS"] = _num(duration_s, "duration_s", lo=2, hi=10)
        if haptic:
            p["haptic"] = _enum(haptic, "haptic", HAPTICS + ("none",))
        if action is not None:
            label, what = action
            a: dict = {"label": _text(label, "action label", 16)}
            if what == "reply":
                a["reply"] = True
            elif isinstance(what, dict) and len(what) == 1 and next(iter(what)) in ("log", "progress"):
                a["opens"] = dict(what)
            else:
                raise _err("action is (label, {'log': id} | {'progress': id} | 'reply')")
            p["action"] = a
        if on_action is not None:
            if not p.get("action", {}).get("reply"):
                raise _err("on_action needs action=(label, 'reply')")
            if "id" not in p:
                p["id"] = "toast-" + uuid.uuid4().hex[:10]
            self._surface_state()
            self.__dict__.setdefault("_toast_actions", {})[p["id"]] = on_action
        return await self._route_surface("toast", p)

    def toast_sync(self, *args, **kw) -> dict:
        """Blocking :meth:`toast` for code on another thread."""
        return self._run_sync(self.toast(*args, **kw))

    # ─── haptic ──────────────────────────────────────────────────────────────
    async def haptic(self, pattern: str) -> bool:
        """Play one haptic profile on the phone (only with the app in front). Returns
        True when it played; a coalesced, rate-limited or background haptic is False."""
        res = await self._route_surface(
            "haptic", {"pattern": _enum(pattern, "pattern", HAPTICS)})
        return bool(res.get("played"))

    def haptic_sync(self, pattern: str) -> bool:
        return self._run_sync(self.haptic(pattern))

    # ─── log ─────────────────────────────────────────────────────────────────
    def log(self, id: str, *, title: str | None = None, progress=None) -> LogStream:
        """A live log console stream; ``progress`` links it to a task (that task's sheet
        gets Show log). Remember to pass the stream to ``progress(log=stream)`` too."""
        s = LogStream(self, _id(id), title, progress)
        self._surface_register(s)
        return s
