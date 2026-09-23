"""Hub-side Connect+ E2EE v2. FROZEN construction — byte-identical to the Swift CryptoKit
core (see the Plan-4a v2 test vectors). ChaCha20-Poly1305 IETF + HKDF-SHA256 with a
per-session random salt (transmitted in the envelope) so reconnects never reuse a nonce.

What this module guarantees, and what it does not:

* Confidentiality and integrity of each frame against anyone WITHOUT the room key
  (the relay, the network, non-members). A forged or tampered envelope fails to open.
* Replay protection (0.12+): every sealed frame carries ``_ts`` (unix ms), ``_ch``
  (channel) and ``_from`` INSIDE the ciphertext. A receiver rejects a duplicate
  ``(salt, counter)`` (per-salt high-water mark plus a 64-frame reorder window), a
  plaintext older or newer than ``MAX_SKEW_MS``, and a frame sealed for another
  channel. Old receivers ignore the extra keys; the wire format is unchanged.
* It does NOT authenticate the sender: room mode is one symmetric key shared by every
  member, so any member can impersonate any other. Sender authentication needs the
  v3 construction (per-member signing keys), which is a later release.
"""
from __future__ import annotations

import base64
import binascii
import json
import os
import struct
import time
from collections import OrderedDict

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

#: The only key length the construction accepts — HKDF adds no entropy, so a short
#: key would give a "working" room with proportionally weak security on both ends.
KEY_LEN = 32
SALT_LEN = 16
#: ChaCha20-Poly1305 tag length: the smallest possible ciphertext (empty plaintext).
MIN_CT_LEN = 16
_MAX_N = 2 ** 64 - 1
#: Accept a sealed timestamp this far either side of local time (clock skew + queueing).
MAX_SKEW_MS = 120_000
#: Derived keys and replay windows are cached per salt; bounded so a peer cannot
#: exhaust memory by rotating salts.
KEY_CACHE = 256
WINDOW_CACHE = 256
REPLAY_WINDOW = 64


def derive_key(secret: bytes, session_salt: bytes, info: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=session_salt, info=info).derive(secret)


def _nonce(counter: int) -> bytes:
    return b"\x00\x00\x00\x00" + struct.pack(">Q", counter)


def _check_key(secret) -> bytes:
    if not isinstance(secret, (bytes, bytearray)) or len(secret) != KEY_LEN:
        raise ValueError(f"e2ee key must be exactly {KEY_LEN} bytes")
    return bytes(secret)


