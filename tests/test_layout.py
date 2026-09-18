"""Tests for the fluent Layout builder."""

import json

import pytest

from carterkit import Layout, build, bind
from carterkit import (cc_button, cc_cycle, cc_set, cc_step, cc_toggle, island,
                       live, scene, tile, widget)
from carterkit.glance import state


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


# ── glance v2: the layout projected onto iOS surfaces ────────────────────────

def _printer_layout():
    """Every control the plan's `glance` example binds, so the block below can be
    validated against a real layout rather than asserted in a vacuum."""
    ui = Layout("Printer", id="printer", columns=4, rows=8)
    ui.tab("Main")
    for cid in ("nozzle", "bed", "progress", "eta", "lux", "volume", "fan-speed"):
        ui.add(build.gauge(id=cid, min=0, max=300, sync=[bind.listen(cid)]))
    ui.add(build.statusLight(id="state", sync=[bind.listen("state")]))
    ui.add(build.toggle(id="lights-toggle", action=bind.action("set_lights")))
    ui.add(build.picker(id="fan-mode", action=bind.action("set_fan")))
    ui.add(build.button(id="pause", action=bind.action("pause")))
    return ui


#: The `glance` block exactly as the Ambient Surfaces v2 plan (§1) writes it.
#: This is the contract; the builders below must produce it.
PLAN_GLANCE = {
    "enabled": True, "title": "Printer", "icon": "printer.fill", "tint": "#FF9F0A",
    "hero": "nozzle", "slots": ["bed", "progress", "state"], "liveActivity": True,
    "controls": [
        {"id": "lights", "kind": "toggle", "label": "Lights", "control": "lights-toggle",
         "on": {"label": "Lit", "icon": "lightbulb.fill", "tint": "#FFD60A"},
         "off": {"label": "Dark", "icon": "lightbulb"},
         "valueControl": "lux", "valueLabel": "{{value}} lx"},
        {"id": "fan", "kind": "cycle", "label": "Fan", "control": "fan-mode",
         "states": [{"value": "off", "label": "Off", "icon": "fan"},
                    {"value": "low", "label": "Low", "icon": "fan", "tint": "#64D2FF"},
                    {"value": "high", "label": "High", "icon": "fan.fill", "tint": "#0A84FF"}]},
        {"id": "vol-up", "kind": "step", "label": "Volume +10", "control": "volume", "delta": 10},
        {"id": "vol-down", "kind": "step", "label": "Volume −10", "control": "volume", "delta": -10},
        {"id": "vol-half", "kind": "set", "label": "Volume 50%", "control": "volume", "value": 50},
        {"id": "restart", "kind": "button", "label": "Restart", "icon": "arrow.clockwise",
         "event": "broadcast_request", "payload": {"msg_type": "restart"}},
    ],
    "live": {
        "tier": "fresh",
        "activity": {"cadence": 1, "remoteCadence": 5, "stale": 120,
                     "priority": "immediate", "start": "onConnect"},
        "widgets": {"refresh": "push", "pullEvery": 900, "stale": 300},
        "controls": {"refresh": "push"},
        "background": {"silentPush": False},
    },
    "widgets": [
        {"id": "temps", "title": "Temps", "icon": "thermometer",
         "families": ["systemSmall", "systemMedium", "accessoryRectangular"],
         "scene": {"rows": [
             [{"tile": "gauge", "control": "nozzle"}, {"tile": "gauge", "control": "bed"}],
             [{"tile": "sparkline", "control": "nozzle", "span": 2}],
             [{"tile": "toggle", "control": "lights-toggle"},
              {"tile": "step", "control": "fan-speed", "delta": 10}]]},
         "systemSmall": {"rows": [[{"tile": "ring", "control": "progress"}]]}},
    ],
    "island": {
        "compactLeading": {"tile": "icon", "effect": "bounce"},
        "compactTrailing": {"tile": "ring", "control": "progress"},
        "minimal": {"tile": "light", "control": "state"},
        "expanded": {
            "leading": {"tile": "icon"}, "trailing": {"tile": "freshness"},
            "center": {"tile": "timer", "control": "eta"},
            "bottom": {"rows": [
                [{"tile": "gauge", "control": "nozzle"}, {"tile": "gauge", "control": "bed"}],
                [{"tile": "button", "control": "pause"},
                 {"tile": "step", "control": "fan-speed", "delta": 10}]]}},
    },
    "lockScreen": {"rows": [[{"tile": "gauge", "control": "nozzle"},
                             {"tile": "gauge", "control": "bed"}]]},
}


