"""Hub.open_sheet()/close_sheet(): routed `sheet` frame, `sheet_closed` broadcast."""
import asyncio

import pytest

from carterkit import Layout, HubError
from test_hub import _FakeSock


class _Sock(_FakeSock):
    def __init__(self, reply=None):
        super().__init__()
        self.reply = reply

    async def request(self, t, payload=None, timeout=5.0):
        self.sent.append(("REQ:" + t, payload))
        if t == "get_nodes":
            return {"clients": [{"id": "dev1", "name": "phone"}]}
        if t == "route_msg" and payload["type"] == "sheet":
            return self.reply or {"ok": True, "id": payload["payload"]["id"]}
        return None


def _hub(reply=None):
    with Layout("P") as ui:
        with ui.tab("T"):
            ui.slider("s", send="x")
    hub = ui.serve()
    hub.client._sock = _Sock(reply)
    return hub


def _sent(hub):
    return [p for t, p in hub.client._sock.sent if t == "REQ:route_msg"][-1]


def test_open_sheet_group_id():
    hub = _hub()
    sid = asyncio.run(hub.open_sheet(group_id="pkg", title="Example", style="sheet"))
    s = _sent(hub)
    assert s["target_id"] == "dev1" and s["type"] == "sheet"
    assert s["payload"] == {"id": sid, "groupId": "pkg", "title": "Example",
                            "style": "sheet", "from": hub.name}


def test_open_sheet_own_group_and_same_id_updates():
    hub = _hub({"ok": True, "id": "pkg-7", "updated": True})
    g = {"grid": {"columns": 4, "rows": 1},
         "children": [{"type": "label", "position": [0, 0], "text": "Hello"}]}
    assert asyncio.run(hub.open_sheet(group=g, id="pkg-7")) == "pkg-7"
    p = _sent(hub)["payload"]
    assert p["id"] == "pkg-7" and p["group"]["type"] == "group"
    assert p["group"]["children"] == g["children"] and "groupId" not in p


def test_open_sheet_argument_errors():
    hub = _hub()
    with pytest.raises(HubError):
        asyncio.run(hub.open_sheet())
    with pytest.raises(HubError):
        asyncio.run(hub.open_sheet(group_id="a", group={}))
    with pytest.raises(HubError, match="style"):
        asyncio.run(hub.open_sheet(group_id="a", style="popup"))


@pytest.mark.parametrize("reason", ["not-hub", "invalid", "not-found", "busy"])
def test_open_sheet_refusal_raises(reason):
    with pytest.raises(HubError, match=reason):
        asyncio.run(_hub({"ok": False, "reason": reason}).open_sheet(group_id="a"))


def test_close_sheet():
    hub = _hub({"ok": True, "id": "x", "closed": True})
    assert asyncio.run(hub.close_sheet("x")) is True
    assert _sent(hub)["payload"] == {"id": "x", "close": True, "from": hub.name}
    with pytest.raises(HubError, match="not-found"):
        asyncio.run(_hub({"ok": False, "id": "x", "reason": "not-found"}).close_sheet("x"))


def test_sheet_closed_reaches_on_handler():
    async def run():
        hub = _hub()
        got = []
        hub.on("sheet_closed", lambda d: got.append(d))
        await hub._dispatch({"msg_type": "sheet_closed", "id": "x", "reason": "user"})
        return got
    assert asyncio.run(run())[0]["reason"] == "user"
