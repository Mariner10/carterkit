"""SDK-to-relay contracts, without contacting APNs or a live account."""
import asyncio
import json
import pytest
from carterkit import (Hub, Layout, CarterNotifyError, CarterAmbientError,
                       apple_date, glance_update, notification_action, slot)
from carterkit import ambient
from carterkit import client as client_module
from test_client import _client, _FakeSock


def make_hub():
    with Layout("Workshop", id="workshop", cols=4, rows=6) as ui:
        with ui.tab("Main"):
            temp = ui.gauge("temperature", label="Temperature", min=0, max=100,
                            formatValue="suffix:°C", listen="temperature")
            fan = ui.toggle("fan", label="Fan", send="set_fan", listen="fan")
            humidity = ui.gauge("humidity", label="Humidity", min=0, max=100, listen="humidity")
        ui.glance(hero=temp, slots=[fan], live_activity=True, controls=[{
            "id": "ventilation", "label": "Ventilation", "kind": "toggle",
            "control": "fan", "event": "set_fan"}])
    hub = ui.serve(connection={"url": "wss://relay.invalid/ws", "channel": "workshop",
                              "token": "device-token", "did": "device-1",
                              "refresh": "refresh-secret", "validator": "https://validator.invalid"})
    hub.client._sock = _FakeSock()
    hub.client._broadcast_registered = False
    hub.client._ensure_broadcast_listener()
    hub.client._sock.auth_token = "device-token"
    return hub, temp, fan, humidity


def capture_notify(monkeypatch):
    requests = []
    original = client_module.notify_http
    def send(url, headers, body):
        requests.append((url, headers, json.loads(body)))
        return {"sent": 1, "stale": 0}
    monkeypatch.setattr(client_module, "notify_http", lambda *a, **kw: original(*a, **kw, _send=send))
    return requests


def test_snapshot_uses_handles_metadata_and_catalog_without_mutating_hub():
    hub, temp, fan, humidity = make_hub()
    state = hub.surfaces.snapshot({temp: 21.5, fan: True, humidity: 42})
    assert state["layoutId"] == "workshop"
    assert state["hero"] == {"controlId": "temperature", "label": "Temperature", "kind": "gauge",
                              "value": 21.5, "min": 0, "max": 100, "formatValue": "suffix:°C", "tint": "#667eea"}
    assert [s["controlId"] for s in state["slots"]] == ["fan"]
    assert state["values"] == {"temperature": 21.5, "fan": True, "humidity": 42}
    assert state["controls"] == {"ventilation": True}
    assert hub.client._control_state == {}


def test_refresh_uses_pushed_state_and_renewed_device_authorization(monkeypatch):
    requests = capture_notify(monkeypatch)
    hub, temp, fan, _ = make_hub()
    monkeypatch.setattr(client_module, "device_refresh_http", lambda *a, **kw: {"deviceToken": "renewed", "expiresAt": 9})
    async def run():
        await hub.push(temp, 24)
        await hub.push(fan, False)
        await hub.client.refresh_device_token()
        return await hub.surfaces.refresh()
    assert asyncio.run(run())["sent"] == 1
    url, headers, body = requests[0]
    assert url == "https://validator.invalid/alerts/notify"
    assert headers["Authorization"] == "renewed" and headers["User-Agent"] == "carterkit/python"
    assert body["silent"] is True and "title" not in body and "sound" not in body
    assert body["glance"]["hero"]["value"] == 24
    assert body["glance"]["controls"] == {"ventilation": False}
    assert body["layoutId"] == "workshop" and body["channel"] == "workshop"


