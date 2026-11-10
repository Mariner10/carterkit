"""carterkit/schema.json: committed file is fresh, and real layouts validate against it."""

import glob
import json
import os
from pathlib import Path

import pytest

from carterkit import layout_schema

_WS = Path(os.environ.get("CARTER_WORKSPACE", "/nas/home/Atlas/projects/CAR-TER-workspace"))
_ROOT = Path(__file__).resolve().parents[2]


def test_committed_schema_is_fresh():
    assert layout_schema.SCHEMA_PATH.read_text() == layout_schema.render(), \
        "stale: run python3 -m carterkit.layout_schema"


def test_schema_is_2020_12_and_valid():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(layout_schema.SCHEMA_PATH.read_text())
    assert schema["$schema"].endswith("2020-12/schema")
    jsonschema.Draft202012Validator.check_schema(schema)


def _corpus(*parts):
    out = []
    for base in (_WS, _ROOT):
        out += glob.glob(str(base.joinpath(*parts)))
    return sorted(set(out))


def _files():
    return (_corpus("layout-library", "*", "*.json")
            + _corpus("CAR-TER", "CAR-TER", "SampleLayouts", "*.json")
            + _corpus("SampleLayouts", "*.json"))


def test_sample_layouts_and_library_validate():
    jsonschema = pytest.importorskip("jsonschema")
    files = [f for f in _files() if os.path.basename(f) != "index.json"]
    if not files:
        pytest.skip("no SampleLayouts / layout-library adjacent")
    v = jsonschema.Draft202012Validator(json.loads(layout_schema.SCHEMA_PATH.read_text()))
    bad = {}
    for f in files:
        doc = json.loads(Path(f).read_text())
        if isinstance(doc, dict) and "tabs" in doc:
            errs = [e.message[:120] for e in v.iter_errors(doc)]
            if errs:
                bad[os.path.basename(f)] = errs[:2]
    assert not bad, bad