def decode_key_b64(key_b64) -> bytes:
    """Decode a base64 E2EE key as it appears in a layout (``e2eeKey``), a pairing QR
    (``k``) or a device credential, enforcing strict base64 and the 32-byte length."""
    if not isinstance(key_b64, str):
        raise ValueError("e2ee key must be a base64 string")
    try:
        raw = base64.b64decode(key_b64, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("e2ee key is not valid base64") from None
    return _check_key(raw)


class _Window:
    """Anti-replay window for one salt: a high-water mark plus a bitmap of the
    ``REPLAY_WINDOW`` counters below it. Small reordering passes; duplicates fail."""
    __slots__ = ("high", "bits")

    def __init__(self):
        self.high, self.bits = -1, 0

    def check(self, n: int) -> None:
        """Raise ValueError if ``n`` was already seen or is too old to track."""
        if n > self.high:
            return
        off = self.high - n
        if off >= REPLAY_WINDOW or (self.bits >> off) & 1:
            raise ValueError("replayed or stale counter")

    def accept(self, n: int) -> None:
        if n > self.high:
            shift = n - self.high
            self.bits = ((self.bits << shift) | 1) & ((1 << REPLAY_WINDOW) - 1) if shift < REPLAY_WINDOW else 1
            self.high = n
            return
        self.bits |= 1 << (self.high - n)


class E2EESession:
    def __init__(self, secret: bytes, is_device_side: bool = False, seal_salt: bytes = None,
                 is_group: bool = False, *, channel: str | None = None,
                 sender: str | None = None, check_freshness: bool = True):
        """``channel``/``sender`` are stamped into every sealed plaintext (``_ch``/``_from``)
        and ``channel`` is checked on open when the peer stamped one.

        ``seal_salt`` fixes the per-session salt instead of drawing a random one. It
        exists for test vectors ONLY: reusing a salt across processes restarts the
        counter at 0 under the same derived key, i.e. nonce reuse, which breaks
        ChaCha20-Poly1305 completely. Never persist a salt."""
        self._secret = _check_key(secret)
        #: Room mode is the only construction the app's push extension can open
        #: ("grp v2" — see PushEnvelope); notification sealing checks this.
        self.is_group = is_group
        if is_group:
            # Symmetric room mode: every member seals AND opens with the same "grp v2" label,
            # so any member reads any other. Multi-sender nonce reuse is prevented because each
            # sender carries an independent per-session salt (in the envelope).
            self._seal_info = self._open_info = b"grp v2"
        else:
            self._seal_info = b"d2c v2" if is_device_side else b"c2d v2"
            self._open_info = b"c2d v2" if is_device_side else b"d2c v2"
        if seal_salt is not None and len(seal_salt) != SALT_LEN:
            raise ValueError(f"seal_salt must be {SALT_LEN} bytes")
        self._seal_salt = seal_salt if seal_salt is not None else os.urandom(SALT_LEN)
        self._seal_key = derive_key(self._secret, self._seal_salt, self._seal_info)
        self._counter = 0
        self.channel = channel
        self.sender = sender
        self.check_freshness = check_freshness
        self._keys: "OrderedDict[bytes, bytes]" = OrderedDict()
        self._windows: "OrderedDict[bytes, _Window]" = OrderedDict()
        #: Counters of frames refused by open(), by reason — for operators' dashboards.
        self.rejected = {"malformed": 0, "auth": 0, "replay": 0, "stale": 0, "channel": 0}

    @classmethod
    def group(cls, secret: bytes, seal_salt: bytes = None, **kw) -> "E2EESession":
        """Symmetric room session matching the app's `mode: room` group cipher — used by a
        hub that shares an encrypted room with several members."""
        return cls(secret, is_group=True, seal_salt=seal_salt, **kw)

    # ── seal ─────────────────────────────────────────────────────────────────
    def seal(self, payload: dict, *, stamp: bool = True) -> dict:
        """Seal ``payload``. ``stamp=True`` (default) adds ``_ts``/``_ch``/``_from`` to a
        dict payload before encrypting; ``stamp=False`` seals the payload verbatim (the
        frozen test vectors, or a receiver that must see the exact plaintext)."""
        if self._counter > _MAX_N:
            raise ValueError("session counter exhausted — start a new session")
        n = self._counter
        self._counter += 1
        body = dict(payload) if isinstance(payload, dict) else payload
        if stamp and isinstance(body, dict):
            # Freshness/context inside the AEAD: old receivers ignore unknown keys.
            body.setdefault("_ts", int(time.time() * 1000))
            if self.channel is not None:
                body.setdefault("_ch", self.channel)
            if self.sender is not None:
                body.setdefault("_from", self.sender)
        pt = json.dumps(body, separators=(",", ":")).encode()
        ct = ChaCha20Poly1305(self._seal_key).encrypt(_nonce(n), pt, None)
        return {"e2ee": 2, "s": base64.b64encode(self._seal_salt).decode(), "n": n,
                "ct": base64.b64encode(ct).decode()}

    # ── open ─────────────────────────────────────────────────────────────────
    def _key_for(self, salt: bytes) -> bytes:
        key = self._keys.get(salt)
        if key is None:
            key = derive_key(self._secret, salt, self._open_info)
            self._keys[salt] = key
            if len(self._keys) > KEY_CACHE:
                self._keys.popitem(last=False)
        else:
            self._keys.move_to_end(salt)
        return key

    def _window_for(self, salt: bytes) -> _Window:
        w = self._windows.get(salt)
        if w is None:
            w = self._windows[salt] = _Window()
            if len(self._windows) > WINDOW_CACHE:
                self._windows.popitem(last=False)
        else:
            self._windows.move_to_end(salt)
        return w

    def open(self, envelope) -> dict:
        """Open a v2 envelope. Raises ``ValueError`` for ANY problem: not an envelope,
        malformed fields, bad tag, replay, stale timestamp, wrong channel."""
        if not (isinstance(envelope, dict) and envelope.get("e2ee") == 2):
            raise ValueError("not a v2 envelope")
        try:
            s, n, ct = envelope["s"], envelope["n"], envelope["ct"]
            if isinstance(n, bool) or not isinstance(n, int) or not 0 <= n <= _MAX_N:
                raise ValueError("bad counter")
            if not isinstance(s, str) or not isinstance(ct, str):
                raise ValueError("bad envelope")
            salt = base64.b64decode(s, validate=True)
            ctb = base64.b64decode(ct, validate=True)
            if len(salt) != SALT_LEN or len(ctb) < MIN_CT_LEN:
                raise ValueError("bad envelope")
        except (KeyError, TypeError, binascii.Error, ValueError) as e:
            self.rejected["malformed"] += 1
            raise ValueError(f"malformed envelope: {e}") from None
        window = self._window_for(salt)
        try:
            window.check(n)
        except ValueError:
            self.rejected["replay"] += 1
            raise
        try:
            pt = ChaCha20Poly1305(self._key_for(salt)).decrypt(_nonce(n), ctb, None)
        except InvalidTag:
            self.rejected["auth"] += 1
            raise ValueError("authentication failed") from None
        try:
            body = json.loads(pt)
        except ValueError:
            self.rejected["malformed"] += 1
            raise ValueError("sealed payload is not JSON") from None
        if isinstance(body, dict):
            self._check_context(body)
        window.accept(n)
        return body

    def _check_context(self, body: dict) -> None:
        ts = body.get("_ts")
        if self.check_freshness and ts is not None:
            if (isinstance(ts, bool) or not isinstance(ts, (int, float))
                    or abs(time.time() * 1000 - ts) > MAX_SKEW_MS):
                self.rejected["stale"] += 1
                raise ValueError("stale frame")
        ch = body.get("_ch")
        if ch is not None and self.channel is not None and ch != self.channel:
            self.rejected["channel"] += 1
            raise ValueError("frame sealed for another channel")
        # Transport metadata, consumed here; `_from` stays (handlers address replies by it).
        body.pop("_ts", None)
        body.pop("_ch", None)

    @staticmethod
    def is_envelope(obj) -> bool:
        return isinstance(obj, dict) and obj.get("e2ee") == 2
