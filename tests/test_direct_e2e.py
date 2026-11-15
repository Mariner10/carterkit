"""Direct link end to end: a real Hub on an embedded LocalRelay, the real carter-direct
sidecar, and a Pion test peer. Skips without Go (and, for video, without ffmpeg)."""
import asyncio
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from carterkit import Hub
from carterkit.client import CarterClient

ROOT = Path(__file__).resolve().parent.parent
GO_CACHE = Path.home() / ".cache" / "carterkit-go" / "go" / "bin"
GO = shutil.which("go") or (str(GO_CACHE / "go") if (GO_CACHE / "go").exists() else None)
SIDECAR = os.environ.get("CARTERKIT_DIRECT_BIN")

pytestmark = [
    pytest.mark.skipif(GO is None, reason="needs Go to build the test peer"),
    pytest.mark.skipif(not SIDECAR or not Path(SIDECAR).exists(),
                       reason="CARTERKIT_DIRECT_BIN must point at a built carter-direct"),
]


@pytest.fixture(scope="module")
def testpeer(tmp_path_factory):
    out = tmp_path_factory.mktemp("peer") / "testpeer"
    subprocess.run([GO, "build", "-o", str(out), "./cmd/testpeer"], cwd=ROOT / "direct", check=True)
    return str(out)


def _port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def _until(pred, t=15.0):
    end = asyncio.get_running_loop().time() + t
    while not pred():
        assert asyncio.get_running_loop().time() < end, "timeout"
        await asyncio.sleep(0.05)


async def _phone(hub):
    p = json.loads(hub.qr_json())
    phone = CarterClient(p["url"], p.get("token") or "", p["channel"],
                         role=p.get("role", "viewer"), name="phone",
                         can_route=True, can_monitor=True,
                         **({"e2ee_key": p["e2eeKey"], "room": True} if p.get("e2eeKey") else {}))
    await phone.connect()
    await asyncio.sleep(0.5)
    return phone


async def _run_peer(testpeer, phone, tmp_path, want, *args):
    sdp_file, ans_file = tmp_path / "offer.sdp", tmp_path / "answer.sdp"
    proc = await asyncio.create_subprocess_exec(
        testpeer, "-sdp-out", str(sdp_file), "-answer-in", str(ans_file), *args,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        await _until(lambda: sdp_file.exists() and sdp_file.stat().st_size > 0)
        nodes = await phone._sock.request("get_nodes", None, timeout=5.0)
        hub_id = next(c["id"] for c in nodes["clients"] if c.get("name") == "hub")
        reply = await phone._sock.request("route_msg", {
            "target_id": hub_id, "type": "direct_offer",
            "payload": {"msg_type": "direct_offer", "v": 1, "session": "e2e-1",
                        "sdp": sdp_file.read_text(), "want": want, "restart": False}},
            timeout=10)
        assert reply and reply.get("sdp"), reply
        ans_file.write_text(reply["sdp"])
        out, err = await asyncio.wait_for(proc.communicate(), 30)
        assert proc.returncode == 0, err.decode()
        return out.decode()
    finally:
        if proc.returncode is None:
            proc.kill()


def test_e2e_rpc_audio_read(testpeer, tmp_path):
    async def go():
        hub = Hub(None, None, name="hub", port=_port())
        hub.client.on("audio_read", lambda p: {"data": b"\x01" * 131072})
        await hub.start()
        phone = None
        try:
            phone = await _phone(hub)
            out = await _run_peer(testpeer, phone, tmp_path, {"video": [], "data": True},
                                  "-type", "audio_read")
            assert "body=131072" in out, out
            assert '"reply_to":"t1"' in out.replace(" ", "")
        finally:
            if phone:
                await phone.close()
            await hub.close()
    asyncio.run(go())


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg for the camera case")
def test_e2e_camera_frames(testpeer, tmp_path):
    clip = tmp_path / "testsrc.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=15",
                    "-t", "20", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-y", str(clip)],
                   check=True)

    async def go():
        hub = Hub(None, None, name="hub", port=_port())
        hub.camera("t", f"file://{clip}")
        await hub.start()
        phone = None
        try:
            phone = await _phone(hub)
            out = await _run_peer(testpeer, phone, tmp_path, {"video": ["t"], "data": True},
                                  "-video", "10")
            assert "rtp=10" in out and "H264" in out.upper(), out
        finally:
            if phone:
                await phone.close()
            await hub.close()
    asyncio.run(go())
