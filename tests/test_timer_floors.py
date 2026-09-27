"""Timer floors mirror the app's LayoutSanitizer (carter-ml2 / carter-n1u, kit fix in 0.13.0):
carousel autoAdvance 0 and web webRefreshInterval 0 mean "off", joystick sendRate is an event
throttle (documented 0.1), and sensor publishers[].interval has its own 0.05 s floor."""
import carterkit


def _layout(child: dict, extra_root: dict | None = None) -> dict:
    root = {
        "name": "timers", "version": 1,
        "tabs": [{"title": "T", "icon": "star", "grid": {"columns": 4, "rows": 4},
                  "children": [child]}],
    }
    root.update(extra_root or {})
    return root


def _timer_errors(layout: dict) -> list[dict]:
    return [f for f in carterkit.validate_layout(layout) if f["kind"] == "bad_timer"]


def test_autoadvance_zero_is_off_not_an_error():
    child = {"type": "carousel", "id": "c", "position": [0, 0], "span": [2, 4],
             "autoAdvance": 0, "items": [{"title": "a"}, {"title": "b"}]}
    assert _timer_errors(_layout(child)) == []


def test_autoadvance_below_floor_still_rejected():
    child = {"type": "carousel", "id": "c", "position": [0, 0], "span": [2, 4],
             "autoAdvance": 0.1, "items": [{"title": "a"}, {"title": "b"}]}
    assert [f["where"] for f in _timer_errors(_layout(child))] == ["root.tabs[0].children[0].autoAdvance"]


def test_joystick_documented_send_rate_passes():
    child = {"type": "joystick", "id": "j", "position": [0, 0], "span": [2, 2], "sendRate": 0.1}
    assert _timer_errors(_layout(child)) == []


def test_publisher_interval_has_its_own_floor():
    child = {"type": "label", "id": "l", "position": [0, 0], "span": [1, 2]}
    ok = _layout(child, {"publishers": [{"sensor": "accelerometer", "interval": 0.1}]})
    bad = _layout(child, {"publishers": [{"sensor": "accelerometer", "interval": 0.01}]})
    assert _timer_errors(ok) == []
    assert [f["where"] for f in _timer_errors(bad)] == ["root.publishers[0].interval"]
