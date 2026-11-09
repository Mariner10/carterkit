---
id: touch-to-learn
kind: recipe
level: beginner
audience: app
title: Touch a control to learn it
time: 1
builds: A look at what any control lets you change.
prerequisites: []
since: "2.2"
uses:
  controls: [control.slider]
  fields: []
  docs: []
  carterkit: []
  profiles: [first-look]
result: quick-controls.layout.json
starterKit: null
next: [first-dial]
steps:
  - id: pick
    goal: Select a control
    where: [editor, pose]
    getThere: {landing: {app: "Tap **Start blank**.", points: {"Start blank": landing.startBlank}}, canvas: {app: "Tap **Menu**, then **Edit Layout**.", points: {Menu: header.settings, "Edit Layout": menu.row.editLayout}}, studio: {app: "Close Studio, then tap **Menu** and **Edit Layout**.", points: {Menu: header.settings, "Edit Layout": menu.row.editLayout}}}
    do:
      app: Touch a control on the page to select it. On an empty page, tap **Add** and choose **Dial**.
      target: editor.add
      points: {Add: editor.add, Dial: editor.addChoice.gauge}
    check: The control is selected, and the editor shows its fields below the page.
    expect: {signal: editor.select}
    profile: first-look
---

# Touch a control to learn it

Touch any control in a layout and it is selected. The editor shows that control's fields below the page, the same
way for every kind of control. The Quick Controls sample is a switch, a dial and a slider with placeholder values;
it sends nothing.

## Select a control {#pick}

Touching a control selects it. The editor lists the fields of that control below the page, so you can see what it
lets you change.
