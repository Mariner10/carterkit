---
type: sources
label: Data Sources
icon: point.3.connected.trianglepath.dotted
category: system
fields:
  - name: type
    type: enum
    values: [mqtt, http, local]
    description: Kind of source (mqtt or http external, local on-device store)
  - name: url
    type: string
    description: "MQTT broker address: mqtt://host[:port] or mqtts://host[:port]"
  - name: baseURL
    tab: advanced
    type: string
    description: HTTP base URL relative sync/action paths resolve against
  - name: username
    type: string
    description: MQTT username
  - name: password
    type: string
    description: "MQTT password; write a {{secret:name}} placeholder, not the literal value"
  - name: clientId
    tab: advanced
    type: string
    description: MQTT client id (auto-generated when omitted)
  - name: headers
    type: object
    description: "Extra HTTP headers sent with every poll/request; put credentials in as {{secret:name}}"
  - name: interval
    min: 1
    max: 3600
    step: 1
    type: number
    default: 5
    description: Default poll interval (seconds) for HTTP syncs that omit their own
---

# Data Sources

Connect controls straight to protocols you already run — an **MQTT broker** or a
plain **HTTP API** — with no MeshSocket bridge and zero server code, or to an
on-device **local store** ([[local-store]]) with no network at all. MeshSocket
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
              "username": "ha", "password": "{{secret:mqtt_password}}" },
  "api":    { "type": "http", "baseURL": "http://192.168.1.5:8080",
              "headers": { "Authorization": "Bearer {{secret:api_token}}" }, "interval": 5 }
},
"secrets": [ { "name": "mqtt_password" }, { "name": "api_token" } ]
```

Credentials go in as `{{secret:name}}` placeholders, not literal values: the
phone fills them in from its Keychain when it dials the broker or sends the
request, and the JSON never carries them. By default a secret may only be sent
to the hosts of the layout's declared sources; `secrets[].hosts` changes that
for one secret. See [[layout-config#Secrets]].

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

## What the header shows

The connection dot in the header stands for the layout's MeshSocket relay link.
A layout that pulls through `sources` gets one extra glyph beside the dot per
pipe — a poll cycle (↻) for each HTTP host, a fan-out mark for each MQTT
broker — each in its own health color: yellow while the first poll or the
broker dial is in flight, green once data is arriving, red after a failed poll
or a dropped session, grey for a source nothing is bound to. A layout with no
relay at all takes the pipes' aggregate color for the dot instead of the idle
grey, so an HTTP-fed dashboard never reads as "Not connected". Tapping the dot
or a glyph opens the connection hub, whose **Data Pipes** box lists every pipe
with its host, cadence or topic count, and state.

## Notes

- Sources live and die with the layout: leaving it disconnects the broker and
  stops all polling.
- MQTT needs a declared source (the broker address); HTTP syncs with an absolute
  `url` work with no `sources` block at all.
- Diagnostics (connects, failures, reconnects) land in the connection console
  like MeshSocket's.
- A request that needs a secret the phone does not have, or may not send to
  that host, is not sent; the pipe shows `needs secret <name>` or
  `secret <name> not allowed for host <h>` ([[layout-config#Secrets]]).

## Local store

`"type": "local"` declares an on-device database instead of an external endpoint:
typed collections of records the layout's controls read with `sync` and write
with `action`, no server or network involved. The keys (`namespace`,
`collections`, `views`, `weekStartsOn`), the field types, the JSON query stages,
the tokens and the write ops are all documented in [[local-store]].

```json
"sources": {
  "db": { "type": "local",
          "collections": { "notes": { "fields": { "text": "string", "at": "date" } } } }
}
```

A local source appears in the header's Data Pipes as `Local`; it is grey until a
control binds it, green while serving, and red with the reason after a schema or
write error.

## Related

- [[sync]] — the standardized inbound binding
- [[actions]] — the standardized outbound command
- [[local-store]] — the on-device `local` source
- [[layout-config]] — where `sources` sits
