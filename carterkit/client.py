"""carter_connect — minimal Connect+ hub client. Wraps MeshSocket + E2EE so a maker
connects hardware to the Connect+ relay in a few lines. When an e2ee_key is provided
every frame this client SENDS (broadcasts AND request replies) is sealed, and every
sealed frame it receives is opened, freshness- and replay-checked, before a handler
sees it. Cleartext otherwise.

Receive-side policy in an E2EE session (`strict_e2ee`, default True): a plaintext
frame from a peer is DROPPED and counted. `strict_e2ee=False` passes such frames
through with a one-time warning per msg_type — a debugging aid for mixed deployments,
not a supported mode. Relay control frames (`_RELAY_CONTROL_TYPES`) are always
plaintext and always allowed. Room mode does not authenticate the sender: every
member holds the same key.

Also exposes `notify_http(...)` and `CarterClient.notify(...)` for sending a one-shot
push to every device on a Connect+ account (POST /alerts/notify). `notify_http` is
stdlib-only (urllib) so a cron job can fire a notification without the MeshSocket stack."""
import asyncio
import base64
import inspect
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from urllib.parse import urlsplit

from .notifications import notification_action

log = logging.getLogger(__name__)

# A device token refresh that comes back 403 is NOT on its own proof the device is
# gone: the validator answers 401 for an unknown or bad credential, so 403 also
# covers edge/WAF/gateway rejections that clear on their own. Treating a single one
# as permanent revocation once killed a hub's link for ~30 h. Require the rejection
# to repeat before believing it.
REFRESH_CONFIRM_ATTEMPTS = 3      # consecutive 403s before declaring revocation
REFRESH_CONFIRM_DELAY = 60.0      # gap between confirmation attempts (background)
REFRESH_CONNECT_DELAY = 2.0       # ...and at connect(), where boot latency matters

try:
    from meshsocket import MeshSocket          # pip install meshsocket
    from .e2ee import E2EESession
except ImportError:  # keep notify_http importable without the MeshSocket/crypto stack
    MeshSocket = None
    E2EESession = None


class CarterNotifyError(Exception):
    """Raised when /alerts/notify rejects a send. `status` is the HTTP code (0 for a
    client-side/config error); `detail` is the server body or a description."""
    def __init__(self, status, detail):
        super().__init__(f"notify failed ({status}): {detail}")
        self.status = status
        self.detail = detail


#: interruption-levels the relay accepts; "critical" needs Apple approval and is
#: rejected server-side, so fail fast here with the same story.
_INTERRUPTION_LEVELS = ("passive", "active", "time-sensitive")


def _normalize_sender(sender):
    """Accept `"Monroe"`, `("Monroe", avatar_url)`, or `{"name": ..., "avatarURL"/
    "avatar_url"/"avatar": ...}` → the wire `{"name", "avatarURL"?}` dict."""
    if sender is None:
        return None
    if isinstance(sender, str):
        out = {"name": sender}
    elif isinstance(sender, (tuple, list)):
        if not sender or len(sender) > 2:
            raise ValueError("sender tuple must be (name,) or (name, avatar_url)")
        out = {"name": sender[0]}
        if len(sender) == 2 and sender[1]:
            out["avatarURL"] = sender[1]
    elif isinstance(sender, dict):
        out = {"name": sender.get("name")}
        avatar = sender.get("avatarURL") or sender.get("avatar_url") or sender.get("avatar")
        if avatar:
            out["avatarURL"] = avatar
    else:
        raise ValueError("sender must be a name, (name, avatar_url), or dict")
    if not out.get("name") or len(out["name"]) > 64:
        raise ValueError("sender name must be non-empty and <= 64 chars")
    if len(out.get("avatarURL", "")) > 512:
        raise ValueError("sender avatar URL must be <= 512 chars")
    return out


def _normalize_actions(actions):
    """Preserve every iOS action option while retaining legacy shorthand forms."""
    if actions is None:
        return None, {}
    items = []
    if isinstance(actions, dict):
        for aid, spec in actions.items():
            if isinstance(spec, str):
                items.append({"id": aid, "title": spec})
            elif callable(spec):
                items.append({"id": aid, "title": aid, "callback": spec})
            elif isinstance(spec, (tuple, list)) and len(spec) == 2:
                items.append({"id": aid, "title": spec[0], "callback": spec[1]})
            elif isinstance(spec, dict):
                items.append({**spec, "id": aid, "title": spec.get("title") or spec.get("name") or aid})
            else:
                raise ValueError(f"action {aid!r}: expected title, callable, (title, fn), or dict")
    elif isinstance(actions, (list, tuple)):
        items = list(actions)
    else:
        raise ValueError("actions must be a dict or a list of dicts")
    if len(items) > 4:
        raise ValueError("at most 4 actions per notification")
    wire, callbacks, seen = [], {}, set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("wire-style actions need dicts with id and title")
        fn = item.get("func") or item.get("funct") or item.get("callback")
        action = notification_action(item.get("id"), item.get("title"), callback=fn,
            destructive=item.get("destructive", False), foreground=item.get("foreground", False),
            authentication_required=item.get("authentication_required", item.get("authenticationRequired", False)),
            text_input=item.get("text_input", item.get("textInput", False)),
            text_input_button_title=item.get("text_input_button_title", item.get("textInputButtonTitle")),
            text_input_placeholder=item.get("text_input_placeholder", item.get("textInputPlaceholder")))
        aid = action["id"]
        if aid in seen:
            raise ValueError("action ids must be unique")
        seen.add(aid)
        if "callback" in action:
            callbacks[aid] = action.pop("callback")
        wire.append(action)
    return wire, callbacks


