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
from urllib.parse import quote, urlsplit, urlunsplit

__all__ = [
    "APPLE_REFERENCE_EPOCH", "LA_ATTRIBUTES_TYPE", "CONTENT_STATE_VERSION",
    "SLOT_KINDS", "CarterAmbientError",
    "apple_date", "slot", "content_state", "activity_attributes",
    "canonical_layout_id",
    "live_activity_register", "live_activity_deregister", "live_activity_push",
    "mesh_broadcast", "glance_update",
    "SURFACE_TOKEN_KINDS", "SURFACE_STATE_LIMIT", "ACTIVITY_PRIORITIES",
    "surfaces_register_token", "surfaces_deregister_token",
    "surfaces_get_state", "surfaces_put_state", "surfaces_publish",
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
    """One request. ``payload=None`` sends no body at all — that is how the GET
    routes ride this helper, and why `Content-Type` is omitted in that case
    rather than announcing a JSON body that isn't there."""
    headers = {"Authorization": token, "User-Agent": _USER_AGENT}
    if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a finite positive number")
    if payload is None:
        body_bytes = None
    else:
        headers["Content-Type"] = "application/json"
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


# ── /surfaces — the relay's retained surface state + push fan-out ─────────────
#
# The Live Activity route above pushes ONE surface. `/surfaces` is the other half
# of the same story: the relay keeps the layout's latest values, and one publish
# pokes every surface that can render them — Home/Lock Screen widgets (iOS 26
# WidgetKit push), Control Center controls (iOS 18 control push) and the Live
# Activity — then the surface pulls the retained state back when iOS wakes it.
#
# That retention is the point. A widget woken by the system hours later has no
# socket and no app process; `GET /surfaces/state/<layoutId>` is the only place
# it can read a value from. A hub that publishes and then dies still leaves every
# surface correct.

#: Push-token kinds the relay stores per layout. `widget` tokens come from
#: WidgetKit's push handler, `control` tokens from the Control Center push
#: handler; each is scoped by a `key` (the widget/control kind) and the bundle id
#: that minted it, because the APNs topic is `<bundleId>.push-type.<kind>`.
SURFACE_TOKEN_KINDS = ("widget", "control")

#: The relay stores the merged surface state as one JSON string with a hard 8 KB
#: cap. Exceeding it is rejected server-side, so it is checked here where the
#: caller can still see which publish was too big.
SURFACE_STATE_LIMIT = 8192

#: `activity.priority` on a publish. These are the ActivityKit words, not the
#: APNs numbers `live_activity_push` takes (`immediate` = 10, `opportunistic` = 5)
#: — the relay does that translation.
ACTIVITY_PRIORITIES = ("immediate", "opportunistic")

#: `activity.event` on a publish. There is no `"start"`: a publish drives the
#: activities that are already registered for the layout. Use
#: :func:`live_activity_push` with `event="start"` and explicit attributes to
#: open one.
ACTIVITY_EVENTS = ("update", "end")

_ACTIVITY_KEYS = ("contentState", "staleSeconds", "priority", "relevanceScore", "event")


def _surface_layout_id(layout_id):
    """Every `/surfaces` route is keyed by the canonical layout id — see
    :func:`canonical_layout_id`. A wrong one is the worst failure here: the call
    returns 200 and no surface ever changes.

    `#` and `|` are refused because the relay builds its storage keys out of them
    (`sf#<layoutId>`, and `"<kind>|<key>|<bundleId>|<token>"` token entries): a
    layout id containing either could address another layout's rate-limit item or
    split a stored token apart."""
    if not isinstance(layout_id, str) or not layout_id:
        raise ValueError("layout_id must be a non-empty string "
                         "— see canonical_layout_id()")
    if len(layout_id.encode()) > 128:
        raise ValueError("layout_id must be <= 128 UTF-8 bytes")
    bad = [c for c in ("#", "|") if c in layout_id]
    if bad:
        raise ValueError(f"layout_id may not contain {bad} — the relay's surface "
                         f"storage keys are delimited by them")
    return layout_id


def _surface_map(mapping, name):
    """Validate a `values`/`controls` map: non-empty string ids to scalars.

    Unlike :func:`glance_update`, `controls` is NOT restricted to booleans — a v2
    Control Center tile may be a `cycle` (string state), a `step` or a `set`
    (numbers), so its mirrored state is any scalar the app's `ControlValue`
    decodes."""
    if not isinstance(mapping, dict):
        raise ValueError(f"{name} must map control ids to scalar values")
    for key, value in mapping.items():
        if not isinstance(key, str) or not key:
            raise ValueError(f"{name} keys must be non-empty control ids")
        try:
            _scalar(value)
        except ValueError:
            raise ValueError(f"{name}[{key!r}] must be a string, bool or finite "
                             f"number — surfaces carry scalars, not objects") from None
    return dict(mapping)


def _surface_state_body(layout_id, values, controls, is_connected):
    """The `{values, controls, isConnected}` half every surface route shares.
    Omitted keys are left alone server-side; the relay merges onto what it holds."""
    body = {"layoutId": _surface_layout_id(layout_id)}
    if values is not None:
        body["values"] = _surface_map(values, "values")
    if controls is not None:
        body["controls"] = _surface_map(controls, "controls")
    if is_connected is not None:
        if not isinstance(is_connected, bool):
            raise ValueError("is_connected must be a bool")
        body["isConnected"] = is_connected
    return body


def _surface_activity(activity):
    """Validate the optional `activity` block of a publish.

    Only the five documented keys are accepted. An unknown key is a typo the relay
    would drop in silence, which on this pipeline reads as "the Live Activity just
    doesn't update" — so it fails here instead."""
    if not isinstance(activity, dict):
        raise ValueError("activity must be an object — see ACTIVITY_PRIORITIES")
    unknown = sorted(set(activity) - set(_ACTIVITY_KEYS))
    if unknown:
        raise ValueError(f"unknown activity key(s) {unknown}; allowed: "
                         f"{list(_ACTIVITY_KEYS)}")
    out = {}
    content = activity.get("contentState")
    if content is not None:
        if not isinstance(content, dict):
            raise ValueError("activity.contentState must be an object — build it "
                             "with content_state()")
        _json_size(content, 3072, "activity.contentState")
        out["contentState"] = content
    stale = activity.get("staleSeconds")
    if stale is not None:
        if isinstance(stale, bool) or not isinstance(stale, int) or stale <= 0:
            raise ValueError("activity.staleSeconds must be a positive integer")
        out["staleSeconds"] = stale
    priority = activity.get("priority")
    if priority is not None:
        if priority not in ACTIVITY_PRIORITIES:
            raise ValueError(f"activity.priority must be one of "
                             f"{list(ACTIVITY_PRIORITIES)}, got {priority!r}")
        out["priority"] = priority
    relevance = activity.get("relevanceScore")
    if relevance is not None:
        _finite_number(relevance, "activity.relevanceScore")
        if not 0 <= relevance <= 100:
            raise ValueError("activity.relevanceScore must be within 0..100")
        out["relevanceScore"] = relevance
    event = activity.get("event")
    if event is not None:
        if event not in ACTIVITY_EVENTS:
            raise ValueError(f"activity.event must be one of {list(ACTIVITY_EVENTS)}, "
                             f"got {event!r} — a publish drives registered "
                             f"activities; open one with live_activity_push(event='start')")
        out["event"] = event
    return out


def _surface_token_body(layout_id, kind, key, bundle_id, token):
    if kind not in SURFACE_TOKEN_KINDS:
        raise ValueError(f"kind must be one of {list(SURFACE_TOKEN_KINDS)}, got {kind!r}")
    fields = {"key": key, "token": token}
    for name, value in fields.items():
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name} is required and must be a non-empty string")
    if len(token) > 200:
        raise ValueError("token must be <= 200 characters")
    # `bundleId` is optional: omitting it lets the relay fall back to its own
    # configured topic. It is part of the stored entry either way, so register and
    # de-register must agree — omit it in both calls or in neither.
    if bundle_id is not None:
        if not isinstance(bundle_id, str) or not bundle_id:
            raise ValueError("bundle_id must be a non-empty string or None")
        fields["bundleId"] = bundle_id
    return {"layoutId": _surface_layout_id(layout_id), "kind": kind, **fields}


