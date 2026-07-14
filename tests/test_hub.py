"""Tests for hub.py — driving a layout through its own bindings."""

import asyncio
import socket

import pytest

from carterkit import Layout, Fragment, Hub, HubError


class _FakeSock:
    def __init__(self):
        self.sent = []
        self.handlers = {}
        self.reply = None

    def on(self, t, f):
        self.handlers[t] = f

    async def send(self, t, payload=None, reply_to=None):
        self.sent.append((t, payload))

    async def request(self, t, payload=None, timeout=5.0):
        self.sent.append(("REQ:" + t, payload))
        return self.reply

    async def start(self):
        pass

    async def wait_until_ready(self):
        pass

    async def stop(self):
        pass


def _thermostat():
    with Layout("Thermostat", cols=4, rows=4) as ui:
        with ui.tab("Main"):
            temp = ui.gauge("temp", label="Temp", min=0, max=40,
                            listen="temp", when={"msg_type": "climate"})
            target = ui.slider("target", min=10, max=30, send="set_target")
            scenes = ui.group("Scenes", span=(2, 4), dynamic="scenes")
    return ui, temp, target, scenes


def _hub(ui, **kw):
    hub = ui.serve(**kw)
    hub.client._sock = _FakeSock()
    return hub


def test_frame_for_derives_filter_and_valuepath():
    ui, temp, target, scenes = _thermostat()
    hub = _hub(ui)
    assert hub.frame_for(temp, 21.5) == {"msg_type": "climate", "temp": 21.5}
    assert hub.frame_for("temp", 30) == {"msg_type": "climate", "temp": 30}


def test_frame_for_dotted_path():
    with Layout("X", cols=4, rows=4) as ui:
        g = ui.gauge("cpu", min=0, max=100, listen="stats.cpu",
                     when={"msg_type": "metrics"})
    hub = _hub(ui)
    assert hub.frame_for(g, 73) == {"msg_type": "metrics", "stats": {"cpu": 73}}


def test_push_broadcasts_and_snapshots_state():
    ui, temp, *_ = _thermostat()
    hub = _hub(ui)

    async def run():
        return await hub.push(temp, 21.5)

    frame = asyncio.run(run())
    assert frame == {"msg_type": "climate", "temp": 21.5}
    assert hub.client._sock.sent == [("broadcast_request", frame)]
    assert hub.client._control_state == {"temp": 21.5}   # authority snapshot


def test_push_errors_are_specific():
    with Layout("X", cols=4, rows=4) as ui:
        btn = ui.button("go", send="go")                    # no sync
        routed = ui.gauge("r", min=0, max=1, sync=[{
            "method": "meshsocket", "type": "listen",
            "event": "router.telemetry", "valuePath": "v"}])
    hub = _hub(ui)
    with pytest.raises(HubError, match="no sync binding"):
        hub.frame_for(btn, 1)
    with pytest.raises(HubError, match="routed"):
        hub.frame_for(routed, 1)
    with pytest.raises(HubError, match="no control with id"):
        hub.frame_for("nope", 1)


def test_on_derives_broadcast_demux_from_action():
    ui, temp, target, scenes = _thermostat()
    hub = _hub(ui)
    got = []

    @target.on
    def _(data):
        got.append(data)

    async def run():
        # what the app emits for the compiled action, post-substitution
        await hub._dispatch({"msg_type": "set_target", "value": 22.0})
        # unrelated broadcasts don't reach the handler
        await hub._dispatch({"msg_type": "climate", "temp": 1})

    asyncio.run(run())
    assert got == [{"msg_type": "set_target", "value": 22.0}]


def test_on_routed_action_registers_inner_type():
    from carterkit import bind
    with Layout("X", cols=4, rows=4) as ui:
        btn = ui.button("stop", action=bind.action(
            "route_msg", mode="request",
            payload={"target_id": "hub-1", "type": "emergency_stop", "payload": {}}))
    hub = _hub(ui)
    hub.on(btn, lambda d: d)
    assert "emergency_stop" in hub.client._sock.handlers


def test_on_raw_command_name_covers_both_transports():
    ui, *_ = _thermostat()
    hub = _hub(ui)
    hub.on("reboot", lambda d: d)
    assert "reboot" in hub._demux
    assert "reboot" in hub.client._sock.handlers


def test_on_control_without_action_raises():
    ui, temp, *_ = _thermostat()
    hub = _hub(ui)
    with pytest.raises(HubError, match="no action binding"):
        hub.on(temp, lambda d: d)


def test_fill_dynamic_group():
    ui, temp, target, scenes = _thermostat()
    hub = _hub(ui)
    frag = Fragment(cols=4, rows=2)
    frag.button("movie", label="Movie", send="scene")

    async def run():
        return await hub.fill(scenes, frag)

    payload = asyncio.run(run())
    assert payload["msg_type"] == "scenes"
    assert payload["children"][0]["id"] == "movie"
    assert hub.client._sock.sent[0][0] == "broadcast_request"


