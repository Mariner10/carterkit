"""io: facts in ControlDocs frontmatter (app bead aif-8whty.20).

A doc's top-level `io:` list says what the control sends (`emits:`), what it can show or
follow (`receives:`) and the editor's placeholder preview (`sample:`); each fact holds exactly
one of the three. These pin catalog.parse_io / parse_doc's "io", that the field parser ignores
the facts, and the schema (controldocs.schema.json `$defs/io`). Mirrors
CAR-TERTests/ControlDocIOTests.swift, with the same fixtures (the spec's worked examples)."""
import json
import os
from pathlib import Path

import pytest

from carterkit import catalog

NO_SHARED = {"fields": {}, "themeFields": {}}

PIE = """io:
  - receives: slices
    role: show
    type: json
    shape: {"slices": [{"label": "text", "value": "number", "color": "hex?", "icon": "symbol?"}]}
    from: [hub, http, store, mqtt, default]
    says: "slices: a label and a number each"
    reacts: bigger numbers get bigger slices; a new label adds a slice and a missing one fades out
    example: {"slices": [{"label": "Sample A", "value": 3}]}
  - emits: slice
    when: tap
    field: pieConfig.sliceAction
    fallback: action
    type: string
    says: the tapped slice's label
    example: "Sample A"
    tokens: {"total": "the sum of every slice"}
  - sample: {"slices": [{"label": "Sample A", "value": 3}, {"label": "Sample B", "value": 2}, {"label": "Sample C", "value": 1}]}
    next: {"slices": [{"label": "Sample A", "value": 2}, {"label": "Sample B", "value": 3}, {"label": "Sample C", "value": 1}, {"label": "Sample D", "value": 1}]}"""

SORTBOARD = """io:
  - emits: pickup
    when: lift
    field: sortboardConfig.events.pickup
    type: id
    says: the lifted card's id
    example: "item-1"
    tokens: {"item": "the card's id", "from": "the column it left"}
    hub: {"item": "item-1", "from": "palette"}
  - emits: place
    when: drop
    field: sortboardConfig.events.place
    type: id
    says: the dropped card's id
    example: "item-1"
  - emits: layout
    when: settle
    field: sortboardConfig.events.layout
    type: json
    says: every column's cards, in order
    example: {"zones": {"column-1": ["item-1"]}}
  - receives: arrangement
    role: follow
    type: json
    shape: {"zones": {"columnId": ["itemId"]}}
    from: [hub, http, store]
    says: which cards sit in which column
    reacts: cards glide to their new columns
    example: {"zones": {"column-1": ["item-2"]}}
  - sample: {"items": [{"id": "item-1", "label": "Item 1"}], "zones": [{"id": "column-1", "label": "Column 1"}]}
    into: sortboardConfig"""

MAP = """io:
  - emits: none
  - receives: pins
    role: show
    type: json
    shape: {"markers": [{"coordinate": "[lat, lng]", "label": "text?"}]}
    from: [hub, http, store]
    says: pins, each a coordinate with an optional label
    reacts: pins glide to new coordinates and the camera refits
    example: {"markers": [{"coordinate": [0, 0], "label": "Pin 1"}]}
  - sample: {"markers": [{"coordinate": [0.0, 0.0], "label": "Pin 1"}, {"coordinate": [0.02, 0.03], "label": "Pin 2"}]}"""

TAP_VALUE = '  - emits: value\n    when: tap\n    type: string\n    says: the text\n    example: "Sample A"'
FOLLOW_VALUE = ('  - receives: value\n    type: string\n    from: [hub, store]\n    says: a text\n'
                '    reacts: it changes\n    example: "Sample A"')


def source(front: str) -> str:
    return f"---\ntype: probe\nlabel: Probe\ncategory: controls\n{front}\n---\nbody"


def io(front: str, shared=NO_SHARED) -> dict:
    return catalog.parse_doc(source(front), "probe", shared=shared)["io"]


# ─── reading the facts ───────────────────────────────────────────────────────


