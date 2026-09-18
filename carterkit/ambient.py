"""Ambient surfaces — the APIs that reach a CAR-TER device when the app is not
running: the Live Activity / Dynamic Island push pipeline, and the outbound mesh
bridge that carries a press with no socket held open.

Stdlib-only (urllib), like `notify_http`, so a cron job or a Pi can drive these
without the MeshSocket stack.

Two hosts, and they are NOT the same one:

* Live Activity endpoints live on the **validator** base URL (the same host as
  `/alerts/notify`) — pass `validator_url`.
* `mesh_broadcast` lives on the **relay** host (`https://` against the same host
  the socket dials with `wss://`) — pass `relay_url`. It is served by the gateway
  so a press costs no Connect+ slot.

Delivery is best-effort. Silent background pushes may be delayed or suppressed,
including after a force-quit. Visible notifications can carry a glance refresh
through the notification extension, but delivery and extension execution are not
guaranteed. ActivityKit uses its own push route. Direct WidgetKit pushes on iOS 26
are not registered by this backend yet.
"""
import json
import math
import urllib.error
import urllib.request
from urllib.parse import urlsplit, urlunsplit

__all__ = [
    "APPLE_REFERENCE_EPOCH", "LA_ATTRIBUTES_TYPE", "CONTENT_STATE_VERSION",
    "SLOT_KINDS", "CarterAmbientError",
    "apple_date", "slot", "content_state", "activity_attributes",
    "canonical_layout_id",
    "live_activity_register", "live_activity_deregister", "live_activity_push",
    "mesh_broadcast", "glance_update",
]

#: ActivityKit decodes ContentState with Swift's DEFAULT ``Codable``, so every
#: ``Date`` on the wire is **seconds since 2001-01-01**, not since 1970 and not
#: ISO-8601. Get it wrong and iOS drops the push with no error anywhere — on the
#: device, in the relay, or in the APNs response. Use :func:`apple_date`.
APPLE_REFERENCE_EPOCH = 978307200

#: Must match the Swift ``ActivityAttributes`` struct name VERBATIM. iOS matches a
#: push-to-start payload to an activity type by this string; a mismatch is
#: discarded on-device, silently. Renaming the Swift type is a wire break.
LA_ATTRIBUTES_TYPE = "LayoutActivityAttributes"

#: Version of the content-state shape this module emits. The shape is a
#: compatibility commitment — the app decodes it with a fixed struct — so bump
#: this when a field is added and keep older readers in mind.
CONTENT_STATE_VERSION = 1

#: Slot kinds the app's renderer understands. An unknown kind fails the on-device
#: decode and the push vanishes without a trace, so this is validated here.
SLOT_KINDS = ("gauge", "ring", "light", "number", "text", "bool")


class CarterAmbientError(Exception):
    """An ambient endpoint rejected the call. ``status`` is the HTTP code (0 for a
    transport failure); ``body`` is the server's message."""

    def __init__(self, status, body):
        super().__init__(f"HTTP {status}: {body}")
        self.status = status
        self.body = body


#: Sent on every request. The relay host sits behind Cloudflare, whose browser
#: integrity check rejects urllib's default `Python-urllib/x.y` agent with a bare
#: `403 error code: 1010` — a body that looks exactly like an entitlement failure
#: and sends you hunting the wrong bug. Verified on dev: default agent 403s, this
#: one gets through. Do not remove.
_USER_AGENT = "carterkit/python"


def _post(url, token, payload, *, method="POST", timeout=10, _send=None):
    headers = {"Authorization": token, "Content-Type": "application/json",
               "User-Agent": _USER_AGENT}
    if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a finite positive number")
    body_bytes = _json_size(payload)
    if _send is not None:
        return _send(url, headers, body_bytes, method)
    req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            out = json.loads(raw) if raw.strip() else {}
            if not isinstance(out, dict):
                raise ValueError("endpoint returned a non-object JSON response")
            out["status"] = resp.status
            return out
    except urllib.error.HTTPError as e:
        raise CarterAmbientError(e.code, e.read().decode(errors="replace")) from None
    except (OSError, ValueError) as e:
        raise CarterAmbientError(0, str(e)) from None


