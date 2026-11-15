---
# Canonical Studio protocol. tests/test_studio_guide.py checks `verbs` against the app
# (CAR-TER/App/AppState+Actions.swift: layoutSocketVerbs, studioOnlyVerbs, registerStudioRequestHandlers,
# registerRequestHandlers; AppState+LocalReadback.swift: localReadbackVerbs; AppState+EntryVerbs.swift: entryVerbs).
# `socket`: studio = the Studio Session socket only; layout = also answered on the loaded layout's own socket.
# `kind`: routed = point-to-point request with a reply (route_msg, ~5 s cap); broadcast = fire-and-forget.
# `persist`: what survives: none = nothing; session = until the Studio Session ends; disk = survives relaunch.
protocol: 2
reply_cap_seconds: 5
approval_sheet_seconds: 60
session_ttl_seconds: 7200
session_background_grace_seconds: 600
mirror_value_debounce_ms: 100
mirror_local_debounce_ms: 250
verbs:
  - name: get-connection-status
    direction: agent->phone
    socket: layout+studio
    kind: routed
    payload: null
    reply: [ok, connected, phase, channel, role, account, listening, studio]
    errors: []
    timeout: 5s
    persist: none
  - name: get-device-info
    direction: agent->phone
    socket: layout+studio
    kind: routed
    payload: null
    reply: [ok, appVersion, build, app, capabilitiesVersion, protocolVersion, catalogFingerprint, model, osVersion, features]
    errors: []
    timeout: 5s
    persist: none
  - name: get-control-state
    direction: agent->phone
    socket: layout+studio
    kind: routed
    payload: "null | {ids: [string]}"
    reply: [ok, values]
    errors: []
    timeout: 5s
    persist: none
  - name: list-layouts
    direction: agent->phone
    socket: studio
    kind: routed
    payload: null
    reply: [layouts]
    errors: []
    timeout: 5s
    persist: none
  - name: get-layout
    direction: agent->phone
    socket: studio
    kind: routed
    payload: "{file} | {name}"
    reply: [ok, file, layout]
    errors: ["pass file or name", "no such layout", "layout file unreadable", "layout nested deeper than N"]
    timeout: 5s
    persist: none
  - name: save-layout
    direction: agent->phone
    socket: studio
    kind: routed
    payload: "{layout: {...}, file?, base?} | {...layout fields, file?, base?}"
    reply: [ok, file, version, renamed, name, copy, id, copyOf, message]
    errors: ["no state", "expected object payload", "layout must have a name", "failed to encode layout", "invalid file name", "conflict"]
    timeout: 5s
    persist: disk
  - name: layout-save
    direction: agent->phone
    socket: studio
    kind: routed
    payload: "{...whole layout fields, base?}"
    reply: [ok, file, version, error, detail]
    errors: ["missing-layout", "invalid", "conflict"]
    timeout: 5s
    persist: disk
  - name: get-current-layout
    direction: agent->phone
    socket: studio
    kind: routed
    payload: "{include?: summary|full}"
    reply: [ok, isLiveEditSession, activeFile, summary, layout]
    errors: []
    timeout: 5s
    persist: none
  - name: set-control-state
    direction: agent->phone
    socket: studio
    kind: routed
    payload: "{values: {controlId: value}}"
    reply: [ok, applied, skipped]
    errors: []
    timeout: 5s
    persist: none
  - name: apply-layout
    direction: agent->phone
    socket: layout+studio
    kind: routed
    payload: "full layout JSON (no msg_type); on the layout socket also {install?: true, hub?: string}"
    reply: [ok, rendered, linked, updated, reason, error]
    errors: ["could not decode layout: ...", "not-member", "editing", "write-failed"]
    timeout: 5s
    persist: session
  - name: get-pending-edit
    direction: agent->phone
    socket: studio
    kind: routed
    payload: null
    reply: [control]
    errors: []
    timeout: 5s
    persist: none
  - name: local.describe
    direction: agent->phone
    socket: studio
    kind: routed
    payload: "{}"
    reply: [ok, layout, layoutId, namespaces, consent]
    errors: [no-layout, no-local-source, unknown-namespace, unknown-collection, bad-request]
    timeout: 5s
    persist: none
  - name: local.query
    direction: agent->phone
    socket: studio
    kind: routed
    payload: "{namespace?, collection, ...}"
    reply: [ok, rows]
    errors: [consent-pending, denied, busy, row-too-large, no-layout, no-local-source, unknown-collection, bad-request]
    timeout: 5s
    persist: none
  - name: local.upsert
    direction: agent->phone
    socket: studio
    kind: routed
    payload: "{namespace?, collection, ...}"
    reply: [ok]
    errors: [consent-pending, denied, busy, no-layout, no-local-source, unknown-collection, bad-request]
    timeout: 5s
    persist: disk
  - name: local.delete
    direction: agent->phone
    socket: studio
    kind: routed
    payload: "{namespace?, collection, ...}"
    reply: [ok]
    errors: [consent-pending, denied, busy, no-layout, no-local-source, unknown-collection, bad-request]
    timeout: 5s
    persist: disk
  - name: entry.add
    direction: agent->phone
    socket: studio
    kind: routed
    payload: "{collection, namespace?, source?, values}"
    reply: [ok, collection]
    errors: [consent-pending, denied, busy, bad-request, unknown-collection]
    timeout: 5s
    persist: disk
  - name: entry.edit
    direction: agent->phone
    socket: studio
    kind: routed
    payload: "{collection, namespace?, source?, id, values}"
    reply: [ok, collection]
    errors: [consent-pending, denied, busy, bad-request, unknown-collection]
    timeout: 5s
    persist: disk
  - name: entry.delete
    direction: agent->phone
    socket: studio
    kind: routed
    payload: "{collection, namespace?, source?, id}"
    reply: [ok, collection]
    errors: [consent-pending, denied, busy, bad-request, unknown-collection]
    timeout: 5s
    persist: disk
  - name: entry.undo
    direction: agent->phone
    socket: studio
    kind: routed
    payload: "{collection}"
    reply: [ok, undone]
    errors: [consent-pending, denied, busy, bad-request]
    timeout: 5s
    persist: disk
  - name: watch-traffic
    direction: agent->phone
    socket: studio
    kind: routed
    payload: "{enable: bool, sample_ms?: int, filter?: string}"
    reply: [ok, enabled, sample_ms]
    errors: ["expected {enable...}", "sample_ms must be an integer"]
    timeout: 5s
    persist: session
  - name: provision-device
    direction: agent->phone
    socket: studio
    kind: routed
    payload: "{channel, role?: hub|controller|viewer, reuse_room_key?: bool}"
    reply: [ok, status, request_id]
    errors: [bad-request, no-connect-session, busy]
    timeout: 5s
    persist: none
  - name: get-provision-result
    direction: agent->phone
    socket: studio
    kind: routed
    payload: "{request_id}"
    reply: [ok, status, request_id, credential, key_reuse, expires_at]
    errors: [denied, mint-failed, unknown-request]
    timeout: 5s
    persist: none
