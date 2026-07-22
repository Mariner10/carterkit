"""carter_connect — minimal Connect+ hub client. Wraps MeshSocket + E2EE so a maker
connects hardware to the Connect+ relay in a few lines. Transparent encryption when an
e2ee_key is provided (broadcasts AND request replies); cleartext otherwise.

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
    """Accept the dict form `{"ack": "Acknowledge"}` / `{"ack": ("Acknowledge", fn)}` /
    `{"ack": {"name"/"title": ..., "func": fn, "destructive": bool}}` or a wire-style
    list of dicts → `(wire_actions, callbacks)` where callbacks maps action id → fn
    (empty when none were given)."""
    if actions is None:
        return None, {}
    wire, callbacks = [], {}
    if isinstance(actions, dict):
        items = []
        for aid, spec in actions.items():
            if isinstance(spec, str):
                items.append({"id": aid, "title": spec})
            elif callable(spec):
                items.append({"id": aid, "title": aid})
                callbacks[aid] = spec
            elif isinstance(spec, (tuple, list)) and len(spec) == 2:
                items.append({"id": aid, "title": spec[0]})
                callbacks[aid] = spec[1]
            elif isinstance(spec, dict):
                item = {"id": aid, "title": spec.get("title") or spec.get("name") or aid}
                if spec.get("destructive"):
                    item["destructive"] = True
                fn = spec.get("func") or spec.get("funct") or spec.get("callback")
                if fn is not None:
                    callbacks[aid] = fn
                items.append(item)
            else:
                raise ValueError(f"action {aid!r}: expected title, callable, (title, fn), or dict")
        wire = items
    elif isinstance(actions, (list, tuple)):
        for a in actions:
            if not isinstance(a, dict) or not a.get("id") or not a.get("title"):
                raise ValueError("wire-style actions need dicts with id and title")
            item = {"id": a["id"], "title": a["title"]}
            if a.get("destructive"):
                item["destructive"] = True
            fn = a.get("func") or a.get("callback")
            if fn is not None:
                callbacks[a["id"]] = fn
            wire.append(item)
    else:
        raise ValueError("actions must be a dict or a list of dicts")
    if len(wire) > 4:
        raise ValueError("at most 4 actions per notification")
    for a in wire:
        if len(a["id"]) > 64 or len(a["title"]) > 48:
            raise ValueError(f"action {a['id']!r}: id <= 64 and title <= 48 chars")
    return wire, callbacks


def notify_http(validator_url, session_jwt, title, body, *, subtitle=None, channel=None,
                category=None, badge=None, sound="default", interruption=None,
                relevance=None, thread_id=None, image=None, sender=None, actions=None,
                notif_id=None, data=None, _send=None):
    """Send a one-shot push to every device on the account (POST /alerts/notify).

    Stdlib-only. `validator_url` is the Connect+ validator base URL; `session_jwt` is the
    Connect+ account session token (NOT the MeshSocket auth token). Returns the parsed
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
    list of `{"id", "title", "destructive"?}` — callback dispatch lives on
    `CarterClient.notify`, not here); `notif_id` is echoed back by button taps. `sound`
    is a sound file name bundled in the app, "default", or "none" (silent) — remote
    sound URLs are not a thing APNs supports."""
    if not title or len(title) > 256:
        raise ValueError("title must be non-empty and <= 256 chars")
    if not body or len(body) > 256:
        raise ValueError("body must be non-empty and <= 256 chars")
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

    payload = {"title": title, "body": body, "sound": sound}
    if subtitle is not None:
        payload["subtitle"] = subtitle
    if channel is not None:
        payload["channel"] = channel
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
    if data is not None:
        payload["data"] = data

    url = validator_url.rstrip("/") + "/alerts/notify"
    headers = {"Authorization": session_jwt, "Content-Type": "application/json"}
    body_bytes = json.dumps(payload).encode()

    if _send is not None:
        return _send(url, headers, body_bytes)

    req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise CarterNotifyError(e.code, e.read().decode(errors="replace")) from None


class CarterDeviceRevoked(Exception):
    """Raised when an external device's refresh is denied (HTTP 403) — the owner revoked the
    device or their Connect+ lapsed. Terminal: the device should stop trying to reconnect."""


def device_refresh_http(validator_url, device_id, refresh_token, *, _send=None):
    """Re-mint an external device's short-lived relay token (POST /devices/sessions/refresh).

    Stdlib-only, mirroring `notify_http`. `validator_url` is the Connect+ validator base URL;
    `device_id` + `refresh_token` are the long-lived credential handed to the device at mint
    time. Returns the parsed `{"deviceToken": ..., "expiresAt": ...}`. Raises
    CarterDeviceRevoked on HTTP 403 (revoked / owner lapsed); other HTTP errors propagate so a
    caller can retry transient failures. `_send` is a test seam: (url, headers, body) -> dict."""
    url = validator_url.rstrip("/") + "/devices/sessions/refresh"
    headers = {"Content-Type": "application/json"}
    body_bytes = json.dumps({"deviceId": device_id, "refreshToken": refresh_token}).encode()

    def _do():
        if _send is not None:
            return _send(url, headers, body_bytes)
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())

    try:
        return _do()
    except urllib.error.HTTPError as e:
        if e.code == 403:
            raise CarterDeviceRevoked(e.read().decode(errors="replace")) from None
        raise CarterNotifyError(e.code, e.read().decode(errors="replace")) from None


class CarterClient:
    def __init__(self, gateway_url, token, channel, role="device", name="hub", e2ee_key=None,
                 validator_url=None, session_jwt=None, room=False,
                 device_id=None, refresh_token=None, refresh_interval=2400,
                 can_route=False, can_monitor=False):
        if MeshSocket is None:
            raise ImportError("MeshSocket is unavailable; run `pip install meshsocket`. "
                              "(notify_http does not need it.)")
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
            secret = base64.b64decode(e2ee_key)
            self._session = (E2EESession.group(secret) if room
                             else E2EESession(secret, is_device_side=(role in ("device", "hub"))))
        else:
            self._session = None
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
        if self._session and isinstance(payload, dict) and E2EESession.is_envelope(payload):
            return self._session.open(payload)
        return payload

    def _seal(self, data):
        return self._session.seal(data) if (self._session and data is not None) else data

    def on(self, msg_type, handler):
        """Register a command handler. handler(data: dict) gets DECRYPTED data and may return a
        dict reply (auto-encrypted). Sync or async handlers are supported."""
        async def wrapper(payload):
            data = self._open(payload)
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
            await self._dispatch_broadcast(self._open(payload))
            return None
        self._sock.on("broadcast", wrapper)

    #: Broadcast msg_types that are protocol plane, not app data — consumed by
    #: _dispatch_broadcast and never handed to on_broadcast handlers. command_ack
    #: is app-directed (a hub's reply to a phone), so hubs must not see each
    #: other's acks as data.
    _PROTOCOL_BROADCASTS = ("control_sync_request", "control_snapshot", "command_ack")

    async def _dispatch_broadcast(self, data):
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
        `notif_action` frame `{"msg_type", "notifId", "actionId", "threadId"?}`.
        Per-send callbacks passed via notify(actions=...) fire first."""
        self._notif_action_handler = handler
        self._ensure_broadcast_listener()

    async def notify(self, title, body, *, subtitle=None, channel=None, category=None,
                     badge=None, sound="default", interruption=None, criticality=None,
                     relevance=None, thread_id=None, image=None, sender=None,
                     actions=None, notif_id=None, data=None, encrypt=None,
                     placeholder_title="", placeholder_body="New notification"):
        """Send a one-shot push to every device on the account. Requires `validator_url`
        and `session_jwt` to have been passed to the constructor (the mesh auth token is
        NOT the session JWT — distinct credentials). Returns
        `{"sent": N, "stale": M, "notifId"?: id}`.

        On top of `notify_http`'s fields this adds the mesh-connected conveniences:

        - `channel` defaults to this client's mesh channel, so tapping the push opens
          the pinned layout for this connection.
        - `actions` may carry callbacks — `{"ack": ("Acknowledge", fn)}` or
          `{"ack": {"name": "Acknowledge", "func": fn}}`; when the user taps the
          button, the app broadcasts `notif_action` on the channel and the callback
          fires with the flat frame. Best-effort: taps only arrive while the app holds
          a live connection on that channel. A `notif_id` is minted per send to key
          the dispatch (pass your own to override).
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
          the clear."""
        if not self._validator_url or not self._session_jwt:
            raise CarterNotifyError(0, "notify() requires validator_url and session_jwt "
                                       "on the CarterClient constructor")
        if interruption is None:
            interruption = criticality
        if channel is None:
            channel = self.channel
        sender = _normalize_sender(sender)
        if sender is not None and thread_id is None:
            thread_id = sender["name"]
        wire_actions, callbacks = _normalize_actions(actions)
        if callbacks:
            if notif_id is None:
                notif_id = "n" + uuid.uuid4().hex[:16]
            for aid, fn in callbacks.items():
                self._notif_callbacks[(notif_id, aid)] = fn
            self._ensure_broadcast_listener()

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
            data["enc"] = self._session.seal(sealed)
            title, body = placeholder_title or "CAR-TER", placeholder_body
            subtitle = image = sender = None

        return await asyncio.to_thread(
            notify_http, self._validator_url, self._session_jwt, title, body,
            subtitle=subtitle, channel=channel, category=category, badge=badge,
            sound=sound, interruption=interruption, relevance=relevance,
            thread_id=thread_id, image=image, sender=sender, actions=wire_actions,
            notif_id=notif_id, data=data)

    async def refresh_device_token(self):
        """Re-mint this device's relay token from its refresh secret and apply it to the
        socket, so any reconnect uses the fresh token. Returns the parsed response. Raises
        CarterDeviceRevoked if the device was revoked or the owner's Connect+ lapsed."""
        if not (self._validator_url and self._device_id and self._refresh_token):
            raise CarterNotifyError(0, "refresh_device_token() needs validator_url, device_id, "
                                       "and refresh_token on the CarterClient constructor")
        res = await asyncio.to_thread(device_refresh_http, self._validator_url,
                                      self._device_id, self._refresh_token)
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
