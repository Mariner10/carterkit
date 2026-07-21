---
type: sources
label: Data Sources
icon: point.3.connected.trianglepath.dotted
category: system
fields:
  - name: type
    type: enum
    values: [mqtt, http]
    description: Kind of external source
  - name: url
    type: string
    description: "MQTT broker address: mqtt://host[:port] or mqtts://host[:port]"
  - name: baseURL
    type: string
    description: HTTP base URL relative sync/action paths resolve against
  - name: username
    type: string
    description: MQTT username
  - name: password
    type: string
    description: MQTT password
  - name: clientId
    type: string
    description: MQTT client id (auto-generated when omitted)
  - name: headers
    type: object
    description: Extra HTTP headers sent with every poll/request
  - name: interval
    type: number
    default: 5
    description: Default poll interval (seconds) for HTTP syncs that omit their own
---

# Data Sources

Connect controls straight to protocols you already run — an **MQTT broker** or a
plain **HTTP API** — with no MeshSocket bridge and zero server code. MeshSocket
stays the power path (dynamic content, rooms, E2EE, readback); sources are the
zero-setup path.

A layout declares named sources at the top level; controls bind them through the
same standardized connection block ([[sync]] / [[actions]]) they use for
MeshSocket. Every control's inputs and outputs are transport-independent: what a
[[gauge]] accepts or a [[button]] emits is defined by the control, and `method`
just picks the wire.

## Definition

```json
"sources": {
  "broker": { "type": "mqtt", "url": "mqtt://192.168.1.10:1883",
              "username": "ha", "password": "secret" },
  "api":    { "type": "http", "baseURL": "http://192.168.1.5:8080",
              "headers": { "Authorization": "Bearer abc" }, "interval": 5 }
}
```

When a layout has exactly **one** source of a kind, sync/action entries may omit
`source` — it resolves automatically. With several, name the one you mean.

## MQTT

Subscribe a topic and bind the payload — the entire connection block of the
control is:

```json
"sync": [{ "method": "mqtt", "topic": "home/livingroom/temp", "valuePath": "value" }]
```

- **Topic wildcards** work (`home/+/temp`, `sensors/#`).
- **Payloads** parse naturally: JSON objects work with `filter`/`valuePath`
  exactly like MeshSocket frames; bare `23.5` / `true` / `ON` payloads become
  number / bool / string values directly (leave `valuePath` empty).
- Actions **publish**:

```json
"action": { "method": "mqtt", "topic": "home/lamp/set", "payload": "{{value}}", "retain": false }
```

String payloads publish raw bytes (`ON`, not `"ON"`); objects publish as JSON.
`mqtt://` is plain TCP (default port 1883), `mqtts://` is TLS (default 8883).
QoS 0 publish; inbound QoS 1 is acknowledged. The client auto-reconnects with
backoff and reports state to the connection console.

## HTTP polling

Poll any JSON endpoint on an interval and extract a value:

```json
"sync": [{ "method": "http", "path": "/api/status", "interval": 10, "valuePath": "cpu.load" }]
```

- `url` (absolute) or `path` (against the source's `baseURL`).
- Controls polling the **same URL at the same interval share one request** — a
  page of gauges over one status endpoint costs one poll.
- The response body is JSON; `filter` and `valuePath` behave exactly as in
  [[sync]]. Special receivers work too: point a [[list]] at an array endpoint,
  a [[sparkline]] at a numeric one.
- Actions fire requests:

```json
"action": { "method": "http", "path": "/api/restart", "httpMethod": "POST",
            "payload": { "service": "media" } }
```

`httpMethod` defaults to POST when a payload is present, else GET. Object
payloads send as JSON bodies; string payloads send as text.

## Full example — an ESP32 + Home Assistant page, no server

```json
{
  "name": "Greenhouse",
  "version": 1,
  "sources": { "broker": { "type": "mqtt", "url": "mqtt://192.168.1.10" } },
  "tabs": [{
    "title": "Climate", "icon": "leaf.fill", "grid": { "columns": 2, "rows": 6 },
    "children": [
      { "type": "gauge", "id": "temp", "position": [0, 0], "min": 0, "max": 40,
        "label": "Temp °C",
        "sync": [{ "method": "mqtt", "topic": "greenhouse/temp" }] },
      { "type": "sparkline", "id": "hum", "position": [0, 1], "label": "Humidity",
        "sync": [{ "method": "mqtt", "topic": "greenhouse/humidity" }] },
      { "type": "toggle", "id": "fan", "position": [2, 0], "label": "Fan",
        "sync": [{ "method": "mqtt", "topic": "greenhouse/fan/state",
                   "valuePath": "" }],
        "action": { "method": "mqtt", "topic": "greenhouse/fan/set",
                    "payload": "{{value}}" } }
    ]
  }]
}
```

## Mixing transports

A layout may use MeshSocket, MQTT, HTTP, and [[sensors]] together — each sync
entry picks its own `method`. A control with several sync entries takes whichever
delivered last.

## Notes

- Sources live and die with the layout: leaving it disconnects the broker and
  stops all polling.
- MQTT needs a declared source (the broker address); HTTP syncs with an absolute
  `url` work with no `sources` block at all.
- Diagnostics (connects, failures, reconnects) land in the connection console
  like MeshSocket's.

## Related

- [[sync]] — the standardized inbound binding
- [[actions]] — the standardized outbound command
- [[layout-config]] — where `sources` sits