def test_activity_lifecycle_derives_identity_dates_state_and_priority(monkeypatch):
    hub, temp, _, _ = make_hub()
    requests = []
    original = ambient.live_activity_push
    def send(url, headers, body, method):
        requests.append((url, headers, json.loads(body)))
        return {"sent": 1}
    monkeypatch.setattr(ambient, "live_activity_push", lambda *a, **kw: original(*a, **kw, _send=send))
    monkeypatch.setattr("carterkit.surfaces.time.time", lambda: 1_800_000_000)
    async def run():
        await hub.surfaces.start_activity({temp: 10}, alert_title="Started")
        hub.client._sock.auth_token = "rotated"
        await hub.surfaces.update_activity({temp: 30}, hero_history=[10, 20, 30])
        await hub.surfaces.end_activity({temp: 40})
    asyncio.run(run())
    start, update, end = [r[2] for r in requests]
    assert requests[0][0].endswith("/alerts/live-activity/push")
    assert requests[1][1]["Authorization"] == "rotated"
    assert start["attributes"]["layoutId"] == start["layoutId"] == "workshop"
    assert start["attributes"]["startedAt"] == apple_date(1_800_000_000)
    assert start["contentState"]["updatedAt"] == apple_date(1_800_000_000)
    assert start["contentState"]["hero"]["value"] == 10
    assert update["priority"] == 5 and update["contentState"]["heroHistory"] == [10, 20, 30]
    assert end["event"] == "end" and end["contentState"]["isConnected"] is False


def test_inline_reply_options_and_callback_round_trip(monkeypatch):
    requests = capture_notify(monkeypatch)
    hub, temp, _, _ = make_hub()
    received, catchall = [], []
    @hub.surfaces.on_notification
    def on_response(frame):
        catchall.append(frame)
    assert callable(on_response)
    async def run():
        await hub.surfaces.notify("Workshop", "Set a target", values={temp: 21}, actions=[
            notification_action("target", "Set target", callback=received.append,
                                text_input=True, text_input_button_title="Set",
                                text_input_placeholder="Degrees", authentication_required=True),
            notification_action("open", "Open", foreground=True)])
        body = requests[0][2]
        await hub.client._sock.handlers["broadcast"]({"msg_type": "notif_action", "notifId": body["notifId"],
                 "actionId": "target", "userText": "23", "channel": "workshop"})
    asyncio.run(run())
    body = requests[0][2]
    assert body["layoutId"] == "workshop" and body["glance"]["hero"]["value"] == 21
    assert body["actions"][0] == {"id": "target", "title": "Set target", "textInput": True,
                                  "authenticationRequired": True, "textInputButtonTitle": "Set",
                                  "textInputPlaceholder": "Degrees"}
    assert body["actions"][1]["foreground"] is True
    assert received == catchall and received[0]["userText"] == "23"


def test_failed_send_restores_callback_registry(monkeypatch):
    c = _client(key=None, validator_url="https://v", session_jwt="owner")
    old = lambda frame: None
    c._notif_callbacks[("stable", "ack")] = old
    def fail(*args, **kwargs):
        raise CarterNotifyError(503, "try later")
    monkeypatch.setattr(client_module, "notify_http", fail)
    with pytest.raises(CarterNotifyError):
        asyncio.run(c.notify("T", "B", notif_id="stable", actions={"ack": ("Ack", lambda f: None)}))
    assert c._notif_callbacks == {("stable", "ack"): old}
    with pytest.raises(ValueError):
        asyncio.run(c.notify("", "", silent=True, glance={"layoutId": "x"}, actions={"ack": old}))
    assert c._notif_callbacks == {("stable", "ack"): old}


def test_local_relay_key_is_not_sent_to_validator(monkeypatch):
    requests = capture_notify(monkeypatch)
    c = _client(key=None, validator_url="https://v")
    with pytest.raises(CarterNotifyError, match="Add Hub"):
        asyncio.run(c.notify("T", "B"))
    assert requests == []


def test_layout_identity_filename_and_adoption(tmp_path):
    path = tmp_path / "printer.json"
    path.write_text('{"name":"Printer"}')
    hub = Hub(path)
    assert hub.surfaces.layout_id == "printer.json"
    hub.adopt_layout({"id": "new-printer"})
    assert hub.surfaces.layout_id == "new-printer"
    with pytest.raises(ValueError, match="filename"):
        Hub({"name": "No identity"}).surfaces.snapshot()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), {}, [], None])
def test_glance_rejects_non_scalar_and_non_finite_readings(value):
    with pytest.raises(ValueError):
        glance_update(layout_id="x", values={"temp": value})


