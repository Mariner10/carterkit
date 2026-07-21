"""Round-trip parity: layouts built with each NEW 0.7.0 authoring sugar (sources,
sensor sync, publishers, alerts, glance, poll groups, appearance, dynamic tabs) must
validate with zero errors and no unknown-field warnings against the vendored docs."""
from __future__ import annotations

import carterkit
from carterkit import Layout, bind


def _errors(ui):
    return [f for f in ui.validate() if f["severity"] == "error"]


def _unknown_field_warnings(ui):
    return [f for f in ui.validate() if f["kind"] == "unknown_field"]


def test_sources_mqtt_http_round_trip():
    ui = Layout("Sources", cols=2, rows=8)
    ui.source_mqtt("broker", "mqtt://192.168.1.10:1883", username="ha", password="x")
    ui.source_http("api", "http://192.168.1.5:8080", interval=5)
    with ui.tab("Main", icon="gauge"):
        ui.gauge("temp", label="Temp", min=0, max=40, sync=[bind.mqtt("greenhouse/temp")])
        ui.toggle("fan", label="Fan", sync=[bind.mqtt("greenhouse/fan/state")],
                  action=bind.mqtt_publish("greenhouse/fan/set", retain=False))
        ui.gauge("cpu", label="CPU", sync=[bind.http("/status", interval=5,
                                                     value_path="cpu", source="api")])
    assert _errors(ui) == []
    assert _unknown_field_warnings(ui) == []
    lay = ui.layout
    assert lay["sources"]["broker"]["type"] == "mqtt"
    assert lay["sources"]["api"]["baseURL"] == "http://192.168.1.5:8080"


def test_unknown_source_ref_errors():
    ui = Layout("BadSrc", cols=2, rows=8)
    ui.source_mqtt("broker", "mqtt://host")
    with ui.tab("Main"):
        ui.gauge("t", label="T", sync=[bind.mqtt("x/y", source="nope")])
    kinds = {f["kind"] for f in ui.validate() if f["severity"] == "error"}
    assert "unknown_source" in kinds


def test_sensor_sugar():
    ui = Layout("Sensors", cols=2, rows=8)
    with ui.tab("Main"):
        ui.compass("hdg", label="Heading", sensor="heading")
        ui.gauge("roll", label="Roll", sensor="motion.roll")
    assert _errors(ui) == []
    syncs = ui.layout["tabs"][0]["children"][0]["sync"]
    assert syncs == [{"method": "sensor", "sensor": "heading"}]


def test_publisher_and_alert_and_poll_and_appearance_and_dyntab():
    ui = Layout("Full", cols=2, rows=8)
    ui.publisher("heading", interval=0.25)
    ui.alert(event="broadcast", value_path="temp", operator="gt", value=30,
             title="Hot", body="Temp high", cooldown=60)
    ui.poll_group("tick", event="broadcast_request", interval=10,
                  payload={"msg_type": "poll"})
    ui.appearance(color_scheme="dark", show_header=True)
    ui.dynamic_tab("inject_tab")
    with ui.tab("Main"):
        ui.gauge("temp", label="Temp", min=0, max=40, defaultValue=21)
    assert _errors(ui) == []
    lay = ui.layout
    assert lay["publishers"][0]["sensor"] == "heading"
    assert lay["alerts"][0]["operator"] == "gt"
    assert lay["pollGroups"]["tick"]["interval"] == 10
    assert lay["appearance"]["colorScheme"] == "dark"
    assert lay["dynamicTabs"] == [{"event": "inject_tab"}]


def test_bad_alert_operator_raises():
    ui = Layout("BadAlert")
    try:
        ui.alert(event="broadcast", value_path="x", operator="bogus", value=1,
                 title="t", body="b")
    except ValueError:
        return
    raise AssertionError("expected ValueError for a bad alert operator")


def test_contract_marks_mqtt_http_sensor_as_app_direct():
    from carterkit import contract
    ui = Layout("Contract", cols=2, rows=8)
    ui.source_mqtt("broker", "mqtt://host")
    with ui.tab("Main"):
        ui.gauge("temp", label="Temp", sync=[bind.mqtt("home/temp")])
        ui.toggle("fan", label="Fan", action=bind.mqtt_publish("home/fan/set"))
        ui.compass("hdg", label="Heading", sensor="heading")
        ui.button("go", label="Go", send="refresh")   # a real meshsocket trigger
    c = contract.extract_contract(ui.layout)
    transports = {a["transport"] for a in c["appDirect"]}
    assert {"mqtt", "sensor"} <= transports
    # app-direct bindings must NOT leak into the meshsocket feeds, and the meshsocket
    # trigger must still be present.
    assert all(f["type"] != "compass" for f in c["feeds"])
    assert any(t["command"] == "refresh" for t in c["triggers"])


def test_codegen_does_not_serve_app_direct():
    from carterkit import codegen
    ui = Layout("Codegen", cols=2, rows=8)
    ui.source_mqtt("broker", "mqtt://host")
    with ui.tab("Main"):
        ui.gauge("temp", label="Temp", sync=[bind.mqtt("home/temp", value_path="v")])
    stub = codegen.generate_service_stub(ui.layout)
    assert "home/temp" not in stub   # the broker topic never appears in a server stub


def test_glance_reference_validation():
    ui = Layout("Glance", cols=2, rows=8)
    with ui.tab("Main"):
        ui.gauge("cpu", label="CPU")
    ui.glance(title="Sys", hero="cpu", slots=["ghost"], live_activity=True)
    warns = {f["kind"] for f in ui.validate() if f["severity"] == "warn"}
    assert "bad_glance" in warns   # 'ghost' isn't a control; 'cpu' is fine
