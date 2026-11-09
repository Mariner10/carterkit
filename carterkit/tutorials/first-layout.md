---
id: first-layout
kind: tutorial
level: beginner
audience: app
title: Your first layout
time: 15
builds: A dial driven by a slider through a value on your phone, named and saved to your library.
prerequisites: []
since: "2.2"
uses:
  controls: [control.gauge, control.slider]
  fields: [gauge.min, gauge.max, gauge.label, slider.min, slider.max, control-def.sync, control-def.action]
  docs: [doc.local-store]
  carterkit: []
  profiles: [first-look]
result: first-layout.layout.json
starterKit: null
next: [first-hub]
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
  - id: bind
    goal: Give it a value to show
    where: [editor, pose]
    getThere: {landing: {app: "Tap **Start blank**.", points: {"Start blank": landing.startBlank}}, canvas: {app: "Tap **Menu**, then **Studio**, then **New Layout**, name it and tap **Create**.", points: {Menu: header.settings, Studio: menu.row.studio, "New Layout": studio.new, Create: studio.create}}, studio: {app: "Tap **New Layout**, name it and tap **Create**.", points: {"New Layout": studio.new, Create: studio.create}}}
    do:
      app: Tap **Binding**. Under **What it shows**, choose **My Data**, then **New value**. Call it **Level** and add it.
      target: editor.binding
    check: Level is ticked under My Data, and the needle rests at 0, where Level starts.
    expect: {signal: editor.change, target: sync}
    profile: {categories: [data], chips: [], binding: [receives]}
  - id: range
    goal: Set its range
    do:
      app: Tap **Range** and set Highest value to **10**.
      target: editor.chip.control
    check: The dial is marked 0 to 10.
    expect: {signal: editor.change, target: max, match: {is: 10}}
    profile: {chips: [control], petals: 0}
  - id: add-slider
    goal: Add a slider
    where: [editor]
    getThere: {pose: {app: "Tap **Done** under the dial to put it down.", points: {Done: editor.pose.done}}, canvas: {app: "Tap **Menu**, then **Edit Layout**.", points: {Menu: header.settings, "Edit Layout": menu.row.editLayout}}, studio: {app: "Close Studio, then tap **Menu** and **Edit Layout**.", points: {Menu: header.settings, "Edit Layout": menu.row.editLayout}}}
    do:
      app: Tap **Done** under the dial to put it down, then tap **Add** and choose **Slider**.
      target: editor.pose.done
      points: {Done: editor.pose.done, Add: editor.add, Slider: editor.addChoice.slider}
    as: knob
    check: A slider titled Slider sits on the page with the dial, set from 0 to 100.
    expect: {signal: editor.add, target: slider}
    profile: {add: [slider], canvas: [place, resize]}
  - id: send
    goal: Make the slider set Level
    where: [editor, pose]
    getThere: {landing: {app: "Tap **Start blank**.", points: {"Start blank": landing.startBlank}}, canvas: {app: "Tap **Menu**, then **Studio**, then **New Layout**, name it and tap **Create**.", points: {Menu: header.settings, Studio: menu.row.studio, "New Layout": studio.new, Create: studio.create}}, studio: {app: "Tap **New Layout**, name it and tap **Create**.", points: {"New Layout": studio.new, Create: studio.create}}}
    do:
      app: With the slider selected, tap **Binding**. Under **When you slide it**, choose **Save on this phone**, then **Level**.
      target: editor.binding
    check: Level is ticked under Save on this phone, and My Data keeps what the slider sends in Level.
    expect: {signal: editor.change, target: action}
    profile: {categories: [data], chips: [], binding: [emits]}
  - id: match
    goal: Give the slider the same range
    do:
      app: Tap **Range** and set Highest value to **10**, like the dial's.
      target: editor.chip.control
    check: The slider runs from 0 to 10.
    expect: {signal: editor.change, target: max, match: {is: 10}}
    profile: {chips: [control], petals: 0}
  - id: try
    goal: Try it
    where: [editor, pose]
    getThere: {canvas: {app: "Tap **Menu**, then **Edit Layout**.", points: {Menu: header.settings, "Edit Layout": menu.row.editLayout}}, studio: {app: "Close Studio, then tap **Menu** and **Edit Layout**.", points: {Menu: header.settings, "Edit Layout": menu.row.editLayout}}}
    do:
      app: Tap **More** (⋯) beside the slider's chips and choose **Try it**. Drag the slider to the middle and let go.
      target: editor.pose.more
      points: {More: editor.pose.more, "Try it": editor.pose.more.tryIt}
    check: The needle swings to 5. Drag again and it follows.
    expect: {signal: control.valueChanged, target: "@knob", match: {gte: 4, lte: 6}}
    profile: {canvas: []}
  - id: keep
    goal: Name it and keep it
    do:
      app: Tap **Done** on the banner. Select the dial, tap **Text** and call it **My dial**. Pick a **Colour** if you like, then tap **Done** at the top.
      target: editor.save
    check: Your layout is in your library, with a dial titled My dial and a slider.
    expect: {signal: editor.save}
    profile: first-look
---

# Your first layout

You will put a dial on a page, give it a value to show, set its range, add a slider that changes that value, and
watch the two work together. Nothing needs a computer or a hub: the value lives on your phone. Each step shows you
only the part of the editor it uses; tap **Full** at any time to see everything.

## Place a dial {#place}

A [[control.gauge]] shows one number between a low and a high end. A new one starts at 0 to 100 with the title
Dial, so it looks right before you change anything.

## Give it a value to show {#bind}

A dial shows a value from somewhere. Here that somewhere is **My Data**, the small set of values a layout keeps on
your phone ([[doc.local-store]]). A dial shows a number, so New value makes a number. Making **Level** now means the
slider in step 5 has something to set. Until a value arrives, the dial rests at Level's starting value.

## Set its range {#range}

The [[gauge.min]] and [[gauge.max]] are the dial's two ends. A value past an end pins the needle there, so pick
ends that fit what you show: 0 to 10 suits a level you set by hand.

## Add a slider {#add-slider}

A [[control.slider]] is the other half: something you move. A new control lands in the first free space on the
page.

## Make the slider set Level {#send}

This is the link between the two. The slider saves its position to Level as you slide it, and the dial shows
Level, so the dial follows the slider. "Save on this phone" keeps it all on the phone; the same card can send to
your own hub instead, which is the next tutorial.

## Give the slider the same range {#match}

A slider from 0 to 100 would push the dial past its end at 10. Matching the ends makes the middle of the slider
the middle of the dial.

## Try it {#try}

**Try it** runs your draft as if it were live without touching anything real: it writes to a scratch copy of Level
and drops it when you tap **Done** on its banner. If the needle does not move, check step 5: the slider has to save
to Level, the same value the dial shows.

## Name it and keep it {#keep}

> app: You can change a title, colour or background any time: select a control and its chips are right there.

The dial's title is its [[gauge.label]]. **Text**, **Colour** and **Background** are the same three chips on every
control, so what you learn here works on a slider, a chart or a button. **Done** saves the layout to your library;
open it from there and the slider drives the dial for real.
