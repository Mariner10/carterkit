"""Dynamic lists: builders, validate, the phone-customization overlay store/apply/ack, examples."""
import asyncio
import importlib
import json
import sys
from pathlib import Path

import pytest

from carterkit import Hub, Layout, catalog, validate
from carterkit.customize import OverlayStore, apply_overlay, sanitize_overlay

ROOT = Path(__file__).parent.parent
CAT = catalog.build_catalog(ROOT / "carterkit" / "controldocs", include_theme=True)


def _errors(layout):
    return [f for f in validate.validate_layout(layout, CAT) if f.get("severity", "error") == "error"]


def _walk(node):
    yield node
    for k in ("tabs", "children"):
        for c in node.get(k) or []:
            yield from _walk(c)


def _find(layout, cid):
    return next(n for n in _walk(layout) if n.get("id") == cid)


# ── builders ─────────────────────────────────────────────────────────────────

def test_group_scroll_snap_peek_edge():
    with Layout("L", id="l", cols=4, rows=4) as ui:
        with ui.group("S", id="s", span=(2, 4), cols=4, rows=2, scroll="horizontal",
                      snap="item", peek=0.2, edge="fade", edge_size=12, customize="look"):
            ui.label("a", text="x", position=(0, 0))
    g = _find(ui.layout, "s")
    assert g["grid"]["scroll"] == "horizontal" and g["grid"]["snap"] == "item"
    assert g["grid"]["peek"] == 0.2 and g["edge"] == "fade" and g["edgeSize"] == 12
    assert g["customize"] == "look"


def test_vertical_slider_and_search_role():
    with Layout("L", id="l", cols=4, rows=4) as ui:
        ui.slider("v", position=(0, 0), span=(3, 1), orientation="vertical", track="hidden",
                  min=0, max=1)
        ui.text_input("find", position=(3, 0), role="search")
    d = ui.layout
    assert _find(d, "v")["orientation"] == "vertical" and _find(d, "v")["track"] == "hidden"
    assert _find(d, "find")["role"] == "search"
    assert _errors(d) == []


def test_layout_customize_sets_connection_opt_in():
    with Layout("L", id="l") as ui:
        ui.customize("arrange", save=True)
    from carterkit.customize import layout_customize
    assert layout_customize(ui.layout) == ("arrange", True)


def test_validate_rejects_bad_scroll():
    with Layout("L", id="l", cols=4, rows=4) as ui:
        with ui.group("S", id="s", span=(2, 4), cols=4, rows=2, scroll="diagonal"):
            ui.label("a", text="x", position=(0, 0))
    assert _errors(ui.layout)


def test_scroll_group_children_may_pass_columns():
    with Layout("L", id="l", cols=4, rows=4) as ui:
        with ui.group("S", id="s", span=(2, 4), cols=4, rows=2, scroll="horizontal"):
            for i in range(10):
                ui.label(f"a{i}", text="x", position=(0, i), span=(1, 1))
    assert _errors(ui.layout) == []


# ── overlay: sanitize, store, apply ──────────────────────────────────────────

OVERLAY = {"patches": {"strip": {"look": {"accentColor": "#FF0000", "action": "evil"},
                                 "arrange": {"hidden": True}}}, "order": {}}


def test_sanitize_drops_unlisted_keys():
    clean = sanitize_overlay(OVERLAY)
    assert clean["patches"]["strip"]["look"] == {"accentColor": "#FF0000"}


def test_store_round_trips_layout_and_rev(tmp_path):
    st = OverlayStore(tmp_path / "o.json")
    st.save("eq", 3, sanitize_overlay(OVERLAY))
    doc = json.loads((tmp_path / "o.json").read_text())
    assert doc["layout"] == "eq" and doc["rev"] == 3
    overlay, rev = st.load("eq")
    assert rev == 3 and overlay["patches"]["strip"]["look"]["accentColor"] == "#FF0000"
    assert st.load("other") == (None, 0)


def test_apply_overlay_idempotent_and_needs_opt_in():
    with Layout("L", id="l", cols=4, rows=4) as ui:
        ui.customize("arrange")
        with ui.group("S", id="strip", span=(2, 4), cols=4, rows=2):
            ui.label("a", text="x", position=(0, 0))
    base = ui.layout
    once = apply_overlay(base, OVERLAY, 2)
    twice = apply_overlay(once, OVERLAY, 2)
    assert once == twice
    assert _find(once, "strip")["accentColor"] == "#FF0000"
    with Layout("N", id="n") as plain:
        pass
    assert apply_overlay(plain.layout, OVERLAY, 1) == plain.layout


# ── hub write-back ───────────────────────────────────────────────────────────

class _Sock:
    def __init__(self):
        self.sent = []

    def on(self, t, f):
        pass

    async def send(self, t, payload=None, reply_to=None):
        self.sent.append((t, payload))

    async def request(self, t, payload=None, timeout=5.0):
        self.sent.append(("REQ:" + t, payload))

    async def start(self):
        pass

    async def wait_until_ready(self):
        pass

    async def stop(self):
        pass


def _hub(tmp_path):
    with Layout("EQ", id="eq", cols=4, rows=4) as ui:
        ui.customize("look", save=True)
        with ui.group("S", id="strip", span=(2, 4), cols=4, rows=2):
            ui.label("a", text="x", position=(0, 0))
    hub = Hub(ui.layout)
    hub.customize_store(tmp_path / "o.json")
    return hub, ui


def _save_msg(rev=1):
    return {"msg_type": "customize_save", "layout": "eq", "rev": rev, "overlay": OVERLAY}


def test_save_is_stored_and_acked_and_applied(tmp_path):
    hub, _ = _hub(tmp_path)
    acks = []

    async def fake_broadcast(t, payload=None, *a, **k):
        acks.append((t, payload))
    hub.broadcast = fake_broadcast
    assert asyncio.run(hub._dispatch(_save_msg(4))) is True
    assert acks == [("customize_ack", {"layout": "eq", "rev": 4})]
    assert json.loads((tmp_path / "o.json").read_text())["rev"] == 4
    out = hub.with_overlay(hub.layout)
    assert _find(out, "strip").get("accentColor") == "#FF0000" or out != hub.layout
    # adopt_layout applies the held overlay as well
    hub.adopt_layout(hub.layout)
    assert _find(hub.layout, "strip").get("accentColor") == "#FF0000"


def test_save_ignored_when_layout_does_not_opt_in(tmp_path):
    with Layout("EQ", id="eq") as ui:
        pass
    hub = Hub(ui.layout)
    hub.customize_store(tmp_path / "o.json")
    assert asyncio.run(hub._on_customize_save(_save_msg())) is False
    assert not (tmp_path / "o.json").exists()


def test_on_customize_replaces_default_store(tmp_path):
    hub, _ = _hub(tmp_path)
    seen = []

    @hub.on_customize
    async def take(overlay, lid, rev):
        seen.append((lid, rev))
        return None

    async def fake_broadcast(*a, **k):
        pass
    hub.broadcast = fake_broadcast
    assert asyncio.run(hub._on_customize_save(_save_msg(7))) is True
    assert seen == [("eq", 7)]
    assert not (tmp_path / "o.json").exists()


# ── examples validate clean ──────────────────────────────────────────────────

@pytest.mark.parametrize("name", ["eq_strip", "paged_cards"])
def test_examples_validate(name):
    sys.path.insert(0, str(ROOT / "examples"))
    try:
        mod = importlib.import_module(name)
    finally:
        sys.path.pop(0)
    assert _errors(mod.ui.layout) == []
