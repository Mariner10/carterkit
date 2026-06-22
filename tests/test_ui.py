"""Tests for the flat builder: handles, sugar bindings, dynamic groups, fragments."""

from carterkit import Layout, Fragment, Condition


def _child(layout, cid):
    for tab in layout["tabs"]:
        for ch in tab.get("children", []):
            if ch.get("id") == cid:
                return ch
    raise AssertionError(f"no top-level child {cid!r}")


def test_flat_with_blocks_and_sugar():
    with Layout("Bench", cols=4, rows=4) as ui:
        ui.connect("ws://h:8765", channel="lab")
        with ui.tab("Main", icon="gauge"):
            cpu = ui.gauge("cpu", label="CPU", min=0, max=100, span=(2, 2),
                           listen="cpu", when={"msg_type": "metrics"})
            ui.button("refresh", label="Refresh", send="refresh", request=True)

    lay = ui.layout
    assert lay["connection"]["url"] == "ws://h:8765"
    t0 = lay["tabs"][0]
    assert t0["title"] == "Main" and t0["icon"] == "gauge"
    assert cpu.id == "cpu"
    g = _child(lay, "cpu")
    assert g["span"] == [2, 2] and g["position"] == [0, 0]
    s = g["sync"][0]
    assert s["type"] == "listen" and s["valuePath"] == "cpu"
    assert s["filter"] == {"msg_type": "metrics"}
    b = _child(lay, "refresh")
    assert b["action"]["event"] == "refresh" and b["action"]["mode"] == "request"


def test_handle_visibility_condition():
    with Layout("X", cols=4, rows=4) as ui:
        cpu = ui.gauge("cpu", min=0, max=100, listen="cpu")
        warn = ui.status_light("warn", visible=cpu > 90)
    cond = _child(ui.layout, "warn")["visible"]
    assert cond == {"when": "cpu", "operator": "gt", "value": 90}
    # equality helpers and the Condition type
    assert isinstance(cpu.eq("hi"), Condition)
    assert cpu.eq(1).to_dict()["operator"] == "eq"
    # `==` stays normal Python (handles aren't conditions)
    assert (cpu == warn) is False


def test_dynamic_generation_in_group():
    with Layout("Rig", cols=4, rows=6) as ui:
        with ui.tab("Motors"):
            with ui.group("Bank", span=(4, 2)) as bank:
                for i in range(4):
                    bank.slider(f"m{i}", min=0, max=255)
    grp = _child(ui.layout, "group")
    assert grp["type"] == "group" and grp["label"] == "Bank"
    ids = [c["id"] for c in grp["children"]]
    assert ids == ["m0", "m1", "m2", "m3"]
    # auto-placed down the group's own 4x4 sub-grid, no overlaps
    positions = [tuple(c["position"]) for c in grp["children"]]
    assert len(set(positions)) == 4


def test_runtime_dynamic_group_and_fragment_payload():
    with Layout("Player", cols=4, rows=4) as ui:
        ui.group("Now Playing", span=(3, 4), dynamic="player_state")
    grp = _child(ui.layout, "group")
    assert grp["dynamic"] == "player_state" and grp["children"] == []

    frag = Fragment(cols=4, rows=3)
    frag.label("title", text="Song", span=(1, 4))
    for t in ("a", "b"):
        frag.button(f"play-{t}", label=t, send="play", payload={"id": t})
    payload = frag.payload("player_state")
    assert payload["msg_type"] == "player_state"
    assert [c["id"] for c in payload["children"]] == ["title", "play-a", "play-b"]
    assert payload["children"][1]["action"]["payload"] == {"id": "a"}


def test_global_id_dedup_across_group_and_tab():
    with Layout("X", cols=4, rows=6) as ui:
        ui.button("go")
        with ui.group("G") as g:
            g.button("go")          # collides -> deduped
    grp = _child(ui.layout, "group")
    assert grp["children"][0]["id"] == "go-2"


def test_validate_clean_on_flat_layout():
    with Layout("X", cols=4, rows=4) as ui:
        ui.gauge("g", min=0, max=100, listen="g", span=(2, 2))
    assert [f for f in ui.validate() if f["severity"] == "error"] == []
