# Backend connectors for iOS surfaces

`Hub.surfaces` connects a layout to notifications, Live Activities, widgets,
Control Center state, and the cached readings exposed to Shortcuts. Use the same
control handles and bindings that already drive the open app.

## Start from Add Hub

Export the credential JSON from CAR-TER's **Hubs → Add Hub** and keep it on your
backend. `ui.serve(connection="device.json")` parses its validator URL, device
token, refresh secret, channel, and encryption key. Start the hub with
`async with hub:` so token renewal and incoming actions keep running. Ambient
calls use the current renewed device token. An owner `session_jwt` also works
with `CarterClient`; a local relay key or room membership token cannot authorize
account push endpoints. Never embed the hub credential in a shared layout.

```python
from carterkit import Layout, notification_action

with Layout("Workshop", id="workshop", cols=4, rows=4) as ui:
    with ui.tab("Main"):
        temp = ui.gauge("temperature", label="Temperature", min=0, max=100,
                        formatValue="suffix:°C", listen="temperature")
        fan = ui.toggle("fan", label="Fan", send="set_fan", listen="fan")
    ui.glance(hero=temp, slots=[fan], live_activity=True)

hub = ui.serve(connection="device.json")
ui.save("workshop.json")  # load/pin this layout in CAR-TER

@fan.on
async def set_fan(frame):
    enabled = frame.get("value")
    if not isinstance(enabled, bool):
        return {"ok": False, "error": "Expected a Boolean"}
    # Set your actual hardware here, then publish its confirmed state.
    await fan.push(enabled)
    return {"ok": True}

@hub.surfaces.on_notification
async def notification_response(frame):
    if frame.get("actionId") == "workshop.reply":
        print("User replied:", frame.get("userText", ""))
```

Inside the running hub:

```python
await temp.push(21.5)                     # live mesh + hub's retained state
await fan.push(True)
print(hub.surfaces.snapshot())            # exact payload preview; no HTTP
await hub.surfaces.refresh()              # one silent widget/control refresh
await hub.surfaces.notify(
    "Workshop", "Ready for the next job", include_glance=True,
    thread_id="workshop", actions=[
        notification_action("workshop.reply", "Reply", text_input=True,
                            text_input_button_title="Send",
                            text_input_placeholder="Instructions",
                            authentication_required=True),
        notification_action("workshop.open", "Open", foreground=True),
    ])
await hub.surfaces.start_activity(alert_title="Workshop started")
await hub.surfaces.update_activity({temp: 25}, hero_history=[21.5, 23, 25])
await hub.surfaces.end_activity({temp: 25})
```

The complete [example](../examples/ios_surfaces.py) previews offline by default.
It can also emit a layout or run against a supplied Add Hub credential.

## Which connector to use

| Intent | Connector | Backend / behavior |
| --- | --- | --- |
| Publish live telemetry | `await control.push(value)` / `hub.push(control, value)` | MeshSocket; retains state for later surface previews and pushes |
| Handle widget, Shortcuts or Control Center actions | `@control.on` / `hub.on(control, handler)` | Existing layout action binding; no separate handler per iOS surface |
| Refresh cached readings and toggle state | `await hub.surfaces.refresh(values)` | Validator `/alerts/notify`, silent `glance` payload |
| Refresh every surface at once, and retain the values | `await hub.surfaces.publish(values, activity=True)` | Validator `/surfaces/publish`; widget + control + Live Activity pushes off one request |
| Read what a surface will render when iOS wakes it | `await hub.surfaces.state()` | Validator `/surfaces/state/<layoutId>`; `None` before the first publish |
| Register a widget / Control Center push token | `await hub.surfaces.register_token(kind=..., key=..., bundle_id=..., token=...)` | Validator `/surfaces/tokens`; the device does this itself, this is for provisioning |
| Send notification with buttons/replies | `await hub.surfaces.notify(title, body, actions=...)` | Validator `/alerts/notify`; optional `include_glance=True` |
| Handle notification responses | `@hub.surfaces.on_notification` | Channel's `notif_action` frames; includes `userText` for replies |
| Start/update/end Live Activity | `await hub.surfaces.start_activity(...)`, `update_activity(...)`, `end_activity(...)` | Validator `/alerts/live-activity/push`; identity, metadata and Apple dates derived |
| Send a command without holding a socket | `mesh_broadcast(relay_url, token, channel=..., event=..., payload=..., action_id=...)` | Relay host `/mesh/broadcast`; accepts HTTP(S) or WS(S) base URL |
| Drive surfaces without a `Hub` layout | `CarterClient.refresh_glance`, `push_live_activity`, `notify` | Async helpers using current client authorization |
| Cron / synchronous backend | `notify_http`, `glance_update`, `notification_action`, `live_activity_push`, `content_state`, `activity_attributes`, `slot` | Low-level HTTP helpers with explicit validator credentials |
| Cron / synchronous backend, retained state | `surfaces_publish`, `surfaces_put_state`, `surfaces_get_state`, `surfaces_register_token`, `surfaces_deregister_token` | Same, for the `/surfaces` routes |

Mesh-backed buttons and toggles are derived into system controls by the app.
Shortcuts reuse the same action definitions and cached reading catalog; they do
not need another backend endpoint. Routed request actions and app-direct
HTTP/MQTT actions retain their existing transport constraints—an arbitrary
protocol binding is not automatically an HTTP bridge action.

`glance.controls` may also declare custom tiles. Their state map is keyed by
**tile ID**, while `values` uses **layout control ID**. The layout-aware connector
maps bound Boolean values to the correct authored tile IDs automatically.

