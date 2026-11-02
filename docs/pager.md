# Agent pager: approve Claude Code tool calls from your phone

`carterkit.pager` turns CAR-TER into an approval pager for the Claude Code agents
running on your Mac (for example tmux pane agents). A Claude Code permission hook
asks a small local daemon; the daemon pages your phone with an Approve/Deny
notification and shows the request in the **Agents** layout. It fails closed: only
an explicit Approve carrying the live request's nonce, before its deadline, ever
allows. A timeout, a restart, a stale button or an unreachable daemon never does
(the terminal falls back to its normal prompt when the daemon is down).

**1. Install on the Mac**

```bash
pip install carterkit
carterkit pager install --dry-run --connection ~/.carter/pager/device.json  # shows the settings.json diff
carterkit pager install --connection ~/.carter/pager/device.json            # backs up, then merges
```

`install` writes the hook to `~/.carter/pager/hook.py`, merges one hook entry into
`~/.claude/settings.json` (a `settings.json.bak-<ts>` backup first; other hooks
are kept; `--event PermissionRequest|PreToolUse`, `--timeout 90`), and writes the
Agents layout to `~/.carter/pager/agents-layout.json`. `carterkit pager uninstall`
removes only that entry.

**2. Mint a personal, non-room credential.** In CAR-TER on the phone, Connect+ →
**Add Hub**, on a personal channel (for example `agents`) that is **not** an E2EE
room. Save the JSON to `~/.carter/pager/device.json` with mode `0600`. A credential
that carries `k` / `e2eeKey` (a room) is refused: in a room the app's plaintext
button frames are dropped, so every request would just time out and be denied.

**3. Run the daemon and pin the layout**

```bash
carterkit pager run --connection ~/.carter/pager/device.json
```

Push `~/.carter/pager/agents-layout.json` to the phone (carter MCP
`push_layout(layout_path=...)`, or import the file), open it, and pin it to the
layout deck so it is one swipe away.

**The Agents layout** (`pager.build_pager_layout()`, standard controls, no code):
a `pg-status` light (idle / waiting), the paged request's agent, tool and summary
labels, a full-width `pg-queue` with an Approve/Deny pair per paged request (each
button's payload carries that request's literal nonce:
`{msg_type: "action", op: "pager_decide", decision, req}`), a "+N waiting" list
of requests queued behind each agent's active one, and a `pg-log` decision audit.
`state.acks` makes a press show pending until the daemon acks it. When the phone
reconnects, the daemon re-pushes the status and re-fills the queue.

**Metrics.** `carterkit pager run` appends one line per decision to
`~/.carter/pager/metrics.jsonl` (`0600`):
`{ts, nonce, agent, tool, decision, source, latency, queued, timed_out}`.
`latency` is the seconds from paging to the decision. The timeout share is
`mean(timed_out)`:

```bash
python -c "import json;m=[json.loads(l) for l in open('$HOME/.carter/pager/metrics.jsonl')];print(len(m),'decisions',sum(x['timed_out'] for x in m)/len(m),'timed out')"
```
