"""Ambient surface: Live Activity push pipeline + the outbound mesh bridge.

The tests that matter most here guard the *silent* failures — the ones where the
call returns 200 and nothing happens on the device: a wrong Date epoch, a missing
attributes key, a guessed layout id, and a retry that re-fires a toggle.
"""
import json
import time

import pytest

from carterkit import ambient
from carterkit.ambient import (APPLE_REFERENCE_EPOCH, CarterAmbientError,
                               activity_attributes, apple_date,
                               canonical_layout_id, content_state,
                               live_activity_deregister, live_activity_push,
                               live_activity_register, mesh_broadcast, slot)


class Recorder:
    """Test seam: captures the request and returns a scripted body."""

    def __init__(self, response=None, status=200):
        self.response = response if response is not None else {}
        self.status = status
        self.url = self.headers = self.body = self.method = None

    def __call__(self, url, headers, body_bytes, method="POST"):
        self.url, self.headers, self.method = url, headers, method
        self.body = json.loads(body_bytes.decode())
        out = dict(self.response)
        out["status"] = self.status
        return out


# ── Shapes: the silent-failure guards ────────────────────────────────────────

def test_apple_date_converts_to_reference_epoch():
    now = time.time()
    assert apple_date(now) == now - APPLE_REFERENCE_EPOCH


def test_content_state_rejects_a_unix_timestamp():
    """ActivityKit decodes dates as seconds since 2001. Passing a unix timestamp
    is the single most common way to make a push vanish with no error anywhere,
    so it must fail loudly here instead."""
    with pytest.raises(ValueError, match="apple_date"):
        content_state(updated_at=time.time())


def test_content_state_accepts_a_reference_date():
    st = content_state(hero=slot("t", "Temp", "gauge", 42),
                       slots=[slot("b", "Bed", "number", 60)],
                       updated_at=apple_date(time.time()))
    assert st["isConnected"] is True
    assert st["hero"]["controlId"] == "t"
    assert st["slots"][0]["label"] == "Bed"


def test_slot_rejects_an_unknown_kind():
    """An unknown kind fails the on-device decode and the push disappears."""
    with pytest.raises(ValueError, match="kind must be"):
        slot("x", "X", "sparkline", 1)


@pytest.mark.parametrize("missing", ["layout_id", "title", "icon", "started_at"])
def test_activity_attributes_requires_every_non_optional_key(missing):
    """Swift's synthesized Decodable does NOT apply property defaults, so a
    missing key — startedAt especially, which looks optional in the Swift source —
    makes iOS drop the push-to-start silently."""
    kwargs = dict(layout_id="printer.json", title="Printer", icon="gear",
                  started_at=apple_date(time.time()))
    kwargs[missing] = None
    with pytest.raises(ValueError, match=missing):
        activity_attributes(**kwargs)


def test_activity_attributes_rejects_a_unix_started_at():
    with pytest.raises(ValueError, match="apple_date"):
        activity_attributes(layout_id="p.json", title="P", icon="gear",
                            started_at=time.time())


def test_canonical_layout_id_prefers_declared_id_over_filename():
    """The wire id must be stable across devices — every member of a shared room
    has to register under the same key for one hub push to reach them all."""
    assert canonical_layout_id({"id": "printer-v2"}, filename="printer.json") == "printer-v2"
    assert canonical_layout_id({}, filename="printer.json") == "printer.json"
    assert canonical_layout_id(None, filename="printer.json") == "printer.json"
    with pytest.raises(ValueError):
        canonical_layout_id({})


# ── Live Activity ────────────────────────────────────────────────────────────

def test_live_activity_register_sends_bundle_id_and_kind():
    r = Recorder({"registered": 1})
    live_activity_register("https://v/", "JWT", layout_id="printer.json",
                           push_token="TOK", bundle_id="Mariner.CAR-TER.dev", _send=r)
    assert r.url == "https://v/alerts/live-activity"
    assert r.method == "POST"
    assert r.headers["Authorization"] == "JWT"
    assert r.body == {"layoutId": "printer.json", "pushToken": "TOK",
                      "bundleId": "Mariner.CAR-TER.dev", "kind": "update"}


