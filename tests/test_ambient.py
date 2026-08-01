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
