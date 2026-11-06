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
    do:
      app: In Studio, start a new blank layout. Tap **+** and choose **Dial**.
      target: editor.add
    as: dial
    check: A dial titled Dial sits on the page, marked 0 to 100.
    expect: {signal: editor.add, target: gauge}
    profile: {add: [gauge], canvas: [place, resize]}
  - id: range
    goal: Set its range
    do:
      app: Tap **Range** and drag the two ends to **0** and **10**.
      target: editor.chip.control
    check: The dial is marked 0 to 10.
    expect: {signal: editor.change, target: max, match: {is: 10}}
    profile: {chips: [control], petals: 0, rows: false}
  - id: try
    goal: Try it
    do:
      app: Tap **Try** to run the page the way it will look on your phone.
      target: editor.try
    check: A banner above the page says you are trying it out, and the dial still reads 0 to 10.
    expect: {signal: editor.try}
    profile: {canvas: []}
  - id: keep
    goal: Name it and keep it
    do:
      app: Leave Try. Select the dial, tap **Text** and call it **My dial**, then tap **Done**.
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

**Try** runs your draft as if it were live without touching anything real. It uses test data only, and nothing is
saved or sent while you try.

## Name it and keep it {#keep}

> app: You can change a title, colour or card any time: select a control and its chips are right there.

The dial's title is its [[gauge.label]]. **Done** saves the layout to your library. To give the dial a value to
show and a slider that moves it, take [[tutorial:first-layout]] next.
