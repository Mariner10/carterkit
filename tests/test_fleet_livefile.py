"""LiveFile.watch: a save pushes once with the new contents; no change pushes nothing."""
import asyncio
import os

from carterkit.livefile import LiveFile


class FakeHub:
    def __init__(self):
        self.pushes = []
        self._index = {}

    def reset_handlers(self):
        pass

    async def push_layout(self):
        self.pushes.append(self.live.path_text())


def _make(tmp_path):
    p = tmp_path / "hello.py"
    p.write_text("v1")
    live = LiveFile(str(p), out=lambda s: None)
    live.hub = FakeHub()
    live.hub.live = live
    live.path_text = lambda: open(live.path).read()
    live.load = lambda: (object(), None, None)
    live.attach = lambda ui: setattr(live, "ui", ui)
    return live, p


async def _run(live, p, edit):
    task = asyncio.create_task(live.watch(interval=0.02))
    await asyncio.sleep(0.1)
    edit(p)
    await asyncio.sleep(0.5)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


def test_modified_file_pushes_once_with_new_contents(tmp_path):
    live, p = _make(tmp_path)

    def edit(path):
        path.write_text("v2")
        os.utime(path, ns=(1, os.stat(path).st_mtime_ns + 10**9))

    asyncio.run(_run(live, p, edit))
    assert live.hub.pushes == ["v2"]


def test_unchanged_file_pushes_nothing(tmp_path):
    live, p = _make(tmp_path)
    asyncio.run(_run(live, p, lambda path: None))
    assert live.hub.pushes == []