events:
  - name: hello
    direction: phone->agent
    socket: studio
    kind: broadcast
    fields: [device, appVersion, app, capabilitiesVersion, layout]
  - name: layout
    direction: phone->agent
    socket: studio
    kind: broadcast
    fields: [layout, layoutId, tabs, controls, tab]
  - name: layout-closed
    direction: phone->agent
    socket: studio
    kind: broadcast
    fields: []
  - name: tab
    direction: phone->agent
    socket: studio
    kind: broadcast
    fields: [tab, title, index]
  - name: action
    direction: phone->agent
    socket: studio
    kind: broadcast
    fields: [control, controlType, payload, local]
  - name: value
    direction: phone->agent
    socket: studio
    kind: broadcast
    fields: [control, value]
  - name: local
    direction: phone->agent
    socket: studio
    kind: broadcast
    fields: [namespace, collection, op, ids, total, seq]
  - name: bye
    direction: phone->agent
    socket: studio
    kind: broadcast
    fields: []
---

# Studio: the protocol for agents

Everything an agent needs to drive a CAR-TER phone through a Studio Session. Read this, not the app
code. The frontmatter above is the machine-checked verb table; `tests/test_studio_guide.py` fails if
the app handles a verb this file does not list (or the reverse). Wire details older than this guide
live in carter-mcp's `PROTOCOL.md`; where the two disagree, this file (checked against the app) wins.

## 1. What a Studio Session is

A **Studio Session** pairs one phone with one agent (carter-mcp, carterkit, a Claude session) over a
MeshSocket channel on a relay. While it lives the agent can list, read, save and push layouts,
drive control values, and watch the user. It is a **bearer pairing**: whoever holds the QR can do all of
that, so the session is time-boxed (`session_ttl_seconds`, 2 h, extendable from the on-phone
banner; `session_background_grace_seconds`, 10 min after the app leaves the foreground) and the
user can tap **End** at any time (Studio, Connect).

### The two sockets

