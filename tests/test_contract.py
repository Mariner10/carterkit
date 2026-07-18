import json

from carterkit.contract import (
    example_frame, expects_spec, extract_contract, sample_value, value_spec,
    walk_with_location,
)


def _layout():
    return {
        "name": "Contract Test",
        "connection": {"url": "wss://relay.example", "mode": "room",
                       "token": "SECRET", "e2eeKey": "ALSO-SECRET",
                       "identity": {"name": "phone", "channel": "lab", "role": "controller"}},
        "publishers": [{"sensor": "heading"}],
        "tabs": [{
            "title": "Main",
            "children": [
                {"type": "slider", "id": "bright", "label": "Brightness",
                 "min": 0, "max": 255, "step": 5,
                 "action": {"method": "meshsocket", "mode": "broadcast",
                            "event": "broadcast_request",
                            "payload": {"msg_type": "set-brightness", "level": "{{value}}"}}},
                {"type": "toggle", "id": "power",
                 "action": {"method": "meshsocket", "mode": "request", "event": "route_msg",
                            "payload": {"target_name": "lamp", "type": "set-power",
                                        "payload": {"on": "{{value}}"}}}},
                {"type": "gauge", "id": "cpu", "label": "CPU", "min": 0, "max": 100,
                 "sync": [{"method": "meshsocket", "type": "listen", "event": "broadcast",
                           "filter": {"msg_type": "metrics"}, "valuePath": "stats.cpu"}]},
                {"type": "group", "id": "deck", "dynamic": "deck-slot", "children": []},
                {"type": "group", "id": "g1", "label": "Nest", "children": [
                    {"type": "statusLight", "id": "st",
                     "statusColors": {"ok": "#0f0", "bad": "#f00"},
                     "sync": [{"method": "meshsocket", "type": "listen", "event": "broadcast",
                               "filter": {"msg_type": "metrics"}, "valuePath": "status"}]},
                ]},
                {"type": "carousel", "id": "car", "panels": [
                    {"title": "P1", "children": [
                        {"type": "sparkline", "id": "spark",
                         "sync": [{"method": "meshsocket", "type": "listen",
                                   "event": "broadcast",
                                   "filter": {"msg_type": "metrics"}, "valuePath": "net"}]},
                    ]},
                ]},
                {"type": "canvas", "id": "board", "canvasConfig": {"items": [
                    {"control": {"type": "button", "id": "cv-btn", "label": "Ping",
                                 "action": {"method": "meshsocket", "mode": "broadcast",
                                            "event": "broadcast_request",
                                            "payload": {"msg_type": "ping"}}}},
                ]}},
                {"type": "sortboard", "id": "kanban",
                 "action": {"method": "meshsocket", "mode": "broadcast",
                            "event": "broadcast_request",
                            "payload": {"msg_type": "card-moved", "item": "{{item}}",
                                        "from": "{{from}}", "to": "{{to}}",
                                        "index": "{{index}}"}}},
                # sensor sync must NOT appear as a feed
                {"type": "compass", "id": "cmp",
                 "sync": [{"method": "sensor", "sensor": "heading"}]},
            ],
        }],
    }


def test_walk_recurses_all_nestings():
    ids = {c.get("id") for c, _, _ in walk_with_location(_layout())}
    assert {"bright", "power", "cpu", "st", "spark", "cv-btn", "kanban"} <= ids


def test_walk_breadcrumbs():
    crumbs = {c.get("id"): (tab, crumb) for c, tab, crumb in walk_with_location(_layout())}
    assert crumbs["st"] == ("Main", ["Nest"])
    assert crumbs["spark"][1] == ["car", "P1"]
    assert crumbs["cv-btn"][1] == ["board"]


def test_value_specs_refine_from_config():
    slider = {"type": "slider", "min": 0, "max": 255, "step": 5}
    assert value_spec(slider) == {"type": "number", "min": 0, "max": 255, "step": 5}
    assert value_spec({"type": "toggle"}) == {"type": "boolean"}
    seg = {"type": "segmentedControl", "options": ["A", "B"]}
    assert value_spec(seg)["enum"] == ["A", "B"]
    assert value_spec({"type": "nonesuch"}) == {"type": "json"}


def test_expects_specs():
    g = expects_spec({"type": "gauge", "min": 10, "max": 20})
    assert (g["min"], g["max"]) == (10, 20)
    sl = expects_spec({"type": "statusLight", "statusColors": {"ok": "#0f0", "bad": "#f00"}})
    assert sl["enum"] == ["bad", "ok"]
    assert expects_spec({"type": "list"})["type"] == "array"


def test_sample_value_bounds_and_enum():
    assert sample_value({"type": "number", "min": 0, "max": 100}) == 50
    assert sample_value({"type": "string", "enum": ["x", "y"]}) == "x"
    assert sample_value({"type": "boolean"}) is True


def test_example_frame_plants_value_at_path():
    feed = {"filter": {"msg_type": "metrics"}, "valuePath": "stats.cpu",
            "expects": {"type": "number", "min": 0, "max": 100}}
    assert example_frame(feed) == {"msg_type": "metrics", "stats": {"cpu": 50}}


def test_contract_triggers():
    c = extract_contract(_layout())
    by_cmd = {t["command"]: t for t in c["triggers"]}
    assert set(by_cmd) == {"set-brightness", "set-power", "ping", "card-moved"}

    sb = by_cmd["set-brightness"]
    assert sb["wire"] == {"event": "broadcast_request", "transport": "broadcast",
                          "mode": "broadcast"}
    assert sb["tokens"]["value"] == {"type": "number", "min": 0, "max": 255, "step": 5}
    assert sb["sources"][0]["id"] == "bright"

    sp = by_cmd["set-power"]
    assert sp["wire"]["transport"] == "routed"
    assert sp["tokens"]["value"] == {"type": "boolean"}

    km = by_cmd["card-moved"]
    assert set(km["tokens"]) == {"item", "from", "to", "index"}
    assert km["tokens"]["index"]["type"] == "number"


def test_contract_feeds_and_sensor_exclusion():
    c = extract_contract(_layout())
    by_id = {f["id"]: f for f in c["feeds"]}
    assert set(by_id) == {"cpu", "st", "spark"}          # compass sensor sync excluded
    cpu = by_id["cpu"]
    assert cpu["expects"]["type"] == "number"
    assert cpu["example"] == {"msg_type": "metrics", "stats": {"cpu": 50}}
    assert by_id["st"]["expects"]["enum"] == ["bad", "ok"]


def test_contract_dynamic_publishers_and_redaction():
    c = extract_contract(_layout())
    assert c["dynamicGroups"][0]["event"] == "deck-slot"
    assert c["publishers"][0]["sensor"] == "heading"
    conn = c["connection"]
    assert conn["channel"] == "lab"
    assert "SECRET" not in json.dumps(c)
    assert conn["token"] == "••• redacted"


def test_contract_json_serializable():
    json.dumps(extract_contract(_layout()))
