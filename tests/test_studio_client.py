"""Studio client: truthful results, conflicts, one version-aware save, the vendored guide."""
import asyncio
from pathlib import Path

import pytest

from carterkit import cli
from carterkit.client import (CarterClient, StudioConflict, StudioError, needs_app_version)
from carterkit.hub import Hub


class Sock:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []

    async def request(self, t, payload=None, timeout=5.0):
        self.calls.append((t, payload))
        r = self.replies.pop(0)
        return r(payload) if callable(r) else r


def client(replies):
    c = CarterClient.__new__(CarterClient)
    c._sock, c._session, c._can_route, c._can_monitor, c.name = Sock(replies), None, True, True, "hub"
    return c


def run(coro):
    return asyncio.run(coro)


def test_conflict_is_typed_and_sends_base():
    c = client([{"ok": False, "error": "conflict", "version": "v9"}])
    with pytest.raises(StudioConflict) as e:
        run(c.studio_save({"name": "A"}, base="v1", route="layout-save", device_id="d"))
    assert e.value.version == "v9"
    assert c._sock.calls[0][1]["payload"]["base"] == "v1"


def test_error_reply_raises():
    c = client([{"ok": False, "error": "missing-layout", "detail": "bare"}])
    with pytest.raises(StudioError, match="missing-layout"):
        run(c.studio_save({"name": "A"}, device_id="d"))


def test_timeout_reads_back_once():
    c = client([None, {"ok": True, "version": "v2"}])
    res = run(c.studio_save({"name": "A"}, device_id="d"))
    assert res["confirmed"] == "readback" and res["version"] == "v2"
    assert [x[1]["type"] for x in c._sock.calls] == ["save-layout", "get-current-layout"]


def test_timeout_and_failed_readback_is_unconfirmed():
    c = client([None, None])
    with pytest.raises(StudioError, match="unconfirmed"):
        run(c.studio_save({"name": "A"}, device_id="d"))
    assert len(c._sock.calls) == 2


def test_broadcast_says_unconfirmed():
    c = client([])
    sent = []

    async def bc(t, d):
        sent.append(t)
    c.broadcast = bc
    res = run(c.studio_broadcast("layout-save", {"name": "A"}))
    assert res["confirmed"] is False and "does not confirm" in res["note"]


def test_needs_app_version():
    assert "needs CAR-TER >= 2.1" in needs_app_version("share/import QR", "2.1", "2.0.1")
    assert needs_app_version("x", "2.1", "2.1") is None
    assert needs_app_version("x", "2.1", None) is None


def hub_with(replies, peer_ver):
    h = Hub.__new__(Hub)
    h.layout = {"name": "A", "children": []}
    h.name = "hub"
    h.peers = {"p": {"appVersion": peer_ver, "manifestHash": None}} if peer_ver else {}
    h.client = client(replies)
    h.validate = lambda: []
    return h


def test_save_layout_new_phone_uses_layout_save():
    h = hub_with([{"clients": [{"id": "d", "name": "phone"}]},
                   {"ok": True, "file": "a.json", "version": "v1"}], "2.1")
    res = run(h.save_layout())
    assert res["route"] == "layout-save" and res["version"] == "v1"


def test_save_layout_old_phone_installs_and_refuses_base():
    h = hub_with([], "2.0.1")
    with pytest.raises(StudioError, match="needs CAR-TER >= 2.1"):
        run(h.save_layout(base="v1"))


def test_guide_prints_and_matches_sibling(capsys):
    assert cli.main(["studio", "guide"]) == 0
    assert "get-device-info" in capsys.readouterr().out
    sib = Path(__file__).resolve().parents[2] / "CAR-TER" / "docs" / "STUDIO.md"
    if sib.exists():
        assert sib.read_text(encoding="utf-8") == cli.studio_guide_text()
