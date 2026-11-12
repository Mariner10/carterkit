---
type: navigation
label: Navigation
icon: arrow.turn.down.right
category: system
since: next
fields:
  - name: navigate
    tab: action
    type: string
    description: "Where a button tap goes after its action fires: tab:<id|title|#index>"
    since: next
---

A button can switch the layout to another tab with `navigate`. The phone does the
switching itself; nothing goes over the wire for it.

```json
{ "type": "button", "id": "open-cams", "label": "Cameras", "position": [0, 0],
  "navigate": "tab:t_cams" }
```

## Targets

| Target | Goes to |
|---|---|
| `"tab:t_cams"` | The tab whose `id` is `t_cams`; if none has that id, the tab titled `t_cams` |
| `"tab:Cameras"` | Same rule: an explicit tab `id` match wins over a title match |
| `"tab:#2"` | The third tab in display order (zero-based, includes live `dynamicTabs`) |

The object form `{"to": "tab:Cameras"}` means the same as the string.

Give the target tab an `id` (see [[layout-config#Tabs]]) so renaming it never breaks
the link. A target that names no tab, or the tab already showing, does nothing.

## Order with `action`

`navigate` fires **after** `action`: the frame (or MQTT/HTTP/local write) goes out
first, then the tab switches. A button with `navigate` and no `action` just navigates.
The switch counts as a normal tab change: Studio Mirror sees one `tab` event.

## Limits (phase 1)

- **Buttons only.** A toggle, slider, stepper or any other control carrying
  `navigate` keeps the field but ignores it.
- **Only `tab:` targets.** `page:`, `sheet:`, `layout:`, `back` and `root` are
  reserved for later phases. This build still opens a layout that uses them; the
  tap just doesn't navigate.
- Tabs of the same layout only. With several resident layouts, only the one on
  screen switches.

## Related

- [[control-def]] — the `navigate` field on every control
- [[layout-config#Tabs]] — tab `id`
- [[actions]] — what fires first