def test_start_token_registration_needs_no_layout_id():
    """A push-to-start token is issued per ActivityAttributes type, not per
    layout, so it is app-wide."""
    r = Recorder({"registered": 1})
    live_activity_register("https://v/", "JWT", layout_id=None, push_token="TOK",
                           bundle_id="Mariner.CAR-TER", kind="start", _send=r)
    assert r.body["kind"] == "start"


def test_update_token_registration_requires_a_layout_id():
    with pytest.raises(ValueError, match="layout_id"):
        live_activity_register("https://v/", "JWT", layout_id=None,
                               push_token="TOK", bundle_id="B", _send=Recorder())


def test_live_activity_deregister_uses_delete():
    r = Recorder({"deregistered": 1})
    live_activity_deregister("https://v/", "JWT", layout_id="printer.json",
                             push_token="TOK", bundle_id="B", _send=r)
    assert r.method == "DELETE"
    assert r.url == "https://v/alerts/live-activity"
    assert r.body["pushToken"] == "TOK"


def test_live_activity_push_start_requires_attributes():
    """Without attributes iOS has no activity identity to create and discards the
    push on-device with no error."""
    st = content_state(updated_at=apple_date(time.time()))
    with pytest.raises(ValueError, match="attributes"):
        live_activity_push("https://v/", "JWT", layout_id="p.json", event="start",
                           content_state=st, _send=Recorder())


def test_live_activity_push_sends_full_start_payload():
    r = Recorder({"sent": 1})
    st = content_state(updated_at=apple_date(1_700_000_000))
    attrs = activity_attributes(layout_id="p.json", title="P", icon="gear",
                                started_at=apple_date(1_700_000_000))
    live_activity_push("https://v/", "JWT", layout_id="p.json", event="start",
                       content_state=st, attributes=attrs, alert_title="CAR-TER",
                       alert_body="Started", stale_seconds=300, priority=5, _send=r)
    assert r.url == "https://v/alerts/live-activity/push"
    assert r.body["event"] == "start"
    assert r.body["attributes"]["startedAt"] == apple_date(1_700_000_000)
    assert r.body["priority"] == 5
    assert r.body["staleSeconds"] == 300


def test_live_activity_push_rejects_bad_event_and_priority():
    st = content_state(updated_at=apple_date(time.time()))
    with pytest.raises(ValueError, match="event"):
        live_activity_push("https://v/", "J", layout_id="p", event="poke",
                           content_state=st, _send=Recorder())
    with pytest.raises(ValueError, match="priority"):
        live_activity_push("https://v/", "J", layout_id="p", event="update",
                           content_state=st, priority=7, _send=Recorder())


# ── Mesh bridge ──────────────────────────────────────────────────────────────

def test_mesh_broadcast_posts_to_the_relay_host():
    """It is served by the gateway on the RELAY host, not the validator — a press
    there costs no Connect+ slot."""
    r = Recorder({"delivered": True})
    out = mesh_broadcast("https://relay.example/", "TOKEN", channel="home",
                         event="set-light", payload={"value": True},
                         action_id="press-1", _send=r)
    assert r.url == "https://relay.example/mesh/broadcast"
    assert r.body == {"channel": "home", "event": "set-light",
                      "payload": {"value": True}, "actionId": "press-1"}
    assert out["delivered"] is True
    assert out["status"] == 200


def test_mesh_broadcast_requires_channel_and_event():
    with pytest.raises(ValueError):
        mesh_broadcast("https://r/", "T", channel="", event="x", _send=Recorder())
    with pytest.raises(ValueError):
        mesh_broadcast("https://r/", "T", channel="home", event="", _send=Recorder())


def test_mesh_broadcast_rejects_a_non_dict_payload():
    """The payload is merged as siblings of msg_type, so it has to be an object."""
    with pytest.raises(ValueError, match="dict"):
        mesh_broadcast("https://r/", "T", channel="home", event="x",
                       payload="nope", _send=Recorder())


def test_mesh_broadcast_202_means_nobody_listening():
    r = Recorder({"delivered": False}, status=202)
    out = mesh_broadcast("https://r/", "T", channel="home", event="x", _send=r)
    assert out["status"] == 202 and out["delivered"] is False


