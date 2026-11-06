---
type: hub-surfaces
label: Hub Surfaces
icon: dot.radiowaves.left.and.right
category: system
depth: complete
since: next
fields:
  - name: progress
    type: bool
    default: true
    title: Progress
    description: "hubSurfaces key. The hub's progress tasks: the pill, the tray and the progress sheet. false refuses progress frames with reason off"
    summary: Progress from your hub
    does: Lets the layout's hub show progress tasks in the pill, the tray and the progress sheet.
  - name: toast
    type: bool
    default: true
    title: Toasts
    description: "hubSurfaces key. The hub's toasts under the status bar. false refuses toast frames with reason off"
    summary: Toasts from your hub
    does: Lets the layout's hub show short messages under the status bar.
  - name: haptic
    type: enum
    values: ["off", "light", "all"]
    default: all
    title: Haptics
    valueTitles: {"off": "Off", "light": "Light only", "all": "All"}
    valueHelp: {"off": "no haptics from the hub", "light": "only light, selection and success play", "all": "every profile the haptic verb takes"}
    description: "hubSurfaces key. Which of the hub's haptics play: all (true), light (light, selection and success only) or off (false). A refused haptic answers reason off"
    summary: Haptics from your hub
    does: Lets the layout's hub play haptics on the phone, only the light ones, or none.
  - name: island
    type: bool
    default: true
    title: Island
    description: "hubSurfaces key. The hub's progress tasks also on the Dynamic Island and Lock Screen. false keeps them in the app; the app-wide Live Activities switch still gates it"
    summary: Tasks on the Island
    does: Shows the hub's progress tasks on the Dynamic Island and Lock Screen while the app is not in front.
  - name: log
    type: bool
    default: true
    title: Log console
    description: "hubSurfaces key. The hub's log streams and the console sheet. false refuses log frames with reason off"
    summary: Logs from your hub
    does: Lets the layout's hub stream log lines into a console sheet.
---

# Hub surfaces

What a layout's hub may draw in the app, beyond the confirmations and sheets it can always ask for: progress
tasks, toasts, haptics, log consoles and tasks on the Dynamic Island. The layout writes them under
[[layout-config]]'s `hubSurfaces`; every key is on unless it says otherwise.

```json
"hubSurfaces": { "progress": true, "toast": true, "haptic": "light", "island": true, "log": true }
```

| Value | Meaning |
|---|---|
| absent | Every surface on |
| `false` | No hub surface. `prompt` and `sheet` are not affected |
| an object | The keys above; one left out is on |

A surface that is off answers the hub's frame with `{ok: false, reason: "off"}`. The person's own switches
(the layout hub's Hubs For This Layout: five per hub, and Mute for 1 hour) always beat the layout's on.

## In the editor

Sharing & connection has the layout's **Hub** chip. Tap it for its tray: a switch per surface (Haptics has
Off, Light only and All) and a **Try** that plays the surface with placeholder data ("Example task", from
"hub-a"), with no hub and nothing sent. Hold it for five petals, one per surface, each a drag dial: Off and On,
and for Haptics Off, Light only and All.

## Examples

### Light haptics only

A build box whose hub buzzes on every step: its progress and toasts stay, and only light haptics play.

```json
{ "hubSurfaces": { "haptic": "light" } }
```

### Progress in the app only

The hub's tasks show in the pill and the sheet, never on the Dynamic Island or the Lock Screen.

```json
{ "hubSurfaces": { "island": false } }
```

### No hub surfaces

The hub may still ask for a confirmation or a sheet; progress, toasts, haptics and logs are refused.

```json
{ "hubSurfaces": false }
```
