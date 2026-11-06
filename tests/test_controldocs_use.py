"""`- use:` shared fields (app bead aif-fa4jj): catalog.parse_doc expands them like the app.

A field many docs share lives once in controldocs/shared-fields.md; a doc's `fields:` /
`themeFields:` entry says `- use: <name>` plus optional overrides. The app's
ControlDocLoader.FieldReader and this parser must expand it the same way.
"""
from carterkit import catalog, controldocs_dir

SHARED = """---
kind: shared-fields
fields:
  - name: confirm
    title: Show confirmation
    type: bool
    default: false
    summary: A short note with Undo
    does: Shows an Undo pill.
themeFields:
  - name: borderWidth
    type: number
    min: 0
    max: 5
    default: 1
    summary: How thick the outline is
    does: Sets the outline width.
---
"""


def probe(fields: str, theme: str = "") -> str:
    return f"---\ntype: probe\nlabel: Probe\ncategory: controls\nfields:\n{fields}\nthemeFields:\n{theme}\n---\nbody"


def test_use_expands_to_the_shared_entry_with_its_overrides():
    shared = catalog.parse_shared(SHARED)
    doc = catalog.parse_doc(probe("  - use: confirm\n    does: Other.", "  - use: borderWidth\n    max: 8"),
                            "probe", shared)
    assert "useErrors" not in doc
    assert doc["fields"] == [{"name": "confirm", "type": "bool", "default": "false", "title": "Show confirmation",
                              "summary": "A short note with Undo", "does": "Other."}]
    written = catalog.parse_doc(probe(
        "  - name: confirm\n    title: Show confirmation\n    type: bool\n    default: false\n"
        "    summary: A short note with Undo\n    does: Other."), "probe", {})
    assert doc["fields"] == written["fields"]
    assert doc["themeFields"] == [{"name": "borderWidth", "type": "number", "default": "1",
                                   "summary": "How thick the outline is", "does": "Sets the outline width."}]


def test_unknown_or_wrong_section_names_are_errors_and_leave_the_field_out():
    shared = catalog.parse_shared(SHARED)
    doc = catalog.parse_doc(probe("  - use: nope\n  - use: borderWidth\n  - name: kept\n    type: string"),
                            "probe", shared)
    assert [f["name"] for f in doc["fields"]] == ["kept"]
    assert len(doc["useErrors"]) == 2
    assert any("use: borderWidth" in e and "themeFields" in e for e in doc["useErrors"])


def test_only_whitelisted_overrides_are_allowed():
    shared = catalog.parse_shared(SHARED)
    doc = catalog.parse_doc(probe("  - use: confirm\n    type: x\n    default: false"), "probe", shared)
    assert any("overrides `type`" in e for e in doc["useErrors"])
    assert any("`default` repeats the shared value" in e for e in doc["useErrors"])
    assert catalog.USE_OVERRIDES == ("default", "min", "max", "step", "does", "since", "summary")


def test_parse_doc_defaults_to_the_bundled_shared_fields():
    shared = catalog.load_shared(controldocs_dir())
    assert shared["themeFields"], "the vendored shared-fields.md has no theme entries"
    name = next(iter(shared["themeFields"]))
    doc = catalog.parse_doc(probe("", f"  - use: {name}"), "probe")
    assert "useErrors" not in doc
    assert doc["themeFields"] == [catalog._make_field(shared["themeFields"][name])]


def test_vendored_docs_use_lines_resolve_and_shared_fields_is_no_control():
    assert catalog.use_errors(controldocs_dir()) == []
    text = (controldocs_dir() / catalog.SHARED_DOC).read_text()
    assert catalog.parse_doc(text, "shared-fields") is None
    assert "shared-fields" not in catalog.parse_all(controldocs_dir())
    docs = catalog.parse_all(controldocs_dir())
    assert any("- use:" in (controldocs_dir() / f"{k}.md").read_text() for k in docs), "no doc uses a shared field"


def test_summary_override_is_allowed_and_lints_equal_values():
    shared = catalog.parse_shared(SHARED)
    doc = catalog.parse_doc(probe("  - use: confirm\n    summary: Mine"), "probe", shared)
    assert doc["useErrors"] == []
    assert doc["fields"][0]["summary"] == "Mine"
    same = catalog.parse_doc(probe("  - use: confirm\n    summary: A short note with Undo"), "probe", shared)
    assert any("override `summary` repeats the shared value" in e for e in same["useErrors"])
