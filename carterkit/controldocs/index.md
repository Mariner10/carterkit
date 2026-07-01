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

Every control in CAR-TER is declared as a JSON object with a `type`, `id`, and grid `position`. The system supports **27 control types** across three categories:

### Input Controls
Buttons, toggles, sliders, steppers, pickers, date pickers, text inputs, color pickers, and segmented controls. These send user actions to your server. Container controls — **carousels**, **flip cards**, and **accordions** — arrange sets of groups into swipeable pages, flippable faces, and collapsible sections.

### Display Controls
Gauges, progress rings, sparklines, labels, images, maps, and graphs. These visualize incoming telemetry data in real time.

![](control-preview://gauge-demo)

### Data Flow
Every control can **sync** with the server. Input controls fire **actions** — events sent over the mesh. Display controls **listen** for incoming data and update automatically.

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
3. **Run a server** — drive your layout from Python with `pip install carterkit`, or
   speak the MeshSocket protocol directly from any language
4. **Connect** — load your layout and watch it come alive

Full developer docs — building servers, the wire protocol, and the `carterkit`
library — live at **carterbeaudoin.net/CAR-TER**.