def surfaces_register_token(validator_url, session_jwt, *, layout_id, kind, key,
                            bundle_id, token, timeout=10, _send=None):
    """Register a widget or Control Center push token (POST /surfaces/tokens).

    The device normally does this itself; this exists so a hub, a test or a
    provisioning script can drive the same route. `key` is the widget/control
    kind the token was issued for, `bundle_id` the build that minted it — both
    ride the APNs topic (`<bundleId>.push-type.<kind>`), so a mismatch is
    rejected by APNs as `DeviceTokenNotForTopic`.

    Anyone on the account may register; only an owner/device/hub credential may
    publish."""
    return _post(validator_url.rstrip("/") + "/surfaces/tokens", session_jwt,
                 _surface_token_body(layout_id, kind, key, bundle_id, token),
                 timeout=timeout, _send=_send)


def surfaces_deregister_token(validator_url, session_jwt, *, layout_id, kind, key,
                              bundle_id, token, timeout=10, _send=None):
    """Drop a registered surface token (DELETE /surfaces/tokens).

    Pass exactly what was registered — the stored entry is the whole
    `kind|key|bundleId|token` tuple. Idempotent."""
    return _post(validator_url.rstrip("/") + "/surfaces/tokens", session_jwt,
                 _surface_token_body(layout_id, kind, key, bundle_id, token),
                 method="DELETE", timeout=timeout, _send=_send)


