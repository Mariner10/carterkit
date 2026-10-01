"""Golden fixtures + property checks for carterkit.wire (the sync matching
reference the app's D1 refactor also runs)."""

import json
import pathlib

import pytest

from carterkit import wire
from carterkit.wire import ABSENT

FIXTURES = sorted((pathlib.Path(__file__).parent / "fixtures" / "wire").glob("*.json"))


def _load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def test_fixture_count_and_names_unique():
    assert len(FIXTURES) >= 20
    names = [_load(p)["name"] for p in FIXTURES]
    assert len(set(names)) == len(names)
    for p, n in zip(FIXTURES, names):
        assert p.stem.split("-", 1)[1] == n


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_golden(path):
    case = _load(path)
    exp = case["expect"]
    sync = {k: case[k] for k in ("filter", "valuePath") if k in case}
    out = wire.evaluate(case["frame"], sync)
    assert out.kind == exp["outcome"]
    if "value" in exp:
        assert wire.json_equal(out.value, exp["value"])
        assert isinstance(out.value, bool) == isinstance(exp["value"], bool)
    if "near" in exp:
        assert out.near is exp["near"]
    if "filterMisses" in exp:
        got = [(m.key, m.near, m.actual is not ABSENT) for m in out.filter_misses]
        want = [(m["key"], m["near"], m["present"]) for m in exp["filterMisses"]]
        assert got == want
        for m, w in zip(out.filter_misses, exp["filterMisses"]):
            assert wire.json_equal(m.expected, w["expected"])
            if w["present"]:
                assert wire.json_equal(m.actual, w["actual"])
    if "pathMiss" in exp:
        pm = exp["pathMiss"]
        assert out.path_miss == wire.PathMiss(pm["segment"], pm["index"], pm["reason"])
    if "typeMiss" in exp:
        assert out.type_miss == wire.TypeMiss(exp["typeMiss"])
    if "logSource" in exp:
        assert wire.json_equal(wire.log_source(case["frame"], case.get("valuePath")),
                               exp["logSource"])


# --- equality: the app's JSONValue, not Python's ==

@pytest.mark.parametrize("a,b,eq", [
    (True, 1, False), (False, 0, False), (1, True, False), (1, 1.0, True),
    (0, -0.0, True), ("1", 1, False), (None, None, True), (None, False, False),
    ([1, True], [1.0, True], True), ([True], [1], False),
    ({"a": 1}, {"a": 1.0}, True), ({"a": 1}, {"a": 1, "b": 2}, False),
    ({"a": True}, {"a": 1}, False), ([], {}, False), (10 ** 400, 10 ** 400, True),
])
def test_json_equal(a, b, eq):
    assert wire.json_equal(a, b) is eq
    assert wire.json_equal(b, a) is eq


def test_true_never_matches_one_in_filter():
    assert wire.match({"x": 1}, {"x": True})
    assert wire.match({"x": True}, {"x": 1})
    assert wire.match({"x": 1.0}, {"x": 1}) == ()


# --- walking

def test_segments_drop_empties():
    assert wire.path_segments("a..b") == ["a", "b"]
    assert wire.path_segments(".a.") == ["a"]
    assert wire.path_segments("") == wire.path_segments(None) == []


@pytest.mark.parametrize("seg,ok", [
    ("0", True), ("+1", True), ("-0", True), ("-1", False), (" 1", False),
    ("1 ", False), ("1_0", False), ("١", False), ("0x1", False), ("1e0", False),
    ("+", False), ("9223372036854775807", False),
])
def test_index_parsing(seg, ok):
    w = wire.walk([5, 6], seg)
    assert w.ok is ok


def test_walk_reports_failing_segment_position():
    w = wire.walk({"a": {"b": [1]}}, "a..b.3")
    assert w.miss == wire.PathMiss("3", 2, "out_of_range")


def test_scalar():
    assert wire.scalar(True) is True
    assert wire.scalar(0) == 0 and wire.scalar("") == ""
    assert wire.scalar(None) == wire.TypeMiss("null")
    assert wire.scalar({}) == wire.TypeMiss("object")
    assert wire.scalar([]) == wire.TypeMiss("array")


def test_require_scalar_false_delivers_containers():
    out = wire.evaluate({"rows": [{"a": 1}]}, {"valuePath": "rows"}, require_scalar=False)
    assert out.delivered and out.value == [{"a": 1}]


# --- near misses

@pytest.mark.parametrize("a,b,near", [
    ("telemetry", "telemetery", True), ("telemetry", "telemtry", True),
    ("telemetry", "telemetry", False), ("telemetry", "weather", False),
    ("ab", "ba", True), ("abc", "xyz", False), ("a", 1, False),
])
def test_near_miss_msg_type(a, b, near):
    assert wire.near_miss_msg_type(a, b) is near


def test_levenshtein():
    assert wire.levenshtein("kitten", "sitting") == 3
    assert wire.levenshtein("", "abc") == 3


# --- frame_for round-trips through evaluate

SYNCS = [
    {"valuePath": "cpu"},
    {"filter": {"msg_type": "telemetry"}, "valuePath": "sys.cpu"},
    {"filter": {"msg_type": "t", "room": {"id": 1}}, "valuePath": ".a..b."},
    {"filter": {"on": True}, "valuePath": "x"},
]


@pytest.mark.parametrize("sync", SYNCS)
@pytest.mark.parametrize("value", [0, 1.5, True, "s"])
def test_frame_for_delivers(sync, value):
    frame = wire.frame_for(sync, value)
    out = wire.evaluate(frame, sync)
    assert out.delivered
    assert wire.json_equal(out.value, value) and type(out.value) is type(value)


def test_frame_for_whole_frame_needs_dict():
    assert wire.frame_for({"filter": {"k": 1}}, {"v": 2}) == {"k": 1, "v": 2}
    with pytest.raises(ValueError):
        wire.frame_for({}, 3)


def test_frame_for_does_not_alias_filter():
    sync = {"filter": {"src": {"id": 1}}, "valuePath": "v"}
    frame = wire.frame_for(sync, 1)
    frame["src"]["id"] = 2
    assert sync["filter"]["src"]["id"] == 1


def test_frozen():
    with pytest.raises(Exception):
        wire.PathMiss("a", 0, "missing_key").segment = "b"
