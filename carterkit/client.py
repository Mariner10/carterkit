"""carter_connect — minimal Connect+ hub client. Wraps MeshSocket + E2EE so a maker
connects hardware to the Connect+ relay in a few lines. Transparent encryption when an
e2ee_key is provided (broadcasts AND request replies); cleartext otherwise.

Also exposes `notify_http(...)` and `CarterClient.notify(...)` for sending a one-shot
push to every device on a Connect+ account (POST /alerts/notify). `notify_http` is
stdlib-only (urllib) so a cron job can fire a notification without the MeshSocket stack."""
import asyncio
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

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


def notify_http(validator_url, session_jwt, title, body, *, channel=None, category=None,
                badge=None, sound="default", data=None, _send=None):
    """Send a one-shot push to every device on the account (POST /alerts/notify).

    Stdlib-only. `validator_url` is the Connect+ validator base URL; `session_jwt` is the
    Connect+ account session token (NOT the MeshSocket auth token). Returns the parsed
    `{"sent": N, "stale": M}` response. Raises CarterNotifyError on an HTTP error or
    ValueError on invalid title/body. `_send` is a test seam: a callable
    (url, headers, body_bytes) -> dict that bypasses the network."""
    if not title or len(title) > 256:
        raise ValueError("title must be non-empty and <= 256 chars")
    if not body or len(body) > 256:
        raise ValueError("body must be non-empty and <= 256 chars")

    payload = {"title": title, "body": body, "sound": sound}
    if channel is not None:
        payload["channel"] = channel
    if category is not None:
        payload["category"] = category
    if badge is not None:
        payload["badge"] = badge
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

    async def notify(self, title, body, *, channel=None, category=None,
                     badge=None, sound="default", data=None):
        """Send a one-shot push to every device on the account. Requires `validator_url`
        and `session_jwt` to have been passed to the constructor (the mesh auth token is
        NOT the session JWT — distinct credentials). Returns `{"sent": N, "stale": M}`."""
        if not self._validator_url or not self._session_jwt:
            raise CarterNotifyError(0, "notify() requires validator_url and session_jwt "
                                       "on the CarterClient constructor")
        return await asyncio.to_thread(
            notify_http, self._validator_url, self._session_jwt, title, body,
            channel=channel, category=category, badge=badge, sound=sound, data=data)

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

    async def _device_refresh_loop(self):
        """Keep the short-lived device token fresh ahead of expiry. On revocation, stop the
        socket and flag `revoked`; transient errors are retried on the next tick."""
        while True:
            await asyncio.sleep(self._refresh_interval)
            try:
                await self.refresh_device_token()
            except CarterDeviceRevoked:
                self.revoked = True
                await self._sock.stop()
                return
            except Exception:
                pass  # transient (network/5xx) — retry next interval

    async def connect(self):
        # A hub that sat stopped past its short-lived token's expiry can never
        # identify (the relay drops it with "not admitted" forever) — when we hold
        # a refresh credential, pre-mint a fresh token so (re)starts self-heal.
        # A transient validator error falls through to the stored token.
        if self._device_id and self._refresh_token and self._validator_url:
            try:
                await self.refresh_device_token()
            except CarterDeviceRevoked:
                self.revoked = True
                raise
            except Exception:
                pass
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