def surfaces_get_state(validator_url, session_jwt, *, layout_id, timeout=10, _send=None):
    """Read the relay's retained surface state (GET /surfaces/state/<layoutId>).

    Returns `{layoutId, values, controls, isConnected, updatedAt, status}`, or
    **None** when the relay holds nothing for this layout yet. A 404 is the normal
    answer before the first publish, not an error — that is why it is `None`
    rather than a raise."""
    url = (validator_url.rstrip("/") + "/surfaces/state/"
           + quote(_surface_layout_id(layout_id), safe=""))
    try:
        out = _post(url, session_jwt, None, method="GET", timeout=timeout, _send=_send)
    except CarterAmbientError as e:
        if e.status == 404:
            return None
        raise
    if isinstance(out, dict) and out.get("status") == 404:
        return None
    return out


def surfaces_put_state(validator_url, session_jwt, *, layout_id, values=None,
                       controls=None, is_connected=None, timeout=10, _send=None):
    """Merge values into the retained state WITHOUT pushing (PUT /surfaces/state/…).

    Use this for the readings a surface should show the next time iOS wakes it,
    when there is no reason to spend a push budget now — telemetry between
    publishes, or seeding state before any surface exists. Returns
    `{ok, updatedAt}`.

    The merge is per key: named keys are replaced, unnamed ones are kept, and
    `isConnected` changes only when sent — so a hub that publishes one sensor does
    not blank the others. Members get `403`; only an owner/device/hub credential
    may write state."""
    body = _surface_state_body(layout_id, values, controls, is_connected)
    if len(body) == 1:
        raise ValueError("nothing to put — pass values, controls or is_connected")
    _json_size(body, SURFACE_STATE_LIMIT, "surface state")
    url = (validator_url.rstrip("/") + "/surfaces/state/"
           + quote(body["layoutId"], safe=""))
    return _post(url, session_jwt, body, method="PUT", timeout=timeout, _send=_send)


def surfaces_publish(validator_url, session_jwt, *, layout_id, values=None,
                     controls=None, is_connected=None, activity=None, force=False,
                     timeout=10, _send=None):
    """Merge state AND poke every surface for the layout (POST /surfaces/publish).

    One call reaches all three push paths: widget tokens, Control Center control
    tokens, and the layout's registered Live Activities. Pass `activity` (even
    `{}`) to include the Live Activity — without it the state merges and only the
    widget/control tokens are poked. With `activity` but no `contentState`, the
    relay builds the content state from the merged values, so a hub rarely needs
    to assemble one.

    The reply reports what happened per surface::

        {"ok": true, "updatedAt": 1758… , "widgets": 2, "controls": 1,
         "activity": 1, "pruned": 0,
         "suppressed": {"widgets": false, "controls": false, "activity": false}}

    `suppressed` is not a failure. The relay enforces its own floors (widgets
    ≥ 60 s, controls ≥ 10 s, activity ≥ 2 s per account+layout): inside a floor
    the **state still merges** — the surface shows the new value at its next
    wake — only the push is skipped. Publishing at telemetry rate is therefore
    safe and simply coalesces. `force=True` asks for the higher-priority push
    where the floor allows it; it does not lift the floor.

    `pruned` counts tokens APNs rejected (410 / BadDeviceToken) and the relay
    dropped.

    Two rejections to expect, both raised as :class:`CarterAmbientError`: `413`
    when the MERGED state passes 8 KB (the size checked here is only what this
    call sends — the relay holds the rest), and `429` with a `retryAfter` body
    when the account's publish bucket (burst 120, 10/min) is empty."""
    body = _surface_state_body(layout_id, values, controls, is_connected)
    if activity is not None:
        body["activity"] = _surface_activity(activity)
    if force:
        if not isinstance(force, bool):
            raise ValueError("force must be a bool")
        body["force"] = True
    if len(body) == 1:
        raise ValueError("nothing to publish — pass values, controls, is_connected "
                         "or activity")
    _json_size(body, SURFACE_STATE_LIMIT, "surfaces publish body")
    return _post(validator_url.rstrip("/") + "/surfaces/publish", session_jwt, body,
                 timeout=timeout, _send=_send)
