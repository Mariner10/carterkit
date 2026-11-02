"""Send a notification with a Reply button.  Run: python3 examples/notification.py"""
import asyncio
import sys

from carterkit import Layout, notification_action
from _common import main

with Layout("Notify", id="notify", cols=4, rows=2) as ui:
    ui.label("hi", text="Notifications arrive on the phone")


async def run(hub, wait=30):
    @hub.on_notif_action
    def tapped(frame):
        print("Tapped:", frame.get("actionId"), frame.get("userText", ""))

    async with hub:
        print("Sent:", await hub.notify(
            "Hello from Python", "Tap Reply to answer", thread_id="demo",
            actions=[notification_action("demo.reply", "Reply", text_input=True)]))
        await asyncio.sleep(wait)       # stay up to hear the tap


if __name__ == "__main__":
    sys.exit(main(run, ui))
