"""Tests for the fluent Layout builder."""

from carterkit import Layout, build, bind


def test_fluent_compose():
    lay = (Layout("Dash", columns=4, rows=4)
           .connect("ws://h:8765", channel="home")
           .tab("Main", icon="gauge")
           .add(build.gauge(id="cpu", min=0, max=100, sync=[bind.listen("cpu")]),
                default_span=[2, 2])
           .add(build.button(id="go", action=bind.action("go"))))
    layout = lay.layout
    assert layout["name"] == "Dash"
    assert layout["connection"]["url"] == "ws://h:8765"
    tab0 = layout["tabs"][0]
    assert tab0["title"] == "Main" and tab0["icon"] == "gauge"
    assert {c["id"] for c in tab0["children"]} == {"cpu", "go"}
    g = next(c for c in tab0["children"] if c["id"] == "cpu")
    assert g["span"] == [2, 2] and g["position"] == [0, 0]


def test_first_tab_renames_then_appends():
    lay = (Layout("X")
           .tab("One").add(build.button(id="a"))
           .tab("Two").add(build.button(id="b")))
    assert [t["title"] for t in lay.layout["tabs"]] == ["One", "Two"]
    assert lay.layout["tabs"][1]["children"][0]["id"] == "b"


def test_validate_and_findings_clean():
    lay = Layout("X").add(
        build.gauge(id="g", min=0, max=100, sync=[bind.listen("g")]), default_span=[2, 2])
    assert [f for f in lay.validate() if f["severity"] == "error"] == []
    assert "No issues" in lay.findings()


def test_repr_counts_controls():
    lay = Layout("X").add(build.button(id="a")).add(build.button(id="b"))
    assert "2 control" in repr(lay)


def test_layout_notify_scopes_to_layout():
    import asyncio

    class _StubHub:
        def __init__(self):
            self.calls = []

        async def notify(self, title, body, **kw):
            self.calls.append((title, body, kw))
            return {"sent": 1, "stale": 0}

    ui = Layout("Monroe Dash")
    hub = _StubHub()
    ui._active_hub = hub
    out = asyncio.run(ui.notify("Door", "Open", image="https://x/i.jpg"))
    assert out == {"sent": 1, "stale": 0}
    title, body, kw = hub.calls[0]
    assert (title, body) == ("Door", "Open")
    assert kw["thread_id"] == "Monroe Dash"  # the layout IS the thread
    assert kw["image"] == "https://x/i.jpg"
    # explicit thread_id wins over the layout default
    asyncio.run(ui.notify("D", "O", thread_id="custom"))
    assert hub.calls[1][2]["thread_id"] == "custom"


def test_layout_notify_unserved_raises():
    import asyncio
    import pytest

    with pytest.raises(RuntimeError, match="serve"):
        asyncio.run(Layout("L").notify("t", "b"))
