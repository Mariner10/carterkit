"""Test the CarterClient async context manager (no network — fake socket)."""

import asyncio

from carterkit import CarterClient


class _FakeSock:
    def __init__(self):
        self.events = []

    async def start(self):
        self.events.append("start")

    async def wait_until_ready(self):
        self.events.append("ready")

    async def stop(self):
        self.events.append("stop")


def test_async_context_manager_connects_and_closes():
    c = CarterClient(gateway_url="ws://x", token="t", channel="home")
    fake = _FakeSock()
    c._sock = fake  # swap the real MeshSocket for a recorder

    async def run():
        async with c as ctx:
            assert ctx is c
        return fake.events

    assert asyncio.run(run()) == ["start", "ready", "stop"]
