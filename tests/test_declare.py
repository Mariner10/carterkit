"""Tests for the declarative-class veneer (compiles to the same Layout engine)."""

import pytest

from carterkit import Layout
from carterkit.declare import (Screen, Tab, Group, Connect, Ref, DeclareError,
                               Gauge, Button, Slider, StatusLight, Label)


def _child(layout, cid):
    def walk(children):
        for ch in children:
            if ch.get("id") == cid:
                return ch
            if ch.get("type") == "group":
                hit = walk(ch.get("children", []))
                if hit:
                    return hit
    for tab in layout["tabs"]:
        hit = walk(tab.get("children", []))
        if hit:
            return hit
    raise AssertionError(f"no child {cid!r}")


def test_basic_declarative_shape():
    class Bench(Screen, cols=4, rows=4):
        relay = Connect("ws://h:8765", channel="lab")

        class Main(Tab, icon="gauge"):
            cpu = Gauge(label="CPU", min=0, max=100, span=(2, 2),
                        listen="cpu", when={"msg_type": "metrics"})
            warn = StatusLight(visible=cpu > 90)
            refresh = Button(label="Refresh", send="refresh")

    lay = Bench.layout
    assert lay["name"] == "Bench"
    assert lay["connection"]["url"] == "ws://h:8765"
    t0 = lay["tabs"][0]
    assert t0["title"] == "Main" and t0["icon"] == "gauge"
    # id = attribute name
    assert {c["id"] for c in t0["children"]} == {"cpu", "warn", "refresh"}
    cpu = _child(lay, "cpu")
    assert cpu["span"] == [2, 2]
    assert cpu["sync"][0]["valuePath"] == "cpu"
    assert cpu["sync"][0]["filter"] == {"msg_type": "metrics"}
    # handle comparison -> visibility condition
    assert _child(lay, "warn")["visible"] == {"when": "cpu", "operator": "gt", "value": 90}
    assert _child(lay, "refresh")["action"]["event"] == "broadcast_request"
    assert _child(lay, "refresh")["action"]["payload"]["msg_type"] == "refresh"


def test_matches_flat_builder():
    class Decl(Screen, cols=4, rows=4):
        class Main(Tab, icon="gauge"):
            cpu = Gauge(label="CPU", min=0, max=100, span=(2, 2), listen="cpu")
            go = Button(label="Go", send="go")

    with Layout("Decl", cols=4, rows=4) as ui:
        with ui.tab("Main", icon="gauge"):
            ui.gauge("cpu", label="CPU", min=0, max=100, span=(2, 2), listen="cpu")
            ui.button("go", label="Go", send="go")

    assert Decl.layout == ui.layout


def test_nested_group_and_loop_free_generation():
    class Rig(Screen, cols=4, rows=6):
        class Motors(Tab):
            class Bank(Group, span=(2, 2), cols=2, rows=2):
                m0 = Slider(min=0, max=255)
                m1 = Slider(min=0, max=255)
                m2 = Slider(min=0, max=255)

    grp = _child(Rig.layout, "Bank")
    assert grp["type"] == "group" and grp["label"] == "Bank"
    assert [c["id"] for c in grp["children"]] == ["m0", "m1", "m2"]


def test_ref_condition_and_dynamic_group():
    class Player(Screen, cols=4, rows=4):
        class Main(Tab):
            hidden = Label(text="hi", visible=Ref("power").eq(True))

            class NowPlaying(Group, span=(3, 4), cols=4, rows=3, dynamic="player_state"):
                pass

    assert _child(Player.layout, "hidden")["visible"] == {
        "when": "power", "operator": "eq", "value": True}
    grp = _child(Player.layout, "NowPlaying")
    assert grp["dynamic"] == "player_state" and grp["children"] == []


def test_controls_outside_tab_with_tabs_is_error():
    with pytest.raises(DeclareError):
        class Bad(Screen):
            loose = Button(label="x")

            class Main(Tab):
                ok = Button(label="ok")

        Bad.build()


def test_validate_clean():
    class Dash(Screen, cols=4, rows=4):
        class Main(Tab):
            g = Gauge(min=0, max=100, listen="g", span=(2, 2))

    assert [f for f in Dash.validate() if f["severity"] == "error"] == []