def test_pie_facts_read_with_their_types():
    got = io(PIE)
    assert got["problems"] == []
    (slices,) = got["receives"]
    assert slices["receives"] == "slices" and slices["role"] == "show" and slices["type"] == "json"
    assert slices["from"] == ["hub", "http", "store", "mqtt", "default"]
    assert slices["says"] == "slices: a label and a number each"
    assert slices["example"] == {"slices": [{"label": "Sample A", "value": 3}]}
    (tap,) = got["emits"]
    assert (tap["emits"], tap["when"], tap["type"]) == ("slice", "tap", "string")
    assert tap["field"] == "pieConfig.sliceAction" and tap["fallback"] == "action"
    assert tap["tokens"] == {"total": "the sum of every slice"} and tap["example"] == "Sample A"
    (sample,) = got["samples"]
    assert len(sample["sample"]["slices"]) == 3 and len(sample["next"]["slices"]) == 4
    assert sample["sample"]["slices"][0] == {"label": "Sample A", "value": 3}
    assert not got["sendsNothing"] and not got["showsNothing"]


def test_sortboard_has_three_events_each_with_its_field():
    got = io(SORTBOARD)
    assert got["problems"] == []
    assert [e["emits"] for e in got["emits"]] == ["pickup", "place", "layout"]
    assert [e["when"] for e in got["emits"]] == ["lift", "drop", "settle"]
    assert got["emits"][0]["hub"] == {"item": "item-1", "from": "palette"}
    assert got["emits"][2]["example"] == {"zones": {"column-1": ["item-1"]}}
    assert got["receives"][0]["role"] == "follow"
    assert got["samples"][0]["into"] == "sortboardConfig"


def test_map_sends_nothing_and_shows_pins():
    got = io(MAP)
    assert got["problems"] == [] and got["sendsNothing"] and got["emits"] == []
    assert got["receives"][0]["role"] == "show"
    assert got["samples"][0]["sample"]["markers"][0]["coordinate"] == [0.0, 0.0]


def test_role_defaults_to_follow_when_the_doc_emits_its_value():
    assert io(f"io:\n{FOLLOW_VALUE}\n{TAP_VALUE}")["receives"][0]["role"] == "follow"
    assert io(f"io:\n{FOLLOW_VALUE}")["receives"][0]["role"] == "show"


def test_a_bare_scalar_payload_stays_a_string():
    got = io("io:\n  - sample: Sample A\n  - sample: 40\n    for: value\n  - sample: [a, b]\n    for: list")
    assert [s["sample"] for s in got["samples"]] == ["Sample A", 40, ["a", "b"]]
    assert got["samples"][1]["for"] == "value"


@pytest.mark.parametrize("fact", [
    '  - emits: value\n    receives: value\n    when: tap\n    type: string\n    says: x\n    example: "A"',
    "  - title: a fact with no kind",
    '  - emits: value\n    when: wiggle\n    type: string\n    says: x\n    example: "A"',
    '  - emits: value\n    when: tap\n    type: colour\n    says: x\n    example: "A"',
    '  - receives: value\n    type: string\n    from: [carrier-pigeon]\n    says: x\n    reacts: y\n    example: "A"',
    '  - receives: value\n    type: string\n    from: [hub]\n    says: x\n    example: "A"',
    '  - receives: value\n    type: string\n    role: mirror\n    from: [hub]\n    says: x\n    reacts: y\n    example: "A"',
])
def test_an_unusable_fact_is_a_problem(fact):
    assert io(f"io:\n{fact}")["problems"]


def test_fact_pins_are_read():
    got = io(f"io:\n{TAP_VALUE}\n    since: next\n    changes: [{{in: next, note: \"now sends on release\"}}]\n"
             f"    deprecated: \"2.1\"\n{FOLLOW_VALUE}\n    since: \"2.1\"")
    emit = got["emits"][0]
    assert emit["since"] == "next" and emit["deprecated"] == "2.1"
    assert emit["changes"] == [{"in": "next", "note": "now sends on release"}]
    assert got["receives"][0]["since"] == "2.1"


def test_a_doc_without_io_has_no_io_key():
    assert "io" not in catalog.parse_doc(source("fields:\n  - name: label\n    type: string"), "probe", shared=NO_SHARED)


# ─── the dialect: fields, use:, resolved form ────────────────────────────────


def test_the_field_parser_ignores_io_items():
    fields = "fields:\n  - name: label\n    type: string\n  - name: tint\n    type: color"
    theme = "themeFields:\n  - name: cornerRadius\n    type: number"
    plain = catalog.parse_doc(source(f"{fields}\n{theme}"), "probe", shared=NO_SHARED)
    with_io = catalog.parse_doc(source(f"{fields}\n{SORTBOARD}\n{theme}"), "probe", shared=NO_SHARED)
    assert with_io["fields"] == plain["fields"] and with_io["themeFields"] == plain["themeFields"]
    assert len(with_io["io"]["emits"]) == 3 and "useErrors" not in with_io


