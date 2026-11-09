---
id: not-updating
kind: fix
level: beginner
audience: app
title: Not updating
time: 1
builds: Check the connection and the feeds behind a layout.
prerequisites: []
since: "2.2"
uses:
  controls: []
  fields: []
  docs: []
  carterkit: []
  profiles: []
result: null
starterKit: null
next: []
steps:
  - id: hub
    goal: Check your hub
    where: [canvas]
    getThere: {landing: {app: "Tap **Start blank** to get past this page; the dot is then at the top of the screen", points: {"Start blank": landing.startBlank}}, studio: {app: "Close Studio to get back to your page, where the dot is at the top."}, editor: {app: "Tap **Done** at the top to leave the editor; the dot is at the top of your page.", points: {Done: editor.save}}}
    do:
      app: Tap the **connection** dot at the top of the screen and find your hub under **Hubs**.
      target: header.connection
      points: {connection: header.connection, Hubs: hub.hubs}
    check: Layout Connection reads Connected. Live beside your hub means its values are arriving.
    expect: {fact: connected}
  - id: pipes
    goal: Check its data pipes
    do:
      app: Under Data Pipes, look for a line that reads Failed or Waiting.
      target: hub.pipes
    check: Every line under Data Pipes reads Live.
    expect: {fact: pipesHealthy}
---

# Not updating

When a layout stops changing, either the hub that feeds it has gone quiet or one of its other feeds has failed. The
hub pane shows both. Tap the dot at the top of the screen to open it, and tap the dot again to close it.

## Check your hub {#hub}

> app: Live: values are arriving. Idle: connected but quiet. Offline: the hub has stopped. Waiting: this phone
> has lost its connection. No data yet: the hub has never sent.

The Hubs box lists each hub that sends to this layout, with how long ago it last sent and one word for its state:

- **Live**: values are arriving as often as this hub usually sends them.
- **Idle**: the hub is still connected but has gone quiet. A hub that sends only when something changes looks like
  this between changes.
- **Offline**: the hub has stopped sending and has left the connection. Start it again on the computer it runs on.
- **Waiting**: this phone has lost its connection, so it cannot tell. Layout Connection above says why.
- **No data yet**: a hub this layout knows about has never sent. Start it, and it turns Live with its first value.

If nothing has ever sent to this layout, the box shows No hub yet and Add a Hub, which opens Layout Info &
Permissions where you add one.

While a hub is Offline, the controls it feeds dim and show how old their last value is, and anything you send to it
shows Not sent instead of going out.

## Check its data pipes {#pipes}

Values that come from somewhere other than a hub, such as a web address or a message broker, show under Data Pipes,
one line each. A line that reads Failed cannot reach its source; Waiting has not heard back yet. Tap the box to open
Layout Info & Permissions. If the layout has no such feeds, this step passes on its own.