def notify_http(validator_url, session_jwt, title, body, *, subtitle=None, channel=None,
                category=None, badge=None, sound="default", interruption=None,
                relevance=None, thread_id=None, image=None, sender=None, actions=None,
                notif_id=None, data=None, glance=None, silent=False, layout_id=None, timeout=10, _send=None):
    """Send a one-shot push to every device on the account (POST /alerts/notify).

    Stdlib-only. `validator_url` is the Connect+ validator base URL; `session_jwt` is the
    owner session or an authorized Add Hub device token (the argument name is legacy).
    A local relay key or room membership token cannot authorize this endpoint. Returns the parsed
    `{"sent": N, "stale": M, "notifId"?: id}` response. Raises CarterNotifyError on an
    HTTP error or ValueError on an invalid field. `_send` is a test seam: a callable
    (url, headers, body_bytes) -> dict that bypasses the network.

    Personalization fields (all optional): `subtitle` (2nd alert line);
    `interruption` "passive" | "active" | "time-sensitive" ("critical" requires Apple
    approval and is rejected); `relevance` 0..1 orders stacked notifications;
    `thread_id` groups notifications (use one id per layout/conversation); `image` is an
    https URL the device downloads and attaches; `sender` renders the push as a
    Communication Notification "from" that persona — name + circular avatar (see
    `_normalize_sender` for accepted shapes); `actions` adds up to 4 buttons (wire-style
    list from `notification_action(...)`, including inline replies and authentication
    options — callback dispatch lives on
    `CarterClient.notify`, not here); `notif_id` is echoed back by button taps. `sound`
    is a sound file name bundled in the app, "default", or "none" (silent) — remote
    sound URLs are not a thing APNs supports.

    Ambient-surface fields:

    `glance` is a glance-refresh object (see `carterkit.ambient`) placed at the
    payload's top level; it updates the device's widgets and Control Center values.

    `silent=True` sends a BACKGROUND push instead of a user-visible one: no
    notification is shown, and `title`/`body` are ignored (pass empty strings).
    It needs `glance` or `data` to carry something.

    Delivery is best-effort: iOS may throttle background pushes and suppress them
    after force-quit. Visible alerts can refresh through the notification service
    extension, but neither presentation nor extension execution is guaranteed.
    `sent` counts APNs acceptance, not on-device application. `channel` and
    `layout_id` route taps; they do not limit the account's recipient devices."""
    from .ambient import _finite_number, _json_size
    _finite_number(timeout, "timeout")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if layout_id is not None and (not isinstance(layout_id, str) or not layout_id or len(layout_id.encode("utf-8")) > 128):
        raise ValueError("layout_id must be non-empty and <= 128 UTF-8 bytes")
    if silent:
        if not glance and not data:
            raise ValueError("a silent push needs glance= or data= to deliver "
                             "(it shows nothing, so title/body carry nothing)")
    else:
        if not title or len(title) > 256:
            raise ValueError("title must be non-empty and <= 256 chars")
        if not body or len(body) > 256:
            raise ValueError("body must be non-empty and <= 256 chars")
    if glance is not None and not isinstance(glance, dict):
        raise ValueError("glance must be a dict")
    if glance is not None:
        _json_size(glance, 2048, "glance")
    if subtitle is not None and len(subtitle) > 256:
        raise ValueError("subtitle must be <= 256 chars")
    if interruption is not None and interruption not in _INTERRUPTION_LEVELS:
        if interruption == "critical":
            raise ValueError('interruption "critical" requires Apple approval and is not enabled')
        raise ValueError(f"interruption must be one of {_INTERRUPTION_LEVELS}")
    if relevance is not None and not (0 <= relevance <= 1):
        raise ValueError("relevance must be within 0..1")
    if thread_id is not None and len(thread_id) > 128:
        raise ValueError("thread_id must be <= 128 chars")
    if image is not None and len(image) > 512:
        raise ValueError("image URL must be <= 512 chars")
    if notif_id is not None and len(notif_id) > 64:
        raise ValueError("notif_id must be <= 64 chars")
    sender = _normalize_sender(sender)
    wire_actions, callbacks = _normalize_actions(actions)
    if callbacks:
        raise ValueError("action callbacks need a mesh connection — use "
                         "CarterClient.notify(); notify_http sends buttons only")

    if silent:
        # A background push must carry NO alert/sound/badge — including any of
        # them makes APNs treat it as user-visible and the silence is lost. So a
        # silent request carries only what a background push can act on, and every
        # presentation field is deliberately dropped rather than sent and ignored.
        payload = {"silent": True}
    else:
        payload = {"title": title, "body": body, "sound": sound}
        if subtitle is not None:
            payload["subtitle"] = subtitle
        if category is not None:
            payload["category"] = category
        if badge is not None:
            payload["badge"] = badge
        if interruption is not None:
            payload["interruption"] = interruption
        if relevance is not None:
            payload["relevance"] = relevance
        if thread_id is not None:
            payload["threadId"] = thread_id
        if image is not None:
            payload["imageURL"] = image
        if sender is not None:
            payload["sender"] = sender
        if wire_actions is not None:
            payload["actions"] = wire_actions
        if notif_id is not None:
            payload["notifId"] = notif_id
    # Carried by both routes: the client applies a glance block through one code
    # path whether it arrived silently or on an alert.
    if glance is not None:
        payload["glance"] = glance
    if channel is not None:
        payload["channel"] = channel
    if data is not None:
        payload["data"] = data
    if layout_id is not None:
        payload["layoutId"] = layout_id

    url = validator_url.rstrip("/") + "/alerts/notify"
    headers = {"Authorization": session_jwt, "Content-Type": "application/json",
               "User-Agent": "carterkit/python"}
    body_bytes = json.dumps(payload, allow_nan=False, ensure_ascii=False, separators=(",", ":")).encode()

    if _send is not None:
        return _send(url, headers, body_bytes)

    req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode())
            if not isinstance(result, dict):
                raise ValueError("notify endpoint returned a non-object JSON response")
            return result
    except urllib.error.HTTPError as e:
        raise CarterNotifyError(e.code, e.read().decode(errors="replace")) from None
    except (OSError, ValueError) as e:
        raise CarterNotifyError(0, str(e)) from None


