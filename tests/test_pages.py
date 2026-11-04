"""@hub.pages(): answer a paged list's request action."""
import asyncio

import pytest

from carterkit import Hub, HubError
from test_hub import _FakeSock

REQ = {"method": "meshsocket", "event": "broadcast_request",
       "payload": {"msg_type": "cat_pages", "off": "{{offset}}", "limit": "{{limit}}",
                   "cursor": "{{cursor}}", "query": "{{query}}", "req": "{{req}}"}}


def _hub(**paging):
    paging = {"pageSize": 2, "replyType": "cat_page", "request": REQ, **paging}
    layout = {"name": "L", "tabs": [{"id": "t", "title": "T", "children": [
        {"type": "list", "id": "cat", "position": [0, 0], "span": [2, 2], "paging": paging}]}]}
    hub = Hub(layout)
    hub.client._sock = _FakeSock()
    return hub


def _ask(hub, **kw):
    req = {"msg_type": "cat_pages", "off": 0, "limit": 2, "cursor": None, "query": "", "req": "r1"}
    req.update(kw)
    asyncio.run(hub._dispatch(req))
    return [p for t, p in hub.client._sock.sent if t == "broadcast_request"]


def test_items_only_infers_more_from_limit():
    hub = _hub()

    @hub.pages("cat")
    def _(offset, limit, cursor, query):
        return ["a", "b"][:limit]
    (frame,) = _ask(hub)
    assert frame["msg_type"] == "cat_page" and frame["req"] == "r1"
    assert frame["items"] == ["a", "b"] and frame["more"] is True
    assert frame["offset"] == 0 and frame["query"] == ""


def test_tuple_cursor_total_and_replytype_target():
    hub = _hub()
    seen = {}

    @hub.pages("cat_page")                      # by replyType
    async def _(offset, limit, cursor, query):
        seen.update(offset=offset, cursor=cursor, query=query)
        return [{"id": 1}], "next", 10
    (frame,) = _ask(hub, off=4, cursor="c", query="q")
    assert seen == {"offset": 4, "cursor": "c", "query": "q"}
    assert frame["cursor"] == "next" and frame["total"] == 10 and frame["more"] is True
    assert frame["offset"] == 4 and frame["query"] == "q"


def test_total_reached_ends_list():
    hub = _hub()
    hub.pages("cat", lambda o, l, c, q: (["z"], None, 5))
    (frame,) = _ask(hub, off=4)
    assert frame["more"] is False and "cursor" not in frame


def test_reply_path_wraps_the_page():
    hub = _hub(replyPath="result")
    hub.pages("cat", lambda o, l, c, q: ["a"])
    (frame,) = _ask(hub)
    assert frame["req"] == "r1" and frame["result"]["items"] == ["a"]
    assert "items" not in frame


def test_handler_error_sends_nothing_and_unknown_target_raises():
    hub = _hub()

    def boom(o, l, c, q):
        raise ValueError("x")
    hub.pages("cat", boom)
    assert _ask(hub) == []
    with pytest.raises(HubError):
        hub.pages("nope", lambda *a: [])
