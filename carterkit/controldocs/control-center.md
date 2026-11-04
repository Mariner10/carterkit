---
type: glance-controls
depth: complete
label: Control Center Controls
icon: switch.2
category: system
fields:
  - name: id
    type: string
    description: Stable id within the layout (the registry key is <layoutId>#<id>)
    summary: A short name for this control
    does: Names the control so the layout can tell it from the others; it is not shown on screen.
  - name: label
    type: string
    description: Name in the controls gallery and on the control
    summary: The name people see
    does: Sets the name shown on the control in the controls gallery and on the control itself.
  - name: icon
    type: string
    description: SF Symbol (defaults per kind)
    summary: The little picture on the control
    does: Sets the SF Symbol drawn on the control; when left out, each kind uses its own default.
  - name: kind
    type: enum
    values: [toggle, button, cycle, step, set]
    default: button
    description: toggle and button are the two templates iOS offers. cycle, step and set are buttons whose press computes a value
    summary: What the control does when pressed
    does: Chooses how the control behaves in Control Center, from a plain button to a switch or a value-sending press.
    valueHelp: {"toggle": "an on/off switch, styled by on and off, that sends the opposite state", "button": "a plain press that sends the bound control's action or the event", "cycle": "a press that moves to the next entry of states", "step": "a press that adds delta to the control's value, within its min and max", "set": "a press that sends one fixed value"}
  - name: control
    type: string
    description: Layout control this one mirrors and drives. Required for cycle, step and set; optional for toggle and button. Its live value is what the control shows, and its own action (with {{value}} substituted) is what a press sends
    summary: Which on-screen control this one runs
    does: Links to a control in your layout; the control shows that control's live value and a press sends its action.
  - name: event
    type: string
    description: Explicit MeshSocket event instead of the bound control's action
    summary: A custom message to send
    does: Sends this named event on press instead of the linked control's action.
  - name: payload
    type: object
    description: "Static payload for event; value-bearing kinds merge {value: <value>} into it"
    summary: Extra data sent with the event
    does: Adds fixed data to the event sent on press; controls that carry a value add it alongside.
  - name: on
    type: object
    description: Toggle styling while on, { label, icon, tint }
    summary: How the switch looks when on
    does: Styles a toggle in its on state with a label, icon and tint.
  - name: off
    type: object
    description: Toggle styling while off, { label, icon, tint }
    summary: How the switch looks when off
    does: Styles a toggle in its off state with a label, icon and tint.
  - name: valueControl
    type: string
    description: Show THIS control's formatted value as the value label (for example a lux reading beside a lights toggle)
    summary: Show another control's reading
    does: Shows the formatted value of the named control as the value label, for example a sensor reading next to a toggle.
  - name: valueLabel
    type: string
    description: Template over the value label; {{value}} is the bound or valueControl display value, for example "{{value}} lx"
    summary: Words around the shown value
    does: Formats the value label from a template, where {{value}} becomes the displayed reading, such as 23 lx.
  - name: states
    type: object[]
    description: cycle ring in press order, each { value, label, icon, tint }; a press sends the next state and the control shows the current one
    summary: The choices a cycle walks through
    does: Lists the steps a cycle control goes through in press order; each press sends the next one and the control shows the current one.
  - name: delta
    type: number
    bounds: none
    description: step increment, added to the control's current value (negative to decrement), clamped to its min and max
    summary: How much each press changes the value
    does: Adds this amount to the control's current value on press (negative subtracts), never going past its min or max.
  - name: value
    type: string
    description: set target value, the value sent on press
    summary: The value a press sends
    does: Sends this exact value to the linked control when a set control is pressed.
  - name: presets
    type: string[]
    description: Preset values for a step or set control (25, 50, 75, 100); one button each in buttons mode
    summary: Quick values to pick from
    does: Lists fixed values for a step or set control, shown as one button each in buttons mode.
  - name: surface
    type: enum
    values: [buttons, cycle, big]
    description: How the control reaches widgets, the Live Activity and Control Center. buttons is a row of press buttons, cycle one button that walks the options, big a tap that opens the app on a full-screen one-control sheet. Absent uses the kind's default
    summary: How the control shows up outside the app
    does: Chooses whether the control appears as a row of buttons, one cycling button, or a tap that opens a full-screen sheet.
    valueHelp: {"buttons": "a row of press buttons, one per option", "cycle": "one button that walks through the options", "big": "a tap that opens the app on a full-screen sheet for this one control"}
constraints: {"surface":"controls","field":"glance.controls","kinds":{"toggle":{"iosTemplate":"ControlWidgetToggle","needsControl":false,"valueDisplay":true,"styling":["on","off"]},"button":{"iosTemplate":"ControlWidgetButton","needsControl":false,"valueDisplay":false},"cycle":{"iosTemplate":"ControlWidgetButton","needsControl":true,"requires":["states"],"valueDisplay":true},"step":{"iosTemplate":"ControlWidgetButton","needsControl":true,"requires":["delta or presets"],"valueDisplay":true},"set":{"iosTemplate":"ControlWidgetButton","needsControl":true,"requires":["value"],"valueDisplay":false}},"defaultKind":"button","iosOffers":["toggle","button"],"noSliderNoText":true,"valueDisplay":{"fields":["valueControl","valueLabel"],"template":"{{value}} is the bound or valueControl display value"},"surfaceModes":["buttons","cycle","big"],"placedBy":"the user: Control Center, lock-screen corners, Action button","refresh":{"live.controls.refresh":["push","app"],"minimumIos":18},"offlinePressQueueHours":24,"authorDeclaredRequiredFor":["Live Activity row","lock-screen banner row","medium and large widgets"]}
---

**Controls** are the glance block's buttons and switches that work outside the app:
Control Center, the Lock Screen corners and the Action button. Declare them in
`glance.controls[]`. A layout that declares none still gets controls derived from its
own buttons, toggles, sliders and steppers, but those are only offered in the
pick-list; a control you declare is also allowed on the Live Activity row and in
medium and large widgets. See [[glance]] for the whole block and [[widgets]] for the
interactive tiles that press the same actions.

## What iOS allows

Apple gives Control Center exactly two templates: a toggle and a button. There is no
slider and no text field. The kinds map like this:

| Kind | Shows | A press sends |
|---|---|---|
| `toggle` | on or off, styled by `on` / `off`, with an optional value label | the opposite state, `{"value": <bool>}` merged into `payload` |
| `button` (default) | a label and icon | the bound control's action, or `event` / `payload` |
| `cycle` | the current entry of `states` | the next entry's `value` |
| `step` | the bound control's value | its value plus `delta`, clamped to the control's `min`/`max` |
| `set` | a label | `value` |

A slider therefore becomes `step` buttons (or `presets`), and a multi-state picker a
`cycle`. The user places every control by hand; the app can only offer them.

## Value display

A control can show a reading, not just a name. A `toggle` shows the bound control's
formatted value; to show another control's reading, name it in `valueControl`, and
shape it with `valueLabel`: `"valueLabel": "{{value}} lx"`.

## Delivery

Presses work with the app closed: the control posts straight to the relay
(`POST /mesh/broadcast`) with the layout's own credential, exactly the frame the
in-app control would send. Offline presses queue for 24 hours. The rendered state
flips only once the relay confirms the frame was published; a press that reached
nothing is rolled back and reported. `live.controls.refresh` (`push` on iOS 18, or
`app`) sets how the displayed value is refreshed; see [[live-activity]].

## Constraints

The frontmatter `constraints` block gives, per kind: the iOS template used, whether a
bound `control` is required, which other fields it needs, and whether it shows a
value. It also lists the surface modes and the 24 h press queue.

## Examples

### Lights toggle with a lux reading

A toggle styled per state, showing the lux sensor beside it.

```json
{
  "controls": [
    { "id": "lights", "kind": "toggle", "label": "Lights", "control": "lights-toggle",
      "valueControl": "nozzle", "valueLabel": "{{value}} °C",
      "on":  { "label": "Lit",  "icon": "lightbulb.fill", "tint": "#FFD60A" },
      "off": { "label": "Dark", "icon": "lightbulb" } }
  ]
}
```

### Fan: cycle and step

A three-state cycle, and a step button that adds 10 to the fan speed slider.

```json
{
  "controls": [
    { "id": "fan", "kind": "cycle", "label": "Fan", "control": "fan-mode",
      "states": [ { "value": "off",  "label": "Off",  "icon": "fan" },
                  { "value": "low",  "label": "Low",  "icon": "fan", "tint": "#64D2FF" },
                  { "value": "high", "label": "High", "icon": "fan.fill", "tint": "#0A84FF" } ] },
    { "id": "fan-up", "kind": "step", "label": "Fan +10", "control": "fan-speed", "delta": 10,
      "surface": "buttons", "presets": [25, 50, 75, 100] }
  ]
}
```

### Pause button and preset

A plain button with an explicit event, and a `set` that sends one value.

```json
{
  "controls": [
    { "id": "pause", "kind": "button", "label": "Pause", "icon": "pause.fill",
      "event": "printer.pause", "payload": { "reason": "control-center" } },
    { "id": "fan-max", "kind": "set", "label": "Fan max", "control": "fan-speed", "value": 100 }
  ]
}
```
