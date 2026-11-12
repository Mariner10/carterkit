---
type: audio
depth: complete
since: next
label: Audio
icon: music.note
category: system
fields:
  - name: hub
    since: next
    type: string
    description: "Required. The hub's target_name: it serves the audio and receives commands"
    summary: Which hub plays music
    does: Names the hub that serves the files and gets the transport commands.
  - name: mode
    since: next
    type: enum
    values: [listen, remote]
    default: listen
    description: "listen: this phone plays the audio. remote: the hub plays on its own speakers and this phone only controls it"
    summary: Play here or control the hub
    does: In listen mode the phone plays and shows Now Playing; in remote mode the hub plays and the phone is a remote (no Now Playing).
    valueHelp: {"listen": "the phone plays the audio", "remote": "the hub plays; the phone only controls it"}
  - name: quality
    since: next
    type: object
    description: "Rule per network: { local, wifi, cellular }, each best | lossless | lossy or an ordered list of rendition ids. Low Data Mode counts as cellular"
    summary: Quality per network
    does: Picks which rendition of a track starts, by the network in use; it never changes mid-track.
  - name: commands
    since: next
    type: object
    description: "hub (every command the hub lists in capabilities) or an object of slots: play, pause, toggle, next, previous, seek, skipForward, skipBackward, like, dislike, shuffle, repeat"
    summary: Lock-screen and headset commands
    does: Chooses which lock-screen, AirPods, Watch and Siri commands are live and what each one does.
  - name: nowPlaying
    since: next
    type: object
    description: "{ title, subtitle } templates over the current item's fields, e.g. {{title}}, {{artist}}"
    summary: Now Playing text
    does: Sets the title and subtitle iOS shows on the lock screen and in Control Center.
  - name: normalize
    since: next
    type: bool
    default: false
    description: Apply each item's gain (dB) so tracks play at the same loudness
    summary: Even out loudness
    does: Applies the gain the hub lists for each track.
playerKeys:
  - { key: state, since: next }
  - { key: title, since: next }
  - { key: artist, since: next }
  - { key: album, since: next }
  - { key: artwork, since: next }
  - { key: position, since: next }
  - { key: duration, since: next }
  - { key: progress, since: next }
  - { key: buffered, since: next }
  - { key: format, since: next }
  - { key: quality, since: next }
  - { key: route, since: next }
  - { key: airplay, since: next }
  - { key: shuffle, since: next }
  - { key: repeat, since: next }
  - { key: liked, since: next }
  - { key: live, since: next }
  - { key: next.title, since: next }
  - { key: next.artist, since: next }
  - { key: next.artwork, since: next }
commandSlots:
  - { slot: play, since: next }
  - { slot: pause, since: next }
  - { slot: toggle, since: next }
  - { slot: next, since: next }
  - { slot: previous, since: next }
  - { slot: seek, since: next }
  - { slot: skipForward, since: next }
  - { slot: skipBackward, since: next }
  - { slot: like, since: next }
  - { slot: dislike, since: next }
  - { slot: shuffle, since: next }
  - { slot: repeat, since: next }
---

A layout turns into a music system with a top-level `audio` block: at most one per layout,
only `hub` required. The hub sends the audio and artwork over its MeshSocket connection;
the phone buffers, decodes and plays it, and iOS shows it on the lock screen, in Control
Center, the Dynamic Island, on Apple Watch, on AirPods and over AirPlay. CAR-TER has no
player screen: controls in the layout (labels, an image, a slider, buttons) bind to the
player, and iOS surfaces carry the rest. Playing needs the Audio background mode and runs in
the background only while sound is playing.

```json
"audio": {
  "hub": "music",
  "mode": "listen",
  "quality": { "local": "best", "wifi": "lossless", "cellular": "lossy" },
  "commands": "hub",
  "nowPlaying": { "title": "{{title}}", "subtitle": "{{artist}} · {{album}}" },
  "normalize": false
}
```

`quality` rules: `best` is the highest the hub offers, hi-res included; `lossless` is lossless
at 48 kHz or less, else the best lossy; `lossy` is the best lossy. `local` means the layout's
connection URL points at a private-network address or a `.local` host.

## Command slots

