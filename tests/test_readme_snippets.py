"""Every python block in README.md and docs/*.md parses, and every carterkit
attribute it references exists in the package."""
import ast
import re
from pathlib import Path

import pytest

import carterkit

ROOT = Path(__file__).resolve().parent.parent
FILES = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
FENCE = re.compile(r"^```python[^\n]*\n(.*?)^```", re.S | re.M)


def _gen():
    for f in FILES:
        for i, m in enumerate(FENCE.finditer(f.read_text(encoding="utf-8"))):
            yield pytest.param(m.group(1), id=f"{f.name}#{i}")


def _refs(tree):
    """(module, name) pairs for `from carterkit[.sub] import name` and
    `carterkit.attr[.attr]` chains."""
    import importlib
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.split(".")[0] == "carterkit":
            out += [(n.module, a.name) for a in n.names]
        elif isinstance(n, ast.Import):
            out += [(a.name, None) for a in n.names if a.name.split(".")[0] == "carterkit"]
        elif isinstance(n, ast.Attribute):
            chain = []
            cur = n
            while isinstance(cur, ast.Attribute):
                chain.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name) and cur.id == "carterkit":
                out.append(("carterkit", chain[-1]))
    return out


@pytest.mark.parametrize("src", list(_gen()))
def test_snippet_parses_and_names_exist(src):
    import importlib
    tree = ast.parse(src)
    for module, name in _refs(tree):
        mod = importlib.import_module(module)
        if name is not None:
            assert hasattr(mod, name) or _is_submodule(module, name), \
                f"{module}.{name} does not exist"


def _is_submodule(module, name):
    import importlib
    try:
        importlib.import_module(f"{module}.{name}")
        return True
    except ImportError:
        return False


def test_blocks_found():
    assert len(list(_gen())) >= 8


def test_no_stale_wording():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Add Device" not in text