class CarterDeviceRevoked(Exception):
    """Raised when an external device's refresh is denied (HTTP 403) — the owner revoked the
    device or their Connect+ lapsed. Terminal: the device should stop trying to reconnect."""


_LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")


def check_validator_url(validator_url, *, allow_insecure=False) -> str:
    """The validator base URL a long-lived credential may be POSTed to. Must be
    ``https``; ``http`` is accepted only for loopback hosts and only when the caller
    passes ``allow_insecure=True``. Raises ValueError otherwise. A device.json pasted
    from a chat saying ``"validator": "http://10.0.0.9"`` must never receive the
    refresh secret in the clear."""
    if not isinstance(validator_url, str) or not validator_url:
        raise ValueError("validator URL must be a non-empty string")
    parts = urlsplit(validator_url)
    if parts.scheme == "https" and parts.hostname:
        return validator_url
    if parts.scheme == "http" and parts.hostname in _LOOPBACK_HOSTS and allow_insecure:
        return validator_url
    raise ValueError(
        f"validator URL must be https (got {parts.scheme or 'no scheme'}://{parts.hostname}); "
        f"plain http is allowed only for 127.0.0.1/localhost with allow_insecure_validator=True")


def device_refresh_http(validator_url, device_id, refresh_token, *, timeout=10,
                        allow_insecure=False, _send=None):
    """Re-mint an external device's short-lived relay token (POST /devices/sessions/refresh).

    Stdlib-only, mirroring `notify_http`. `validator_url` is the Connect+ validator base URL
    (https required — see `check_validator_url`); `device_id` + `refresh_token` are the
    long-lived credential handed to the device at mint time. Returns the parsed
    `{"deviceToken": ..., "expiresAt": ...}`. Raises CarterDeviceRevoked on HTTP 403
    (revoked / owner lapsed); other HTTP errors propagate so a caller can retry transient
    failures. `_send` is a test seam: (url, headers, body) -> dict."""
    check_validator_url(validator_url, allow_insecure=allow_insecure)
    url = validator_url.rstrip("/") + "/devices/sessions/refresh"
    headers = {"Content-Type": "application/json"}
    body_bytes = json.dumps({"deviceId": device_id, "refreshToken": refresh_token}).encode()

    def _do():
        if _send is not None:
            return _send(url, headers, body_bytes)
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())

    try:
        return _do()
    except urllib.error.HTTPError as e:
        if e.code == 403:
            raise CarterDeviceRevoked(e.read().decode(errors="replace")) from None
        raise CarterNotifyError(e.code, e.read().decode(errors="replace")) from None


#: Frames the relay itself emits (or answers) in plaintext even inside an E2EE room.
#: Always passed through `_open` untouched, whatever `strict_e2ee` says.
_RELAY_CONTROL_TYPES = frozenset({
    "welcome", "server_client_list", "node_status", "roster", "error", "ack", "pong",
    "handshake", "status_request", "get_nodes", "ping", "identify",
})

#: Inbound dispatch defaults: at most this many handlers run concurrently, and each
#: msg_type is admitted at most `DEFAULT_RATE_PER_TYPE` frames per second (burst = 2x).
DEFAULT_MAX_INFLIGHT = 32
DEFAULT_RATE_PER_TYPE = 20.0