def test_mesh_broadcast_omits_delivered_when_roster_unknown():
    """No `delivered` key means "sent, but we do not know" — the caller must make
    no delivery claim, and must NOT read it as a failure."""
    r = Recorder({}, status=200)
    out = mesh_broadcast("https://r/", "T", channel="home", event="x", _send=r)
    assert out["status"] == 200
    assert "delivered" not in out


def test_mesh_broadcast_returns_rather_than_raises_on_429_and_503():
    """Both mean "try again later", not "you called this wrong" — a raise would
    push every caller into an except block for the normal backoff path."""
    for status, body in ((429, '{"retryAfter": 7}'), (503, '{"reason":"mesh_unavailable"}')):
        def boom(url, headers, body_bytes, method="POST", _s=status, _b=body):
            raise CarterAmbientError(_s, _b)
        out = mesh_broadcast("https://r/", "T", channel="home", event="x", _send=boom)
        assert out["status"] == status
    # ...while a real client error still raises.
    def unauthorized(url, headers, body_bytes, method="POST"):
        raise CarterAmbientError(401, "unauthorized")
    with pytest.raises(CarterAmbientError):
        mesh_broadcast("https://r/", "T", channel="home", event="x", _send=unauthorized)


def test_module_is_importable_without_the_meshsocket_stack():
    """Stdlib-only, like notify_http, so a cron job or a Pi can drive these."""
    assert ambient.__spec__ is not None
    src = open(ambient.__file__).read()
    for forbidden in ("import meshsocket", "from meshsocket", "from .e2ee"):
        assert forbidden not in src


def test_every_request_sends_an_explicit_user_agent():
    """The relay host is behind Cloudflare, whose browser integrity check rejects
    urllib's default `Python-urllib/x.y` with a bare `403 error code: 1010` — a
    body indistinguishable from an entitlement failure. Verified on dev."""
    r = Recorder({"delivered": True})
    mesh_broadcast("https://r/", "T", channel="home", event="x", _send=r)
    assert r.headers.get("User-Agent"), "no User-Agent — Cloudflare will 403 this"
    assert "urllib" not in r.headers["User-Agent"].lower()

    r2 = Recorder({"registered": 1})
    live_activity_register("https://v/", "J", layout_id="x", push_token="T",
                           bundle_id="B", _send=r2)
    assert r2.headers.get("User-Agent")


# ── /surfaces: retained state + the one-call push fan-out ────────────────────
#
# The failure mode these guard is the same one the Live Activity tests guard: a
# call that returns 200 while no surface ever changes. For `/surfaces` that means
# a wrong layout id, a scalar that is quietly an object, or an `activity` key the
# relay does not read.

class SurfaceRecorder(Recorder):
    """Like Recorder, but tolerates the GET route's bodiless request."""

    def __call__(self, url, headers, body_bytes, method="POST"):
        self.url, self.headers, self.method = url, headers, method
        self.body = json.loads(body_bytes.decode()) if body_bytes else None
        out = dict(self.response)
        out["status"] = self.status
        return out


def test_register_token_posts_the_stored_tuple():
    rec = SurfaceRecorder({"ok": True})
    ambient.surfaces_register_token("https://v.example/", "jwt", layout_id="printer",
                                    kind="widget", key="temps",
                                    bundle_id="Mariner.CAR-TER", token="a1b2",
                                    _send=rec)
    assert rec.url == "https://v.example/surfaces/tokens" and rec.method == "POST"
    assert rec.body == {"layoutId": "printer", "kind": "widget", "key": "temps",
                        "token": "a1b2", "bundleId": "Mariner.CAR-TER"}


def test_deregister_token_uses_delete_with_the_same_body():
    rec = SurfaceRecorder({"ok": True})
    ambient.surfaces_deregister_token("https://v.example", "jwt", layout_id="printer",
                                      kind="control", key="lights",
                                      bundle_id="Mariner.CAR-TER", token="a1b2",
                                      _send=rec)
    assert rec.method == "DELETE"
    assert rec.body["kind"] == "control" and rec.body["key"] == "lights"


