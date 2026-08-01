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

Delivery guarantees, which the choice of route decides (see also `notify_http`'s
`silent=`):

=========================  ===========  ===========  ==================
App state                  silent push  NSE (alert)  Live Activity push
=========================  ===========  ===========  ==================
foreground / backgrounded  yes          yes          yes
evicted by system          yes          yes          yes
**force-quit by user**     **NO**       **yes**      yes
=========================  ===========  ===========  ==================

A widget or Control Center value can only be refreshed by a process of ours, and
after a force-quit the only one iOS will start is the notification service
extension — which exists to service a *user-visible* notification. So a silent
refresh is free and invisible but stops at force-quit; an alerting one always
shows a notification and always works. Never promise the latter on the former.
"""
import json
import urllib.error
import urllib.request

__all__ = [
    "APPLE_REFERENCE_EPOCH", "LA_ATTRIBUTES_TYPE", "CONTENT_STATE_VERSION",
    "SLOT_KINDS", "CarterAmbientError",
    "apple_date", "slot", "content_state", "activity_attributes",
    "canonical_layout_id",
    "live_activity_register", "live_activity_deregister", "live_activity_push",
    "mesh_broadcast",
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


def _post(url, token, payload, *, method="POST", _send=None):
    headers = {"Authorization": token, "Content-Type": "application/json",
               "User-Agent": _USER_AGENT}
    body_bytes = json.dumps(payload).encode()
    if _send is not None:
        return _send(url, headers, body_bytes, method)
    req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            out = json.loads(raw) if raw.strip() else {}
            out["status"] = resp.status
            return out
    except urllib.error.HTTPError as e:
        raise CarterAmbientError(e.code, e.read().decode(errors="replace")) from None


# ── Shapes ───────────────────────────────────────────────────────────────────

def apple_date(unix_seconds):
    """Convert a normal unix timestamp to the reference-date seconds ActivityKit
    expects. Always run timestamps through this — see APPLE_REFERENCE_EPOCH."""
    return unix_seconds - APPLE_REFERENCE_EPOCH


def slot(control_id, label, kind, value, **extra):
    """One hero/slot entry. Validates `kind`, because an unknown one fails the
    on-device decode and the push disappears with no error to trace."""
    if kind not in SLOT_KINDS:
        raise ValueError(f"kind must be one of {SLOT_KINDS}, got {kind!r}")
    out = {"controlId": control_id, "label": label, "kind": kind, "value": value}
    out.update(extra)
    return out


def content_state(*, hero=None, slots=None, is_connected=True, updated_at,
                  hero_history=None):
    """Build a `LayoutActivityAttributes.ContentState`.

    `updated_at` must already be reference-date seconds — pass
    ``apple_date(time.time())``. It is required rather than defaulted precisely
    because a wrong epoch here is the single most common silent failure in this
    pipeline, and a default would hide it.
    """
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
        state["hero"] = hero
    if hero_history:
        state["heroHistory"] = [float(v) for v in hero_history]
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
    if started_at > APPLE_REFERENCE_EPOCH:
        raise ValueError(
            "started_at looks like a unix timestamp; pass apple_date(time.time())")
    attrs = {"layoutId": layout_id, "title": title, "icon": icon,
             "startedAt": started_at}
    if tint is not None:
        attrs["tint"] = tint
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
    if isinstance(layout, dict):
        declared = layout.get("id")
    elif layout is not None:
        declared = getattr(layout, "id", None)
    if declared:
        return declared
    if not filename:
        raise ValueError("layout declares no id — pass filename= for the fallback")
    return filename


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
                       relevance_score=None, _send=None):
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
                 session_jwt, payload, _send=_send)


# ── Outbound mesh bridge ─────────────────────────────────────────────────────

def mesh_broadcast(relay_url, token, *, channel, event, payload=None,
                   layout_id=None, action_id=None, _send=None):
    """Put one broadcast frame on a channel over HTTP (POST /mesh/broadcast).

    This is the escape hatch for a caller that cannot hold a WebSocket — the
    widget/Control Center extension with the app dead, a shell script, a cron job.
    The frame the mesh sees is ``{"msg_type": event, **payload}``, exactly what a
    control's sync filter matches on.

    `relay_url` is the **relay** host (`https://` against the host the socket
    dials with `wss://`), NOT the validator base URL. `token` is the same
    credential the layout connects with.

    `action_id` makes the call idempotent. Re-POSTing the same one never
    re-broadcasts: the reply carries ``duplicate: true`` and echoes the first
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
    body = {"channel": channel, "event": event}
    if payload is not None:
        body["payload"] = payload
    if layout_id is not None:
        body["layoutId"] = layout_id
    if action_id is not None:
        body["actionId"] = action_id
    try:
        return _post(relay_url.rstrip("/") + "/mesh/broadcast", token, body, _send=_send)
    except CarterAmbientError as e:
        if e.status in (429, 503):
            try:
                out = json.loads(e.body) if e.body.strip() else {}
            except ValueError:
                out = {}
            out["status"] = e.status
            return out
        raise
