"""carter-m7s.6 — the document contract lint (controldocs/document-contract.md).

Limits come from the doc's table (the app's DocumentContractTests pin its sanitizer to
the same rows); extensions{} is bounded and opaque; unknown core keys point authors at
extensions; depth past the limit, inline blobs, schemaVersion, reserved keys,
provenance and requires.features are linted.
"""

import base64
import json
from pathlib import Path

import pytest

from carterkit import catalog, validate

DOCS = Path(validate.__file__).parent / "controldocs"
CAT = catalog.build_catalog(DOCS, include_theme=True)


def _layout(children=None, **top):
    doc = {"name": "t", "version": 1, "tabs": [{
        "title": "A", "icon": "star", "grid": {"columns": 4, "rows": 8},
        "children": children if children is not None else [
            {"type": "label", "id": "c_7f3a9e", "text": "x", "position": [0, 0]}],
    }]}
    doc.update(top)
    return doc


def _kinds(layout, kind):
    return [f for f in validate.validate_layout(layout, CAT) if f["kind"] == kind]


# ── limits: one table ────────────────────────────────────────────────────────

def test_contract_doc_is_in_the_catalog_docs():
    parsed = catalog.parse_all(DOCS)
    assert "document-contract" in parsed
    assert parsed["document-contract"]["category"] == "models"


def test_limits_are_read_from_the_contract_table():
    text = (DOCS / "document-contract.md").read_text()
    assert "| `maxNestingDepth` | 8 |" in text
    assert validate.MAX_DEPTH == validate.LIMITS["maxNestingDepth"] == 8
    assert validate.MAX_CONTROLS == validate.LIMITS["maxControls"]
    assert validate.MAX_STRING == validate.LIMITS["maxStringBytes"]
    assert validate.MAX_EXTENSIONS == validate.LIMITS["maxExtensionsBytes"] == 65536
    assert validate.LIMITS["minTimerSeconds"] == 0.25
    # Every row in the doc parsed (no silent fallback to the defaults).
    assert set(validate.LIMITS) == set(validate._LIMIT_DEFAULTS)


# ── depth > limit ────────────────────────────────────────────────────────────

def _nested(levels):
    node = {"type": "label", "id": "leaf", "text": "x", "position": [0, 0]}
    for i in range(levels):
        node = {"type": "group", "id": f"g{i}", "position": [0, 0],
                "grid": {"columns": 1, "rows": 1}, "children": [node]}
    return node


def test_depth_at_the_limit_is_clean():
    assert _kinds(_layout([_nested(validate.MAX_DEPTH)]), "too_deep") == []


def test_depth_past_the_limit_says_placeholder():
    found = _kinds(_layout([_nested(validate.MAX_DEPTH + 1)]), "too_deep")
    assert len(found) == 1 and found[0]["severity"] == "error"
    assert "Nested too deeply" in found[0]["detail"]


# ── unknown core keys → extensions ───────────────────────────────────────────

def test_unknown_control_key_suggests_extensions():
    kids = [{"type": "label", "id": "a", "text": "x", "position": [0, 0], "plantId": 7}]
    found = _kinds(_layout(kids), "unknown_field")
    assert len(found) == 1 and "extensions" in found[0]["detail"]


def test_unknown_group_and_top_level_keys_suggest_extensions():
    group = {"type": "group", "id": "g", "position": [0, 0], "grid": {"columns": 1, "rows": 1},
             "children": [], "zoneColor": "red"}
    found = _kinds(_layout([group], myToolState={"a": 1}), "unknown_field")
    wheres = sorted(f["where"] for f in found)
    assert wheres == ["root", "tab[0]/g"]
    assert all("extensions" in f["detail"] for f in found)


def test_contract_top_level_keys_are_known():
    doc = _layout(schemaVersion=1, format="carter", extensions={"com.example.t": {}},
                  provenance={"parents": [{"id": "X", "relation": "copy"}]},
                  requires={"features": ["local.store@2", "sensors"]})
    bad = [f for f in validate.validate_layout(doc, CAT) if f["severity"] != "info"]
    assert bad == []


# ── extensions ───────────────────────────────────────────────────────────────