def test_token_registration_rejects_a_bad_kind_and_an_oversized_token():
    with pytest.raises(ValueError, match="kind must be one of"):
        ambient.surfaces_register_token("https://v.example", "jwt", layout_id="p",
                                        kind="island", key="k", bundle_id="b",
                                        token="a1", _send=SurfaceRecorder())
    with pytest.raises(ValueError, match="200 characters"):
        ambient.surfaces_register_token("https://v.example", "jwt", layout_id="p",
                                        kind="widget", key="k", bundle_id="b",
                                        token="f" * 201, _send=SurfaceRecorder())


def test_bundle_id_is_optional_so_the_relay_can_use_its_own_topic():
    rec = SurfaceRecorder({"ok": True})
    ambient.surfaces_register_token("https://v.example", "jwt", layout_id="p",
                                    kind="widget", key="k", bundle_id=None,
                                    token="a1", _send=rec)
    assert "bundleId" not in rec.body


def test_get_state_uses_GET_with_no_body_and_an_escaped_layout_id():
    rec = SurfaceRecorder({"layoutId": "my printer", "values": {"nozzle": 210}})
    out = ambient.surfaces_get_state("https://v.example", "jwt",
                                     layout_id="my printer", _send=rec)
    assert rec.method == "GET" and rec.body is None
    assert rec.url == "https://v.example/surfaces/state/my%20printer"
    assert out["values"] == {"nozzle": 210}


def test_get_state_returns_none_when_nothing_has_been_published():
    """404 is the normal answer before the first publish, not a failure — the
    caller wants `None`, not an exception to special-case."""
    assert ambient.surfaces_get_state("https://v.example", "jwt", layout_id="p",
                                      _send=SurfaceRecorder(status=404)) is None

    def raiser(url, headers, body, method="GET"):
        raise CarterAmbientError(404, "no state")
    assert ambient.surfaces_get_state("https://v.example", "jwt", layout_id="p",
                                      _send=raiser) is None


def test_get_state_still_raises_on_a_real_error():
    def raiser(url, headers, body, method="GET"):
        raise CarterAmbientError(403, "not entitled")
    with pytest.raises(CarterAmbientError):
        ambient.surfaces_get_state("https://v.example", "jwt", layout_id="p",
                                   _send=raiser)


def test_put_state_merges_without_pushing():
    rec = SurfaceRecorder({"ok": True, "updatedAt": 1700000000})
    ambient.surfaces_put_state("https://v.example", "jwt", layout_id="printer",
                               values={"nozzle": 215}, is_connected=True, _send=rec)
    assert rec.method == "PUT"
    assert rec.url == "https://v.example/surfaces/state/printer"
    assert rec.body == {"layoutId": "printer", "values": {"nozzle": 215},
                        "isConnected": True}


def test_put_state_needs_something_to_merge():
    with pytest.raises(ValueError, match="nothing to put"):
        ambient.surfaces_put_state("https://v.example", "jwt", layout_id="p",
                                   _send=SurfaceRecorder())


def test_publish_sends_state_and_activity_in_one_call():
    rec = SurfaceRecorder({"ok": True, "updatedAt": 1, "widgets": 2, "controls": 1,
                           "activity": 1, "pruned": 0,
                           "suppressed": {"widgets": False, "controls": False,
                                          "activity": False}})
    out = ambient.surfaces_publish("https://v.example", "jwt", layout_id="printer",
                                   values={"nozzle": 215, "state": "printing"},
                                   controls={"lights": True}, is_connected=True,
                                   activity={"priority": "opportunistic",
                                             "staleSeconds": 120, "event": "update"},
                                   force=True, _send=rec)
    assert rec.url == "https://v.example/surfaces/publish" and rec.method == "POST"
    assert rec.body == {"layoutId": "printer",
                        "values": {"nozzle": 215, "state": "printing"},
                        "controls": {"lights": True}, "isConnected": True,
                        "activity": {"staleSeconds": 120, "priority": "opportunistic",
                                     "event": "update"},
                        "force": True}
    assert out["suppressed"] == {"widgets": False, "controls": False, "activity": False}


