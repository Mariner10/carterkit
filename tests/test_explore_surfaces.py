import json
import socket
import urllib.request

from carterkit.explore import SURFACE_SIZES, surfaces_preview

LAYOUT = {
    "name": "S",
    "tabs": [{"title": "Main", "children": [
        {"type": "gauge", "id": "cpu", "label": "CPU", "min": 0, "max": 200},
        {"type": "toggle", "id": "lamp", "label": "Lamp"},
    ]}],
    "glance": {
        "widgets": [{"id": "w", "title": "Temps", "scene": {"rows": [
            [{"tile": "gauge", "control": "cpu"}, {"tile": "gauge", "control": "ghost"}],
            [{"tile": "light", "control": "lamp"}]]}}],
        "island": {"compactLeading": {"tile": "icon"},
                   "compactTrailing": {"tile": "ring", "control": "cpu"},
                   "expanded": {"leading": {"tile": "icon"}, "bottom": {"rows": [[{"tile": "value", "control": "cpu"}]]}}},
    },
}


def test_hint_without_surfaces():
    r = surfaces_preview({"name": "x", "tabs": []})
    assert r["surfaces"] == [] and "no surfaces" in r["hint"]


def test_surfaces_listed_with_real_sizes_and_sample_values():
    r = surfaces_preview(LAYOUT)
    by = {s["name"]: s for s in r["surfaces"]}
    assert set(by) == {"systemSmall", "systemMedium", "systemLarge", "compactLeading",
                       "compactTrailing", "expanded", "lockScreen"}
    for n, s in by.items():
        assert (s["width"], s["height"]) == SURFACE_SIZES[n]
    small = by["systemSmall"]["rows"]
    assert len(small) == 1                       # small = first row only
    assert [t["control"] for t in small[0]] == ["cpu"]   # unknown id dropped
    assert small[0][0]["value"] == 100 and small[0][0]["sample"] is True
    assert len(by["systemMedium"]["rows"]) == 2
    assert by["lockScreen"]["rows"][0][0]["control"] == "cpu"  # defaults to expanded.bottom


def test_known_value_beats_sample():
    r = surfaces_preview(LAYOUT, {"cpu": 42})
    t = r["surfaces"][0]["rows"][0][0]
    assert t["value"] == 42 and t["sample"] is False


def test_page_serves_surfaces():
    from carterkit.explore import Explorer
    from carterkit.hub import Hub
    import threading
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    hub = Hub.__new__(Hub)
    hub.layout = LAYOUT
    ex = Explorer.__new__(Explorer)
    ex.hub, ex.port, ex.control_values, ex._subs = hub, port, {}, []
    ex.token = "t"
    ex.start_http()
    get = lambda p: urllib.request.urlopen(f"http://127.0.0.1:{port}{p}", timeout=5).read()
    assert len(json.loads(get("/api/surfaces"))["surfaces"]) == 7
    assert b"sf-box" in get("/assets/surfaces.js")
    assert b"sec-surfaces" in get("/")
    ex._httpd.shutdown()
