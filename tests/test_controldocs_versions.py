"""ControlDocs version pins and the frontmatter schema (app bead aif-xd1w8.1).

Pins sit at the smallest level that changed: a doc, a field, an enum value. `baseline`
(absent = 2.0) covers everything unpinned; `since: next` marks an addition until the
release step stamps it. Mirrors CAR-TERTests/ControlDocVersionTests.swift."""
import json
from pathlib import Path

import pytest

from carterkit import catalog

DOCS_DIR = Path(catalog.__file__).resolve().parent / "controldocs"
SCHEMA = json.loads((DOCS_DIR / "controldocs.schema.json").read_text())
SHARED = catalog.load_shared(DOCS_DIR)
DOCS = sorted(DOCS_DIR.rglob("*.md"))


def probe(fields: str, top: str = "") -> str:
    return f"---\ntype: probe\nlabel: Probe\ncategory: controls\n{top}fields:\n{fields}\n---\nbody"


# ─── flow values ─────────────────────────────────────────────────────────────


def test_flow_reads_json_and_yaml_flow_alike():
    assert catalog.parse_flow('["a", "b"]') == ["a", "b"]
    assert catalog.parse_flow("[a, b]") == ["a", "b"]
    assert catalog.parse_flow('{"in": "2.1", "note": "x, y"}') == {"in": "2.1", "note": "x, y"}
    assert catalog.parse_flow("[a, { value: pill, since: next }]") == ["a", {"value": "pill", "since": "next"}]
    assert catalog.parse_flow('{"set": {"style": null, "n": 2}}') == {"set": {"style": "null", "n": "2"}}
    assert catalog.parse_flow('["say \\"hi\\"", \'it\']') == ['say "hi"', "it"]
    assert catalog.parse_flow("{note: Long press: repeats}") == {"note": "Long press: repeats"}


@pytest.mark.parametrize("bad", ["[a, b", "{a: 1", "[a] tail", '["a" b]', "{a}", "plain"])
def test_flow_refuses_malformed_text(bad):
    assert catalog.parse_flow(bad) is None


# ─── values: plain and pinned forms ──────────────────────────────────────────


INLINE = "  - name: style\n    type: enum\n    values: [filled, { value: pill, since: next }, {value: outline, deprecated: \"2.1\", alias: outlined}, outlined]"
BLOCK = ("  - name: style\n    type: enum\n    values:\n      - filled\n      - { value: pill, since: next }\n"
         "      - {value: outline, deprecated: \"2.1\", alias: outlined}\n      - outlined")


@pytest.mark.parametrize("src", [INLINE, BLOCK], ids=["inline", "block"])
def test_pinned_values_resolve_to_the_plain_list_plus_metadata(src):
    doc = catalog.parse_doc(probe(src), "probe", shared=SHARED)
    style = doc["fields"][0]
    assert style["values"] == ["filled", "pill", "outline", "outlined"]
    assert style["valueMeta"] == {"pill": {"since": "next"},
                                  "outline": {"deprecated": "2.1", "alias": "outlined"}}
    assert catalog.introduced(doc, style, "pill") == "next"
    assert catalog.introduced(doc, style, "filled") == "2.0"


def test_a_plain_list_has_no_value_metadata():
    doc = catalog.parse_doc(probe("  - name: size\n    type: enum\n    values: [compact, \"large\"]"), "probe", shared=SHARED)
    assert doc["fields"][0]["values"] == ["compact", "large"]
    assert "valueMeta" not in doc["fields"][0]


# ─── field and doc pins ──────────────────────────────────────────────────────


def test_field_pins_are_read():
    src = probe("  - name: pressEffect\n    type: string\n    since: next\n"
                "    changes: [{in: \"2.1\", note: \"Holds now repeat\"}]\n"
                "  - name: old\n    type: string\n    removed: \"2.2\"\n    alias: pressEffect")
    doc = catalog.parse_doc(src, "probe", shared=SHARED)
    press, old = doc["fields"]
    assert press["since"] == "next"
    assert press["changes"] == [{"in": "2.1", "note": "Holds now repeat"}]
    assert old["removed"] == "2.2" and old["alias"] == "pressEffect"
    assert catalog.introduced(doc, press) == "next"
    assert catalog.introduced(doc, old) == "2.0"


