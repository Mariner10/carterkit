"""Provision a hub device through the paired phone (Studio ``provision-device``).

Human-gated: the phone raises an approval sheet; this module polls
``get-provision-result`` until the owner taps. See ``carterkit studio guide`` section 7.
The credential is written to a 0600 file and never printed.
"""
from __future__ import annotations

import asyncio
import json
import os
import time

SECRET_KEYS = ("token", "refresh", "k", "validator")


class ProvisionError(RuntimeError):
    """The phone refused, timed out, or could not mint the credential."""


async def provision(hub, channel: str, *, role: str = "hub", reuse_room_key: bool = True,
                    timeout: float = 70.0, poll: float = 1.5, out=print) -> dict:
    """Run provision-device and poll for the result. Returns the full reply
    (``credential``, ``key_reuse``, ``expires_at``)."""
    res = await hub.route("provision-device", {"channel": channel, "role": role,
                                               "reuse_room_key": reuse_room_key}, timeout=5.0)
    if not isinstance(res, dict) or res.get("error") or res.get("ok") is False:
        why = (res or {}).get("reason") or (res or {}).get("error") or "no reply"
        raise ProvisionError(f"provision-device refused: {why}")
    rid = res.get("request_id")
    out("Look at the phone and approve the new device (60 s).")
    deadline = time.monotonic() + timeout
    while True:
        r = await hub.route("get-provision-result", {"request_id": rid}, timeout=5.0)
        if isinstance(r, dict) and r.get("error"):
            raise ProvisionError(f"provisioning failed: {r['error']}"
                                 + (f" ({r['reason']})" if r.get("reason") else ""))
        if isinstance(r, dict) and r.get("credential"):
            return r
        if time.monotonic() >= deadline:
            raise ProvisionError("timed out waiting for approval on the phone")
        await asyncio.sleep(poll)


def write_device(path: str, credential: dict) -> None:
    """Write the credential JSON with mode 0600 (created private, never widened)."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(credential, f, indent=2)
        f.write("\n")
    os.chmod(path, 0o600)


def summary(reply: dict) -> str:
    """What was minted, without any secret."""
    c = reply.get("credential") or {}
    bits = [f"{k}={c[k]}" for k in ("did", "channel", "role", "url") if c.get(k)]
    for k in ("key_reuse", "expires_at"):
        if reply.get(k):
            bits.append(f"{k}={reply[k]}")
    return " ".join(bits)
