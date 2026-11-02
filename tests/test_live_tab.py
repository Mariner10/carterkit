"""Hub.live_tab: temporary tab added on enter, removed on exit."""

import asyncio

import pytest

from carterkit import Layout, Hub
from test_hub import _FakeSock


def _hub():
    with Layout("T", cols=4, rows=4) as ui:
        with ui.tab("Main"):
            ui.gauge("temp", label="Temp", min=0, max=40, listen="temp",
                     when={"msg_type": "climate"})
    hub = ui.serve()
    hub.client._sock = _FakeSock()
    return hub


def _ids(hub):
    return [t.get("id") for t in hub.layout["tabs"]]


def _run(coro):
    return asyncio.run(coro)


def test_add_and_remove_on_exit():
    hub = _hub()
    before = _ids(hub)

    async def go():
        async with hub.live_tab("lab", "Lab") as t:
            assert "lab" in _ids(hub)
            ctrl = {"id": "lab_g", "type": "gauge", "label": "G", "min": 0, "max": 9,
                    "position": [0, 0], "span": [2, 2],
                    "sync": [{"event": "broadcast", "filter": {"msg_type": "lab"},
                              "valuePath": "v"}]}
            await t.add(ctrl)
            frame = await t.push("lab_g", 3)
            assert frame == {"msg_type": "lab", "v": 3}
            await t.clear()
            tab = [x for x in hub.layout["tabs"] if x["id"] == "lab"][0]
            assert tab["children"] == []
    _run(go())
    assert _ids(hub) == before


def test_removed_on_exception():
    hub = _hub()
    before = _ids(hub)

    async def go():
        async with hub.live_tab("lab"):
            raise ValueError("boom")
    with pytest.raises(ValueError):
        _run(go())
    assert _ids(hub) == before


def test_reuses_existing_tab_and_keeps_it():
    hub = _hub()
    existing = hub.layout["tabs"][0]["id"]
    before = _ids(hub)

    async def go():
        async with hub.live_tab(existing):
            assert _ids(hub) == before
    _run(go())
    assert _ids(hub) == before