def _finite_number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")


def _scalar(value):
    if isinstance(value, (str, bool)):
        return
    _finite_number(value, "control value")


def _json_size(value, limit=None, name="payload"):
    encoded = json.dumps(value, allow_nan=False, ensure_ascii=False, separators=(",", ":")).encode()
    if limit is not None and len(encoded) > limit:
        raise ValueError(f"{name} exceeds the backend's {limit}-byte limit")
    return encoded


def _validate_slot(value):
    if not isinstance(value, dict):
        raise ValueError("a slot must be an object built with slot()")
    if value.get("kind") not in SLOT_KINDS or not isinstance(value.get("controlId"), str) or not value["controlId"]:
        raise ValueError("slot requires a controlId and supported kind")
    if not isinstance(value.get("label"), str):
        raise ValueError("slot requires a string label")
    if value.get("value") is not None:
        _scalar(value["value"])
    for key in ("min", "max"):
        if value.get(key) is not None:
            _finite_number(value[key], key)
    for key in ("formatValue", "tint"):
        if value.get(key) is not None and not isinstance(value[key], str):
            raise ValueError(f"slot {key} must be a string")
    colors = value.get("statusColors")
    if colors is not None and (not isinstance(colors, dict) or
                              any(not isinstance(k, str) or not isinstance(v, str) for k, v in colors.items())):
        raise ValueError("statusColors must map strings to color strings")


def glance_update(*, layout_id, values=None, controls=None, hero=None, slots=None,
                  is_connected=None, title=None, icon=None, tint=None):
    """Build a widget/Control Center refresh for ``notify_http(glance=...)``.

    ``values`` updates existing readings by control ID without replacing the
    featured slots. ``controls`` mirrors toggle state keyed by system-control ID.
    Use title/icon plus hero/slots to seed a snapshot before its first publication.
    """
    if not isinstance(layout_id, str) or not layout_id or len(layout_id.encode()) > 128:
        raise ValueError("layout_id must be non-empty and <= 128 UTF-8 bytes")
    out = {"layoutId": layout_id}
    for name, mapping in (("values", values), ("controls", controls)):
        if mapping is not None:
            if not isinstance(mapping, dict) or any(not isinstance(k, str) or not k for k in mapping):
                raise ValueError(f"{name} must map non-empty control IDs to values")
            for value in mapping.values():
                if name == "controls" and not isinstance(value, bool):
                    raise ValueError("controls must contain Boolean toggle states")
                _scalar(value)
            out[name] = dict(mapping)
    if is_connected is not None:
        if not isinstance(is_connected, bool):
            raise ValueError("is_connected must be a bool")
        out["isConnected"] = is_connected
    if slots is not None:
        if len(slots) > 3:
            raise ValueError("glance supports at most 3 secondary slots; use values for other readings")
        out["slots"] = list(slots)
        for entry in out["slots"]:
            _validate_slot(entry)
    if hero is not None:
        _validate_slot(hero)
    for key, value in (("title", title), ("icon", icon), ("tint", tint)):
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
    for key, value in (("hero", hero), ("title", title), ("icon", icon), ("tint", tint)):
        if value is not None:
            out[key] = value
    _json_size(out, 2048, "glance")
    return out


# ── Shapes ───────────────────────────────────────────────────────────────────

def apple_date(unix_seconds):
    """Convert a normal unix timestamp to the reference-date seconds ActivityKit
    expects. Always run timestamps through this — see APPLE_REFERENCE_EPOCH."""
    _finite_number(unix_seconds, "unix_seconds")
    return unix_seconds - APPLE_REFERENCE_EPOCH