def test_publish_omits_activity_unless_asked():
    rec = SurfaceRecorder({"ok": True})
    ambient.surfaces_publish("https://v.example", "jwt", layout_id="p",
                             values={"a": 1}, _send=rec)
    assert "activity" not in rec.body and "force" not in rec.body


def test_publish_accepts_an_empty_activity_so_the_relay_synthesizes_the_state():
    rec = SurfaceRecorder({"ok": True})
    ambient.surfaces_publish("https://v.example", "jwt", layout_id="p",
                             values={"a": 1}, activity={}, _send=rec)
    assert rec.body["activity"] == {}


def test_publish_rejects_a_nested_value():
    """Surfaces carry scalars; a dict would be stored and then fail to decode into
    the app's ControlValue, which reads on-device as 'the widget never updated'."""
    with pytest.raises(ValueError, match="values\\['nozzle'\\]"):
        ambient.surfaces_publish("https://v.example", "jwt", layout_id="p",
                                 values={"nozzle": {"c": 1}}, _send=SurfaceRecorder())


def test_publish_control_state_is_not_restricted_to_booleans():
    """A v2 Control Center tile may be a cycle (string) or a step (number), so its
    mirrored state is any scalar — unlike the v1 glance_update payload."""
    rec = SurfaceRecorder({"ok": True})
    ambient.surfaces_publish("https://v.example", "jwt", layout_id="p",
                             controls={"fan": "high", "volume": 40}, _send=rec)
    assert rec.body["controls"] == {"fan": "high", "volume": 40}


def test_publish_rejects_an_unknown_activity_key():
    with pytest.raises(ValueError, match="unknown activity key"):
        ambient.surfaces_publish("https://v.example", "jwt", layout_id="p",
                                 values={"a": 1}, activity={"contentstate": {}},
                                 _send=SurfaceRecorder())


def test_publish_rejects_a_start_event():
    """A publish drives activities that are already registered; opening one needs
    the attributes only /alerts/live-activity/push carries."""
    with pytest.raises(ValueError, match="event must be one of"):
        ambient.surfaces_publish("https://v.example", "jwt", layout_id="p",
                                 values={"a": 1}, activity={"event": "start"},
                                 _send=SurfaceRecorder())


def test_publish_rejects_a_bad_priority_and_relevance():
    with pytest.raises(ValueError, match="priority must be one of"):
        ambient.surfaces_publish("https://v.example", "jwt", layout_id="p",
                                 values={"a": 1}, activity={"priority": 10},
                                 _send=SurfaceRecorder())
    with pytest.raises(ValueError, match="relevanceScore"):
        ambient.surfaces_publish("https://v.example", "jwt", layout_id="p",
                                 values={"a": 1}, activity={"relevanceScore": 400},
                                 _send=SurfaceRecorder())


def test_publish_rejects_an_oversized_body():
    big = {f"c{i}": "x" * 80 for i in range(200)}
    with pytest.raises(ValueError, match="8192-byte limit"):
        ambient.surfaces_publish("https://v.example", "jwt", layout_id="p",
                                 values=big, _send=SurfaceRecorder())


def test_surface_layout_id_rejects_the_relay_key_delimiters():
    """`sf#<layoutId>` and `<kind>|<key>|…` are built by string concatenation, so a
    layout id carrying either could reach another layout's stored items."""
    for bad in ("ratelimit#other", "a|b"):
        with pytest.raises(ValueError, match="may not contain"):
            ambient.surfaces_publish("https://v.example", "jwt", layout_id=bad,
                                     values={"a": 1}, _send=SurfaceRecorder())


def test_surface_layout_id_must_be_present_and_bounded():
    with pytest.raises(ValueError, match="non-empty string"):
        ambient.surfaces_publish("https://v.example", "jwt", layout_id="",
                                 values={"a": 1}, _send=SurfaceRecorder())
    with pytest.raises(ValueError, match="128 UTF-8 bytes"):
        ambient.surfaces_publish("https://v.example", "jwt", layout_id="x" * 129,
                                 values={"a": 1}, _send=SurfaceRecorder())
