"""One canonical JSON (RFC 8785 JCS) and the layout ``contentDigest``.

This is THE single canonical-JSON implementation in carterkit. Every digest a
layout carries (K11 patch ``layout_hash``, package ``baseDigest``, the "Modified
locally" check, provenance ``parents[].digest``, future attestations) calls
:func:`content_digest` — never ``json.dumps(sort_keys=True)``.

The app's twin is ``LayoutDigest`` (``CAR-TER/Services/LayoutDigest.swift``). Both
are held byte-identical by the shared golden fixtures in
``tests/fixtures/canonical-fixtures.json`` (copied verbatim into
``CAR-TERTests/Fixtures/``).

JCS in short:
  - objects: members sorted by key compared as UTF-16 code units, no whitespace
  - strings: only ``"`` ``\\`` and U+0000..U+001F are escaped (``\\b \\t \\n \\f \\r``
    short forms, else ``\\u00xx`` lowercase); everything else is raw UTF-8
  - numbers: IEEE-754 doubles printed as ECMAScript ``Number.prototype.toString``
    (``1e+21``, ``0.000001``, ``1e-7``, ``-0`` → ``0``); NaN/Infinity are errors
  - ``true`` / ``false`` / ``null`` as literals

Digest scope (decision carter-m7s.2 Q3): SHA-256 over JCS of the layout with every
credential removed (the app's ``LayoutRedaction`` wire flavour: ``connection.token``,
``connection.e2eeKey``, ``sources.*.{username,password,token,headers}``) and minus
``provenance``, ``attestations`` and ``extensions.editor``. So two people who
installed the same template with different tokens get the same digest.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any

__all__ = [
    "canonical_json", "canonical_bytes", "loads",
    "strip_credentials", "digest_scope", "content_digest",
    "DIGEST_PREFIX", "CONNECTION_SECRET_KEYS", "SOURCE_SECRET_KEYS",
    "EXCLUDED_TOP_LEVEL_KEYS", "EXCLUDED_EXTENSION_KEYS",
]

#: Every digest string is ``"sha256:" + 64 lowercase hex`` (algorithm-tagged so an
#: attestation can name what it signed).
DIGEST_PREFIX = "sha256:"

#: Mirrors ``LayoutRedaction.connectionSecretKeys`` / ``sourceSecretKeys`` in the app.
CONNECTION_SECRET_KEYS = ("token", "e2eeKey")
SOURCE_SECRET_KEYS = ("username", "password", "token", "headers")

#: Top-level keys outside the digest (they describe the document, not its content).
EXCLUDED_TOP_LEVEL_KEYS = ("provenance", "attestations")
#: ``extensions.<key>`` entries outside the digest (editor-only state).
EXCLUDED_EXTENSION_KEYS = ("editor",)


# ── canonical JSON ───────────────────────────────────────────────────────────

def _reject_constant(name: str):
    raise ValueError(f"canonical JSON has no {name}")


def loads(text: str | bytes) -> Any:
    """Parse JSON text for canonicalization (NaN/Infinity literals are rejected)."""
    return json.loads(text, parse_constant=_reject_constant)


def _number(x: float | int) -> str:
    """ECMAScript Number.prototype.toString for an IEEE-754 double."""
    if isinstance(x, int):
        try:
            x = float(x)
        except OverflowError:
            raise ValueError("integer out of IEEE-754 double range") from None
    if not math.isfinite(x):
        raise ValueError("canonical JSON has no NaN or Infinity")
    if x == 0:
        return "0"                                  # also -0
    sign = "-" if x < 0 else ""
    digits, n = _shortest_digits(abs(x))
    return sign + _es_format(digits, n)


def _shortest_digits(x: float) -> tuple[str, int]:
    """(significant digits, decimal exponent n) with value = 0.DIGITS × 10^n,
    from the shortest round-trip repr."""
    text = repr(x)
    mantissa, _, exp = text.partition("e")
    exponent = int(exp) if exp else 0
    whole, _, frac = mantissa.partition(".")
    digits = whole + frac
    n = len(whole) + exponent
    stripped = digits.lstrip("0")
    n -= len(digits) - len(stripped)
    digits = stripped.rstrip("0")
    return digits, n


def _es_format(digits: str, n: int) -> str:
    k = len(digits)
    if k <= n <= 21:
        return digits + "0" * (n - k)
    if 0 < n <= 21:
        return digits[:n] + "." + digits[n:]
    if -6 < n <= 0:
        return "0." + "0" * (-n) + digits
    e = n - 1
    mant = digits[0] + ("." + digits[1:] if k > 1 else "")
    return f"{mant}e{'+' if e >= 0 else '-'}{abs(e)}"


_SHORT_ESCAPES = {'"': '\\"', "\\": "\\\\", "\b": "\\b", "\t": "\\t",
                  "\n": "\\n", "\f": "\\f", "\r": "\\r"}


def _string(s: str) -> str:
    out = ['"']
    for ch in s:
        esc = _SHORT_ESCAPES.get(ch)
        if esc is not None:
            out.append(esc)
        elif ord(ch) < 0x20:
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _utf16_key(key: str) -> bytes:
    # Big-endian UTF-16 bytes compare exactly like UTF-16 code-unit sequences.
    return key.encode("utf-16-be", "surrogatepass")


def _serialize(value: Any, out: list[str]) -> None:
    if value is None:
        out.append("null")
    elif value is True:
        out.append("true")
    elif value is False:
        out.append("false")
    elif isinstance(value, (int, float)):
        out.append(_number(value))
    elif isinstance(value, str):
        out.append(_string(value))
    elif isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise TypeError(f"canonical JSON object keys must be str, got {type(key).__name__}")
        out.append("{")
        for i, key in enumerate(sorted(value, key=_utf16_key)):
            if i:
                out.append(",")
            out.append(_string(key))
            out.append(":")
            _serialize(value[key], out)
        out.append("}")
    elif isinstance(value, (list, tuple)):
        out.append("[")
        for i, item in enumerate(value):
            if i:
                out.append(",")
            _serialize(item, out)
        out.append("]")
    else:
        raise TypeError(f"not a JSON value: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    """RFC 8785 canonical JSON text of a parsed JSON value."""
    out: list[str] = []
    _serialize(value, out)
    return "".join(out)


def canonical_bytes(value: Any) -> bytes:
    """RFC 8785 canonical JSON as UTF-8 bytes (what gets hashed)."""
    return canonical_json(value).encode("utf-8")


# ── layout digest ────────────────────────────────────────────────────────────

def strip_credentials(layout: dict) -> dict:
    """A deep copy of ``layout`` with every credential field removed (the app's
    ``LayoutRedaction.strippingCredentials``)."""
    out = copy.deepcopy(layout)
    conn = out.get("connection")
    if isinstance(conn, dict):
        for key in CONNECTION_SECRET_KEYS:
            conn.pop(key, None)
    sources = out.get("sources")
    if isinstance(sources, dict):
        for source in sources.values():
            if isinstance(source, dict):
                for key in SOURCE_SECRET_KEYS:
                    source.pop(key, None)
    return out


def digest_scope(layout: dict) -> dict:
    """The part of a layout the digest covers: credentials stripped, minus
    ``provenance``, ``attestations`` and ``extensions.editor`` (an ``extensions``
    object left empty by that is dropped too)."""
    if not isinstance(layout, dict):
        raise TypeError("a layout digest needs a JSON object")
    out = strip_credentials(layout)
    for key in EXCLUDED_TOP_LEVEL_KEYS:
        out.pop(key, None)
    ext = out.get("extensions")
    if isinstance(ext, dict):
        for key in EXCLUDED_EXTENSION_KEYS:
            ext.pop(key, None)
        if not ext:
            out.pop("extensions")
    return out


def content_digest(layout: dict | str | bytes) -> str:
    """``"sha256:<hex>"`` over the JCS bytes of :func:`digest_scope`. Accepts a
    parsed layout or its JSON text."""
    if isinstance(layout, (str, bytes, bytearray)):
        layout = loads(layout)
    return DIGEST_PREFIX + hashlib.sha256(canonical_bytes(digest_scope(layout))).hexdigest()
