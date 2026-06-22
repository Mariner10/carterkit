"""Tests for controls.py — typed builders generated from the bundled catalog."""

import pytest

import carterkit
from carterkit import build, control


def test_build_gauge_returns_valid_control():
    g = build.gauge(id="cpu", min=0, max=100, position=[0, 0], span=[2, 2])
    assert g["type"] == "gauge" and g["id"] == "cpu"
    assert g["position"] == [0, 0] and g["span"] == [2, 2]
    assert g["min"] == 0 and g["max"] == 100


def test_snake_case_alias_maps_to_camel_type():
    assert build.color_picker(id="tint")["type"] == "colorPicker"
    assert build.status_light(id="s")["type"] == "statusLight"


def test_unknown_control_raises():
    with pytest.raises(AttributeError):
        build.frobnicator  # noqa: B018


def test_bad_enum_value_raises():
    with pytest.raises(ValueError):
        build.gauge(id="g", gaugeStyle="triangular")  # gaugeStyle is half|full


def test_good_enum_value_ok():
    assert build.gauge(id="g", gaugeStyle="full")["gaugeStyle"] == "full"


def test_control_factory_unknown_type():
    with pytest.raises(ValueError):
        control("nope", id="x")


def test_builder_doc_comes_from_controldocs():
    assert build.gauge.__doc__.startswith("# Gauge")


def test_types_listing_nonempty():
    types = build.types()
    assert "gauge" in types and "button" in types and "colorPicker" in types


def test_built_controls_validate_clean():
    b = carterkit.LayoutBuffer.blank(columns=4, rows=4)
    b.add_control(build.gauge(id="cpu", min=0, max=100), default_span=[2, 2])
    b.add_control(build.button(id="go", label="Go"))
    errs = [f for f in carterkit.validate_layout(b.layout) if f["severity"] == "error"]
    assert errs == [], errs
