"""carterkit.derive: the reference evaluator against the shared fixtures.

The fixture files are byte-identical copies of the app's
CAR-TERTests/Fixtures/derive/ (DeriveFixtureTests.swift runs the same cases), so a
pass here and there means Python and Swift compute the same numbers.
"""
import json
import math
from pathlib import Path

import pytest

from carterkit import derive

FIXTURES = Path(__file__).parent / "fixtures" / "derive"


def _cases(pattern):
    out = []
    for path in sorted(FIXTURES.glob(pattern)):
        for case in json.loads(path.read_text())["cases"]:
            out.append(pytest.param(case, id=f"{path.stem}:{case['name']}"))
    return out


def _same(got, want):
    if want is None or got is None:
        return got is None and want is None
    if isinstance(want, str) or isinstance(got, str):
        return got == want
    if isinstance(want, bool) or isinstance(got, bool):
        return got == want
    return math.isclose(got, want, rel_tol=1e-9, abs_tol=1e-9)


def test_fixtures_exist():
    names = sorted(p.name for p in FIXTURES.iterdir())
    assert "derive-problems.json" in names and len([n for n in names if n.startswith("derive-eval-")]) >= 4


@pytest.mark.parametrize("case", _cases("derive-eval-*.json"))
def test_eval_fixture(case):
    got = derive.evaluate(case["derive"], case["inputs"], now=case["now"])
    assert set(got) == set(case["expected"]), f"evaluated {sorted(got)}"
    for key, want in case["expected"].items():
        assert _same(got[key], want), f"{key}: got {got[key]!r}, want {want!r}"


@pytest.mark.parametrize("case", _cases("derive-problems.json"))
def test_problems_fixture(case):
    got = derive.problems(case["derive"], case["controls"], case["consumers"])
    assert [list(p) for p in got] == case["problems"]


def test_parse_round_trips_raw_and_flags_unknown_ops():
    assert derive.invalid_paths({"w": {"add": [{"frobnicate": [1]}, 1]}}) == [
        ("w", "/0", {"frobnicate": [1]})]
    assert derive.invalid_paths({"w": {"mul": [{"control": "v"}, 2]}}) == []
    assert derive.parse({"clamp": {"of": 1, "min": 0}}).raw == {"clamp": {"of": 1, "min": 0}}


def test_consumers_walk_panels_and_canvas():
    layout = {"tabs": [{"children": [
        {"type": "group", "children": [
            {"type": "gauge", "id": "g", "sync": [{"method": "derive", "from": "w"}]}]},
        {"type": "carousel", "id": "c", "panels": [{"children": [
            {"type": "label", "id": "l", "sync": [{"method": "derive", "from": "w"}]}]}]},
        {"type": "canvas", "id": "cv", "canvasConfig": {"items": [
            {"control": {"type": "label", "id": "ci", "sync": [{"method": "derive", "from": "kw"}]}}]}},
    ]}]}
    assert derive.consumers(layout) == {"w": ["g", "l"], "kw": ["ci"]}


def test_swift_double_parsing_rules():
    assert derive.to_number(" 12 ") == 12
    assert derive.to_number("1_000") is None       # Python float() would accept this
    assert derive.to_number("\n12") is None        # Swift trims spaces and tabs only
    assert derive.to_number("0x1A") == 26
    assert derive.to_number(True) == 1 and derive.to_number(False) == 0
    assert derive.to_number(None) is None


# ── validate / contract / codegen / builder (carter-bkm.5) ──

import carterkit
from carterkit import Layout, bind, codegen, contract
from carterkit.derive import ops


def _layout(derive_block, syncs):
    children = [{"type": "label", "id": "volts", "position": [0, 0]},
                {"type": "label", "id": "amps", "position": [0, 1]}]
    for i, (cid, sync) in enumerate(syncs):
        children.append({"type": "gauge", "id": cid, "position": [1 + i, 0], "sync": sync})
    lay = {"name": "x", "version": 1,
           "tabs": [{"title": "t", "icon": "bolt", "grid": {"columns": 2, "rows": 4}, "children": children}]}
    if derive_block is not None:
        lay["derive"] = derive_block
    return lay


def _findings(lay, kind=None):
    out = carterkit.validate_layout(lay)
    return [f for f in out if kind is None or f["kind"] == kind]


WATTS = {"watts": {"mul": [{"control": "volts"}, {"control": "amps"}]}}


def test_derive_sync_needs_no_value_path():
    lay = _layout(WATTS, [("w", [{"method": "derive", "from": "watts"}])])
    found = _findings(lay)
    assert not [f for f in found if "valuePath" in f["detail"]]
    assert not [f for f in found if f["severity"] == "error"], found
    assert not [f for f in found if "derive" in f["detail"] and f["kind"] == "unknown_field"]


