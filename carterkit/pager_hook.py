#!/usr/bin/env python3
"""CAR-TER pager hook for Claude Code (stdlib only — copied to ~/.carter/pager/hook.py).

Claude Code runs this as a ``PermissionRequest`` (default) or ``PreToolUse`` command
hook. It reads the hook JSON on stdin, asks the running ``carterkit pager run``
daemon over its Unix socket, blocks up to ``--timeout`` + 5 s, and prints the hook
decision JSON.

FAIL CLOSED toward the human: only an explicit ``allow`` from the daemon ever
allows. Any error — bad stdin, no daemon, socket timeout, a garbled reply —
yields NO decision (PermissionRequest: the normal terminal prompt appears) or
``permissionDecision: "ask"`` (PreToolUse). It never auto-allows.

Output shapes (Claude Code hooks reference, https://code.claude.com/docs/en/hooks,
checked 2026-09-25):

- PermissionRequest: ``{"hookSpecificOutput": {"hookEventName": "PermissionRequest",
  "decision": {"behavior": "allow"|"deny", "message": ...}}}``; no output = the
  permission flow proceeds unchanged (the user is prompted).
- PreToolUse: ``{"hookSpecificOutput": {"hookEventName": "PreToolUse",
  "permissionDecision": "allow"|"deny"|"ask", "permissionDecisionReason": ...}}``.
"""
import argparse
import json
import os
import socket
import sys

EVENTS = ("PermissionRequest", "PreToolUse")
DEFAULT_SOCKET = "~/.carter/pager/pager.sock"
DEFAULT_TIMEOUT = 90.0
GRACE = 5.0                # the daemon denies at its deadline; wait a little past it
SUMMARY_MAX = 400          # the daemon clips further before anything leaves the Mac


def agent_name(data, env=None):
    """``claude %3 · 1a2b3c4d`` — the tmux pane plus a short session id."""
    env = os.environ if env is None else env
    pane = env.get("TMUX_PANE") or ""
    sid = str(data.get("session_id") or "")[:8]
    name = f"claude {pane}" if pane else "claude"
    return f"{name} · {sid}" if sid else name


def summarize(tool, tool_input):
    """One short line describing the tool call (the command, the file, …)."""
    if not isinstance(tool_input, dict):
        text = "" if tool_input is None else str(tool_input)
    else:
        for key in ("command", "file_path", "notebook_path", "url", "pattern", "path",
                    "query", "prompt", "description"):
            val = tool_input.get(key)
            if isinstance(val, str) and val.strip():
                text = val
                break
        else:
            try:
                text = json.dumps(tool_input, default=str)
            except (TypeError, ValueError):
                text = str(tool_input)
    text = " ".join(text.split())
    return text if len(text) <= SUMMARY_MAX else text[:SUMMARY_MAX - 1] + "…"


def ask_daemon(agent, tool, summary, socket_path, timeout):
    """``(decision, reason)`` from the daemon; raises on anything unexpected."""
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect(os.path.expanduser(socket_path))
        s.sendall(json.dumps({"agent": agent, "tool": tool, "summary": summary}).encode()
                  + b"\n")
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
            if len(buf) > 65536:
                raise ValueError("reply too long")
    reply = json.loads(buf)
    if not isinstance(reply, dict) or reply.get("decision") not in ("allow", "deny"):
        raise ValueError(f"bad pager reply: {reply!r}")
    reason = reply.get("reason")
    return reply["decision"], reason if isinstance(reason, str) else ""


def hook_output(event, decision, reason=""):
    """The hook JSON for ``decision`` in {"allow", "deny", None}; None = no
    decision (PermissionRequest → ``None``: print nothing; PreToolUse → ask)."""
    if event == "PreToolUse":
        out = {"hookEventName": "PreToolUse",
               "permissionDecision": decision if decision in ("allow", "deny") else "ask"}
        if reason:
            out["permissionDecisionReason"] = reason
        return {"hookSpecificOutput": out}
    if decision == "allow":
        return {"hookSpecificOutput": {"hookEventName": "PermissionRequest",
                                       "decision": {"behavior": "allow"}}}
    if decision == "deny":
        return {"hookSpecificOutput": {"hookEventName": "PermissionRequest",
                                       "decision": {"behavior": "deny",
                                                    "message": reason or "Denied from CAR-TER"}}}
    return None


def run(stdin_text, *, event, socket_path, timeout, env=None):
    """Pure core: hook stdin text in, hook stdout object (or None) out."""
    decision, reason = None, ""
    try:
        data = json.loads(stdin_text)
        if not isinstance(data, dict):
            raise ValueError("hook input is not an object")
        tool = str(data.get("tool_name") or "tool")
        decision, reason = ask_daemon(agent_name(data, env), tool,
                                      summarize(tool, data.get("tool_input")),
                                      socket_path, timeout + GRACE)
        if decision == "deny":
            reason = f"Denied from CAR-TER ({reason})" if reason else "Denied from CAR-TER"
        else:
            reason = "Approved from CAR-TER"
    except Exception as e:  # noqa: BLE001 — every failure means "ask the human"
        decision = None
        reason = f"CAR-TER pager unavailable ({type(e).__name__}); asking in the terminal"
        print(reason, file=sys.stderr)
    return hook_output(event, decision, reason)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--event", choices=EVENTS, default="PermissionRequest")
    p.add_argument("--socket", default=DEFAULT_SOCKET)
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    try:
        args = p.parse_args(argv)
    except SystemExit:
        return 0                    # a bad hook command line must not block anything
    try:
        stdin_text = sys.stdin.read()
    except Exception:  # noqa: BLE001
        stdin_text = ""
    out = run(stdin_text, event=args.event, socket_path=args.socket, timeout=args.timeout)
    if out is not None:
        sys.stdout.write(json.dumps(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
