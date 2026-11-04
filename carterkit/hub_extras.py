"""Hub helpers for the app's generic controls: the confirm prompt and list paging.

Mixed into :class:`carterkit.hub.Hub`. App contracts (ControlDocs `list.md`, app docs
HUB-PROMPT.md): ``hub.confirm()`` sends the routed ``prompt`` frame and awaits the
``prompt_reply`` broadcast; ``@hub.pages(...)`` answers a paged list's request action.
"""
from __future__ import annotations

import asyncio
import inspect
import logging
import uuid

log = logging.getLogger("carterkit.hub")

_TOKENS = ("offset", "limit", "cursor", "query", "req")


def _page_frame(items, *, offset: int, limit: int, cursor, total, query, req) -> dict:
    """The page object a paged list reads: items plus the echoes it matches on."""
    page: dict = {"items": list(items), "offset": offset, "query": query, "req": req}
    if cursor is not None:
        page["cursor"] = cursor
    if total is not None:
        page["total"] = total
    if cursor is not None:
        more = True
    elif total is not None:
        more = offset + len(page["items"]) < total
    else:
        more = len(page["items"]) >= limit
    page["more"] = bool(more)
    return page


class HubExtras:
    """Mixin: confirm() and pages()."""

    # ─── confirm (routed `prompt` → `prompt_reply`) ──────────────────────────
    async def confirm(self, title: str, message: str | None = None, *,
                      confirm_label: str = "OK", destructive: bool = False,
                      cancel_label: str = "Cancel", timeout_s: float = 60) -> str:
        """Ask the user to confirm something in the app's own frame; returns
        ``'confirm'``, ``'cancel'``, ``'timeout'`` or ``'busy'``. Raises
        :class:`HubError` when the app refuses the prompt outright (not this hub's
        layout, invalid request) or no device is on the channel."""
        from .hub import HubError
        waiters = self.__dict__.setdefault("_prompt_waiters", {})
        handlers = self._demux.setdefault("prompt_reply", [])
        if self._on_prompt_reply not in handlers:
            handlers.append(self._on_prompt_reply)
        peer = await self._first_peer()
        if not peer:
            raise HubError("no device on the channel — have the phone connect first")
        timeout_s = max(5, min(300, timeout_s))
        pid = uuid.uuid4().hex[:16]
        payload: dict = {"id": pid, "title": title[:80], "hub": self.name,
                         "from": self.name, "timeoutS": timeout_s,
                         "confirm": {"label": confirm_label,
                                     "role": "destructive" if destructive else "default"},
                         "cancel": {"label": cancel_label}}
        if message:
            payload["message"] = message
        fut = asyncio.get_running_loop().create_future()
        waiters[pid] = fut
        try:
            res = await self.client._sock.request(
                "route_msg", {"target_id": peer.get("id"), "type": "prompt",
                              "payload": payload}, timeout=10.0)
            if isinstance(res, dict) and res.get("ok") is False:
                if res.get("reason") == "busy":
                    return "busy"
                raise HubError(f"the app refused the prompt: {res.get('reason') or 'no reason'}")
            try:
                return await asyncio.wait_for(fut, timeout_s + 5)
            except asyncio.TimeoutError:
                return "timeout"
        finally:
            waiters.pop(pid, None)

    def confirm_sync(self, *args, **kw) -> str:
        """Blocking :meth:`confirm` for code on another thread than the hub's event
        loop (the loop the hub started on)."""
        from .hub import HubError
        loop = self.__dict__.get("_loop")
        if loop is None or not loop.is_running():
            raise HubError("confirm_sync needs a started hub whose event loop is running")
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is loop:
            raise HubError("confirm_sync would block the hub's own loop; await confirm()")
        return asyncio.run_coroutine_threadsafe(self.confirm(*args, **kw), loop).result()

    def _on_prompt_reply(self, data) -> None:
        fut = self.__dict__.get("_prompt_waiters", {}).get((data or {}).get("id"))
        if fut is not None and not fut.done():
            fut.set_result(data.get("choice") or "cancel")

    # ─── list paging ─────────────────────────────────────────────────────────
    def _paged_list(self, target) -> dict:
        from .hub import HubError
        ctrl = None
        if isinstance(target, str) and target in self._index:
            ctrl = self._index[target]
        elif isinstance(target, str):
            for c in self._index.values():
                if isinstance(c.get("paging"), dict) and c["paging"].get("replyType") == target:
                    ctrl = c
                    break
        else:
            ctrl = self._control(target)
        if not ctrl or not isinstance(ctrl.get("paging"), dict):
            raise HubError(f"no list with `paging` matches {target!r} — give pages() a "
                           f"paged list's id or its paging.replyType")
        return ctrl

    def pages(self, target, fn=None):
        """Answer a paged list. ``target`` is the list (handle or id) or its
        ``paging.replyType``. The handler gets ``(offset, limit, cursor, query)`` and
        returns the page's items, or ``(items, next_cursor, total)``; it may be sync
        or async. The reply is broadcast as the list's ``replyType`` with the
        request's ``req``/``query`` echoed. Usable as ``@hub.pages("catalogue")``."""
        if fn is None:
            return lambda f: self.pages(target, f) or f
        from .hub import HubError, _set_path
        ctrl = self._paged_list(target)
        paging = ctrl["paging"]
        req_action = paging.get("request") or {}
        payload = req_action.get("payload") if isinstance(req_action, dict) else None
        mt = isinstance(payload, dict) and payload.get("msg_type")
        if not mt:
            raise HubError(f"list '{ctrl.get('id')}' paging.request has no payload msg_type "
                           f"— nothing to demux on")
        keys = {tok: tok for tok in _TOKENS}           # token -> payload key
        for k, v in payload.items():
            if isinstance(v, str) and v.startswith("{{") and v.endswith("}}") \
                    and v[2:-2].strip() in _TOKENS:
                keys[v[2:-2].strip()] = k
        reply_type = paging.get("replyType")
        if not reply_type:
            raise HubError(f"list '{ctrl.get('id')}' paging has no replyType")
        reply_path = paging.get("replyPath")
        default_limit = int(paging.get("pageSize") or 50)

        async def _serve(data):
            def get(tok):
                return data.get(keys[tok])
            try:
                offset = int(get("offset") or 0)
                limit = int(get("limit") or default_limit)
            except (TypeError, ValueError):
                log.warning("page request with a non-numeric offset/limit ignored: %r", data)
                return
            cursor, query, req = get("cursor"), get("query") or "", get("req")
            try:
                res = fn(offset, limit, cursor, query)
                if inspect.isawaitable(res):
                    res = await res
            except Exception:
                log.exception("pages handler for %r failed", ctrl.get("id"))
                return                                  # the list re-asks after 8 s
            nxt = total = None
            if isinstance(res, tuple):
                items, nxt, total = (list(res) + [None, None])[:3]
            else:
                items = res
            page = _page_frame(items or [], offset=offset, limit=limit, cursor=nxt,
                               total=total, query=query, req=req)
            frame: dict = {"req": req}
            if reply_path:
                _set_path(frame, reply_path, page)
            else:
                frame.update(page)
            await self.broadcast(reply_type, frame)

        self._demux.setdefault(mt, []).append(_serve)
        return fn