def test_derive_sync_without_from_is_an_error():
    found = _findings(_layout(WATTS, [("w", [{"method": "derive"}])]), "bad_sync")
    assert found and found[0]["severity"] == "error"


def test_unknown_from_is_an_error():
    found = _findings(_layout(WATTS, [("w", [{"method": "derive", "from": "wats"}])]),
                      "unknown_derive_ref")
    assert found and found[0]["severity"] == "error" and "wats" in found[0]["detail"]
    found = _findings(_layout(None, [("w", [{"method": "derive", "from": "watts"}])]),
                      "unknown_derive_ref")
    assert found and "no 'derive' block" in found[0]["detail"]


def test_cycle_unknown_op_unknown_ref_and_collision_are_errors():
    block = {"a": {"add": [{"derive": "b"}, 1]}, "b": {"add": [{"derive": "a"}, 1]},
             "f": {"frobnicate": [1]}, "t": {"add": [{"control": "tmep2"}, 1]},
             "volts": {"add": [1, 1]}}
    found = _findings(_layout(block, []))
    kinds = {(f["kind"], f["where"]) for f in found if f["severity"] == "error"}
    assert ("derive_cycle", "derive.a") in kinds and ("derive_cycle", "derive.b") in kinds
    assert ("unknown_derive_op", "derive.f") in kinds
    assert ("unknown_derive_ref", "derive.t") in kinds
    assert ("duplicate_id", "derive.volts") in kinds


def test_cycle_through_a_binding_is_an_error():
    block = {"loop": {"add": [{"control": "w"}, 1]}}
    found = _findings(_layout(block, [("w", [{"method": "derive", "from": "loop"}])]), "derive_cycle")
    assert found


def test_malformed_node_and_hostile_nesting_are_errors():
    found = _findings(_layout({"b": {"band": {"of": 1, "stops": [2, 1], "labels": ["a", "b", "c"]}}}, []),
                      "bad_derive")
    assert found
    deep = 1
    for _ in range(3000):
        deep = {"abs": deep}
    found = _findings(_layout({"deep": deep}, []), "derive_limits")
    assert found


def test_contract_and_codegen_emit_no_event_for_derive_syncs():
    lay = _layout(WATTS, [("w", [{"method": "derive", "from": "watts", "valuePath": "x"}])])
    c = contract.extract_contract(lay)
    assert not [f for f in c["feeds"] if f["id"] == "w"]
    assert [a for a in c["appDirect"] if a["id"] == "w" and a["transport"] == "derive"]
    info = codegen.analyze_layout(lay)
    assert info["emits"] == {} and info["pushes"] == []
    assert "watts" not in codegen.generate_service_stub(lay)


def test_builder_round_trips_through_validate():
    with Layout("Power", cols=2, rows=3) as ui:
        with ui.tab("Main", icon="bolt"):
            volts = ui.label("volts", label="Volts", listen="v", when={"msg_type": "plug"})
            amps = ui.label("amps", label="Amps", listen="a", when={"msg_type": "plug"})
            watts = ui.derive("watts", ops.mul(volts, amps))
            kw = ui.derive("kw", ops.round(ops.div(watts, 1000), places=2))
            level = ui.derive("level", ops.band(watts, stops=[500, 1500], labels=["low", "ok", "high"]))
            ui.gauge("w", label="W", min=0, max=1800, sync=watts.sync)
            ui.label("kwl", label="kW", sync=[bind.derive(kw)])
            ui.label("lvl", label="Load", sync=[bind.derive("level")])
    lay = json.loads(ui.json())          # a real JSON round trip
    assert lay["derive"]["watts"] == {"mul": [{"control": "volts"}, {"control": "amps"}]}
    assert lay["derive"]["kw"] == {"round": {"of": {"div": [{"derive": "watts"}, 1000]}, "places": 2}}
    errors = [f for f in carterkit.validate_layout(lay) if f["severity"] in ("error", "warn")]
    assert not errors, errors
    assert carterkit.derive.evaluate(lay["derive"], {"volts": 120, "amps": 2.5}) == {
        "watts": 300.0, "kw": 0.3, "level": "low"}
    assert level.sync == [{"method": "derive", "from": "level"}]


def test_builders_reject_bad_shapes():
    with pytest.raises(ValueError):
        ops.add()
    with pytest.raises(ValueError):
        ops.clamp(1)
    with pytest.raises(ValueError):
        ops.band(1, stops=[1], labels=["a"])
    with pytest.raises(ValueError):
        ops.since(1, unit="fortnights")
    with pytest.raises(ValueError):
        bind.derive("")
