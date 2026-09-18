"""Preview: python examples/ios_surfaces.py
Layout:  python examples/ios_surfaces.py --layout > workshop.json
Run:     python examples/ios_surfaces.py --connection device.json [--activity]

Run mode sends a demo alert and refresh to your account. Load/pin workshop.json
in CAR-TER on the credential's channel first. Ctrl-C stops the demo hub.
"""
import argparse
import asyncio
import json

from carterkit import Layout, notification_action


def workshop():
    with Layout("Workshop", id="workshop", cols=4, rows=4) as ui:
        with ui.tab("Main"):
            temp = ui.gauge("temperature", label="Temperature", min=0, max=100,
                            formatValue="suffix:°C", listen="temperature")
            fan = ui.toggle("fan", label="Fan", listen="fan", send="set_fan")
        ui.glance(hero=temp, slots=[fan], live_activity=True)
    return ui, temp, fan


async def run(hub, temp, fan, activity):
    @fan.on
    async def set_fan(frame):
        value = frame.get("value")
        if not isinstance(value, bool):
            return {"ok": False, "error": "Expected a Boolean"}
        print("Demo fan state:", value)  # replace with your actuator + confirmed state
        await fan.push(value)
        return {"ok": True}

    @hub.surfaces.on_notification
    def response(frame):
        if frame.get("actionId") == "workshop.reply":
            print("Reply:", frame.get("userText", ""))

    async with hub:
        await temp.push(21.5)
        await fan.push(False)
        print("Refresh acceptance:", await hub.surfaces.refresh())
        print("Alert acceptance:", await hub.surfaces.notify(
            "Workshop", "Demo is ready", include_glance=True, thread_id="workshop",
            actions=[notification_action("workshop.reply", "Reply", text_input=True,
                                         text_input_button_title="Send",
                                         authentication_required=True)]))
        if activity:
            print("Activity acceptance:", await hub.surfaces.start_activity(alert_title="Workshop demo"))
        try:
            await asyncio.Event().wait()
        finally:
            if activity:
                await hub.surfaces.end_activity()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connection", help="Private Add Hub credential JSON")
    parser.add_argument("--layout", action="store_true", help="Print the layout JSON and exit")
    parser.add_argument("--activity", action="store_true", help="Also start a Live Activity in run mode")
    args = parser.parse_args()
    ui, temp, fan = workshop()
    hub = ui.serve(connection=args.connection)
    if args.layout:
        print(json.dumps(ui.layout, indent=2))
    elif args.connection:
        try:
            asyncio.run(run(hub, temp, fan, args.activity))
        except KeyboardInterrupt:
            pass
    else:
        print(json.dumps(hub.surfaces.snapshot({temp: 21.5, fan: False}), indent=2))


if __name__ == "__main__":
    main()
