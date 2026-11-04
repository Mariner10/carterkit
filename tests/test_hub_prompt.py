"""Hub.confirm(): routed `prompt`, answered by the `prompt_reply` broadcast."""
import asyncio

import pytest

from carterkit import Layout, HubError
from test_hub import _FakeSock


class _Sock(_FakeSock):
    def __init__(self, hub_holder, answer=None, reply=None):
        super().__init__()
        self.holder, self.answer, self.prompt_reply = hub_holder, answer, reply

    async def request(self, t, payload=None, timeout=5.0):
        self.sent.append(("REQ:" + t, payload))
        if t == "get_nodes":
            return {"clients": [{"id": "dev1", "name": "phone"}]}
        if t == "route_msg" and payload["type"] == "prompt":
            if self.answer:
                p = payload["payload"]
                asyncio.get_running_loop().call_later(0.01, lambda: asyncio.ensure_future(
                    self.holder[0]._dispatch({"msg_type": "prompt_reply", "id": p["id"],
                                              "choice": self.answer, "from": "phone"})))
            return self.prompt_reply or {"ok": True, "queued": 0}
        return None


def _hub(answer=None, reply=None):
    with Layout("P") as ui:
        with ui.tab("T"):
            ui.slider("s", send="x")
    hub = ui.serve()
    holder = [hub]
    hub.client._sock = _Sock(holder, answer, reply)
    return hub


def _prompt_sent(hub):
    return [p for t, p in hub.client._sock.sent if t == "REQ:route_msg"][0]


@pytest.mark.parametrize("choice", ["confirm", "cancel", "timeout", "busy"])
def test_confirm_returns_the_choice(choice):
    hub = _hub(answer=choice)
    assert asyncio.run(hub.confirm("Remove?", "Later", confirm_label="Remove",
                                   destructive=True, cancel_label="Keep")) == choice
    sent = _prompt_sent(hub)
    assert sent["target_id"] == "dev1" and sent["type"] == "prompt"
    p = sent["payload"]
    assert p["title"] == "Remove?" and p["message"] == "Later"
    assert p["confirm"] == {"label": "Remove", "role": "destructive"}
    assert p["cancel"] == {"label": "Keep"} and p["timeoutS"] == 60 and p["from"] == hub.name


def test_confirm_busy_immediate_and_refusal():
    assert asyncio.run(_hub(reply={"ok": False, "id": "x", "reason": "busy"}).confirm("t")) == "busy"
    with pytest.raises(HubError, match="not-hub"):
        asyncio.run(_hub(reply={"ok": False, "reason": "not-hub"}).confirm("t"))


def test_confirm_without_reply_times_out_and_clamps(monkeypatch):
    hub = _hub()
    real = asyncio.wait_for

    async def quick(fut, t):
        assert t == 5 + 5                      # timeout_s clamped to 5, plus grace
        return await real(fut, 0.05)
    monkeypatch.setattr(asyncio, "wait_for", quick)
    assert asyncio.run(hub.confirm("t", timeout_s=1)) == "timeout"
    assert _prompt_sent(hub)["payload"]["timeoutS"] == 5
    assert not hub._prompt_waiters


def test_confirm_sync_from_another_thread():
    async def run():
        hub = _hub(answer="confirm")
        hub._loop = asyncio.get_running_loop()
        return await asyncio.to_thread(hub.confirm_sync, "t")
    assert asyncio.run(run()) == "confirm"


def test_confirm_sync_refuses_on_the_loop():
    async def run():
        hub = _hub()
        hub._loop = asyncio.get_running_loop()
        hub.confirm_sync("t")
    with pytest.raises(HubError):
        asyncio.run(run())
