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
import urllib.error
import urllib.request

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


class CarterClient:
    def __init__(self, gateway_url, token, channel, role="device", name="hub", e2ee_key=None,
                 validator_url=None, session_jwt=None):
        if MeshSocket is None:
            raise ImportError("MeshSocket is unavailable; run `pip install meshsocket`. "
                              "(notify_http does not need it.)")
        self._sock = MeshSocket(url=gateway_url, name=name, auth_token=token,
                                channel=channel, role=role, can_broadcast=True, can_route=False)
        self._session = (E2EESession(base64.b64decode(e2ee_key), is_device_side=(role in ("device", "hub")))
                         if e2ee_key else None)
        # Connect+ validator credentials for notify(); distinct from the mesh auth token.
        self._validator_url = validator_url
        self._session_jwt = session_jwt

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
        async def wrapper(payload):
            result = handler(self._open(payload))
            if asyncio.iscoroutine(result):
                await result
            return None
        self._sock.on("broadcast", wrapper)

    async def broadcast(self, msg_type, data):
        await self._sock.send("broadcast_request", self._seal({**data, "msg_type": msg_type}))

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

    async def connect(self):
        await self._sock.start()
        await self._sock.wait_until_ready()

    async def close(self):
        await self._sock.stop()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *exc):
        await self.close()
        return False
