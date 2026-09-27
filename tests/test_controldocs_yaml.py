"""Every vendored ControlDoc's frontmatter is valid YAML (carter-3825).

The app, carterkit and build-docs-site read frontmatter with their own line parsers
(which strip only double quotes), but external tools read it as YAML, so a value that
YAML rejects is a doc bug: double-quote it, inner double quotes become single ones."""
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

DOCS = sorted((Path(__file__).resolve().parents[1] / "carterkit" / "controldocs").glob("*.md"))


@pytest.mark.parametrize("path", DOCS, ids=[p.stem for p in DOCS])
def test_frontmatter_is_yaml(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return
    front = text.split("---", 2)[1]
    yaml.safe_load(front)
    for line in front.splitlines():
        value = line.split("description:", 1)[1].strip() if "description:" in line else ""
        assert not (value.startswith("'") and value.endswith("'")), \
            f"{path.name}: single-quoted description shows its quotes in every loader: {value[:60]}"
