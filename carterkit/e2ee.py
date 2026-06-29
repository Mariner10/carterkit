"""Hub-side Connect+ E2EE v2. FROZEN construction — byte-identical to the Swift CryptoKit
core (see the Plan-4a v2 test vectors). ChaCha20-Poly1305 IETF + HKDF-SHA256 with a
per-session random salt (transmitted in the envelope) so reconnects never reuse a nonce."""
import base64
import json
import os
import struct
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305


def derive_key(secret: bytes, session_salt: bytes, info: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=session_salt, info=info).derive(secret)


def _nonce(counter: int) -> bytes:
    return b"\x00\x00\x00\x00" + struct.pack(">Q", counter)


class E2EESession:
    def __init__(self, secret: bytes, is_device_side: bool = False, seal_salt: bytes = None,
                 is_group: bool = False):
        self._secret = secret
        if is_group:
            # Symmetric room mode: every member seals AND opens with the same "grp v2" label,
            # so any member reads any other. Multi-sender nonce reuse is prevented because each
            # sender carries an independent per-session salt (in the envelope).
            self._seal_info = self._open_info = b"grp v2"
        else:
            self._seal_info = b"d2c v2" if is_device_side else b"c2d v2"
            self._open_info = b"c2d v2" if is_device_side else b"d2c v2"
        self._seal_salt = seal_salt if seal_salt is not None else os.urandom(16)
        self._seal_key = derive_key(secret, self._seal_salt, self._seal_info)
        self._counter = 0

    @classmethod
    def group(cls, secret: bytes, seal_salt: bytes = None) -> "E2EESession":
        """Symmetric room session matching the app's `mode: room` group cipher — used by a
        hub that shares an encrypted room with several members."""
        return cls(secret, is_group=True, seal_salt=seal_salt)

    def seal(self, payload: dict) -> dict:
        n = self._counter
        self._counter += 1
        pt = json.dumps(payload, separators=(",", ":")).encode()
        ct = ChaCha20Poly1305(self._seal_key).encrypt(_nonce(n), pt, None)
        return {"e2ee": 2, "s": base64.b64encode(self._seal_salt).decode(), "n": n, "ct": base64.b64encode(ct).decode()}

    def open(self, envelope: dict) -> dict:
        if envelope.get("e2ee") != 2 or "s" not in envelope:
            raise ValueError("not a v2 envelope")
        salt = base64.b64decode(envelope["s"])
        key = derive_key(self._secret, salt, self._open_info)
        pt = ChaCha20Poly1305(key).decrypt(_nonce(envelope["n"]), base64.b64decode(envelope["ct"]), None)
        return json.loads(pt)

    @staticmethod
    def is_envelope(obj) -> bool:
        return isinstance(obj, dict) and obj.get("e2ee") == 2