| | studio socket | layout socket |
|---|---|---|
| Opened by | scanning the pairing QR | loading any layout that has a `connection` block |
| Lifetime | the session; survives every layout swap | the loaded layout |
| Answers | every verb in the table | only `get-connection-status`, `get-device-info`, `get-control-state`, `apply-layout` (hub install/linked push) and the hub surface verbs (`prompt`, `sheet`, `toast`, `progress`, `haptic`, `log`) |
| Carries | routed verbs, `studio.event` mirror frames, editor broadcasts | the layout's own sync and action traffic |

An agent only ever talks on the studio socket. The layout socket belongs to the layout (a hub or
server); Studio verbs that read or write the library are refused there on purpose.
`get-connection-status` describes the **layout** link at top level and the Studio link in its
`studio` object, which exists only during a session.

## 2. Pairing

The QR (a JSON object, shown by the agent) has these fields:

| field | meaning |
|---|---|
| `url` | relay WebSocket URL (required) |
| `channel` | MeshSocket channel (required; sanitized to `[A-Za-z0-9_-]`, max 64) |
| `role` | `viewer` by default when absent |
| `token` | relay token, optional |
| `k` | optional base64 end-to-end key; present means E2EE on |

Flow: phone opens Studio, Connect, **Open Scanner**, scans. The scanner never connects on its own:
it shows **"Start a Studio Session?"** with the relay host, channel, role and whether E2EE is on, and
waits for the owner's **confirm tap**. After the tap the phone dials the studio socket (identifying with
broadcast rights, routing off: it answers routed requests, it never sends them). Until that tap, nothing
reaches the phone. Other QR types (layout links, Room invites) are handled by the same scanner and are
not Studio.

On connect the phone shows a blank "Studio Session" placeholder layout (so `get-current-layout` has
`summary: null`-ish content until something is pushed or opened) and announces `hello` + `layout`.

## 3. Push, apply, save, persist

These words are not interchangeable. The reply that proves each:

| You want | Verb | What happens | Survives relaunch? | Proof |
|---|---|---|---|---|
| Show it on the phone now | `apply-layout` (routed) | Layout is decoded, swapped onto the screen, dials its own `connection` on the layout socket. Nothing is written to the library. | **No**, until saved | reply `ok: true` + `rendered` (the structural echo built from what decoded); then `get-current-layout` |
| Show it, no reply | `layout-update` broadcast | Same render, fire-and-forget | No | none: always read back |
| Keep it in the library | `save-layout` (routed) | Written to the layouts folder; the library is rescanned | **Yes** | reply `ok: true` + `file` + `version`; then `get-layout` / `list-layouts` |
| Save, routed layout-save | `layout-save` (routed) | Same write as the broadcast form | Yes | reply `ok: true` + `file` + `version`; a bare or undecodable body gets `{ok: false, error: "missing-layout" \| "invalid", detail}`. The broadcast form still carries the whole layout and has no reply. |
| Read what is live | `get-current-layout` (reply carries `version`, the content digest of the active file; `apply-layout` replies carry it too) | Echo from the applied config | n/a | `summary` (or `layout` with `include: full`) |
| Read what is on disk | `get-layout` | Raw saved JSON, credentials redacted | n/a | `layout` |

Rules that follow from the code:

- **Push does not save and save does not push.** `save-layout` never changes what is on screen;
  `apply-layout` never writes to the library. To "ship" a layout do both, and confirm each with its
  own reply.
- `apply-layout` outside a live session (the layout socket, a hub): with `install: true` the layout is
  installed into the library; without it the layout is held in the single **linked** slot (shown, actions
  routed back, offered "Keep this layout") and is not in the library until the user keeps it. Membership:
  the pushed layout's channel must equal the channel on screen (or the studio pairing); else
  `{ok: false, reason: "not-member"}`. `editing` means the on-phone editor is open; retry later.
- `rendered` is truthful about what *decoded*: a control dropped on decode does not appear. It is not a
  pixel check. A pushed layout without a `connection` block is studio-only: drive it with
  `set-control-state`, not by simulating broadcasts.
- `save-layout` never overwrites a *different* layout that merely shares a name: the planner matches by layout
  `id`; a name clash gets `renamed: true` and a new `name`. A layout that is read-only here (newer
  `schemaVersion`) is saved beside the original: `copy: true`, `copyOf`, `message`.
- The `file` you pass is reduced to its last path component and forced to `.json`; anything with
  separators, dots-first, or empty is `invalid file name`.
- `get-layout` redacts credentials. A save that round-trips redacted JSON must restore secrets
  agent-side.
- `set-control-state` is session-only: values are not persisted and it emits no `value` event.
  Unknown ids and unusable values are `skipped`, not an error: check `applied`.
- `local.upsert` / `local.delete` / `entry.*` write on-device records and **do persist** (the local
  store), behind the owner's consent tap (section 6).