A slot is `"hub"` (send to the hub), an action object (runs like a button's action),
`{ "seconds": 15 }` for the skip slots, or absent (off). AirPods, Apple Watch, headphone
buttons and Siri's "skip" all reach the same slots. With `"commands": "hub"`, a hub that lists
`play` and `pause` also gets the headset's play/pause, and the skip slots need `skip` (15 s).
A slot's action sees the command's value as `{{value}}`: the seek position in seconds, the
signed skip, or the new shuffle or repeat mode.

```json
"commands": { "play": "hub", "pause": "hub", "next": "hub", "previous": "hub",
              "skipForward": { "seconds": 30 },
              "like": { "method": "meshsocket", "event": "route_msg_noreply",
                        "payload": { "target_name": "music", "type": "fav", "payload": {} } } }
```

## The player

### Readings

Any control binds the player like a sensor:
`{ "type": "label", "id": "song", "sync": [{ "method": "player", "key": "title" }] }`

| Key | Type | Notes |
|---|---|---|
| `state` | string | `idle`, `loading`, `playing`, `paused`, `buffering`, `ended`, `error`, `unavailable` |
| `title`, `artist`, `album` | string | From the current item |
| `artwork` | string | A URL an `image` control shows: the hub's https URL, or a `file:` URL of the cached art |
| `position`, `duration` | number (s) | Published at 2 Hz while playing, at once on seek or state change |
| `progress` | number 0-1 | |
| `buffered` | number (s) | Audio fetched ahead of the position |
| `format` | string | e.g. `FLAC 24/96`, `AAC 256` |
| `quality` | string | `hi-res`, `lossless` or `lossy` |
| `route` | string | Output name, e.g. `iPhone Speaker` or an AirPlay device |
| `airplay` | bool | Playing to an AirPlay device |
| `shuffle`, `repeat`, `liked` | | From the hub's state |
| `live` | bool | The item is a live stream |
| `next.title`, `next.artist`, `next.artwork` | | The hub's next item |

### Actions

```json
{ "type": "button", "id": "pp", "action": { "method": "player", "verb": "toggle" } }
{ "type": "slider", "id": "seek", "action": { "method": "player", "verb": "seek", "value": "{{value}}" },
  "sync": [{ "method": "player", "key": "position" }] }
```

A slider bound to `position` takes its upper bound from the track's `duration`, so it fills in
step with the song; its `max` applies only while `duration` is 0 or the item is `live`.

Verbs: `play`, `pause`, `toggle`, `stop`, `next`, `previous`, `seek` (seconds), `skip` (± seconds),
`like`, `dislike`, `shuffle`, `repeat`.

## What the hub sends and answers

Ordinary MeshSocket payloads with a `msg_type`, sealed like every hub message.

**`audio_state`** (hub to app): broadcast on change only, and the reply to `hello`. The app
ignores a `rev` older than the last one it applied.

```json
{ "msg_type": "audio_state", "rev": 12, "state": "playing", "position": 12.5, "at": 1731180000000,
  "item": { "id": "t-123", "title": "…", "artist": "…", "album": "…", "duration": 245.3,
            "artwork": { "url": "https://…" }, "gain": -6.2, "live": false,
            "renditions": [
              { "id": "flac", "codec": "flac", "container": "flac", "lossless": true,
                "sampleRate": 44100, "bitDepth": 16, "channels": 2, "bitrate": 910000, "bytes": 27917312 },
              { "id": "aac", "codec": "aac", "container": "m4a", "lossless": false,
                "sampleRate": 44100, "channels": 2, "bitrate": 256000, "bytes": 7851008 } ] },
  "next": { },
  "capabilities": ["play", "pause", "next", "previous", "seek", "like", "shuffle", "repeat", "listen", "remote"],
  "shuffle": false, "repeat": "off", "liked": null,
  "queue": { "index": 3, "count": 12 }, "budget": 6 }
```

`artwork` is `{ "url": "https://…" }` or `{ "ref": "art-55", "bytes": 182044, "type": "image/jpeg" }`
for art the hub serves itself. `budget` is the `audio_read`s a second each phone may send
(default 6). In `listen` mode the phone's own playback leads; `state`, `position` and `at` are
advisory. Several phones: the hub sees which phone sent each command and decides whether they
share one queue (broadcast) or have their own (routed `audio_state`).

**`audio_read`** (app to hub, request):

```json
{ "msg_type": "audio_read", "item": "t-123", "rendition": "flac", "offset": 0, "length": 65536 }
{ "msg_type": "audio_read", "art": "art-55", "offset": 0, "length": 131072 }
```

Reply `{ "msg_type": "audio_data", "item": "t-123", "rendition": "flac", "offset": 0, "data": "<base64>", "total": 27917312, "eof": false }`.
`length` is never above 131072 (128 KiB, the hard cap per chunk); a hub may return fewer bytes.
Errors: `{ "msg_type": "audio_data", "error": "not_found" | "range" | "busy" }`; on `busy` the app backs off.

**`audio_live`** (app to hub, request) for streams with no end:
`{ "msg_type": "audio_live", "item": "radio", "rendition": "aac", "from": 1042, "max": 8 }`. The
reply is `{ "chunks": [{ "seq": 1042, "data": "<base64>" }], "head": 1050, "chunkMs": 250 }`;
`from: null` asks for the chunk nearest the live edge. Keep at least 10 s of recent chunks;
one reply stays at or under 131072 bytes.

**`audio_command`** (app to hub, no reply): `{ "msg_type": "audio_command", "verb": "next", "item": "t-123", "position": 12.5 }`.
Verbs are the command slots plus `hello` (a request sent when the layout opens; reply
`audio_state`), `advanced` (the phone moved on to `next` by itself) and `ended`.

## Files that stream well

Serve streamable files: m4a (AAC, ALAC) with the index at the front (fast-start), FLAC with a
SEEKTABLE, MP3 with a Xing or VBRI header, CAF, WAV and AIFF. Other files still play, but
starting and seeking are slower.

## The smallest hub that works

Answer `hello` with `audio_state`. Answer `audio_read` with the file's bytes at `offset`. On
`next`, `previous` and `advanced`, update `item` and `next` and broadcast. About 40 lines in
any language; the app does the buffering, retrying and pacing.

## Examples

### Everything the hub offers

Every command the hub lists goes to the hub; the lock screen shows the title, artist and album.

```json
{ "hub": "music", "commands": "hub",
  "nowPlaying": { "title": "{{title}}", "subtitle": "{{artist}} · {{album}}" } }
```

### Podcast skips

Play, pause and seek go to the hub; skips jump 30 s forward and 15 s back; nothing else shows.

```json
{ "hub": "podcasts",
  "commands": { "play": "hub", "pause": "hub", "toggle": "hub", "seek": "hub",
                "skipForward": { "seconds": 30 }, "skipBackward": { "seconds": 15 } },
  "nowPlaying": { "title": "{{title}}", "subtitle": "{{album}}" } }
```

### Like sends the hub a message

The lock screen's like runs a layout action instead of the hub's own `like`.

```json
{ "hub": "music",
  "commands": { "toggle": "hub", "next": "hub", "previous": "hub",
                "like": { "method": "meshsocket", "event": "route_msg_noreply",
                          "payload": { "target_name": "music", "type": "fav", "payload": {} } } } }
```

### Best at home, smaller away

Highest quality at home, ALAC then AAC on other Wi-Fi, lossy on cellular, even loudness.

```json
{ "hub": "music", "quality": { "local": "best", "wifi": ["alac", "aac"], "cellular": "lossy" },
  "normalize": true }
```

### Control the hub's speakers

The hub plays on its own speakers; this phone is the remote and shows no Now Playing.

```json
{ "hub": "speakers", "mode": "remote" }
```

## A minimal music layout

An `image` bound to `artwork`, two `label`s (title, artist), a `slider` for position with
`seek`, three `button`s (previous, toggle, next), an [[airplay]] control, and a `list` fed by
the hub's own queue broadcast (queue data is ordinary hub data, not a player reading).

```json
{ "audio": { "hub": "music" },
  "tabs": [{ "name": "Music", "grid": { "columns": 4, "controls": [
    { "type": "image", "id": "art", "position": { "row": 0, "col": 0, "rowSpan": 2, "colSpan": 4 },
      "sync": [{ "method": "player", "key": "artwork" }] },
    { "type": "label", "id": "song", "position": { "row": 2, "col": 0, "colSpan": 4 },
      "sync": [{ "method": "player", "key": "title" }] },
    { "type": "label", "id": "who", "position": { "row": 3, "col": 0, "colSpan": 4 },
      "sync": [{ "method": "player", "key": "artist" }] },
    { "type": "slider", "id": "seek", "position": { "row": 4, "col": 0, "colSpan": 4 },
      "action": { "method": "player", "verb": "seek", "value": "{{value}}" },
      "sync": [{ "method": "player", "key": "position" }] },
    { "type": "button", "id": "prev", "label": "Back", "position": { "row": 5, "col": 0 },
      "action": { "method": "player", "verb": "previous" } },
    { "type": "button", "id": "pp", "label": "Play", "position": { "row": 5, "col": 1 },
      "action": { "method": "player", "verb": "toggle" } },
    { "type": "button", "id": "next", "label": "Next", "position": { "row": 5, "col": 2 },
      "action": { "method": "player", "verb": "next" } },
    { "type": "airplay", "id": "route", "position": { "row": 5, "col": 3 } }
  ] } }] }
```

## Notes

- Playing audio keeps the app running in the background; nothing plays silence to stay alive.
  See [[background]] (`audio.playback`) for keeping it going after the layout closes.
- The first layout that starts playback owns Now Playing; one player runs app-wide.
- `nowPlaying` templates take `{{title}}`, `{{artist}}`, `{{album}}` and `{{id}}`; an empty
  field leaves no stray separator at either end. Now Playing changes only when the item, the
  play state, the art or a seek does; iOS moves the progress bar itself.
- `ref` art is read in chunks like audio and kept on the phone; Now Playing gets it at up to
  1024 px, and an `image` bound to `artwork` shows its `file:` URL.
- No lyrics, equalizer or in-app player screen: the layout is the interface.
