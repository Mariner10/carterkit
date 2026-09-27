"""carter-7vs — defaultValue per type (control-def.md#defaultValue per type).

The app accepts an array/object `defaultValue` as a seed on buffer and dataset controls
and drops it, with a repair note, anywhere else; the kit warns on the dropped cases.
"""
from pathlib import Path

import pytest

from carterkit import catalog, validate

DOCS = Path(__file__).resolve().parent.parent / "carterkit" / "controldocs"
CAT = catalog.build_catalog(DOCS, include_theme=True)


def _layout(control):
    control = {"id": "c", "position": [0, 0], **control}
    return {"name": "T", "version": 1,
            "tabs": [{"title": "A", "icon": "star", "grid": {"columns": 2, "rows": 2},
                      "children": [control]}]}


def _kinds(control):
    return [f for f in validate.validate_layout(_layout(control), CAT) if f["kind"] == "bad_default_value"]


@pytest.mark.parametrize("control", [
    {"type": "sparkline", "defaultValue": [41, 40, None, 39]},
    {"type": "sparkline", "defaultValue": 41},
    {"type": "list", "defaultValue": [{"name": "a"}]},
    {"type": "logConsole", "defaultValue": ["[info] up", {"text": "hot", "level": "warn"}]},
    {"type": "chart", "defaultValue": {"series": [{"values": [1, 2]}]}},
    {"type": "pieChart", "defaultValue": {"slices": [{"label": "A", "value": 1}]}},
    {"type": "gauge", "defaultValue": 42},
])
def test_supported_seeds_are_clean(control):
    assert _kinds(control) == []


@pytest.mark.parametrize("control", [
    {"type": "gauge", "defaultValue": [1, 2]},
    {"type": "toggle", "defaultValue": {"on": True}},
    {"type": "sparkline", "defaultValue": ["a", "b"]},
    {"type": "sparkline", "defaultValue": {"values": [1]}},
    {"type": "list", "defaultValue": [1, 2]},
    {"type": "chart", "defaultValue": {"series": [{"values": list(range(2000))}]}},
])
def test_dropped_seeds_warn(control):
    found = _kinds(control)
    assert found and all(f["severity"] == "warn" for f in found)
