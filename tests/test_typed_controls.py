"""carterkit/typed.py is generated from the bundled ControlDocs; keep it fresh and wired."""
import importlib.util
import inspect
from pathlib import Path

import pytest

from carterkit import Layout, build
from carterkit.typed import BuildControls, ScopeControls

GEN = Path(__file__).resolve().parent.parent / "scripts" / "gen-typed-controls.py"


def _gen():
    spec = importlib.util.spec_from_file_location("gen_typed_controls", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.skipif(not GEN.exists(), reason="generator not shipped (installed package)")
def test_typed_py_is_fresh():
    gen = _gen()
    assert gen.OUT.read_text() == gen.generate(), \
        "ControlDocs changed: run python3 scripts/gen-typed-controls.py"


def test_static_methods_not_getattr():
    assert "gauge" in vars(ScopeControls) and "color_picker" in vars(ScopeControls)
    assert "gauge" in vars(BuildControls)
    assert inspect.signature(ScopeControls.gauge).parameters["gaugeStyle"].default is None


def test_layout_and_build_runtime_unchanged():
    ui = Layout("t")
    c = ui.gauge("cpu", min=0, max=100, gaugeStyle="full", custom_prop=1)
    assert c.ref["gaugeStyle"] == "full" and c.ref["custom_prop"] == 1 and c.id == "cpu"
    assert ui.color_picker("tint").ref["type"] == "colorPicker"
    assert build.gauge(id="g", min=1) == {"type": "gauge", "id": "g", "min": 1}
    with pytest.raises(ValueError):
        build.gauge(id="g", gaugeStyle="bogus")