def slot(control_id, label, kind, value, **extra):
    """One hero/slot entry. Validates `kind`, because an unknown one fails the
    on-device decode and the push disappears with no error to trace."""
    if kind not in SLOT_KINDS:
        raise ValueError(f"kind must be one of {SLOT_KINDS}, got {kind!r}")
    if not isinstance(control_id, str) or not control_id or not isinstance(label, str):
        raise ValueError("control_id must be non-empty and label must be a string")
    if value is not None:
        _scalar(value)
    aliases = {"format_value": "formatValue", "status_colors": "statusColors"}
    extra = {aliases.get(key, key): val for key, val in extra.items()}
    if {"controlId", "label", "kind", "value"}.intersection(extra):
        raise ValueError("extra fields cannot override slot identity or value")
    out = {"controlId": control_id, "label": label, "kind": kind, "value": value}
    out.update(extra)
    _validate_slot(out)
    _json_size(out)
    return out


def content_state(*, hero=None, slots=None, is_connected=True, updated_at,
                  hero_history=None):
    """Build a `LayoutActivityAttributes.ContentState`.

    `updated_at` must already be reference-date seconds — pass
    ``apple_date(time.time())``. It is required rather than defaulted precisely
    because a wrong epoch here is the single most common silent failure in this
    pipeline, and a default would hide it.
    """
    _finite_number(updated_at, "updated_at")
    if not isinstance(is_connected, bool):
        raise ValueError("is_connected must be a bool")
    if updated_at > APPLE_REFERENCE_EPOCH:
        raise ValueError(
            "updated_at looks like a unix timestamp; ActivityKit wants seconds "
            "since 2001-01-01 — pass apple_date(time.time())")
    state = {
        "slots": list(slots or []),
        "isConnected": bool(is_connected),
        "updatedAt": updated_at,
    }
    if hero is not None:
        _validate_slot(hero)
        state["hero"] = hero
    for entry in state["slots"]:
        _validate_slot(entry)
    if hero_history:
        history = list(hero_history)
        if len(history) > 24:
            raise ValueError("hero_history supports at most 24 points")
        for value in history:
            _finite_number(value, "hero_history")
        state["heroHistory"] = history
    if len(state["slots"]) > 3:
        raise ValueError("a Live Activity supports at most 3 secondary slots")
    _json_size(state, 3072, "content_state")
    return state


def activity_attributes(*, layout_id, title, icon, started_at, tint=None):
    """Build the fixed `LayoutActivityAttributes` a **push-to-start** needs.

    Every field except `tint` is REQUIRED. Swift's synthesized `Decodable` does
    not apply property default values, so a missing key — `startedAt` especially,
    which *looks* optional because the Swift property has a default — throws
    `keyNotFound` and iOS drops the start push with no error anywhere.
    """
    for name, value in (("layout_id", layout_id), ("title", title),
                        ("icon", icon), ("started_at", started_at)):
        if value is None or value == "":
            raise ValueError(f"{name} is required — a missing key makes iOS drop "
                             "the push-to-start silently")
    _finite_number(started_at, "started_at")
    for name, value in (("layout_id", layout_id), ("title", title), ("icon", icon)):
        if not isinstance(value, str):
            raise ValueError(f"{name} must be a string")
    if tint is not None and not isinstance(tint, str):
        raise ValueError("tint must be a string")
    if started_at > APPLE_REFERENCE_EPOCH:
        raise ValueError(
            "started_at looks like a unix timestamp; pass apple_date(time.time())")
    attrs = {"layoutId": layout_id, "title": title, "icon": icon,
             "startedAt": started_at}
    if tint is not None:
        attrs["tint"] = tint
    _json_size(attrs, 1024, "attributes")
    return attrs


def canonical_layout_id(layout, *, filename=None):
    """The one id every ambient wire surface means by ``layoutId``.

    It is ``config.id`` when the layout declares one, else the layout's filename.
    That is the only form stable across devices, which is what a shared room needs
    — every member must register under the same key for one hub push to reach them
    all. Guessing wrong is the worst failure mode in this pipeline: the call
    returns ``200`` and nothing happens.

    `layout` may be a dict (a parsed layout), an object with `.id`, or None.
    """
    declared = None
    if not isinstance(layout, dict) and isinstance(getattr(layout, "layout", None), dict):
        layout = layout.layout
    if isinstance(layout, dict):
        declared = layout.get("id")
    elif layout is not None:
        declared = getattr(layout, "id", None)
    resolved = declared or filename
    if not resolved:
        raise ValueError("layout declares no id — pass filename= for the fallback")
    if not isinstance(resolved, str) or len(resolved.encode()) > 128:
        raise ValueError("layout id must be a string of at most 128 UTF-8 bytes")
    return resolved


