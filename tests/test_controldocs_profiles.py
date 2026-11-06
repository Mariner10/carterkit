"""Editor profiles (app bead aif-qs8b0.11.1): controldocs/profiles.md, parsed like the app's
ControlDocLoader.profiles, resolved against a control doc by the spec's rules 1-3, and linted: an unknown
category, chip, field id, Binding card, canvas verb or control type is an error."""

from pathlib import Path

from carterkit import catalog

DOCS = Path(__file__).parent.parent / "carterkit" / "controldocs"

SHARED = """---
kind: shared-fields
title: Shared fields
fields:
  - name: confirm
    type: bool
chips:
  - name: look
    title: Look
    icon: paintbrush.pointed
    order: 2
    categories: [look, layout]
    since: next
  - name: colour
    title: Colour
    icon: paintpalette
    order: 3
    categories: [colour]
    since: next
  - name: text
    title: Text
    icon: textformat
    order: 4
    categories: [text]
    since: next
  - name: card
    title: Background
    icon: rectangle.on.rectangle
    order: 5
    categories: [card]
    always: true
    since: next
categories:
  - name: card
    title: Background
    fields: [backgroundColor]
    since: next
  - name: text
    title: Text
    fields: [label]
    since: next
  - name: colour
    title: Colour
    types: [color]
    since: next
  - name: look
    title: Look
    fields: [style]
    since: next
  - name: layout
    title: Layout
    fields: [span]
    since: next
  - name: data
    title: Binding
    home: binding
    fields: [sync]
    since: next
  - name: behaviour
    title: Behaviour
    home: control
    fields: [min, max]
    since: next
  - name: internal
    title: Internal
    home: none
    fields: [type, id]
    since: next
internal: [type, id, "*Config"]
canvas: [span]
---
"""

GAUGE = """---
type: gauge
label: Gauge
category: display
fields:
  - name: min
    chip: Range
    type: number
  - name: max
    type: number
  - name: style
    type: enum
    values: [ring, half]
  - name: label
    type: string
  - name: unit
    category: text
    simple: hide
    type: string
  - name: gaugeConfig
    type: object
  - name: needle
    group: gaugeConfig
    type: bool
themeFields:
  - name: accentColor
    type: color
---
"""

SLIDER = """---
type: slider
label: Slider
category: input
fields:
  - name: step
    category: behaviour
    type: number
  - name: label
    type: string
---
"""

COMMON = """---
type: control-def
label: Control Definition
category: models
fields:
  - name: type
    type: enum
  - name: id
    type: string
  - name: span
    type: array
  - name: sync
    type: object
  - name: backgroundColor
    type: color
---
"""

PROFILES = """---
kind: profiles
title: Editor profiles
profiles:
  - name: all
    title: Everything
    since: next
    categories: [card, text, colour, look, layout, data, behaviour]
    json: true
  - name: simple
    title: Simple
    since: next
    extends: all
    json: false
  - name: first-look
    title: First look
    since: next
    categories: [text, card]
    petals: 2
    rows: false
  - name: binding-only
    title: Wiring
    since: next
    categories: [data]
    chips: []
    binding: [emits, receives]
---

# Editor profiles
"""

TAX = catalog.parse_taxonomy(SHARED)
DOCS_BY_TYPE = {t: catalog.resolved_frontmatter(src, {}) for t, src in (("gauge", GAUGE), ("slider", SLIDER))}
COMMON_DOC = catalog.resolved_frontmatter(COMMON, {})
NAMED = catalog.parse_profiles(PROFILES)


def shown(profile: dict, typ: str = "gauge") -> list[str]:
    return catalog.profile_fields(profile, NAMED, TAX, DOCS_BY_TYPE[typ], COMMON_DOC)


def inline(on: str = "gauge", **keys) -> list[str]:
    return shown(catalog.parse_profile(keys), on)


def errors(*entries):
    return catalog.profile_errors([*NAMED, *map(catalog.parse_profile, entries)], TAX, DOCS_BY_TYPE, COMMON_DOC)


# ─── parsing ─────────────────────────────────────────────────────────────────


def test_parse_profiles_reads_every_key_in_file_order():
    assert [p["name"] for p in NAMED] == ["all", "simple", "first-look", "binding-only"]
    first = NAMED[2]
    assert first == {"name": "first-look", "title": "First look", "since": "next",
                     "categories": ["text", "card"], "petals": 2, "rows": False}
    assert NAMED[0]["json"] is True and NAMED[1]["json"] is False and NAMED[1]["extends"] == "all"
    assert NAMED[3]["chips"] == [] and NAMED[3]["binding"] == ["emits", "receives"]
    assert "chips" not in first  # absent stays absent: an empty list names no chip


def test_parse_profile_keeps_wrong_kinds_for_the_lint():
    p = catalog.parse_profile({"name": "x", "petals": "lots", "rows": "maybe", "chips": "control", "colour": "x"})
    assert p["petals"] == "lots" and p["rows"] == "maybe" and p["chips"] == ["control"]
    assert p["unknownKeys"] == ["colour"]
    # A tutorial step's JSON profile has real ints and bools.
    assert catalog.parse_profile({"chips": ["control"], "petals": 0, "rows": False}) == {
        "name": "", "title": "", "chips": ["control"], "petals": 0, "rows": False}


def test_no_profiles_doc_is_empty(tmp_path):
    assert catalog.parse_profiles("---\nkind: profiles\n---\n") == []
    assert catalog.load_profiles(tmp_path) == []
    assert catalog.profile_lint(tmp_path) == []


