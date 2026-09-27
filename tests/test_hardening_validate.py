import json
import math
import time
import pytest
import carterkit


def _layout(children, **top):
    return {"name": "x", "version": 1, **top,
            "tabs": [{"title": "t", "grid": {"columns": 4, "rows": 8}, "children": children}]}


def _kinds(layout):
    return {f["kind"] for f in carterkit.validate_layout(layout)}


def test_bad_span_type_is_a_finding_not_a_crash():
    lay = _layout([{"type": "gauge", "id": "g", "position": [0, 0], "span": [1, "wide"]}])
    assert "bad_span" in _kinds(lay)                     # ValueError today


def test_bad_grid_type_is_a_finding_not_a_crash():
    lay = _layout([])
    lay["tabs"][0]["grid"] = {"columns": "four"}
    assert "bad_grid" in _kinds(lay)                     # ValueError today


def test_non_finite_numbers_are_errors():
    lay = _layout([{"type": "gauge", "id": "g", "position": [0, 0],
                    "min": float("nan"), "max": float("inf")}])
    assert "non_finite" in _kinds(lay)                   # clean today; the phone cannot decode NaN


def test_huge_span_is_rejected_cheaply():
    lay = _layout([{"type": "gauge", "id": "g", "position": [0, 0], "span": [1500, 1500]}])
    t0 = time.perf_counter()
    kinds = _kinds(lay)
    assert time.perf_counter() - t0 < 0.2                # enumerates 2.25M cells today
    assert "out_of_bounds" in kinds


def test_embedded_credentials_are_flagged():
    lay = _layout([], connection={"url": "ws://h:1", "token": "eyJhY2N0.secret",
                                  "identity": {"name": "n", "channel": "c", "role": "controller"}},
                  sources={"broker": {"type": "mqtt", "url": "mqtt://b", "password": "hunter2"}})
    assert "embedded_secret" in _kinds(lay)


def test_dangerous_url_schemes_are_flagged():
    lay = _layout([
        {"type": "webView", "id": "w", "position": [0, 0], "url": "javascript:alert(1)"},
        {"type": "image", "id": "i", "position": [1, 0], "url": "file:///etc/passwd"},
    ])
    assert "bad_url" in _kinds(lay)


def test_deep_nesting_is_a_finding_not_a_recursion_error():
    inner = {"type": "gauge", "id": "g", "position": [0, 0]}
    for i in range(2000):
        inner = {"type": "group", "id": f"grp{i}", "position": [0, 0], "children": [inner]}
    assert "too_deep" in _kinds(_layout([inner]))        # RecursionError today


def test_absurd_control_count_warns():
    kids = [{"type": "label", "id": f"l{i}", "position": [0, 0], "text": "x"} for i in range(20000)]
    assert "too_many_controls" in _kinds(_layout(kids))


def _wrap(inner, kind, n):
    grid = {"columns": 1, "rows": 1}
    if kind == "group":
        return {"type": "group", "id": f"g{n}", "position": [0, 0], "grid": grid, "children": [inner]}
    if kind in ("carousel", "flipCard", "accordion"):
        return {"type": kind, "id": f"c{n}", "position": [0, 0],
                "panels": [{"id": f"p{n}", "position": [0, 0], "grid": grid, "children": [inner]}]}
    if kind == "longPressGroup":
        return {"type": "button", "id": f"b{n}", "position": [0, 0],
                "longPressGroup": {"id": f"l{n}", "position": [0, 0], "grid": grid, "children": [inner]}}
    return {"type": "canvas", "id": f"v{n}", "position": [0, 0],
            "canvasConfig": {"items": [{"id": f"i{n}", "control": inner}]}}


def _chain(kind, levels):
    node = {"type": "button", "id": "leaf", "position": [0, 0]}
    for n in range(levels):
        node = _wrap(node, kind, n)
    return _layout([node])


def _nests_too_deep(layout):
    # The nesting-limit finding itself; a 15-deep canvas also trips the separate generic
    # 64-level JSON cap (4 JSON levels per canvas), which is not what these pin.
    return any(f["kind"] == "too_deep" and "nest deeper than" in f["detail"]
               and "document" not in f["detail"] for f in carterkit.validate_layout(layout))


# Every container kind costs exactly one level, as in the app's sanitizer and renderer:
# MAX_DEPTH containers of any kind around a leaf are accepted, one more is refused.
@pytest.mark.parametrize("kind", ["group", "longPressGroup", "canvas", "carousel", "flipCard", "accordion"])
def test_every_container_kind_counts_toward_the_app_depth_limit(kind):
    from carterkit.validate import MAX_DEPTH
    assert not _nests_too_deep(_chain(kind, MAX_DEPTH))
    assert _nests_too_deep(_chain(kind, MAX_DEPTH + 1))


def test_thirty_deep_canvas_is_too_deep():
    assert _nests_too_deep(_chain("canvas", 30))            # uncounted before carter-7np
    assert _nests_too_deep(_chain("canvas", 3000))          # and never a RecursionError
