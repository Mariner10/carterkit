---
type: index
label: CAR-TER Guide
icon: book.fill
category: system
fields:
  - name: overview
    type: section
    description: What CAR-TER is and how it works
---

# CAR-TER

**Customizable Adaptive Remote & Telemetry Enabled Reporting**

Your phone becomes any remote. Design your own interface with JSON, connect over MeshSocket, and control anything — smart home, music, IoT, dev tools — all from one app.

---

## How It Works

CAR-TER renders **layouts** — JSON files that describe a grid of interactive controls. Each control can send commands and receive live data over a persistent WebSocket mesh.

![](control-preview://controls-showcase)

A layout defines **tabs**, each containing a **grid** of controls. Controls range from simple buttons and toggles to live gauges, sparklines, maps, and graphs. Everything is driven by data — what you see on screen is exactly what the JSON describes.

---

## The Control System

Every control in CAR-TER is declared as a JSON object with a `type`, `id`, and grid `position`. The system supports **43 control types** across three categories:

### Input Controls
Buttons, toggles, sliders, steppers, pickers, date pickers, text inputs, color pickers, and segmented controls. These send user actions to your server. The **camera** control scans QR codes, barcodes, and text live — detections are on the mesh the moment they're seen. Container controls — **carousels**, **flip cards**, and **accordions** — arrange sets of groups into swipeable pages, flippable faces, and collapsible sections.

The **drag pack** makes arrangement itself the input: [[sortboard|sortboards]] drag items between bound zones (kanban, seating, triage), [[pinboard|pinboards]] place markers anywhere on a freeform surface (floor plans, maps, photos), and the [[compass|compass ring]] mixes drag with the device's heading sensor — point the needle at a puck to fire its action. The [[canvas]] goes structural: a pan/zoom freeform surface hosting whole *working* controls at any position and size, rearrangeable in place. Every drop emits `pickup`/`place`/`layout` events, and the whole arrangement round-trips as synced state a server can seed or rearrange.

### Display Controls
Gauges, progress rings, sparklines, labels, images, maps, and graphs. These visualize incoming telemetry data in real time.

The **chart pack** blurs the line: [[chart|charts]] (bar/line/area/scatter/histogram/waterfall) with tappable datums, [[pie-chart|pie charts]] that double as spin-to-select wheels and radial menus, [[heatmap|heatmaps]] you can paint like an LED matrix or weekly scheduler, and [[radar|radar profiles]] whose vertices drag like a multi-parameter tuner. The statistical wing goes further: [[box-plot|box/violin plots]] that compute quartiles and densities on-device, [[gantt|gantt timelines]] whose bars drag like progress sliders, [[sankey|sankey flows]] and [[chord|chord matrices]] that spotlight on tap, and [[treemap|treemaps]] with Files-style drill-down. Every one displays live data *and* talks back.

![](control-preview://gauge-demo)

### Data Flow
Every control can **sync** with a backend. Input controls fire **actions**; display controls **listen** for incoming data and update automatically. The connection block is standardized: the same `filter`/`valuePath`/`{{value}}` vocabulary works over a MeshSocket server, an **MQTT broker**, or a polled **HTTP API** ([[sources]]) — `method` just picks the wire, so you know exactly what a control accepts and emits no matter the backend.

![](control-preview://sparkline-demo)

---

## MeshSocket Protocol

CAR-TER communicates through **MeshSocket** — a lightweight WebSocket mesh networking protocol. Devices connect to a central server and join **channels** with assigned **roles**.

![](control-preview://mesh-diagram)

### How Devices Connect

1. Each device opens a WebSocket to the MeshSocket server
2. The device sends an `identify` message with its name, channel, and role
3. The server routes messages between devices in the same channel
4. Controls fire events that flow through the mesh to all listeners

### Message Types

- **emit** — fire-and-forget broadcast to the channel
- **request** — send a message and await a response
- **broadcast** — server pushes data to all channel members
- **identify** — authenticate and join a channel

### Sync Configuration

Controls declare their data bindings in a `sync` array:

```json
{
  "type": "gauge",
  "id": "cpu-gauge",
  "sync": [{
    "method": "meshsocket",
    "type": "listen",
    "event": "telemetry",
    "valuePath": "cpu"
  }]
}
```

When the server emits a `telemetry` event with `{"cpu": 73}`, the gauge updates to 73 automatically.

---

## Chat

CAR-TER includes a built-in **chat** control powered by MeshSocket. Messages flow through the mesh in real time and are persisted locally with SwiftData.

![](control-preview://chat-demo)

Chat uses the same channel and identity system as all other controls — your display name comes from the connection config, and messages are routed through the mesh to all channel members.

---

## Layout Structure

A layout JSON file has this shape:

```json
{
  "name": "My Layout",
  "headerTitle": "Dashboard",
  "accentColor": "#667eea",
  "tabs": [
    {
      "title": "Controls",
      "icon": "slider.horizontal.3",
      "grid": { "columns": 4, "rows": 6 },
      "children": [ ... ]
    }
  ],
  "connection": {
    "url": "ws://192.168.1.100:4444",
    "identity": {
      "name": "My Phone",
      "channel": "home",
      "role": "controller"
    }
  }
}
```

Each tab lays its children out on a **2-D grid** — a control's `position` and `span`
place it in a `row × col` rectangle, so a tall control can sit beside two stacked
shorter ones. Set a grid's `mode` to `"flow"` for the simpler row-banded layout
(full-page content, plain forms). See [[grid-dimensions]].

Tap any node in the graph to explore the full documentation for each control type, system feature, and data model.

---

## Get Started

1. **Explore the docs** — tap nodes in the graph to learn about each control
2. **Write a layout** — create a JSON file following the [[layout-config]] schema
3. **Bind your data** — point controls at an MQTT broker or HTTP API you already
   run ([[sources]], zero server code), or run a server: drive your layout from
   Python with `pip install carterkit`, or speak the MeshSocket protocol directly
   from any language
4. **Connect** — load your layout and watch it come alive

Full developer docs — building servers, the wire protocol, and the `carterkit`
library — live at **carterbeaudoin.net/CAR-TER**.
