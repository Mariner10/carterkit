"""Inspector tab coverage (carter-k6ir, mirrors the app's carter-m7s.17).

Every ControlDocs field carries a `tab` (content|style|data|action|advanced): the
doc's authored `tab:` or its group default, resolved exactly as the app's
`InspectorTab.resolve` does, and the compact catalog (catalog.json / the MCP)
exposes it.
"""

import re
from pathlib import Path

from carterkit import catalog

DOCS = Path(__file__).parent.parent / "carterkit" / "controldocs"


def _all_fields(docs):
    for node_id, doc in docs.items():
        for f in doc["fields"]:
            yield node_id, "fields", f
        for f in doc["themeFields"]:
            yield node_id, "themeFields", f


def test_every_field_has_a_known_tab():
    missing = [f"{n}.{f['name']}" for n, _, f in _all_fields(catalog.parse_all(DOCS))
               if f.get("tab") not in catalog.INSPECTOR_TABS]
    assert not missing, f"fields without a valid tab: {missing[:20]}"


def test_authored_tab_values_are_inspector_tabs():
    # The coverage lint: a typo'd `tab:` silently falls back to the group default,
    # so catch it in the source (the app's ControlDocLoader.unknownTabFields()).
    bad = []
    for path in sorted(DOCS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        front = text.split("\n---", 1)[0]
        for m in re.finditer(r"^\s+tab:\s*(\S+)\s*$", front, re.M):
            if m.group(1).strip("\"'").lower() not in catalog.INSPECTOR_TABS:
                bad.append(f"{path.stem}={m.group(1)}")
    assert not bad, f"unknown tab: values: {bad}"


def test_docs_actually_author_tabs():
    authored = sum(
        len(re.findall(r"^\s+tab:", p.read_text(encoding="utf-8").split("\n---", 1)[0], re.M))
        for p in DOCS.glob("*.md"))
    assert authored > 100  # m7s.17 tagged ~230 fields; guards a stale vendored copy


def test_wiring_keys_pinned_to_advanced():
    for _, _, f in _all_fields(catalog.parse_all(DOCS)):
        if f["name"] in catalog.ADVANCED_ONLY_KEYS:
            assert f["tab"] == "advanced", f
    assert catalog.resolve_tab("valuePath", None, "content") == "advanced"
    assert catalog.resolve_tab("id", "theme", "style") == "advanced"


def test_group_defaults_and_authored_override():
    assert catalog.resolve_tab("tint", "theme", None) == "style"
    assert catalog.resolve_tab("label", None, None) == "content"
    assert catalog.resolve_tab("label", None, "Data") == "data"
    assert catalog.resolve_tab("label", "theme", "bogus") == "style"
    assert catalog.resolve_tab("label", "chartConfig", "bogus") == "content"


def test_parse_doc_resolves_theme_and_authored():
    doc = catalog.parse_doc(
        "---\ntype: demo\nlabel: Demo\ncategory: display\nfields:\n"
        "  - name: label\n    type: string\n"
        "  - name: sweep\n    type: number\n    tab: style\n"
        "  - name: valuePath\n    type: string\n    tab: data\n"
        "themeFields:\n  - name: accentColor\n    type: color\n"
        "  - name: fontSize\n    type: number\n    tab: content\n---\nbody\n", "demo")
    tabs = {f["name"]: f["tab"] for f in doc["fields"] + doc["themeFields"]}
    assert tabs == {"label": "content", "sweep": "style", "valuePath": "advanced",
                    "accentColor": "style", "fontSize": "content"}


def test_compact_catalog_carries_tab():
    cat = catalog.build_catalog(DOCS, include_theme=True)
    gauge = cat["gauge"]
    assert all("tab" in f for f in gauge["fields"] + gauge.get("themeFields", []))
    assert {f["tab"] for c in cat.values() for f in c.get("fields", [])} >= {
        "content", "style", "advanced"}