def _plan_glance_via_builders(ui):
    ui.glance(
        enabled=True, title="Printer", icon="printer.fill", tint="#FF9F0A",
        hero="nozzle", slots=["bed", "progress", "state"], live_activity=True,
        controls=[
            cc_toggle("lights", "Lights", "lights-toggle",
                      on={"label": "Lit", "icon": "lightbulb.fill", "tint": "#FFD60A"},
                      off={"label": "Dark", "icon": "lightbulb"},
                      value_control="lux", value_label="{{value}} lx"),
            cc_cycle("fan", "Fan", "fan-mode",
                     states=[state("off", "Off", "fan"),
                             state("low", "Low", "fan", "#64D2FF"),
                             state("high", "High", "fan.fill", "#0A84FF")]),
            cc_step("vol-up", "Volume +10", "volume", delta=10),
            cc_step("vol-down", "Volume −10", "volume", delta=-10),
            cc_set("vol-half", "Volume 50%", "volume", value=50),
            cc_button("restart", "Restart", icon="arrow.clockwise",
                      event="broadcast_request", payload={"msg_type": "restart"}),
        ],
        live=live(tier="fresh",
                  activity=dict(cadence=1, remote_cadence=5, stale=120,
                                priority="immediate", start="onConnect"),
                  widgets=dict(refresh="push", pull_every=900, stale=300),
                  controls=dict(refresh="push"),
                  background=dict(silent_push=False)),
        widgets=[widget("temps", title="Temps", icon="thermometer",
                        families=["systemSmall", "systemMedium", "accessoryRectangular"],
                        scene=scene([tile("gauge", "nozzle"), tile("gauge", "bed")],
                                    [tile("sparkline", "nozzle", span=2)],
                                    [tile("toggle", "lights-toggle"),
                                     tile("step", "fan-speed", delta=10)]),
                        system_small=scene([tile("ring", "progress")]))],
        island=island(compact_leading=tile("icon", effect="bounce"),
                      compact_trailing=tile("ring", "progress"),
                      minimal=tile("light", "state"),
                      expanded=dict(leading=tile("icon"), trailing=tile("freshness"),
                                    center=tile("timer", "eta"),
                                    bottom=scene([tile("gauge", "nozzle"),
                                                  tile("gauge", "bed")],
                                                 [tile("button", "pause"),
                                                  tile("step", "fan-speed", delta=10)]))),
        lock_screen=scene([tile("gauge", "nozzle"), tile("gauge", "bed")]))
    return ui.layout["glance"]


def test_glance_builders_emit_the_plan_contract_verbatim():
    built = _plan_glance_via_builders(_printer_layout())
    assert json.dumps(built, sort_keys=True) == json.dumps(PLAN_GLANCE, sort_keys=True)
    # Key order matters only for a clean diff against hand-written JSON, but that
    # is the whole reason the helpers exist alongside plain dicts.
    assert list(built["controls"][0]) == ["id", "kind", "label", "control", "on",
                                          "off", "valueControl", "valueLabel"]


def test_the_plan_contract_validates_clean():
    import carterkit
    ui = _printer_layout()
    _plan_glance_via_builders(ui)
    glance_findings = [f for f in carterkit.validate_layout(ui.layout)
                       if f["kind"].startswith("bad_glance")]
    assert glance_findings == [], glance_findings


def test_glance_v1_call_still_emits_v1_only():
    """The v1 signature is untouched: adding v2 keywords must not start emitting
    v2 keys for layouts that never asked for them."""
    ui = Layout("X", id="x")
    ui.tab("Main").add(build.gauge(id="cpu", min=0, max=100))
    ui.glance(hero="cpu", slots=["cpu"], live_activity=True)
    assert ui.layout["glance"] == {"hero": "cpu", "slots": ["cpu"], "liveActivity": True}


def test_glance_accepts_control_handles_everywhere():
    with Layout("H", id="h", cols=4, rows=4) as ui:
        with ui.tab("Main"):
            cpu = ui.gauge("cpu", min=0, max=100, listen="cpu")
            lights = ui.toggle("lights", send="set_lights")
        ui.glance(hero=cpu,
                  controls=[cc_toggle("cc-lights", "Lights", lights, value_control=cpu)],
                  widgets=[widget("w", scene=scene([tile("gauge", cpu)]))],
                  # a hand-written dict with a handle inside is normalized too
                  island={"compactTrailing": {"tile": "ring", "control": cpu}},
                  lock_screen=scene([tile("value", cpu)]))
    block = ui.layout["glance"]
    assert block["hero"] == "cpu"
    assert block["controls"][0] == {"id": "cc-lights", "kind": "toggle", "label": "Lights",
                                    "control": "lights", "valueControl": "cpu"}
    assert block["widgets"][0]["scene"]["rows"][0][0]["control"] == "cpu"
    assert block["island"]["compactTrailing"]["control"] == "cpu"
    assert block["lockScreen"]["rows"][0][0]["control"] == "cpu"
    assert json.dumps(block)          # no handle survived into the JSON


def test_glance_builders_reject_what_a_surface_would_silently_drop():
    with pytest.raises(ValueError, match="tile kind"):
        tile("chart", "cpu")
    with pytest.raises(ValueError, match="unknown tile field"):
        tile("gauge", "cpu", colour="#fff")
    with pytest.raises(ValueError, match="at least two states"):
        cc_cycle("fan", control="fan-mode", states=[state("off", "Off")])
    with pytest.raises(ValueError, match="pass control="):
        cc_step("up", "Up", delta=1)
    with pytest.raises(ValueError, match="delta must be a number"):
        cc_step("up", "Up", "volume", delta="10")
    with pytest.raises(ValueError, match="no room for a scene"):
        island(minimal=scene([tile("value", "cpu")]))
    with pytest.raises(ValueError, match="family must be one of"):
        widget("w", families=["systemHuge"], scene=scene([tile("value", "cpu")]))
    with pytest.raises(ValueError, match="live.tier"):
        live(tier="instant")
    with pytest.raises(ValueError, match="live.widgets.refresh"):
        live(widgets=dict(refresh="sometimes"))
    with pytest.raises(ValueError, match="has no scene"):
        widget("w", title="Empty")


def test_layout_glance_rejects_a_malformed_control_entry():
    ui = Layout("X", id="x")
    ui.tab("Main").add(build.gauge(id="cpu", min=0, max=100))
    with pytest.raises(ValueError, match="kind must be one of"):
        ui.glance(controls=[{"id": "c", "kind": "slider", "control": "cpu"}])
    with pytest.raises(ValueError, match="must be a dict with an 'id'"):
        ui.glance(widgets=[{"title": "no id"}])
