"""The Playground: the layout ``carterkit start`` puts on a freshly paired phone.

Four controls that cover the two directions of a hub: values pushed from Python
(``hello``, ``level``) and actions sent by the phone (``dial``, ``tap``). The REPL
binds each one by id, so the first thing a new user types can be
``await level.push(42)``.
"""
from __future__ import annotations

from .layout import Layout

#: The layout id; stable so a second ``carterkit start`` updates the same layout.
PLAYGROUND_ID = "carterkit-playground"

#: Control ids, in the order they sit on the page.
CONTROL_IDS = ("hello", "level", "dial", "tap")


def build_playground(name: str = "Playground") -> Layout:
    """Build the Playground layout (not connected to anything yet)."""
    with Layout(name, id=PLAYGROUND_ID, cols=4, rows=4) as ui:
        ui.label("hello", text="Hello from Python", style="headline", span=(4, 1),
                 listen="hello")
        ui.gauge("level", label="Level", min=0, max=100, span=(2, 2), listen="level")
        ui.slider("dial", label="Dial", min=0, max=100, span=(2, 1), send="dial")
        ui.button("tap", label="Tap me", icon="hand.tap", span=(2, 1), send="tap")
    return ui


async def live_prompt(send, *, read=input, write=print, prompt: str = "playground> ") -> int:
    """A live prompt: each entry goes to the playground through ``send`` (an async
    callable taking the text, e.g. ``lambda t: hub.push(hello_ref, t)``) and the
    result is shown. A blank line is skipped; ``exit``/``quit``/EOF ends it.
    A failing send is reported and the prompt carries on. Returns the entries sent."""
    import asyncio
    sent = 0
    while True:
        try:
            line = await asyncio.to_thread(read, prompt)
        except EOFError:
            break
        line = line.strip()
        if not line:
            continue
        if line in ("exit", "quit"):
            break
        try:
            result = await send(line)
        except Exception as e:  # keep the prompt alive
            write(f"error: {e}")
            continue
        sent += 1
        write(f"-> {result!r}")
    return sent