## 4. Verbs

The table in the frontmatter is exhaustive. Behaviour notes the table cannot carry:

- **Reply envelope.** Replies are objects; most carry `ok`. A bare `null`/no reply is a timeout (the
  phone is locked, the app predates the verb, or the relay dropped it). Some errors have no `ok` and use
  `{error: <code>, reason}` (provision, consent). `list-layouts` and `get-pending-edit` have no `ok`.
- `list-layouts` returns `{layouts: [{name, file, tabs: [{title, icon}], accentColor}]}`.
- `get-pending-edit` drains once: `{control: {...}}` then `{control: null}`. It is the pull half of the
  on-glass control editor ("shape it on glass"): broadcast `control-edit-request` (`{control: {type, id, ...props}}`), the user edits and taps
  **Send to Editor**, you poll.
- `watch-traffic` enables a tap: while on, the phone broadcasts `studio.traffic` frames (control, event,
  valuePath, value up to 1 KB, frameMsgType) after decrypt and before render, at most one per control per
  `sample_ms` (default 250, floor 100). It turns off when the session ends.
- `get-device-info.features` is the exact list of things the build speaks (`control.<type>`,
  `sync.<method>`, `action.<method>`, `layout.<key>`, optionally `name@N`). Absent on old builds, which
  means unknown, not empty. Debug builds also handle `end-studio-session` (never shipped; not part of
  the contract).
- `provision-device` / `get-provision-result`: section 7.

## 5. Mirror events (phone to agent)

While a session is live the phone broadcasts on the studio socket: `broadcast_request` with
`msg_type: "studio.event"` and a flat `event` discriminator. No timestamps; stamp arrival yourself.

| event | fields | when |
|---|---|---|
| `hello` | `device`, `appVersion`, `layout` (name or null on the blank placeholder) | studio socket confirmed connect, listener re-arm, layout load |
| `layout` | `layout`, `layoutId` (file/id or null), `tabs` `[{id,title}]`, `controls` (count), `tab` (initially selected) | a real layout finished loading |
| `layout-closed` | none | the active layout was torn down with no replacement |
| `tab` | `tab` (id = title), `title`, `index` | the user switches tabs |
| `action` | `control`, `controlType`, `payload`; for a `method: "local"` action `local: {op, collection}` instead of `payload` (record data never leaves the phone) | an action fires; additive, the real action is dispatched separately |
| `value` | `control`, `value` | a **person** edited a control; wire-originated values are never echoed; coalesced to 100 ms (first and last sample of a drag) |
| `local` | `namespace`, `collection`, `op` (`upsert` or `delete`), `ids`, `total`, `seq` | a write to a `mirror: true` collection; ids only, no bodies; 250 ms trailing coalesce; `seq` counts from 1 per session |
| `bye` | none | the session ends |

**`hello` and `layout` repeat.** They are re-announced on every confirmed connect (including transport
auto-reconnects) and listener re-arm, because a frame sent while the socket is still dialing is
dropped. Treat them as idempotent state, never as a once-per-session handshake. If you attach late,
do not wait: `get-current-layout` and `get-device-info` give the same facts, and a real event
overrides what you inferred.

## 6. Timing and consent

- **Routed reply cap ~5 s** (`reply_cap_seconds`). A verb that needs a human therefore never waits
  inside the request: `provision-device` answers `pending` at once and you poll
  `get-provision-result`; `local.*`/`entry.*` answer `consent-pending` and you retry after the tap.
- **Approval sheet: 60 s** (`approval_sheet_seconds`) for provisioning and for local-data consent. No tap
  in time is `denied` with reason `timeout`. Only one sheet at a time across both: a second request
  gets `busy`.
- **Local-data consent** is per session, per layout and per scope (read, or read+write). `local.describe`
  needs none; `local.query` needs read; `upsert`/`delete`/`entry.*` need read+write. A denial is reported
  once; the next call re-arms the sheet. The grant is dropped when the session ends or the layout
  changes.
- **Debounce:** mirror `value` 100 ms, `local` 250 ms.
- **Session lifetime:** 2 h (extend on the banner), 10 min background grace.
- A reply you did not get within about 5 s is *unknown*, not *failed*. Read back before retrying.

## 7. Provision a hub device

Mints a hub credential through the phone (the Add Device flow), gated by a human tap.

1. `provision-device {channel, role?: "hub", reuse_room_key?: true}`. Reply `{ok: true, status:
   "pending", request_id}` or `{error, reason}`: `bad-request` (empty channel, bad role),
   `no-connect-session` (the phone has no Connect+ session), `busy`.