def test_doc_baseline_defaults_to_2_0_and_doc_pins_are_read():
    plain = catalog.parse_doc(probe("  - name: a\n    type: string"), "probe", shared=SHARED)
    assert plain["baseline"] == catalog.DEFAULT_BASELINE == "2.0"
    pinned = catalog.parse_doc(probe("  - name: a\n    type: string",
                                     top='baseline: "2.1"\nsince: next\ndeprecated: "3.0"\n'
                                         'changes: [{"in": "2.2", "note": "Taps debounce"}]\n'),
                               "probe", shared=SHARED)
    assert pinned["baseline"] == "2.1" and pinned["since"] == "next" and pinned["deprecated"] == "3.0"
    assert pinned["changes"] == [{"in": "2.2", "note": "Taps debounce"}]
    assert catalog.introduced(pinned, pinned["fields"][0]) == "next"


def test_a_use_entry_may_carry_its_own_pins():
    shared = catalog.parse_shared("---\nkind: shared-fields\nfields:\n  - name: confirm\n    type: bool\n---\n")
    src = probe("  - use: confirm\n    since: next\n    changes: [{in: next, note: Undo lasts longer}]")
    doc = catalog.parse_doc(src, "probe", shared=shared)
    assert "useErrors" not in doc
    assert doc["fields"][0]["since"] == "next"
    assert doc["fields"][0]["changes"] == [{"in": "next", "note": "Undo lasts longer"}]


# ─── the schema, over every vendored doc ─────────────────────────────────────


def _validator(name: str):
    jsonschema = pytest.importorskip("jsonschema")
    return jsonschema.Draft202012Validator({"$defs": SCHEMA["$defs"], "$ref": f"#/$defs/{name}"})


def test_the_schema_is_a_valid_json_schema():
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.Draft202012Validator.check_schema(SCHEMA)


@pytest.mark.parametrize("path", DOCS, ids=[p.relative_to(DOCS_DIR).as_posix() for p in DOCS])
def test_every_doc_matches_the_schema(path):
    resolved = catalog.resolved_frontmatter(path.read_text(), SHARED)
    if resolved is None:
        return
    kind = {"pattern": "patternDoc", "shared-fields": "sharedFieldsDoc", "profiles": "profilesDoc"}.get(resolved.get("kind"), "controlDoc")
    errors = [f"{'/'.join(map(str, e.absolute_path))}: {e.message[:200]}" for e in _validator(kind).iter_errors(resolved)]
    assert errors == []
    jsonschema = pytest.importorskip("jsonschema")
    assert jsonschema.Draft202012Validator(SCHEMA).is_valid(resolved), "the root oneOf picks exactly one doc kind"


def test_the_schema_rejects_a_bad_pin():
    bad = catalog.resolved_frontmatter(probe("  - name: a\n    type: string\n    since: soon\n    sinse: next"), SHARED)
    messages = [e.message for e in _validator("controlDoc").iter_errors(bad)]
    assert any("soon" in m for m in messages) and any("sinse" in m for m in messages)


@pytest.mark.parametrize("path", DOCS, ids=[p.relative_to(DOCS_DIR).as_posix() for p in DOCS])
def test_every_alias_names_a_live_field_or_value(path):
    doc = catalog.parse_doc(path.read_text(), path.stem, shared=SHARED)
    if doc is None:
        return
    for section in ("fields", "themeFields"):
        names = {f["name"] for f in doc[section]}
        for f in doc[section]:
            if f.get("alias"):
                assert f["alias"] in names - {f["name"]}, f"{section}.{f['name']} alias {f['alias']}"
            for value, pins in (f.get("valueMeta") or {}).items():
                if pins.get("alias"):
                    assert pins["alias"] in set(f["values"]) - {value}, f"{f['name']}.{value} alias {pins['alias']}"
