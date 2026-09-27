"""device_support_findings (carter-5sn.1): warn, never error, when the paired phone's
app doesn't know a control type; say whether it shows the fallback or the placeholder."""

import carterkit
from carterkit.validate import device_support_findings

FEATURES = ["control.slider", "control.button", "control.carousel", "control.canvas",
            "control.stepper@2", "sync.meshsocket"]


def _layout(children):
    return {"name": "FC", "version": 1,
            "tabs": [{"title": "T", "icon": "house", "grid": {"columns": 4, "rows": 8},
                      "children": children}]}


def test_unknown_control_warns_placeholder():
    f = device_support_findings(_layout([{"type": "knob", "id": "k", "position": [0, 0]}]), FEATURES)
    assert [x["severity"] for x in f] == ["warn"]
    assert f[0]["kind"] == "needs_newer_app"
    assert "Update CAR-TER" in f[0]["detail"] and "'knob'" in f[0]["detail"]


def test_known_controls_and_versioned_features_are_quiet():
    lay = _layout([{"type": "slider", "id": "s", "position": [0, 0]},
                   {"type": "stepper", "id": "st", "position": [1, 0]}])
    assert device_support_findings(lay, FEATURES) == []


def test_fallback_chain_is_reported():
    lay = _layout([{"type": "knob", "id": "k", "position": [0, 0],
                    "fallback": {"type": "dial", "fallback": {"type": "slider"}}}])
    f = device_support_findings(lay, FEATURES)
    assert "fallback (slider)" in f[0]["detail"]


def test_nested_group_panel_longpress_and_canvas():
    knob = {"type": "knob", "id": "k", "position": [0, 0]}
    lay = _layout([
        {"type": "group", "id": "g", "position": [0, 0], "grid": {"columns": 1, "rows": 1},
         "children": [dict(knob, id="k1")]},
        {"type": "carousel", "id": "c", "position": [1, 0],
         "panels": [{"id": "p", "children": [dict(knob, id="k2")]}]},
        {"type": "button", "id": "b", "position": [2, 0],
         "longPressGroup": {"id": "l", "children": [dict(knob, id="k3")]}},
        {"type": "canvas", "id": "cv", "position": [3, 0], "canvasConfig": {"items": [
            {"id": "i", "control": {"type": "knob", "id": "k4",
                                    "fallback": {"type": "group", "children": []}}}]}},
    ])
    f = device_support_findings(lay, FEATURES)
    assert [x["where"].rsplit("/", 1)[-1] for x in f] == ["k1", "k2", "k3", "k4"]
    assert "placeholder" in f[3]["detail"]      # a canvas can't host a group fallback


def test_no_reported_features_means_no_judgement():
    lay = _layout([{"type": "knob", "id": "k", "position": [0, 0]}])
    assert device_support_findings(lay, None) == []
    assert device_support_findings(lay, []) == []
    assert device_support_findings("junk", FEATURES) == []


def test_exported():
    assert carterkit.device_support_findings is device_support_findings
