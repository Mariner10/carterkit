"""Progress: a task the app draws as a pill, a sheet and on the Dynamic Island.

Run:  python hub.py   then scan the QR it prints with the CAR-TER app.
Edit hub.py or layout.json while it runs: every save reaches the phone.

Start example task opens hub.progress(...) with a Cancel button, a step strip and a live
log; the hub runs the work, updates the task, and ends it. Cancel sets task.cancelled; the
hub stops and says so (cancelled_ok). The Toast and Haptic buttons play those surfaces.
"""
import asyncio
from pathlib import Path

from carterkit import Layout

ui = Layout.load(Path(__file__).with_name("layout.json"))

TOTAL = 48_000_000        # placeholder: "bytes" to fetch
CHUNK = 2_000_000
TICK = 0.5                # seconds per chunk; the example is slow on purpose
STEPS = ("Downloading", "Unpacking", "Setting up")


async def say(hub, text: str) -> None:
    await hub.push("status", text, force=True)


async def run_task(hub) -> str:
    """The example work. Returns how it ended: done, cancelled or failed."""
    logs = hub.log("example-log", title="Example log")
    async with hub.progress("Installing Example package", total=TOTAL, unit="bytes",
                            cancellable=True, ask="Stop installing Example package?",
                            show="sheet", log=logs) as task:
        await logs.info("Starting Example package")
        for index, label in enumerate(STEPS, 1):
            await task.update(step=(index, len(STEPS), label), detail=label)
            if index == 1:
                while task.done < TOTAL:
                    if task.cancelled:
                        await logs.warn("Cancelled")
                        await task.cancelled_ok()
                        await logs.close()
                        return "cancelled"
                    await task.update(done=min(TOTAL, task.done + CHUNK))
                    await asyncio.sleep(TICK)
            else:
                await task.update(done=TOTAL)
                await asyncio.sleep(TICK)
            await logs.info(f"{label} finished")
        await task.finish("Installed 1.2.0")
    await logs.close()
    await hub.toast("Example package installed", message="Version 1.2.0", style="success",
                    haptic="success", action=("Show log", {"log": logs.id}))
    return "done"


async def run(hub):
    """Handlers; restarted on every save."""
    running: list = []

    @hub.on("task_start")
    async def start(frame):
        if running and not running[0].done():
            await say(hub, "A task is already running")
            return
        async def go():
            await say(hub, "Task running")
            await say(hub, f"Task {await run_task(hub)}")
        running[:] = [asyncio.create_task(go())]

    @hub.on("task_toast")
    async def toast(frame):
        await hub.toast("Example toast", message="Plain, short, with the hub's name", style="info")

    @hub.on("task_haptic")
    async def buzz(frame):
        played = await hub.haptic("success")
        await say(hub, "Haptic played" if played else "Haptic not played (app in background?)")

    await say(hub, "Start the task, then lock the phone")


if __name__ == "__main__":
    from carterkit import livefile
    raise SystemExit(livefile.main(__file__))
