from carterkit import peer_caps
from carterkit.validate import capabilities_manifest

caps = capabilities_manifest()["capabilities"]
NEXT = next(k for k, v in caps.items() if v["since"] == "next" and "." in k
            and not k.startswith("control.") and k.count(".") == 1)
OLD = next(k for k, v in caps.items() if v["since"] == "2.0" and k.count(".") == 1
           and not k.startswith("control."))


def test_next_unsupported_released_supported():
    assert not peer_caps.field_supported(NEXT, "9.9")
    assert peer_caps.field_supported(OLD, "2.0")
    assert not peer_caps.field_supported(OLD, "1.9")
    assert peer_caps.field_supported(NEXT, None)


def test_filter_layout_drops_newer_fields():
    t, f = NEXT.split(".", 1)
    o = OLD.split(".", 1)[1]
    ot = OLD.split(".", 1)[0]
    layout = {"tabs": [{"children": [{"type": t, "id": "a", f: 1}, {"type": ot, "id": "b", o: 1}]}]}
    out, dropped = peer_caps.filter_layout(layout, "2.0")
    assert NEXT in dropped and f not in out["tabs"][0]["children"][0]
    assert f in layout["tabs"][0]["children"][0]
    same, none = peer_caps.filter_layout(layout, None)
    assert same is layout and none == []
    same, none = peer_caps.filter_layout(layout, "2.0", capabilities_manifest()["hash"])
    assert none == []