def test_extensions_are_opaque_and_clean():
    ext = {"com.example.plantdb": {"url": "ftp://not-checked", "blob": "A" * 5000,
                                   "position": [999]}}
    kids = [{"type": "label", "id": "a", "text": "x", "position": [0, 0], "extensions": ext},
            {"type": "group", "id": "g", "position": [1, 0], "grid": {"columns": 1, "rows": 1},
             "children": [], "extensions": ext}]
    findings = validate.validate_layout(_layout(kids, extensions=ext), CAT)
    assert [f for f in findings if f["severity"] != "info"] == []


def test_oversized_extensions_is_an_error_everywhere():
    big = {"com.example.big": "a" * validate.MAX_EXTENSIONS}
    kids = [{"type": "label", "id": "a", "text": "x", "position": [0, 0], "extensions": big}]
    found = [f for f in _kinds(_layout(kids, extensions=big), "bad_extensions")
             if f["severity"] == "error"]
    assert sorted(f["where"] for f in found) == ["root.extensions", "tab[0]/a.extensions"]


def test_extensions_must_be_an_object_with_reverse_dns_keys():
    assert _kinds(_layout(extensions=["x"]), "bad_extensions")[0]["severity"] == "error"
    warn = _kinds(_layout(extensions={"mytool": {}}), "bad_extensions")
    assert len(warn) == 1 and warn[0]["severity"] == "warn"


# ── inline blobs ─────────────────────────────────────────────────────────────

def test_inline_blobs_are_flagged():
    b64 = base64.b64encode(bytes(range(256)) * 8).decode()
    kids = [
        {"type": "label", "id": "a", "text": b64, "position": [0, 0]},
        {"type": "label", "id": "b", "text": "x", "position": [1, 0],
         "icon": "data:font/woff2;base64,AAAA"},
        {"type": "image", "id": "c", "position": [2, 0],
         "url": "data:image/png;base64," + "A" * (validate.MAX_DATA_IMAGE + 10)},
    ]
    found = _kinds(_layout(kids), "inline_blob")
    assert sorted(f["where"].split(".")[-1] for f in found) == ["icon", "text", "url"]


def test_bounded_data_image_url_and_prose_are_not_blobs():
    kids = [
        {"type": "image", "id": "c", "position": [0, 0],
         "url": "data:image/png;base64," + "A" * 6000},
        {"type": "label", "id": "d", "text": "Data: Open-Meteo, polled every 15 min",
         "position": [1, 0]},
    ]
    findings = validate.validate_layout(_layout(kids), CAT)
    assert [f for f in findings if f["kind"] in ("inline_blob", "long_string", "bad_url")] == []


# ── schemaVersion / reserved / provenance / requires ─────────────────────────

@pytest.mark.parametrize("sv,severity", [(0, "error"), ("2", "error"), (True, "error"), (3, "warn")])
def test_schema_version(sv, severity):
    found = _kinds(_layout(schemaVersion=sv), "bad_schema_version")
    assert [f["severity"] for f in found] == [severity]


def test_sections_need_schema_version_2():
    placed = {"c_7f3a9e": {"position": [0, 0]}}
    assert _kinds(_layout(placements=placed), "bad_schema_version")
    assert _kinds(_layout(placements=placed, schemaVersion=2), "bad_schema_version") == []


def test_reserved_keys_warn():
    found = _kinds(_layout(revision=4, attestations=[]), "reserved_key")
    assert sorted(f["where"] for f in found) == ["root.attestations", "root.revision"]


def test_provenance_and_requires_shapes():
    doc = _layout(provenance={"parents": [{"id": "X", "relation": "stolen"}]},
                  requires={"features": ["local.store@2", "Local Store", "x@0"]})
    assert len(_kinds(doc, "bad_provenance")) == 1
    assert [f["where"] for f in _kinds(doc, "bad_requires")] == [
        "root.requires.features[1]", "root.requires.features[2]"]


def test_extensions_block_measured_as_compact_json():
    ext = {"com.example.t": "a" * 100}
    size = len(json.dumps(ext, separators=(",", ":")).encode())
    assert size < validate.MAX_EXTENSIONS
    assert _kinds(_layout(extensions=ext), "bad_extensions") == []
