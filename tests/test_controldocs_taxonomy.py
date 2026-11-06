"""The settings taxonomy (app bead aif-8whty.19): shared-fields.md's `chips:`, `categories:`, `internal:` and
`canvas:`, parsed like the app's ControlDocLoader.taxonomy, and each field's category by the same rules as
SettingsTaxonomy.category(of:) and CAR-TER's scripts/settings-taxonomy.py."""

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
  - name: text
    title: Text
    icon: textformat
    order: 4
    categories: [text]
    tap: [label, title]
    petals: ["labelFontSize|labelSize", align]
    petalTitles: {"labelFontSize": "Title size"}
    since: next
  - name: look
    title: Look
    icon: paintbrush.pointed
    order: 2
    categories: [look, motion]
    tap: [style, "*Style"]
    petals: [own, animation]
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
    fields: [hideBackground]
    theme: [cornerRadius]
    since: next
  - name: text
    title: Text
    fields: [label, formatValue]
    theme: [labelFontSize]
    since: next
  - name: colour
    title: Colour
    fields: [tint]
    types: [color]
    suffixes: [Color, Tint]
    since: next
  - name: look
    title: Look
    fields: [style]
    prefixes: [show, hide]
    suffixes: [Style, Mode]
    since: next
  - name: motion
    title: Motion
    fields: [animation]
    since: next
  - name: data
    title: Binding
    home: binding
    fields: [sync]
    suffixes: [Action]
    groups: [data.series]
    since: next
  - name: content
    title: Content
    home: control
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
canvas: [span, position]
---

# Shared fields
"""


def test_parse_taxonomy_reads_the_chips_in_bar_order():
    t = catalog.parse_taxonomy(SHARED)
    assert [c["name"] for c in t["chips"]] == ["look", "text", "card"]
    text = t["chips"][1]
    assert text["title"] == "Text" and text["order"] == 4 and text["always"] is False
    assert text["tap"] == ["label", "title"] and text["petals"] == ["labelFontSize|labelSize", "align"]
    assert text["petalTitles"] == {"labelFontSize": "Title size"}
    assert text["since"] == "next"
    assert t["chips"][0]["tap"] == ["style", "*Style"]
    assert t["chips"][2]["always"] is True and t["chips"][2]["petals"] == []


def test_parse_taxonomy_reads_the_categories_and_lists():
    t = catalog.parse_taxonomy(SHARED)
    assert [c["name"] for c in t["categories"]][:3] == ["card", "text", "colour"]
    colour = t["categories"][2]
    assert colour["types"] == ["color"] and colour["suffixes"] == ["Color", "Tint"] and "home" not in colour
    assert t["categories"][0]["theme"] == ["cornerRadius"]
    assert t["internal"] == ["type", "id", "*Config"] and t["canvas"] == ["span", "position"]
    assert all(c["since"] == "next" for c in t["categories"])
    assert catalog.taxonomy_home(t, "motion") == "look"
    assert catalog.taxonomy_home(t, "data") == "binding"
    assert catalog.taxonomy_home(t, "behaviour") == "control"


def test_the_shared_fields_still_parse_beside_the_taxonomy():
    shared = catalog.parse_shared(SHARED)
    assert list(shared["fields"]) == ["confirm"] and shared["themeFields"] == {}


def test_no_taxonomy_is_empty_lists(tmp_path):
    assert catalog.parse_taxonomy("---\nkind: shared-fields\n---\n") == {
        "chips": [], "categories": [], "internal": [], "canvas": []}
    assert catalog.load_taxonomy(tmp_path)["chips"] == []
    shaped = catalog.load_taxonomy(DOCS)
    assert set(shaped) == {"chips", "categories", "internal", "canvas"}


def test_field_category_follows_the_rules_in_order():
    t = catalog.parse_taxonomy(SHARED)
    cat = lambda raw, **kw: catalog.field_category(t, raw, **kw)  # noqa: E731
    assert cat({"name": "text", "category": "text"}) == "text"                     # the doc's own word
    assert cat({"name": "cornerRadius", "type": "number"}, theme=True) == "card"   # a theme list
    assert cat({"name": "thumbColor", "type": "color"}, theme=True) == "colour"    # unlisted theme colour
    assert cat({"name": "thumbSize", "type": "number"}, theme=True) == "look"      # any other theme token
    assert cat({"name": "old", "type": "number", "deprecated": "next"}) == "internal"
    assert cat({"name": "type", "type": "enum", "group": "data.series"}) == "data"  # a group's leaves
    assert cat({"name": "chartConfig", "type": "object"}, containers={"chartConfig"}) == "internal"
    assert cat({"name": "min", "type": "number"}) == "behaviour"                   # a name list
    assert cat({"name": "datumAction", "type": "object"}) == "data"                # a suffix
    assert cat({"name": "nodeColor", "type": "string"}) == "colour"
    assert cat({"name": "showLegend", "type": "bool"}) == "look"                   # a prefix
    assert cat({"name": "gaugeStyle", "type": "enum"}) == "look"
    assert cat({"name": "wraps", "type": "bool"}) == "behaviour"                   # the type fallbacks
    assert cat({"name": "arcAngle", "type": "number", "edit": "scrub"}) == "look"
    assert cat({"name": "zoom", "type": "number"}) == "behaviour"
    assert cat({"name": "fit", "type": "enum", "tab": "style"}) == "look"
    assert cat({"name": "url", "type": "string"}) == "content"


def test_internal_list_matches_plain_names_and_patterns():
    t = catalog.parse_taxonomy(SHARED)
    assert catalog.is_internal(t, {"name": "id"})
    assert not catalog.is_internal(t, {"name": "id", "group": "pucks"})
    assert catalog.is_internal(t, {"name": "sortboardConfig"})
    assert not catalog.is_internal(t, {"name": "id"}, theme=True)


def test_parse_doc_keeps_a_fields_category_and_chip():
    doc = catalog.parse_doc("""---
type: demo
label: Demo
fields:
  - name: min
    chip: Range
    type: number
  - name: text
    category: text
    type: string
---
""", "demo", shared={})
    fields = {f["name"]: f for f in doc["fields"]}
    assert fields["min"]["chip"] == "Range" and "category" not in fields["min"]
    assert fields["text"]["category"] == "text"
