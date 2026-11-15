# Direct link: a peer-to-peer connection between the phone and your hub

The direct link is a WebRTC connection between the CAR-TER app and a carterkit hub.
The relay (MeshSocket) is used only to set it up: the phone's offer and the hub's
answer travel as sealed, routed requests. After that, video and a data channel go
straight between the two, so a camera stream or a 128 KiB audio read never crosses
the relay.

It is optional. A hub with no `carter-direct` sidecar replies `no_sidecar` to an
offer and everything else keeps working over the relay.

## What you get

- **Cameras.** `hub.camera(id, url)` offers an RTSP or HTTP stream as H.264 video.
- **Request/reply data.** The phone calls your normal `hub.on(...)` handlers over a
  data channel named `rpc` (reliable, ordered, messages up to 262144 bytes, at most
  32 requests in flight per session). A handler that returns a `data` value of
  `bytes` sends it as a raw body, with no base64.

Sessions are bound to the offer's relay-stamped sender (`_relayFrom`). An offer
without one is refused with `denied`, and handlers only ever see that bound peer.

## Cameras: `hub.camera()`

```python
from carterkit import Hub

hub = Hub(layout)
hub.camera("printer", "rtsp://192.168.1.40/stream1", name="Printer")
hub.run()
```

`camera(id, url, name=None)` is synchronous and safe to call before the hub runs or
while it is running. The hub tells the phone which cameras exist (`direct_hello`),
each with a status: `ok`, `idle`, `starting`, `needs_ffmpeg` or `unreachable`.

The encoder runs only while someone watches: one ffmpeg per camera however many
viewers there are, started on the first viewer and stopped 10 s after the last one
leaves. Keyframes come every second. A `video` control in a layout is a Pro control.

## ffmpeg

Cameras need the `ffmpeg` program on `PATH`. carterkit runs it as a separate process
(`nice 10`) and never bundles or links it. Without it the camera reports
`needs_ffmpeg` and the app shows "Camera unavailable"; the data channel still works.
Install it with your package manager (`apt install ffmpeg`, `brew install ffmpeg`).

The video is H.264 constrained baseline or main profile, no B-frames. A camera that
already sends H.264 is repackaged without re-encoding where ffmpeg can; anything else
is encoded, with a hardware encoder if the machine has one and `libx264` otherwise.

## Networks that block direct paths

There is no TURN relay. The phone and the hub find each other through the public STUN
servers `stun.cloudflare.com:3478` and `stun.l.google.com:19302` (override them with
`iceServers` in config). This works on home Wi-Fi and most mobile networks. Some
networks (corporate or hotel Wi-Fi, some carrier-grade NATs) block direct paths, and
there the app shows:

> **Can't connect from this network**
> This network blocks direct connections. It works on home Wi-Fi and most mobile
> networks. Support for networks like this is coming.

Everything that does not need the direct link keeps working over the relay. Candidates
are gathered before the offer is sent (no trickle ICE): up to 2.0 s on the phone and
1.5 s on the hub. Switching between Wi-Fi and cellular restarts ICE in the same session.

## Lifecycle

- The link closes 30 s after the last lease.
- If the sidecar crashes, carterkit restarts it with backoff; open sessions end as
  `failed` and the phone offers again on its next lease. No ffmpeg is left behind.

## CPU on a small machine

The cost is the encoder. Figures for a Raspberry Pi come from the task 11 on-device
measurement and are recorded here when it lands:

| Machine | Stream | Mode | CPU |
|---|---|---|---|
| Raspberry Pi | 720p15 H.264 | repackage | _pending task 11_ |
| Raspberry Pi | 720p15 H.264 | re-encode | _pending task 11_ |

## Testing

`tests/test_direct_e2e.py` runs a real hub on an embedded `LocalRelay`, the real
sidecar and a Pion test peer. It skips without Go (video also without ffmpeg), and
uses the relay-stamped `_relayFrom` (meshsocket>=0.4.3; on older relays the test stamps it on the hub side):

```bash
bash direct/scripts/check.sh
CARTERKIT_DIRECT_BIN=direct/build/carter-direct python3 -m pytest -q tests/test_direct_e2e.py
```
