"""carter-m7s.8 — the golden schema corpus, shared with the app.

tests/fixtures/schema-corpus/ is a copy of the app's CAR-TERTests/Fixtures/schema-v*/ and
schema-gate/ (LayoutSchemaCorpusTests / LayoutSchemaGateTests). The app round-trips every
file through LayoutDecoder; here the same files go through the kit validator and the
inline <-> sectioned migration. Re-copy the folders when the app's corpus changes.
"""
import copy
import json
from pathlib import Path

import pytest

from carterkit import catalog, validate
from carterkit.sections import inline_view, is_sectioned, to_inline, to_sectioned

ROOT = Path(__file__).resolve().parent / "fixtures" / "schema-corpus"
DOCS = Path(__file__).resolve().parent.parent / "carterkit" / "controldocs"
CAT = catalog.build_catalog(DOCS, include_theme=True)

FILES = sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("schema-v*/**/*.json"))

#: Known kit/device drift: the device accepts these; the kit's lint is stricter
#: (carter-c1n.11 lists the first three as intentional lint; the sample is a
#: repair-on-load nesting test).
KNOWN_ERRORS = {
    "schema-v1/conformance/conformance-grid-rows-500.json": {"bad_grid"},
    "schema-v1/conformance/conformance-outside-grid-bounds.json": {"out_of_bounds"},
    "schema-v1/conformance/conformance-overlapping-controls.json": {"overlap"},
    "schema-v1/samples/sample-deep-nest-test.json": {"too_deep"},
    # Tab "Radio" has a flow grid with no `rows`: the app's `.file` decode repairs it, a
    # strict import refuses it, and kit 0.13.0 reports it (conformance parity). The fixture
    # is shared byte-for-byte with the app corpus, so it stays as seeded (kit-next-0.14).
    "schema-v1/library/advanced-film-set.json": {"missing_field"},
}


def _load(rel):
    return json.loads((ROOT / rel).read_text())


def _without_schema(doc):
    doc = copy.deepcopy(doc)
    doc.pop("schemaVersion", None)
    return doc


def _errors(doc):
    return {f["kind"] for f in validate.validate_layout(doc, CAT) if f["severity"] == "error"}


def test_corpus_covers_every_known_grammar():
    assert len(FILES) > 70
    for version in range(1, validate.KNOWN_SCHEMA_VERSION + 1):
        assert any(f.startswith(f"schema-v{version}/") for f in FILES), version


@pytest.mark.parametrize("rel", FILES)
def test_validates(rel):
    assert _errors(_load(rel)) <= KNOWN_ERRORS.get(rel, set())


@pytest.mark.parametrize("rel", [f for f in FILES if f.startswith("schema-v1/")])
def test_inline_sectioned_round_trip(rel):
    doc = _load(rel)
    sectioned = to_sectioned(doc)
    assert _without_schema(to_inline(sectioned)) == _without_schema(inline_view(doc))
    assert _errors(sectioned) <= KNOWN_ERRORS.get(rel, set())


@pytest.mark.parametrize("rel", [f for f in FILES if f.startswith("schema-v2/") and f.endswith("-sectioned.json")
                                 and "/conformance/" not in f])
def test_sectioned_rendition_matches_original(rel):
    original = "schema-v1/" + rel[len("schema-v2/"):-len("-sectioned.json")] + ".json"
    doc = _load(rel)
    assert is_sectioned(doc) and doc["schemaVersion"] == 2
    assert _without_schema(to_inline(doc)) == _without_schema(_load(original))


def test_newer_grammar_is_a_warning_not_an_error():
    doc = _load("schema-gate/newer-v3.json")
    findings = validate.validate_layout(doc, CAT)
    newer = [f for f in findings if f["kind"] == "bad_schema_version"]
    assert newer and all(f["severity"] == "warn" for f in newer)
    assert "read-only" in newer[0]["detail"]