# ── Live Activity ────────────────────────────────────────────────────────────

def live_activity_register(validator_url, session_jwt, *, layout_id, push_token,
                           bundle_id, kind="update", _send=None):
    """Register a device's ActivityKit push token (POST /alerts/live-activity).

    `layout_id` must be the canonical id (see :func:`canonical_layout_id`), and is
    ignored for ``kind="start"`` (a push-to-start token is app-wide, issued per
    ActivityAttributes type, not per layout).

    `bundle_id` decides the APNs topic and must match the build that minted the
    token — `Mariner.CAR-TER` for App Store/TestFlight, `Mariner.CAR-TER.dev` for
    a Personal build. One account legitimately mixes both; a wrong topic is
    rejected by APNs as `DeviceTokenNotForTopic`.
    """
    if kind not in ("update", "start"):
        raise ValueError('kind must be "update" or "start"')
    if kind != "start" and not layout_id:
        raise ValueError("layout_id is required for an update-token registration")
    if not push_token:
        raise ValueError("push_token is required")
    return _post(validator_url.rstrip("/") + "/alerts/live-activity", session_jwt,
                 {"layoutId": layout_id or "", "pushToken": push_token,
                  "bundleId": bundle_id, "kind": kind}, _send=_send)


def live_activity_deregister(validator_url, session_jwt, *, layout_id, push_token,
                             bundle_id, kind="update", _send=None):
    """Drop a registered token (DELETE /alerts/live-activity), called when a
    session ends.

    Pass exactly what was registered — including `bundle_id`, which is part of the
    stored entry. Idempotent: de-registering an unknown token succeeds.

    Without this the stored set is append-only in practice: APNs staleness is the
    only other way a token leaves, and a token whose activity ended cleanly is not
    stale — the device would keep receiving pushes for a dead session.
    """
    return _post(validator_url.rstrip("/") + "/alerts/live-activity", session_jwt,
                 {"layoutId": layout_id or "", "pushToken": push_token,
                  "bundleId": bundle_id, "kind": kind},
                 method="DELETE", _send=_send)


def live_activity_push(validator_url, session_jwt, *, layout_id, event,
                       content_state, attributes=None, alert_title=None,
                       alert_body=None, stale_seconds=None, priority=10,
                       relevance_score=None, timeout=10, _send=None):
    """Drive a device's Live Activity (POST /alerts/live-activity/push).

    `event` is ``"start"`` (open one on a device where the app is not running),
    ``"update"``, or ``"end"``. ``"start"`` requires `attributes` — build it with
    :func:`activity_attributes`, which enforces the required keys.

    `priority` 10 is immediate and draws on the device's ActivityKit budget; 5 is
    opportunistic. Sending every update at 10 is what gets an app throttled.
    """
    if event not in ("start", "update", "end"):
        raise ValueError('event must be "start", "update" or "end"')
    if event == "start" and not attributes:
        raise ValueError('event "start" requires attributes — see activity_attributes()')
    if priority not in (5, 10):
        raise ValueError("priority must be 5 (opportunistic) or 10 (immediate)")
    if not isinstance(layout_id, str) or not layout_id or len(layout_id.encode()) > 128:
        raise ValueError("layout_id must be non-empty and <= 128 UTF-8 bytes")
    if not isinstance(content_state, dict):
        raise ValueError("content_state must be an object")
    _json_size(content_state, 3072, "content_state")
    if attributes is not None:
        if not isinstance(attributes, dict):
            raise ValueError("attributes must be an object")
        if attributes.get("layoutId") != layout_id:
            raise ValueError("attributes.layoutId must match layout_id")
        _json_size(attributes, 1024, "attributes")
    if stale_seconds is not None and (isinstance(stale_seconds, bool) or not isinstance(stale_seconds, int) or stale_seconds <= 0):
        raise ValueError("stale_seconds must be a positive integer")
    if relevance_score is not None:
        _finite_number(relevance_score, "relevance_score")
        if not 0 <= relevance_score <= 100:
            raise ValueError("relevance_score must be within 0..100")
    payload = {"layoutId": layout_id, "event": event, "contentState": content_state,
               "priority": priority}
    if attributes is not None:
        payload["attributes"] = attributes
    if alert_title is not None:
        payload["alertTitle"] = alert_title
    if alert_body is not None:
        payload["alertBody"] = alert_body
    if stale_seconds is not None:
        payload["staleSeconds"] = stale_seconds
    if relevance_score is not None:
        payload["relevanceScore"] = relevance_score
    return _post(validator_url.rstrip("/") + "/alerts/live-activity/push",
                 session_jwt, payload, timeout=timeout, _send=_send)