def test_use_fields_and_io_read_together():
    shared = {"fields": {"tint": {"name": "tint", "type": "color", "summary": "The accent"}}, "themeFields": {}}
    doc = catalog.parse_doc(source(f"fields:\n  - use: tint\n    summary: The fill\nio:\n{TAP_VALUE}"), "probe",
                            shared=shared)
    assert [f["name"] for f in doc["fields"]] == ["tint"] and doc["fields"][0]["summary"] == "The fill"
    assert "useErrors" not in doc
    assert doc["io"]["emits"][0]["when"] == "tap"


def test_resolved_frontmatter_yields_io_as_a_list_of_maps():
    facts = catalog.resolved_frontmatter(source(PIE), NO_SHARED)["io"]
    assert len(facts) == 3 and facts[0]["receives"] == "slices"
    assert facts[0]["from"] == ["hub", "http", "store", "mqtt", "default"]
    assert facts[1]["tokens"] == {"total": "the sum of every slice"}


# ─── the schema ──────────────────────────────────────────────────────────────


def _schema() -> dict:
    """controldocs.schema.json with `$defs/io`: the vendored copy once it has it, else the app's
    (CARTER_APP_CONTROLDOCS or a CAR-TER checkout beside the kit), else skip until re-vendored."""
    vendored = json.loads((Path(catalog.__file__).resolve().parent / "controldocs" / "controldocs.schema.json").read_text())
    if "io" in vendored["$defs"]:
        return vendored
    root = Path(__file__).resolve().parents[1]
    candidates = [Path(os.environ["CARTER_APP_CONTROLDOCS"])] if os.environ.get("CARTER_APP_CONTROLDOCS") else []
    candidates += [p / "CAR-TER" / "CAR-TER" / "ControlDocs" for p in root.parents]
    for docs in candidates:
        f = docs / "controldocs.schema.json"
        if f.is_file() and "io" in (schema := json.loads(f.read_text()))["$defs"]:
            return schema
    pytest.skip("the vendored controldocs.schema.json predates io: (re-vendor from CAR-TER; "
                "or set CARTER_APP_CONTROLDOCS)")


def _schema_errors(front: str) -> list:
    jsonschema = pytest.importorskip("jsonschema")
    schema = _schema()
    check = jsonschema.Draft202012Validator({"$ref": "#/$defs/controlDoc", "$defs": schema["$defs"]})
    return list(check.iter_errors(catalog.resolved_frontmatter(source(front), NO_SHARED)))


@pytest.mark.parametrize("front", [PIE, SORTBOARD, MAP, f"io:\n{TAP_VALUE}\n{FOLLOW_VALUE}\n  - sample: \"Sample A\"",
                                   "io:\n  - emits: none\n  - receives: none"],
                         ids=["pie", "sortboard", "map", "input", "nothing"])
def test_the_schema_accepts_the_worked_examples(front):
    assert _schema_errors(front) == []


@pytest.mark.parametrize("fact", [
    '  - emits: value\n    receives: value\n    when: tap\n    type: string\n    says: x\n    example: "A"',
    '  - emits: value\n    when: wiggle\n    type: string\n    says: x\n    example: "A"',
    "  - emits: none\n    when: tap",
    '  - emits: value\n    when: tap\n    type: string\n    example: "A"',
    '  - receives: value\n    type: string\n    from: [hub]\n    says: x\n    example: "A"',
    '  - receives: value\n    type: string\n    from: [carrier-pigeon]\n    says: x\n    reacts: y\n    example: "A"',
    '  - receives: value\n    type: string\n    from:\n      - hub\n    says: x\n    reacts: y\n    example: "A"',
    '  - receives: value\n    type: id\n    from: [hub]\n    says: x\n    reacts: y\n    example: "A"',
    '  - sample: "A"\n    colour: red',
    '  - emits: value\n    when: tap\n    type: string\n    says: x\n    example: "A"\n    since: soon',
])
def test_the_schema_refuses_a_bad_fact(fact):
    assert _schema_errors(f"io:\n{fact}")