def test_fill_non_dynamic_group_raises():
    with Layout("X", cols=4, rows=4) as ui:
        g = ui.group("Static", span=(2, 2))
    hub = _hub(ui)
    with pytest.raises(HubError, match="dynamic"):
        asyncio.run(hub.fill(g, []))


def test_hub_from_dict_drives_by_id():
    ui, *_ = _thermostat()
    hub = Hub(ui.layout)                      # plain dict, e.g. loaded from JSON
    hub.client._sock = _FakeSock()
    assert hub.frame_for("temp", 5) == {"msg_type": "climate", "temp": 5}
    hub.on("set_target", lambda d: d)
    assert "set_target" in hub._demux


def test_control_push_requires_active_hub():
    with Layout("X", cols=4, rows=4) as ui:
        g = ui.gauge("g", min=0, max=1, listen="g")
    with pytest.raises(RuntimeError, match="no active hub"):
        asyncio.run(g.push(1))


def test_serve_stamps_connection_block():
    ui, *_ = _thermostat()
    hub = _hub(ui)
    block = ui.layout["connection"]
    assert block["url"].startswith("ws://")
    assert block["identity"]["channel"] == "home"


def test_hub_name_prefers_connection_hub_key():
    with Layout("X", cols=4, rows=4) as ui:
        ui.connect("ws://h:1", channel="lab", hub="bench-hub")
        ui.gauge("g", min=0, max=1, listen="g")
    hub = _hub(ui)
    assert hub.name == "bench-hub"


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_live_end_to_end_author_serve_drive():
    """The whole loop over a real embedded relay: push reaches a peer as the sync
    frame; the peer's action broadcast reaches the @on handler; state authority
    answers a late joiner."""
    from meshsocket import MeshSocket

    ui, temp, target, scenes = _thermostat()
    port = _free_port()
    got = {"cmd": None, "frames": []}

    async def run():
        hub = ui.serve(port=port)

        @target.on
        def _(data):
            got["cmd"] = data

        async with hub:
            app = MeshSocket(url=f"ws://127.0.0.1:{port}", name="phone",
                             channel="home", role="controller", can_broadcast=True)
            app.on("broadcast", lambda p: got["frames"].append(p))
            asyncio.ensure_future(app.start())
            await app.wait_until_ready()
            await asyncio.sleep(0.3)

            peer = await hub.wait_for_device(timeout=5)
            assert peer.get("name") == "phone"

            await temp.push(21.5)
            await app.send("broadcast_request", {"msg_type": "set_target", "value": 22.0})
            await app.send("broadcast_request",
                           {"msg_type": "control_sync_request", "from": "phone"})
            await asyncio.sleep(0.6)
            await app.stop()

    asyncio.run(run())
    assert got["cmd"] == {"msg_type": "set_target", "value": 22.0}
    assert {"msg_type": "climate", "temp": 21.5} in got["frames"]
    snaps = [f for f in got["frames"] if isinstance(f, dict)
             and f.get("msg_type") == "control_snapshot"]
    assert snaps and snaps[0]["controls"] == {"temp": 21.5}


# ─── ack'd commands: handled-gated at the hub ────────────────────────────────


def _acked_thermostat():
    with Layout("Thermostat", cols=4, rows=4) as ui:
        with ui.tab("Main"):
            target = ui.slider("target", min=10, max=30, send="set_target")
    ui.state(authority="hub", acks=True)
    return ui, target


def test_state_acks_auto_enables_command_acks():
    ui, _target = _acked_thermostat()
    hub = _hub(ui)
    assert hub.client._ack_commands is True
    plain, _ = _thermostat()[0], None
    assert _hub(plain).client._ack_commands is False


def test_hub_acks_only_commands_a_demux_handler_ran_for():
    async def run():
        ui, target = _acked_thermostat()
        hub = _hub(ui)
        got = []
        hub.on(target, got.append)
        # enter at the client's dispatch (the fake sock was swapped in after the
        # real socket registered the wrapper, so drive the level under test)
        deliver = hub.client._dispatch_broadcast
        # matched demux → handled → ok:true ack
        await deliver({"msg_type": "set_target", "value": 21,
                       "_cmd": "c-1", "_from": "Phone"})
        assert got and got[0]["value"] == 21
        acks = [p for _, p in hub.client._sock.sent
                if p.get("msg_type") == "command_ack"]
        assert acks == [{"msg_type": "command_ack", "cmd_id": "c-1",
                         "to": "Phone", "ok": True}]
        # unmatched command → NOT handled → silence (app times out + reverts)
        await deliver({"msg_type": "someone.elses", "_cmd": "c-2", "_from": "Phone"})
        acks = [p for _, p in hub.client._sock.sent
                if p.get("msg_type") == "command_ack"]
        assert len(acks) == 1

    asyncio.run(run())


def test_hub_on_sync_request_gets_dynamic_scope():
    async def run():
        ui, _target = _acked_thermostat()
        hub = _hub(ui)
        seen = []
        hub.on_sync_request(seen.append)
        await hub.client._dispatch_broadcast(
            {"msg_type": "control_sync_request", "from": "Phone",
             "dynamic": ["scenes"]})
        assert seen and seen[0]["dynamic"] == ["scenes"]

    asyncio.run(run())