2. The phone raises the approval sheet (60 s). Tell the user to look at the phone.
3. Poll `get-provision-result {request_id}`: `{ok: true, status: "pending"}` while waiting; then once:
   `{ok: true, credential: {url, channel, token, role, refresh, did, validator, k}, key_reuse:
   reused-existing | fresh-channel-had-none | fresh-forced, expires_at}`, or
   `{error: "denied", reason: user-denied | timeout | dismissed}`, `{error: "mint-failed", reason}`,
   `{error: "unknown-request"}` (unknown id, session ended, or **already drained**).
4. The result is drained exactly once, keyed by `request_id` for the whole Studio Session, so a poll
   after a redial (new socket) still gets it. Write the credential to a `0600` file at once; never print `token`, `refresh` or `k`.

`reuse_room_key: true` reuses the channel's existing key (changing it breaks every layout that pins the
old one); `false` forces a fresh 32-byte key. Pending state dies with the session.

## 8. Failure table

| Situation | What the agent sees | What to do |
|---|---|---|
| Phone locked or app suspended | routed verbs time out (~5 s, `null`) | ask the user to wake and open the app; a pushed layout may be lost; read back after |
| Relay down or token expired | the connection fails before any verb; pairing never completes | check the relay, mint a fresh pairing QR |
| Second Studio (another agent, or a re-scan while live) | the app ends the first session (`bye`, disconnect) and starts the new one; the first agent's verbs time out. Ending the new session returns to the user's own layout, not the placeholder | assume one agent per phone; ask before re-scanning |
| Session ended (End tap, 2 h TTL, background grace) | `bye` event, then timeouts; verbs are no longer armed | re-pair. A real layout on screen stays up; the blank placeholder reverts to the previous layout |
| Layout deleted on the phone | `get-layout` -> `{ok: false, error: "no such layout"}`; `list-layouts` omits it | `list-layouts` before relying on a file name; re-`save-layout` if you still hold the source |
| Invalid layout | `apply-layout` -> `{ok: false, error: "could not decode layout: ..."}`; nothing rendered | fix the named field and push again; never assume success from a non-error |
| App too old for a verb | the verb times out | `get-device-info` (it may time out too): update the app |
| Name clash on save | `ok: true` with `renamed: true` / `copy: true` | use the returned `file`/`name`/`id`, not the one you sent |
| Wrong socket | studio-only verb sent on the layout socket is not answered | send on the studio socket |
| Linked push refused | `{ok: false, reason: not-member | editing | write-failed}` | `editing`: retry when the editor closes; `not-member`: the channel does not match |
| Consent pending / denied | `{error: consent-pending, request_id}` / `{error: denied}` | tell the user to tap the sheet; retry; do not spam (denial is per call) |
| Provision gate | `no-connect-session`, `busy`, `denied` | see section 7 |
| Save conflict | `save-layout {base}` / `layout-save {base}` -> `{ok: false, error: "conflict", version: <current>}`; nothing written | `get-layout`, merge, retry with `base` = the `version` you read. Without `base` the save is last write wins |
| Expired share link | the link says "This link expired. Ask for a new one." (`exp` query, unix seconds) | mint a new link |

## 9. Worked sequences

### Pair, push, read back, save

1. Agent shows the pairing QR (`url`, `channel`, optional `role`/`token`/`k`).
2. User scans (Studio, Connect, Open Scanner) and taps **Start**. The agent sees `hello` (and `layout`
   once something is open). If it sees neither, call `get-connection-status`, then `get-device-info`.
3. `get-device-info` -> check `appVersion` and `features` before pushing newer controls.
4. `apply-layout <layout json>` -> `ok: true, rendered`. Compare `rendered` to what you sent.
5. `get-current-layout {include: "summary"}` to confirm the live state. `set-control-state` to drive
   values, `get-control-state` to read them back, `watch-traffic` if the layout syncs.
6. When the user is happy: `save-layout {layout, file?}` -> `ok: true, file`. Then `get-layout {file}`
   to prove it landed. Only now is it safe across a relaunch.
7. End: the user taps End, or the TTL runs out. The agent sees `bye`.

### Provision a hub device

1. Paired as above; the user has Connect+ on the phone.
2. `provision-device {channel: "lights"}` -> `request_id`; tell the user to approve on the phone.
3. Poll `get-provision-result {request_id}` every second or two, up to ~60 s, until not `pending`.
4. On success write `credential` to a `0600` file; give the hub its path. Report only non-secret
   metadata (did, channel, role, expiry, host, key_reuse).
5. Push the hub's layout with `apply-layout` (with `install: true` when the hub pushes over its own
   layout socket) and confirm with `get-current-layout`.
