"""secrets[] declarations, {{secret:name}} placeholders and the destination-policy
lint (carter-7gve; app side carter-hlkg SecretPolicy)."""
import pytest

import carterkit
from carterkit import Layout, bind


def _base(**extra):
    layout = {
        "name": "S", "version": 1,
        "sources": {
            "ha": {"type": "http", "baseURL": "https://ha.local:8123",
                   "headers": {"Authorization": "Bearer {{secret:ha_token}}"}},
            "broker": {"type": "mqtt", "url": "mqtts://broker.local",
                       "username": "ha", "password": "{{secret:mqtt_pw}}"},
        },
        "secrets": [{"name": "ha_token", "label": "HA", "kind": "token"},
                    {"name": "mqtt_pw", "kind": "password"}],
        "tabs": [{"title": "T", "icon": "house", "grid": {"columns": 4, "rows": 4},
                  "children": []}],
    }
    layout.update(extra)
    return layout


def _button(action):
    return {"type": "button", "id": "b", "label": "B", "position": [0, 0], "span": [1, 1],
            "action": action}


def _with_child(layout, child):
    layout["tabs"][0]["children"] = [child]
    return layout


def _kinds(layout):
    return {(f["kind"], f["severity"]) for f in carterkit.validate_layout(layout)}


def _of(layout, kind):
    return [f for f in carterkit.validate_layout(layout) if f["kind"] == kind]


def test_bind_secret_placeholder_and_names():
    assert bind.secret("ha_token") == "{{secret:ha_token}}"
    with pytest.raises(ValueError):
        bind.secret("bad name}}")
    assert bind.secret_names({"a": ["x {{secret:a}}", {"b": "{{secret.b}} {{secret:a}}"}]}) == ["a", "b"]


def test_layout_secret_builder_declares_and_returns_placeholder():
    with Layout("S") as ui:
        key = ui.secret("ha_token", label="HA", kind="token", hosts=["api.example.com"], mesh=True)
        ui.secret("ha_token", label="HA 2")          # re-declaring replaces
        with ui.tab("Main", icon="house"):
            pass
    assert key == "{{secret:ha_token}}"
    assert ui.layout["secrets"] == [{"name": "ha_token", "label": "HA 2"}]
    with pytest.raises(ValueError):
        ui.secret("x", hosts="api.example.com")


def test_placeholders_in_sources_are_clean():
    kinds = _kinds(_base())
    assert not any(k in ("embedded_secret", "secret_host", "secret_mesh", "bad_secrets",
                         "secret_not_filled", "secret_unused") for k, _ in kinds), kinds


def test_literal_credentials_still_warn_and_suggest_placeholder():
    layout = _base()
    layout["sources"]["ha"]["headers"]["Authorization"] = "Bearer abc123"
    layout["sources"]["broker"]["password"] = "hunter2"
    found = _of(layout, "embedded_secret")
    assert {f["where"] for f in found} == {"sources.ha.headers.Authorization", "sources.broker.password"}
    assert all("{{secret:name}}" in f["detail"] for f in found)


def test_literal_credential_in_action_headers_warns():
    layout = _with_child(_base(), _button({"method": "http", "path": "/x",
                                           "headers": {"X-Api-Key": "k-123"}}))
    assert _of(layout, "embedded_secret")


def test_action_url_on_undeclared_host_warns():
    layout = _with_child(_base(), _button({"method": "http", "url": "https://hooks.example.com/{{secret:ha_token}}"}))
    found = _of(layout, "secret_host")
    assert found and "not allowed for host hooks.example.com" in found[0]["detail"]
    layout["secrets"][0]["hosts"] = ["hooks.example.com", "ha.local"]
    assert not _of(layout, "secret_host")


def test_hosts_replaces_the_default_set():
    layout = _base()
    layout["secrets"][0]["hosts"] = ["elsewhere.example.com"]
    found = _of(layout, "secret_host")               # the ha source itself is no longer allowed
    assert found and "ha.local" in found[0]["detail"]


def test_mesh_action_needs_mesh_opt_in():
    act = {"method": "meshsocket", "event": "broadcast_request",
           "payload": {"msg_type": "unlock", "pin": "{{secret:ha_token}}"}}
    layout = _with_child(_base(), _button(act))
    assert _of(layout, "secret_mesh")
    layout["secrets"][0]["mesh"] = True
    assert not _of(layout, "secret_mesh")


def test_secret_in_url_host_is_refused():
    layout = _with_child(_base(), _button({"method": "http", "url": "https://{{secret:ha_token}}.example.com/x"}))
    assert _of(layout, "secret_in_url")


def test_placeholder_where_the_app_never_fills_it():
    layout = _base(connection={"url": "wss://r.example.com", "token": "{{secret:ha_token}}"})
    layout = _with_child(layout, {"type": "label", "id": "l", "text": "{{secret:ha_token}}",
                                  "position": [0, 0], "span": [1, 1]})
    wheres = {f["where"] for f in _of(layout, "secret_not_filled")}
    assert "connection" in wheres and any(w.endswith(".text") for w in wheres)


def test_declaration_shape_and_unused_undeclared():
    layout = _base(secrets=[{"name": "ha_token"}, {"name": "mqtt_pw", "mesh": "yes"},
                            {"label": "no name"}, {"name": "spare", "hosts": ["https://x.com/"]}])
    kinds = _kinds(layout)
    assert ("bad_secrets", "error") in kinds and ("bad_secrets", "warn") in kinds
    assert ("secret_unused", "info") in kinds
    layout = _base(secrets=[{"name": "ha_token"}])
    assert [f for f in _of(layout, "secret_undeclared") if "mqtt_pw" in f["detail"]]
    assert _of(_base(secrets={"name": "x"}), "bad_secrets")[0]["severity"] == "error"