## Retained surface state (`/surfaces`)

`refresh` pushes a payload *at* the device and hopes a process is alive to apply
it. `/surfaces` inverts that: the relay **retains** the layout's latest values, and
a surface pulls them whenever iOS wakes it. A widget that reloads at 3am renders
current data with no app process, no socket and nothing queued.

```python
await hub.surfaces.publish({nozzle: 214.5, bed: 60},
                           controls={"lights": True}, activity=True)
```

One request merges the state and pokes all three push paths — widget tokens
(iOS 26 WidgetKit push), Control Center control tokens (iOS 18) and the layout's
registered Live Activities. Omit `activity` for the first two only; pass `True` to
let the relay synthesize the Live Activity content state from the merged values,
`"end"` to finish the session, or a dict (`contentState`, `staleSeconds`,
`priority`, `relevanceScore`, `event`) to say exactly what to send.

Publishing at telemetry rate is safe. The relay enforces per-surface floors —
widgets 60s, controls 10s, activity 2s per account and layout — and inside a floor
the **state still merges** while the push is skipped and reported in
`suppressed`. The surface shows the newest value at its next wake either way, so a
suppressed surface is not a failed one. `force=True` raises the APNs priority
where the floor allows; it does not lift the floor. On top of that, publishes share
one account bucket (burst 120, 10/min) and `429` carries `retryAfter`.

`surfaces_put_state` merges without pushing at all — the right call for readings
that should be correct on the next wake but do not justify spending a budget now.

The merge is per key: named keys are replaced, unnamed ones kept, and
`isConnected` changes only when sent, so a hub publishing one sensor never blanks
the others. `values` is keyed by **layout control id** (handles are resolved for
you); `controls` is keyed by **`glance.controls[].id`**, and unlike the v1 glance
payload its values are any scalar — a `cycle` reports a string, a `step` a number.
Only an owner, device or hub credential may publish or `PUT`; members get `403`
but may register tokens and read state.

## Identity, values and limits

Declare a stable `Layout(id="workshop")`. Loaded JSON files may instead use their
filename as the canonical ID. In-memory layouts without an ID fail explicitly;
guessing one would send pushes to a different registration. The phone must have
loaded/pinned the matching layout to provide its controls and full reading catalog.

`values={temp: 25}` overrides one payload without changing the hub's retained
state. Use `await temp.push(25)` when the underlying source has changed. Supported
surface values are Boolean, finite number, and string. Charts/arrays/objects are
not scalar readings. Labels, ranges, formatting, colors, featured hero and up to
three secondary slots come from the layout. All retained scalar readings are
included in `values`, including ones outside those four featured readings.

`glance_update(layout_id="workshop", values={"humidity": 42})` updates an
**existing** catalog reading while preserving featured slots and metadata.
Unknown IDs do not create catalog entries. This additive `values` field requires
the matching iOS update; older clients ignore it, while still decoding hero,
slots and controls. When both a slot and `values` name a control, `values` wins.
The snapshot timestamp records receipt of the refresh, not a sensor sample time
or proof that every retained reading was freshly sampled.

The SDK checks the relay's 2,048-byte glance limit, 3,072-byte Live Activity state
limit, 1,024-byte attributes limit, and 24-point hero history limit. Keep strings
short; for a large layout, use `CarterClient.refresh_glance` with a small values
patch. The relay also validates the complete APNs payload size. Low-level HTTP
calls default to a ten-second timeout; transport failures report status `0`.

## Delivery and response semantics

- `sent` counts APNs acceptance, not device receipt or applied values. Account
  notifications fan out to the account's registered devices: `layout_id` and
  `channel` route taps and responses, **they are not recipient filters**.
- Refreshes are explicit. Telemetry-rate `push()` calls never consume notification
  or ActivityKit budgets automatically. Coalesce updates and use meaningful state
  transitions. Live Activity updates default to priority 5; priority 10 is explicit.
- Background refresh may be delayed or suppressed, including after force-quit.
  Alert payloads can refresh through the notification extension; this is also
  best-effort. See Apple's [background push guidance](https://developer.apple.com/documentation/usernotifications/pushing-background-updates-to-your-app).
- ActivityKit token registration is performed by the app. A start needs an eligible
  push-to-start token; updates/ends need the layout's registered activity token.
  A zero `sent` result is not evidence that an activity was created or updated.
- Direct iOS 26 [WidgetKit push notifications](https://developer.apple.com/documentation/widgetkit/updating-widgets-with-widgetkit-push-notifications)
  require a separate widget token/data-fetch path, which this backend does not
  currently register. These connectors use the existing app/NSE shared-store path.
- Action callbacks passed to `notification_action(callback=...)` are process-local.
  Register the catch-all handler on every startup to handle responses to earlier
  notifications. It receives the channel's responses, not just this layout's;
  namespace action IDs (for example `workshop.reply`). Handle retries idempotently.
- `glance` and Live Activity state are cleartext surface data. Room encryption seals
  notification content fields, not glance values, action labels, or routing hints.
- The HTTP mesh bridge's `delivered: true` means a peer was present when the frame
  was published, not that hardware acted. HTTP 202 means no subscribers, 200 with
  no `delivered` field means peer status is unknown, and 429/503 are retryable.
  Reuse one `action_id` for retries within the relay's ten-minute deduplication
  window; use a new ID for a new user action.

No service credentials are needed for the SDK, relay contract, or iOS decoder
unit tests. Live APNs acceptance, force-quit behavior and physical-device controls
still need a configured account and device integration check before release.
