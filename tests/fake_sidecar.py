#!/usr/bin/env python3
"""Stand-in for the Go `carter-direct` binary: speaks the stdio IPC table.
Logs every received frame to $FAKE_LOG (json lines). Test-only ops: `inject` (forward
`frame` + base64 `body_b64` back out as a sidecar frame), `die` (exit 1)."""
import base64
import json
import os
import struct
import sys

inp, out = sys.stdin.buffer, sys.stdout.buffer


def send(h, body=b""):
    hb = json.dumps(h).encode()
    out.write(struct.pack(">II", 4 + len(hb) + len(body), len(hb)) + hb + body)
    out.flush()


send({"op": "ready", "version": "fake"})
while True:
    raw = inp.read(4)
    if len(raw) < 4:
        break
    n = struct.unpack(">I", raw)[0]
    buf = inp.read(n)
    hl = struct.unpack(">I", buf[:4])[0]
    h, body = json.loads(buf[4:4 + hl]), buf[4 + hl:]
    if os.environ.get("FAKE_LOG"):
        with open(os.environ["FAKE_LOG"], "a") as f:
            f.write(json.dumps({"h": h, "n": len(body), "pid": os.getpid()}) + "\n")
    op = h.get("op")
    if op == "offer":
        send({"op": "answer", "session": h["session"], "sdp": "fake-answer-" + h["session"]})
        send({"op": "session", "session": h["session"], "state": "connected", "path": "lan"})
    elif op == "inject":
        send(h["frame"], base64.b64decode(h.get("body_b64", "")))
    elif op == "die":
        sys.exit(1)
if os.environ.get("FAKE_LOG"):                     # stdin closed: the stop path a real sidecar takes
    with open(os.environ["FAKE_LOG"], "a") as f:
        f.write(json.dumps({"h": {"op": "eof"}, "n": 0, "pid": os.getpid()}) + "\n")
