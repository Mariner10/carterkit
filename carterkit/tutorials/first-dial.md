---
id: first-dial
kind: quickstart
level: beginner
audience: app
title: Build your first layout
time: 5
builds: A dial you set and try, named and saved to your library.
prerequisites: []
since: "2.2"
uses:
  controls: [control.gauge]
  fields: [gauge.min, gauge.max, gauge.label]
  docs: []
  carterkit: []
  profiles: [first-look]
result: first-dial.layout.json
starterKit: null
next: [first-layout]
steps:
  - id: place
    goal: Place a dial
    where: [editor, pose]
    getThere: {landing: {app: "Tap **Start blank**.", points: {"Start blank": landing.startBlank}}, canvas: {app: "Tap **Menu**, then **Studio**, then **New Layout**, name it and tap **Create**.", points: {Menu: header.settings, Studio: menu.row.studio, "New Layout": studio.new, Create: studio.create}}, studio: {app: "Tap **New Layout**, name it and tap **Create**.", points: {"New Layout": studio.new, Create: studio.create}}}
    do:
      app: Tap **Add** and choose **Dial**.
      target: editor.add
      points: {Add: editor.add, Dial: editor.addChoice.gauge}
    already: {fact: controlCount, id: gauge, match: {gte: 1}}
    as: dial
    check: A dial titled Dial sits on the page, marked 0 to 100.
    expect: {signal: editor.add, target: gauge}
    profile: {add: [gauge], canvas: [place, resize]}
  - id: range
    goal: Set its range
    do:
      app: Tap **Range** and set Highest value to **10**.
      target: editor.chip.control
    check: The dial is marked 0 to 10.
    expect: {signal: editor.change, target: max, match: {is: 10}}
    profile: {chips: [control], petals: 0}
  - id: try
    goal: Try it
    where: [editor, pose]
    getThere: {canvas: {app: "Tap **Menu**, then **Edit Layout**.", points: {Menu: header.settings, "Edit Layout": menu.row.editLayout}}, studio: {app: "Close Studio, then tap **Menu** and **Edit Layout**.", points: {Menu: header.settings, "Edit Layout": menu.row.editLayout}}}
    do:
      app: Tap **More** (⋯) beside the dial's chips and choose **Try it** to run the page with test data.
      target: editor.pose.more
      points: {More: editor.pose.more, "Try it": editor.pose.more.tryIt}
    check: A banner above the page reads Trying it out, and the dial is still marked 0 to 10.
    expect: {signal: editor.try}
    profile: {canvas: []}
  - id: keep
    goal: Name it and keep it
    do:
      app: Tap **Done** on the banner. Select the dial, tap **Text** and call it **My dial**, then tap **Done** at the top.
      target: editor.save
    check: Your layout is in your library, with a dial titled My dial.
    expect: {signal: editor.save}
    profile: first-look
---

# Build your first layout

Five minutes, one dial: place it, set its range, try it and keep it. Each step shows you only the part of the editor
it uses; tap **Full** at any time to see everything.

## Place a dial {#place}

A [[control.gauge]] shows one number between a low and a high end. A new one starts at 0 to 100 with the title
Dial, so it looks right before you change anything.

## Set its range {#range}

The [[gauge.min]] and [[gauge.max]] are the dial's two ends. A value past an end pins the needle there, so pick
ends that fit what you show: 0 to 10 suits a level you set by hand.

## Try it {#try}

**Try it** runs your draft as if it were live without touching anything real. It uses test data only, and nothing
is saved or sent while you try. **Done** on its banner takes you back to editing.

## Name it and keep it {#keep}

> app: You can change a title, colour or background any time: select a control and its chips are right there.

The dial's title is its [[gauge.label]]. **Done** saves the layout to your library. To give the dial a value to
show and a slider that moves it, take [[tutorial:first-layout]] next.