# ── Outbound mesh bridge ─────────────────────────────────────────────────────

def mesh_broadcast(relay_url, token, *, channel, event, payload=None,
                   layout_id=None, action_id=None, timeout=10, _send=None):
    """Put one broadcast frame on a channel over HTTP (POST /mesh/broadcast).

    This is the escape hatch for a caller that cannot hold a WebSocket — the
    widget/Control Center extension with the app dead, a shell script, a cron job.
    The frame the mesh sees is ``{"msg_type": event, **payload}``, exactly what a
    control's sync filter matches on.

    `relay_url` is the **relay** host (`https://` against the host the socket
    dials with `wss://`), NOT the validator base URL. `token` is the same
    credential the layout connects with.

    `action_id` makes the call idempotent. The relay deduplicates within its ten-minute window; retrying inside that window
    normally avoids rebroadcasting: the reply carries ``duplicate: true`` and echoes the first
    result. Pass one for anything non-idempotent — a toggle re-fired by a retry
    flips the light back.

    Returns the parsed body plus ``status``:

    * ``200`` with ``delivered: true`` — at least one peer was on the channel.
    * ``200`` with no ``delivered`` key — sent, but the roster did not answer in
      time. Make no delivery claim; do NOT treat it as a failure.
    * ``202`` with ``delivered: false`` — accepted, nobody was listening. Queue it.
    * ``429`` — rate limited; back off using ``retryAfter``.
    * ``503`` — the mesh was unreachable and nothing was sent. Queue and retry;
      the `action_id` claim is released, so the retry genuinely sends.

    ``429`` and ``503`` are returned rather than raised, because both mean "try
    again later" rather than "you called this wrong".
    """
    if not channel or not event:
        raise ValueError("channel and event are required")
    if payload is not None and not isinstance(payload, dict):
        raise ValueError("payload must be a dict (it is merged as siblings of msg_type)")
    parts = urlsplit(relay_url)
    scheme = {"wss": "https", "ws": "http"}.get(parts.scheme, parts.scheme)
    if scheme not in ("https", "http") or not parts.netloc or parts.username or parts.password:
        raise ValueError("relay_url must be an HTTP(S) or WS(S) endpoint without embedded credentials")
    relay_url = urlunsplit((scheme, parts.netloc, "", "", ""))
    # Match CAR-TER's bridge: broadcast_request is a transport verb; the
    # semantic msg_type in the authored payload is the event the hub handles.
    semantic = payload.get("msg_type") if payload else None
    if isinstance(semantic, str) and semantic.strip():
        event = semantic
    body = {"channel": channel, "event": event}
    if payload is not None:
        body["payload"] = payload
    if layout_id is not None:
        body["layoutId"] = layout_id
    if action_id is not None:
        body["actionId"] = action_id
    try:
        return _post(relay_url.rstrip("/") + "/mesh/broadcast", token, body, timeout=timeout, _send=_send)
    except CarterAmbientError as e:
        if e.status in (429, 503):
            try:
                out = json.loads(e.body) if e.body.strip() else {}
            except ValueError:
                out = {}
            out["status"] = e.status
            return out
        raise