def test_payload_limits_and_bad_slot_metadata_fail_before_network():
    with pytest.raises(ValueError, match="2048-byte"):
        glance_update(layout_id="x", values={"text": "é" * 1024})
    with pytest.raises(ValueError, match="Boolean"):
        glance_update(layout_id="x", controls={"fan": 1})
    with pytest.raises(ValueError, match="finite"):
        slot("t", "Temp", "gauge", 1, max="100")
    with pytest.raises(ValueError, match="supported kind"):
        glance_update(layout_id="x", hero={"controlId": "t", "kind": "typo", "label": "T"})
    with pytest.raises(ValueError, match="24"):
        ambient.content_state(updated_at=1, hero_history=list(range(25)))
    with pytest.raises(ValueError, match="match"):
        ambient.live_activity_push("https://v", "t", layout_id="x", event="start",
                                   content_state={}, attributes={"layoutId": "y"})


@pytest.mark.parametrize("actions", [
    [{"id": "same", "title": "A"}, {"id": "same", "title": "B"}],
    [{"id": "com.apple.reserved", "title": "A"}], [{"id": "a", "title": "é" * 25}],
    [{"id": "a", "title": "A", "foreground": "false"}],
    [{"id": "a", "title": "A", "textInputPlaceholder": "Enter"}],
])
def test_actions_reject_invalid_ios_contract(actions):
    with pytest.raises(ValueError):
        client_module.notify_http("https://v", "t", "T", "B", actions=actions, _send=lambda *a: {})


def test_mesh_bridge_normalizes_socket_url_and_semantic_event():
    requests = []
    def send(url, headers, body, method):
        requests.append((url, json.loads(body)))
        return {"delivered": True, "status": 200}
    ambient.mesh_broadcast("wss://relay.invalid:8443/ws?unused=true", "token", channel="home",
                           event="broadcast_request", payload={"msg_type": "set_fan", "value": True},
                           action_id="press-1", _send=send)
    assert requests[0][0] == "https://relay.invalid:8443/mesh/broadcast"
    assert requests[0][1]["event"] == "set_fan" and requests[0][1]["actionId"] == "press-1"


def test_http_connectors_bound_wait_and_report_transport_errors(monkeypatch):
    timeouts = []
    def fail(request, *, timeout):
        timeouts.append(timeout)
        raise TimeoutError("deadline")
    monkeypatch.setattr("urllib.request.urlopen", fail)
    with pytest.raises(CarterNotifyError) as notify_error:
        client_module.notify_http("https://v", "t", "T", "B", timeout=2)
    with pytest.raises(CarterAmbientError) as ambient_error:
        ambient.mesh_broadcast("https://r", "t", channel="home", event="go", timeout=3)
    assert timeouts == [2, 3]
    assert notify_error.value.status == ambient_error.value.status == 0


def test_auto_hero_does_not_steal_explicit_secondary_and_humanizes_label():
    with Layout("Bench", id="bench") as ui:
        with ui.tab("Main"):
            pinned = ui.gauge("first", listen="first", min=0, max=100)
            ui.gauge("battery-ring", listen="battery", min=0, max=100)
        ui.glance(slots=[pinned])
    hub = ui.serve()
    snapshot = hub.surfaces.snapshot()
    assert snapshot["hero"]["controlId"] == "battery-ring"
    assert snapshot["hero"]["label"] == "Battery"
    assert snapshot["slots"][0]["controlId"] == "first"
    assert ambient.canonical_layout_id(ui) == "bench"


def test_nested_popup_readings_are_available_to_surfaces():
    hub = Hub({"id": "bench", "name": "Bench", "glance": {"hero": "popup-temp"},
               "tabs": [{"children": [{"type": "button", "id": "open", "longPressGroup": {
                   "children": [{"type": "gauge", "id": "popup-temp", "label": "Temperature",
                                 "min": 0, "max": 100}]
               }}]}]})
    assert hub.surfaces.snapshot({"popup-temp": 31})["hero"]["value"] == 31


@pytest.mark.parametrize("response", [b'[]', b'null', b'not json'])
def test_malformed_http_response_is_a_connector_error(monkeypatch, response):
    class Response:
        status = 200
        def read(self): return response
        def __enter__(self): return self
        def __exit__(self, *args): pass
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: Response())
    with pytest.raises(CarterNotifyError):
        client_module.notify_http("https://v", "t", "T", "B")
    with pytest.raises(CarterAmbientError):
        ambient.mesh_broadcast("https://r", "t", channel="home", event="go")