class _TokenBucket:
    __slots__ = ("rate", "burst", "tokens", "last")

    def __init__(self, rate, burst):
        self.rate, self.burst, self.tokens, self.last = rate, burst, burst, time.monotonic()

    def take(self) -> bool:
        now = time.monotonic()
        self.tokens = min(self.burst, self.tokens + (now - self.last) * self.rate)
        self.last = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class CarterClient:
    def __init__(self, gateway_url, token, channel, role="device", name="hub", e2ee_key=None,
                 validator_url=None, session_jwt=None, room=False,
                 device_id=None, refresh_token=None, refresh_interval=2400,
                 can_route=False, can_monitor=False, *, strict_e2ee=True,
                 allow_insecure_validator=False, max_inflight=DEFAULT_MAX_INFLIGHT,
                 rate_per_type=DEFAULT_RATE_PER_TYPE):
        """`strict_e2ee=True` (default) drops every non-envelope frame from a peer while
        an E2EE session exists; `False` passes them through with one warning per
        msg_type (debugging aid only). `allow_insecure_validator` permits an http:// validator on loopback
        only. `max_inflight` bounds concurrent inbound handler runs; `rate_per_type` is
        a per-msg_type admission rate (frames/s, 0 disables) — excess frames are dropped
        and counted in `dropped`."""
        if MeshSocket is None:
            raise ImportError("MeshSocket is unavailable; run `pip install meshsocket`. "
                              "(notify_http does not need it.)")
        if validator_url is not None:
            check_validator_url(validator_url, allow_insecure=allow_insecure_validator)
        self._allow_insecure_validator = allow_insecure_validator
        # can_route lets this client SEND routed requests (route_msg); can_monitor
        # unlocks get_nodes roster reads. Both off by default — a plain data hub
        # needs neither; Hub turns them on to resolve and push to devices.
        self._sock = MeshSocket(url=gateway_url, name=name, auth_token=token,
                                channel=channel, role=role, can_broadcast=True,
                                can_route=can_route, can_monitor=can_monitor)
        #: The mesh channel — also the default tap-routing key notify() stamps on
        #: pushes, so tapping one opens the pinned layout for this connection.
        self.channel = channel
        # `room=True` matches the app's `mode: room`: a symmetric group cipher so the hub
        # shares an encrypted room with several members. Otherwise the directional 1:1 cipher.
        if e2ee_key:
            from .e2ee import decode_key_b64
            secret = decode_key_b64(e2ee_key)          # strict base64, exactly 32 bytes
            ctx = {"channel": channel, "sender": name}
            self._session = (E2EESession.group(secret, **ctx) if room
                             else E2EESession(secret, is_device_side=(role in ("device", "hub")), **ctx))
        else:
            self._session = None
        self.strict_e2ee = strict_e2ee
        #: Inbound frames refused before any handler ran, by reason.
        self.dropped = {"plaintext": 0, "e2ee_open": 0, "rate": 0}
        self._warned_plaintext = set()
        self._inflight = asyncio.Semaphore(max(1, int(max_inflight)))
        self._rate_per_type = float(rate_per_type or 0)
        self._buckets = {}
        self._last_rate_warning = 0.0
        # Connect+ validator credentials for notify(); distinct from the mesh auth token.
        self._validator_url = validator_url
        self._session_jwt = session_jwt
        # External-device self-refresh: a headless device provisioned via POST /devices holds
        # a long-lived refresh secret and re-mints its short-lived relay token before expiry,
        # updating the socket's auth_token so any reconnect uses the fresh one. Revocation
        # (HTTP 403) surfaces as `revoked = True` and tears the socket down.
        self._device_id = device_id
        self._refresh_token = refresh_token
        self._refresh_interval = refresh_interval
        self._refresh_task = None
        self.revoked = False
        # Control-state authority (matches the app's Phase 2): when enabled, this hub answers
        # a replica's control_sync_request with a snapshot of set_control_state() values.
        self._control_state = {}
        self._state_version = 0
        self._is_state_authority = False
        self._broadcast_handler = None
        self._broadcast_registered = False
        self._join_handler = None
        self._ack_commands = False
        # Notification action-button plumbing: per-send callbacks keyed by
        # (notifId, actionId), plus an optional catch-all. Fed by the app's flat
        # `notif_action` broadcast when a user taps a button on a push.
        self._notif_callbacks = {}
        self._notif_action_handler = None

    def _open(self, payload):
        """Decrypt an inbound payload. Returns None when the frame must be DROPPED: a
        sealed frame that fails to open (bad tag, replay, stale, malformed) never
        reaches a handler; a plaintext frame in an E2EE session is dropped under
        `strict_e2ee` and passed through (with a one-time warning per msg_type)
        otherwise. Relay control frames are always passed through. Never raises."""
        if not self._session:
            return payload
        if isinstance(payload, dict) and E2EESession.is_envelope(payload):
            try:
                data = self._session.open(payload)
            except ValueError as exc:
                self.dropped["e2ee_open"] += 1
                log.warning("dropped undecryptable frame: %s", exc)
                return None
            # The relay stamps the sender's name on the OUTER frame; it knows who sent
            # it, whereas the sealed `_from` is only the sender's own claim. Prefer it.
            if isinstance(data, dict) and isinstance(payload.get("_from"), str):
                data["_from"] = payload["_from"]
            return data
        if isinstance(payload, dict) and payload.get("type") in _RELAY_CONTROL_TYPES:
            return payload
        mt = payload.get("msg_type") if isinstance(payload, dict) else None
        if self.strict_e2ee:
            self.dropped["plaintext"] += 1
            if mt not in self._warned_plaintext:
                self._warned_plaintext.add(mt)
                log.warning("dropped plaintext frame (msg_type=%r) in an E2EE session "
                            "(strict_e2ee=True)", mt)
            return None
        if mt not in self._warned_plaintext:
            self._warned_plaintext.add(mt)
            log.warning("plaintext frame (msg_type=%r) accepted in an E2EE session "
                        "because strict_e2ee=False — this peer is not sealing; fix the "
                        "peer rather than relying on this", mt)
        return payload

    def _admit(self, data) -> bool:
        """Per-msg_type token bucket. False means drop (counted, warning rate-limited)."""
        if self._rate_per_type <= 0 or not isinstance(data, dict):
            return True
        mt = data.get("msg_type")
        bucket = self._buckets.get(mt)
        if bucket is None:
            if len(self._buckets) >= 1024:          # bounded: a peer inventing msg_types
                self._buckets.clear()
            bucket = self._buckets[mt] = _TokenBucket(self._rate_per_type, self._rate_per_type * 2)
        if bucket.take():
            return True
        self.dropped["rate"] += 1
        now = time.monotonic()
        if now - self._last_rate_warning > 5.0:
            self._last_rate_warning = now
            log.warning("inbound rate limit: dropping msg_type=%r (%d dropped so far)",
                        mt, self.dropped["rate"])
        return False

    def _seal(self, data):
        return self._session.seal(data) if (self._session and data is not None) else data

    def on(self, msg_type, handler):
        """Register a command handler. handler(data: dict) gets DECRYPTED data and may return a
        dict reply (auto-encrypted). Sync or async handlers are supported."""
        async def wrapper(payload):
            data = self._open(payload)
            if data is None or not self._admit(data):
                return None
            async with self._inflight:
                result = handler(data)
                if asyncio.iscoroutine(result):
                    result = await result
            return self._seal(result) if result is not None else None
        self._sock.on(msg_type, wrapper)

    def on_broadcast(self, handler):
        """Register a handler for relayed broadcasts. handler(data: dict) gets DECRYPTED data."""
        self._broadcast_handler = handler
        self._ensure_broadcast_listener()

    def _ensure_broadcast_listener(self):
        """Arm the single 'broadcast' socket listener (one handler per event) that dispatches
        to the control-state responder and then the user's on_broadcast handler."""
        if self._broadcast_registered:
            return
        self._broadcast_registered = True

        async def wrapper(payload):
            data = self._open(payload)
            if data is None or not self._admit(data):
                return None
            async with self._inflight:
                await self._dispatch_broadcast(data)
            return None
        self._sock.on("broadcast", wrapper)

    #: Broadcast msg_types that are protocol plane, not app data — consumed by
    #: _dispatch_broadcast and never handed to on_broadcast handlers. command_ack
    #: is app-directed (a hub's reply to a phone), so hubs must not see each
    #: other's acks as data.
    _PROTOCOL_BROADCASTS = ("control_sync_request", "control_snapshot", "command_ack")

    async def _dispatch_broadcast(self, data):
        # A phone publishing with `batchPublishers: true` sends one `sensor_batch`
        # frame per tick; every element of `readings` is a complete `sensor` frame,
        # so hubs see exactly what they'd see unbatched.
        if isinstance(data, dict) and data.get("msg_type") == "sensor_batch":
            for reading in data.get("readings") or []:
                if isinstance(reading, dict):
                    await self._dispatch_broadcast(reading)
            return
        # Notification action taps (the app's flat `notif_action` frame) are kit
        # plane, like protocol frames: dispatched to the per-send callback
        # registered by notify(actions=...) and the on_notif_action catch-all,
        # never to on_broadcast handlers.
        if isinstance(data, dict) and data.get("msg_type") == "notif_action":
            fn = self._notif_callbacks.get((data.get("notifId"), data.get("actionId")))
            for handler in (fn, self._notif_action_handler):
                if handler is not None:
                    result = handler(data)
                    if asyncio.iscoroutine(result):
                        await result
            return
        # Protocol frames are consumed here so they never reach the user's
        # on_broadcast handler. A sync request is answered by an authority AND
        # surfaced via on_sync_request (the join signal); snapshots/acks are for
        # replicas (the app), not for us.
        if isinstance(data, dict) and data.get("msg_type") in self._PROTOCOL_BROADCASTS:
            if data.get("msg_type") == "control_sync_request":
                if self._is_state_authority:
                    await self._answer_control_sync(data)
                if self._join_handler is not None:
                    result = self._join_handler(data)
                    if asyncio.iscoroutine(result):
                        await result
            return
        if self._broadcast_handler is None:
            return
        # Ack'd-command layer (the app's layout `state.acks`): a `_cmd`-stamped frame
        # is acknowledged only when the handler REPORTS it handled it (returns True) —
        # a hub whose demux matched nothing must stay silent so the app times out and
        # reverts (and so another hub on the channel can be the one that answers).
        # ok:false on a raised exception, which still propagates unchanged.
        cmd_id = data.get("_cmd") if (self._ack_commands and isinstance(data, dict)) else None
        try:
            result = self._broadcast_handler(data)
            if asyncio.iscoroutine(result):
                result = await result
        except Exception:
            if cmd_id is not None:
                await self.broadcast("command_ack", {
                    "cmd_id": cmd_id, "to": data.get("_from"), "ok": False})
            raise
        if cmd_id is not None and result is True:
            await self.broadcast("command_ack", {
                "cmd_id": cmd_id, "to": data.get("_from"), "ok": True})

    def on_sync_request(self, handler):
        """Register the deterministic "a replica just joined / came back" signal: the
        app broadcasts `control_sync_request` when a layout with synced or dynamic
        content loads AND on every reconnect. handler(data: dict) gets the decrypted
        frame (`{from, dynamic?: [...]}` — `dynamic` lists the layout's dynamic slot
        events); sync or async. Use it to re-push dynamic decks and any full-state
        snapshot a late joiner needs. (Distinct from LocalRelay.on_join, which is the
        relay-auth join of a socket, not a layout replica asking for state.)"""
        self._join_handler = handler
        self._ensure_broadcast_listener()

    def enable_command_acks(self):
        """Acknowledge `_cmd`-stamped command broadcasts (the app's opt-in ack'd
        commands, layout `state.acks: true`) with `command_ack {cmd_id, to, ok}`.
        The on_broadcast handler must return True for frames it actually handled —
        only those are acked ok:true; a raised exception acks ok:false; anything
        else gets NO ack, so the app's pending control times out and reverts (and a
        different hub on the channel may be the one that answers). Frames without
        `_cmd` are untouched, so servers stay compatible with plain layouts."""
        self._ack_commands = True
        self._ensure_broadcast_listener()

    def set_control_state(self, control_id, value):
        """Record the authoritative current value of a control so the hub can answer a
        replica's control_sync_request. Call this alongside your normal broadcast of the
        value — it only updates the snapshot served to late joiners / reconnecting devices."""
        self._control_state[control_id] = value

    def enable_state_authority(self):
        """Declare this hub the source of truth for control state. It will answer replicas'
        control_sync_request broadcasts with a control_snapshot of set_control_state()
        values — the hub side of the app's Phase 2 designated-authority sync."""
        self._is_state_authority = True
        self._ensure_broadcast_listener()

    async def _answer_control_sync(self, data):
        to = data.get("from")
        if not to or not self._control_state:
            return
        self._state_version += 1
        await self.broadcast("control_snapshot",
                             {"to": to, "v": self._state_version, "controls": dict(self._control_state)})

    async def broadcast(self, msg_type, data):
        await self.broadcast_frame({**data, "msg_type": msg_type})

    async def broadcast_frame(self, frame):
        """Broadcast a pre-assembled payload verbatim (no msg_type is forced on it) —
        the escape hatch for frames whose shape a control's sync filter dictates."""
        await self._sock.send("broadcast_request", self._seal(frame))

    async def chat(self, text, *, name="Server", role="device", channel=None, msg_id=None, **extra):
        """Send a channel chat message a chat control will display, as a bubble from `name`.

        Builds the exact shape the app requires — a unique `id`, a `sender.name`, an
        ISO-8601 `timestamp`, and the `chat_message` type — which is easy to get subtly
        wrong by hand (a missing `id` is silently dropped). Extra keys pass through
        (e.g. `_from=` to tag your own echo). Returns the message id."""
        mid = msg_id or uuid.uuid4().hex
        payload = {
            "id": mid,
            "text": text,
            "sender": {"name": name, "role": role},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        if channel is not None:
            payload["channel"] = channel
        payload.update(extra)
        await self.broadcast("chat_message", payload)
        return mid

    async def request(self, command, data, timeout=5.0):
        reply = await self._sock.request(command, self._seal(data), timeout=timeout)
        return self._open(reply) if reply is not None else None

    def on_notif_action(self, handler):
        """Catch-all for notification button taps: handler(data) gets the flat
        `notif_action` frame with notifId, actionId, optional threadId and userText.
        The handler can be used as a decorator and should be restored at startup.
        Per-send callbacks passed via notify(actions=...) fire first."""
        self._notif_action_handler = handler
        self._ensure_broadcast_listener()
        return handler

    async def notify(self, title, body, *, subtitle=None, channel=None, category=None,
                     badge=None, sound="default", interruption=None, criticality=None,
                     relevance=None, thread_id=None, image=None, sender=None,
                     actions=None, notif_id=None, data=None, glance=None, silent=False,
                     encrypt=None, placeholder_title="", placeholder_body="New notification",
                     layout_id=None, timeout=10):
        """Send a one-shot push to every device on the account. Requires `validator_url`
        and either an owner `session_jwt` or Add Hub device credentials. Device
        authorization follows the socket's renewed token. Returns
        `{"sent": N, "stale": M, "notifId"?: id}`.

        On top of `notify_http`'s fields this adds the mesh-connected conveniences:

        - `channel` defaults to this client's mesh channel, so tapping the push opens
          the pinned layout for this connection.
        - `actions` may carry callbacks — `{"ack": ("Acknowledge", fn)}` or
          `{"ack": {"name": "Acknowledge", "func": fn}}`; when the user taps the
          button, the app broadcasts `notif_action` on the channel and the callback
          fires with the flat frame (inline replies include `userText`). iOS may
          queue actions for retry; delivery and execution are best-effort. The hub
          must be listening. A `notif_id` is minted per send to key the dispatch.
          Callbacks live in memory; register `on_notif_action` at startup for a
          stable handler that can also handle responses to earlier notifications.
        - `sender` (persona) defaults `thread_id` to the sender's name so avatar
          grouping and thread grouping agree.
        - `criticality` is an alias for `interruption`.
        - E2EE: in a room (`room=True` + e2ee_key) the content fields — title, body,
          subtitle, image, sender — are sealed into the `enc` envelope the app's push
          extension decrypts on-device; APNs and the relay carry only
          `placeholder_title`/`placeholder_body`. That is the default in a room
          (`encrypt=None`); pass `encrypt=False` to send in the clear, `encrypt=True`
          to fail loudly when no room cipher is available. Delivery hints
          (interruption/relevance/thread/sound/badge/channel/actions) always ride in
          the clear.
        - `glance` refreshes the device's widgets and Control Center values, and
          `silent=True` delivers it as a background push instead of a visible one.
          Both routes are best-effort; silent pushes can be suppressed after
          force-quit. E2EE never
          seals `glance` — it is surface values, not message content, and the
          extension applies it before the decrypt step."""
        authorization = self._ambient_authorization()
        if interruption is None:
            interruption = criticality
        if channel is None:
            channel = self.channel
        sender = _normalize_sender(sender)
        if sender is not None and thread_id is None:
            thread_id = sender["name"]
        wire_actions, callbacks = _normalize_actions(actions)
        # Register before sending so an immediate reply cannot race registration.
        # Restore any previous callbacks if validation or the HTTP request fails.
        if callbacks and silent:
            raise ValueError("silent pushes cannot carry action callbacks")
        if callbacks and notif_id is None:
            notif_id = "n" + uuid.uuid4().hex[:16]

        can_seal = self._session is not None and getattr(self._session, "is_group", False)
        if encrypt is None:
            encrypt = can_seal
        elif encrypt and not can_seal:
            raise CarterNotifyError(0, "encrypted notifications need a room cipher "
                                       "(e2ee_key + room=True) — the push extension "
                                       "only opens the group construction")
        if encrypt:
            sealed = {"title": title, "body": body}
            if subtitle is not None:
                sealed["subtitle"] = subtitle
            if image is not None:
                sealed["imageURL"] = image
            if sender is not None:
                sealed["sender"] = sender
            data = dict(data or {})
            # Notification content rides APNs, not the mesh: no freshness/replay stamps.
            data["enc"] = self._session.seal(sealed, stamp=False)
            title, body = placeholder_title or "CAR-TER", placeholder_body
            subtitle = image = sender = None

        keys = {(notif_id, aid): fn for aid, fn in callbacks.items()}
        previous = {key: self._notif_callbacks[key] for key in keys if key in self._notif_callbacks}
        self._notif_callbacks.update(keys)
        if callbacks:
            self._ensure_broadcast_listener()
        try:
            return await asyncio.to_thread(
                notify_http, self._validator_url, authorization, title, body,
                subtitle=subtitle, channel=channel, category=category, badge=badge,
                sound=sound, interruption=interruption, relevance=relevance,
                thread_id=thread_id, image=image, sender=sender, actions=wire_actions,
                notif_id=notif_id, data=data, glance=glance, silent=silent,
                layout_id=layout_id, timeout=timeout)
        except BaseException:
            for key, fn in keys.items():
                if self._notif_callbacks.get(key) is fn:
                    self._notif_callbacks.pop(key, None)
                    if key in previous:
                        self._notif_callbacks[key] = previous[key]
            raise

    def _ambient_authorization(self):
        """Owner session or the current, refreshable Add Hub credential."""
        if self.revoked:
            raise CarterNotifyError(0, "this hub credential has been revoked")
        token = self._session_jwt
        if not token and self._device_id and self._refresh_token:
            token = self._sock.auth_token
        if not self._validator_url or not token:
            raise CarterNotifyError(0, "ambient APIs require validator_url and session_jwt, "
                                       "or an Add Hub device credential; a local relay key is not sufficient")
        return token

    async def push_live_activity(self, *, layout_id, event, content_state, **options):
        """Async ActivityKit connector using this hub's current authorization."""
        from .ambient import live_activity_push
        token = self._ambient_authorization()
        return await asyncio.to_thread(live_activity_push, self._validator_url, token,
            layout_id=layout_id, event=event, content_state=content_state, **options)

    async def _ambient_call(self, request, **kwargs):
        """Run one `carterkit.ambient` request builder off the event loop with this
        client's current authorization — the same credential resolution
        `push_live_activity` uses, so a renewed Add Hub device token is picked up on
        every call rather than captured once at construction."""
        token = self._ambient_authorization()
        return await asyncio.to_thread(request, self._validator_url, token, **kwargs)

    async def refresh_glance(self, *, layout_id, values=None, controls=None, **options):
        """Request a silent widget/control refresh. iOS may delay or suppress it.

        Use ``notify(glance=glance_update(...))`` to attach data to a visible alert.
        This is explicit; ``push()`` never spends a push budget automatically.
        """
        from .ambient import glance_update
        update = glance_update(layout_id=layout_id, values=values, controls=controls, **options)
        return await self.notify("", "", layout_id=layout_id, glance=update, silent=True, encrypt=False)


    async def refresh_device_token(self):
        """Re-mint this device's relay token from its refresh secret and apply it to the
        socket, so any reconnect uses the fresh token. Returns the parsed response. Raises
        CarterDeviceRevoked if the device was revoked or the owner's Connect+ lapsed."""
        if not (self._validator_url and self._device_id and self._refresh_token):
            raise CarterNotifyError(0, "refresh_device_token() needs validator_url, device_id, "
                                       "and refresh_token on the CarterClient constructor")
        res = await asyncio.to_thread(device_refresh_http, self._validator_url,
                                      self._device_id, self._refresh_token,
                                      allow_insecure=self._allow_insecure_validator)
        token = res.get("deviceToken") if isinstance(res, dict) else None
        if token:
            self._sock.auth_token = token  # MeshSocket re-sends this on every (re)connect
        return res

    async def _stop_socket(self, reason):
        """Stop the socket, marking it a fault. meshsocket >= 0.1.2 records the reason
        and logs the supervisor's exit; older builds only accept the bare call."""
        try:
            takes_reason = "reason" in inspect.signature(self._sock.stop).parameters
        except (TypeError, ValueError):
            takes_reason = False
        if takes_reason:
            await self._sock.stop(reason=reason)
        else:
            await self._sock.stop()

    async def _refresh_confirming_revocation(self, delay):
        """Refresh the device token, treating 403 as suspect until it repeats.

        Returns normally on success. Raises CarterDeviceRevoked only after
        REFRESH_CONFIRM_ATTEMPTS consecutive 403s — a genuinely revoked device keeps
        being refused, a transient rejection does not. Non-403 errors (network, 5xx)
        propagate immediately for the caller to treat as transient."""
        for attempt in range(1, REFRESH_CONFIRM_ATTEMPTS + 1):
            try:
                await self.refresh_device_token()
                if attempt > 1:
                    log.warning("device token refresh recovered after %d rejection(s) "
                                "— the 403 was transient, not a revocation", attempt - 1)
                return
            except CarterDeviceRevoked as exc:
                log.warning("device token refresh rejected 403 (%d/%d): %s",
                            attempt, REFRESH_CONFIRM_ATTEMPTS, exc)
                if attempt == REFRESH_CONFIRM_ATTEMPTS:
                    raise
                await asyncio.sleep(delay)

    async def _device_refresh_loop(self):
        """Keep the short-lived device token fresh ahead of expiry. On *confirmed*
        revocation, stop the socket and flag `revoked`; transient errors — including
        an isolated 403 — are retried rather than treated as fatal."""
        while True:
            await asyncio.sleep(self._refresh_interval)
            try:
                await self._refresh_confirming_revocation(REFRESH_CONFIRM_DELAY)
            except CarterDeviceRevoked as exc:
                log.error("device revoked after %d consecutive 403s — stopping the "
                          "client; it will not reconnect: %s",
                          REFRESH_CONFIRM_ATTEMPTS, exc)
                self.revoked = True
                await self._stop_socket(f"device token revoked: {exc}")
                return
            except Exception as exc:
                log.warning("device token refresh failed, retrying next tick: %s", exc)

    async def connect(self):
        # A hub that sat stopped past its short-lived token's expiry can never
        # identify (the relay drops it with "not admitted" forever) — when we hold
        # a refresh credential, pre-mint a fresh token so (re)starts self-heal.
        # A transient validator error falls through to the stored token; only a
        # CONFIRMED revocation aborts the connect, so a momentary 403 can't turn
        # startup into a crash-loop for the consumer.
        if self._device_id and self._refresh_token and self._validator_url:
            try:
                await self._refresh_confirming_revocation(REFRESH_CONNECT_DELAY)
            except CarterDeviceRevoked:
                self.revoked = True
                raise
            except Exception as exc:
                log.warning("device token pre-mint failed, using stored token: %s", exc)
        await self._sock.start()
        await self._sock.wait_until_ready()
        # Auto-start the refresh loop only for a self-refreshing external device.
        if self._device_id and self._refresh_token and self._validator_url and self._refresh_task is None:
            self._refresh_task = asyncio.create_task(self._device_refresh_loop())

    async def close(self):
        if self._refresh_task is not None:
            self._refresh_task.cancel()
            self._refresh_task = None
        await self._sock.stop()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *exc):
        await self.close()
        return False
