---
id: style-any-control
kind: recipe
level: beginner
audience: app
title: Style any control
time: 2
builds: A control with your own title, colour and background.
prerequisites: [first-dial]
since: "2.2"
uses:
  controls: []
  fields: []
  docs: []
  carterkit: []
  profiles: [first-look]
result: first-dial.layout.json
starterKit: null
next: []
steps:
  - id: title
    goal: Change its title
    where: [editor, pose]
    getThere: {landing: {app: "Tap **Start blank**.", points: {"Start blank": landing.startBlank}}, canvas: {app: "Tap **Menu**, then **Edit Layout**.", points: {Menu: header.settings, "Edit Layout": menu.row.editLayout}}, studio: {app: "Close Studio, then tap **Menu** and **Edit Layout**.", points: {Menu: header.settings, "Edit Layout": menu.row.editLayout}}}
    do:
      app: Select a control, or on an empty page tap **Add** and choose **Dial**. Then tap **Text** and type a new title, such as **Reading**.
      target: editor.add
      points: {Add: editor.add, Dial: editor.addChoice.gauge, Text: editor.chip.text}
    check: The control's title is open for editing, and the page shows each letter as you type.
    expect: {signal: editor.chip, target: text}
    profile: first-look
  - id: colour
    goal: Change its colour and background
    do:
      app: Tap **Colour** and pick one, then tap **Background** and pick one. Tap **Done** to keep it.
      target: editor.save
    check: The editor closes, and the control keeps its new title, colour and background.
    expect: {signal: editor.save}
---

# Style any control

Every control has the same three chips for how it looks: **Text**, **Colour** and **Background**. This recipe uses
them on one control, and they work the same way on every other. Any layout will do, such as the one from
[[tutorial:first-dial]].

## Change its title {#title}

The **Text** chip opens on the control's title, whatever kind of control it is. The page shows each change at
once.

## Change its colour and background {#colour}

**Colour** sets the control's own colour. **Background** sets the card behind it. **Done** saves the layout to your
library, where it opens with its new look.