def test_profile_manifest_lists_the_ids():
    m = catalog.profile_manifest(TAX, NAMED)
    assert m["categories"] == ["card", "text", "colour", "look", "layout", "data", "behaviour", "internal"]
    assert m["chips"] == ["look", "colour", "text", "card", "control"]
    assert m["profiles"][1] == {"name": "simple", "title": "Simple", "since": "next"}
    assert catalog.profile_manifest(TAX, [{"name": "x", "title": "X"}])["profiles"] == [
        {"name": "x", "title": "X", "since": catalog.DEFAULT_BASELINE}]


# ─── resolving against a control ─────────────────────────────────────────────


def test_all_shows_every_field_but_the_internal_ones():
    assert shown(NAMED[0]) == ["min", "max", "style", "label", "unit", "gaugeConfig.needle", "theme.accentColor",
                               "span", "sync", "backgroundColor"]


def test_simple_hides_the_simple_hide_fields_and_keeps_the_control_chip():
    assert shown(NAMED[1]) == [f for f in shown(NAMED[0]) if f != "unit"]
    assert "min" in shown(NAMED[1])


def test_an_inline_profile_starts_from_nothing():
    assert inline() == []
    assert inline(categories=["text"]) == ["label", "unit"]
    assert inline(chips=["control"]) == ["min", "max", "gaugeConfig.needle"]  # chip: + behaviour (home: control)
    assert inline(chips=["look"]) == ["style"]  # the canvas field `span` is on no chip
    assert inline(chips=["colour"]) == ["theme.accentColor"]
    assert inline(chips=["card"]) == ["backgroundColor"]  # control-def's fields count on every control


def test_field_ids_bare_and_dotted():
    assert inline(fields=["label"]) == ["label"]
    assert inline(fields=["label"], on="slider") == ["label"]
    assert inline(fields=["gauge.min", "gauge.gaugeConfig.needle", "gauge.theme.accentColor"]) == [
        "min", "gaugeConfig.needle", "theme.accentColor"]
    assert inline(fields=["gauge.min"], on="slider") == []
    assert inline(fields=["needle"]) == []  # a grouped field needs its path


def test_extends_then_hide_then_internal():
    p = {"extends": "first-look", "fields": ["gauge.min", "type", "id"], "hide": ["unit", "gauge.label"]}
    assert inline(**p) == ["min", "backgroundColor"]
    # The container itself is internal; its leaves keep their own category.
    assert inline(categories=["behaviour"], fields=["gaugeConfig"]) == ["min", "max", "gaugeConfig.needle"]


def test_no_named_profile_shows_an_internal_field():
    internal = {"type", "id", "gaugeConfig"}
    for p in NAMED:
        for typ in DOCS_BY_TYPE:
            assert not internal & set(shown(p, typ)), p["name"]


# ─── the lint ────────────────────────────────────────────────────────────────


def test_the_named_profiles_are_clean():
    assert errors() == []


def test_unknown_ids_are_errors():
    found = errors({"name": "bad", "title": "Bad", "categories": ["nope", "internal"], "chips": ["nope"],
                    "fields": ["nope", "gauge.nope", "dial.min", "label"], "hide": ["slider.min"],
                    "binding": ["nope"], "canvas": ["fly"], "add": ["dial", "gauge"]})
    assert len(found) == 10, found
    text = "\n".join(found)
    for needle in ("unknown category `nope`", "categories names `internal`", "unknown chip `nope`",
                   "fields `nope` is no control's field", "fields `gauge.nope` is not a field of gauge",
                   "fields `dial.min` names no control `dial`", "hide `slider.min` is not a field of slider",
                   "unknown binding `nope`", "unknown canvas `fly`", "unknown add `dial`"):
        assert needle in text, needle


def test_shape_errors():
    found = "\n".join(errors({"name": "Bad Name", "title": ""}, {"name": "first-look", "title": "Again"},
                             {"name": "loop", "title": "L", "extends": "loop"},
                             {"name": "orphan", "title": "O", "extends": "nope"},
                             {"name": "caps", "title": "C", "petals": "9", "rows": "maybe", "json": "yes",
                              "colour": "x"}))
    for needle in ("profiles.Bad Name: a profile needs a lowercase `name`", "profiles.Bad Name: no `title`",
                   "profiles.first-look: the name is used twice", "profiles.loop: extends loops (loop -> loop)",
                   "profiles.orphan: extends `nope`, which is not a named profile",
                   "profiles.caps: petals is 9; a chip has 0 to 5", "profiles.caps: rows is maybe",
                   "profiles.caps: json is yes", "profiles.caps: unknown key `colour`"):
        assert needle in found, needle
    assert catalog.profile_errors([catalog.parse_profile({"name": "x", "title": "X"})], TAX, {}, None) == [
        "profiles: no `all` profile (the one an unknown name falls back to)"]


def test_profile_lint_reads_a_docs_folder(tmp_path):
    (tmp_path / "shared-fields.md").write_text(SHARED)
    (tmp_path / "gauge.md").write_text(GAUGE)
    (tmp_path / "control-def.md").write_text(COMMON)
    (tmp_path / "profiles.md").write_text(PROFILES)
    assert catalog.profile_lint(tmp_path) == []
    (tmp_path / "profiles.md").write_text(PROFILES.replace("[text, card]", "[text, cards]"))
    assert catalog.profile_lint(tmp_path) == [
        "profiles.first-look: unknown category `cards` (shared-fields.md categories:)"]
    (tmp_path / "profiles.md").write_text("---\nkind: profiles\n---\n")
    assert catalog.profile_lint(tmp_path) == ["profiles.md: no profiles"]


def test_the_vendored_docs_lint_clean():
    assert catalog.profile_lint(DOCS) == []
