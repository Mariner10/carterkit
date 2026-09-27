"""carterkit.patch — the app's LayoutOp applier ported + the K11 differ (carter-n4x.10).

Goldens: tests/fixtures/layout-ops/*.json, a snapshot of the app's
CAR-TERTests/Fixtures/layout-ops (see the README there)."""
from __future__ import annotations

import copy
import itertools
import json
from pathlib import Path

import pytest

import carterkit
from carterkit import canonical, patch

HERE = Path(__file__).parent
GOLDEN_DIR = HERE / "fixtures" / "layout-ops"
CORPUS_DIR = HERE / "fixtures" / "schema-corpus"
GOLDENS = sorted(GOLDEN_DIR.glob("*.json"))

#: Goldens the kit can't reproduce, and why.
KNOWN_GAPS = {
    "error-decode": "needs the app's LayoutDecoder (post-apply validate); the kit doesn't port it",
}
#: Goldens whose inverse doesn't restore the input byte-for-byte (same in Swift).
INVERSE_GAPS = {
    "settheme": "undoing setTheme on a theme-less layout leaves theme: {}",
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def same(a, b) -> bool:
    return canonical.canonical_bytes(a) == canonical.canonical_bytes(b)


def counter_mint():
    n = itertools.count(1)
    return lambda prefix, taken: f"{prefix}_{next(n):06x}"


# ── goldens through apply ────────────────────────────────────────────────────

def test_golden_snapshot_is_present():
    assert len(GOLDENS) >= 20
    assert any(load(p).get("kit") for p in GOLDENS)


@pytest.mark.parametrize("path", GOLDENS, ids=lambda p: p.stem)
def test_golden_apply(path):
    g = load(path)
    if g["name"] in KNOWN_GAPS and not g.get("kit"):
        pytest.xfail(KNOWN_GAPS[g["name"]])
    before = copy.deepcopy(g["input"])
    if "error" in g:
        with pytest.raises(patch.PatchError) as err:
            patch.apply(g["input"], g["batch"])
        assert g["error"] in str(err.value)
        assert g["input"] == before, "a failed batch must not touch the input"
        return
    out = patch.apply(g["input"], g["batch"])
    assert same(out.document, g["expected"]), canonical.canonical_json(out.document)
    assert g["input"] == before
    if g["name"] not in INVERSE_GAPS:
        assert same(patch.apply(out.document, out.inverse).document, g["input"])


@pytest.mark.parametrize("path", GOLDENS, ids=lambda p: p.stem)
def test_golden_ops_round_trip_the_wire_form(path):
    for raw in load(path)["batch"]["ops"]:
        op = patch.decode_op(raw)
        assert op["op"] in patch.OPS
        assert patch.decode_op(op) == op


# ── diff round trip ──────────────────────────────────────────────────────────

def assert_diff(old, new, *, expressible=True):
    ops = patch.diff(old, new)
    if not expressible:
        assert ops is None
        return None
    assert ops is not None, "expected an expressible diff"
    for op in ops:
        assert op["op"] in patch.OPS and patch.decode_op(op) == op
    assert same(patch.apply(old, ops).document, new)
    json.dumps(ops)  # plain JSON on the wire
    return ops


@pytest.mark.parametrize("path", [p for p in GOLDENS if "expected" in load(p)], ids=lambda p: p.stem)
def test_golden_diff_round_trip(path):
    g = load(path)
    ops = patch.diff(g["input"], g["expected"])
    if g["name"] == "sectioned-renameid":
        # an id change reads as remove+add; the re-added node's facets would land
        # inline, not in the section they lived in -> caller full-pushes
        assert ops is None
        return
    assert ops is not None
    assert same(patch.apply(g["input"], ops).document, g["expected"])


def test_no_change_is_empty():
    base = load(GOLDEN_DIR / "setprop-tint.json")["input"]
    assert patch.diff(base, copy.deepcopy(base)) == []


def test_layout_hash_is_the_canonical_digest():
    base = load(GOLDEN_DIR / "setprop-tint.json")["input"]
    assert patch.layout_hash(base) == canonical.content_digest(base)
    assert patch.layout_hash(base).startswith("sha256:")
    assert carterkit.patch is patch and "patch" in carterkit.__all__


BASE = {
    "name": "Hand", "version": 1,
    "tabs": [
        {"id": "t_a", "title": "A", "icon": "gauge", "grid": {"columns": 4, "rows": 8}, "children": [
            {"id": "g1", "type": "group", "label": "G", "position": [0, 0], "span": [2, 4], "children": [
                {"id": "x", "type": "label", "label": "X", "position": [0, 0]},
                {"id": "y", "type": "label", "label": "Y", "position": [0, 1]}]},
            {"id": "z", "type": "gauge", "label": "Z", "position": [2, 0], "span": [1, 2]}]},
        {"id": "t_b", "title": "B", "icon": "list.bullet", "grid": {"columns": 2, "rows": 4}, "children": []},
    ],
}


def _tab(d, i):
    return d["tabs"][i]


def _node(d, nid):
    def walk(kids):
        for k in kids:
            if k.get("id") == nid:
                return k
            hit = walk(k.get("children") or [])
            if hit:
                return hit
    for t in d["tabs"]:
        hit = walk(t.get("children") or [])
        if hit:
            return hit


def e_tint(d): _node(d, "x")["tint"] = "#ff8800"
def e_span(d): _node(d, "z")["span"] = [2, 4]
def e_unset(d): del _node(d, "z")["span"]
def e_add(d): _tab(d, 1)["children"].append({"id": "new", "type": "toggle", "label": "Neu/ü", "position": [0, 0]})
def e_add_group(d): _tab(d, 0)["children"].insert(0, {"id": "g2", "type": "group", "position": [5, 0], "children": [
    {"id": "n1", "type": "label", "position": [0, 0]}]})
def e_remove(d): _tab(d, 0)["children"].pop(1)
def e_remove_group(d): _tab(d, 0)["children"].pop(0)
def e_move_in_group(d): _node(d, "g1")["children"].reverse()
def e_reparent(d): _tab(d, 1)["children"].append(_node(d, "g1")["children"].pop(0))
def e_into_group(d): _node(d, "g1")["children"].append(_tab(d, 0)["children"].pop(1))
def e_tab_rename(d): _tab(d, 1)["title"] = "Bee"
def e_tab_icon_grid(d): _tab(d, 0).update(icon="star", grid={"columns": 6, "rows": 6})
def e_layout_set(d): d.update(name="Renamed", accentColor="#00ff00")
def e_layout_unset(d): del d["version"]
def e_theme(d): d["theme"] = {"accentColor": "#123456"}
def e_add_tab(d): d["tabs"].insert(1, {"id": "t_c", "title": "C", "icon": "star", "children": [
    {"id": "c1", "type": "label", "position": [0, 0]}]})
def e_remove_tab(d): d["tabs"].pop(0)
def e_reorder_tabs(d): d["tabs"].reverse()
def e_move_to_new_tab(d):
    e_add_tab(d)
    d["tabs"][1]["children"].append(_tab(d, 0)["children"].pop(1))
def e_many(d):
    e_tint(d); e_span(d); e_reparent(d); e_tab_rename(d); e_layout_set(d); e_add(d)


def e_idless_child(d): _tab(d, 1)["children"].append({"type": "label", "position": [0, 0]})
def e_duplicate_id(d): _tab(d, 1)["children"].append({"id": "x", "type": "label"})
def e_null_value(d): _node(d, "x")["tint"] = None
def e_no_tabs(d): d["tabs"] = []


HAND = [
    ("tint", e_tint, True), ("span", e_span, True), ("unset-span", e_unset, True),
    ("add", e_add, True), ("add-group-with-child", e_add_group, True),
    ("remove", e_remove, True), ("remove-group", e_remove_group, True),
    ("move-within-group", e_move_in_group, True), ("reparent-to-tab", e_reparent, True),
    ("reparent-into-group", e_into_group, True), ("tab-rename", e_tab_rename, True),
    ("tab-icon-grid", e_tab_icon_grid, True), ("layout-set", e_layout_set, True),
    ("layout-unset", e_layout_unset, True), ("theme", e_theme, True), ("add-tab", e_add_tab, True),
    ("remove-tab", e_remove_tab, True), ("reorder-tabs", e_reorder_tabs, True),
    ("move-to-new-tab", e_move_to_new_tab, True), ("many", e_many, True),
    ("idless-child", e_idless_child, False), ("duplicate-id", e_duplicate_id, False),
    ("json-null-value", e_null_value, False), ("no-tabs", e_no_tabs, False),
]


@pytest.mark.parametrize("name,edit,expressible", HAND, ids=[h[0] for h in HAND])
def test_hand_diff(name, edit, expressible):
    new = copy.deepcopy(BASE)
    edit(new)
    assert_diff(BASE, new, expressible=expressible)


def test_hand_diff_ops_are_small():
    new = copy.deepcopy(BASE)
    e_tint(new)
    assert patch.diff(BASE, new) == [{"op": "update", "id": "x", "set": {"tint": "#ff8800"}, "unset": []}]
    new = copy.deepcopy(BASE)
    e_tab_rename(new)
    assert patch.diff(BASE, new) == [{"op": "setTab", "tab": "t_b", "key": "title", "value": "Bee"}]


def test_legacy_idless_tabs_match_by_index():
    old = copy.deepcopy(BASE)
    for t in old["tabs"]:
        del t["id"]
    new = copy.deepcopy(old)
    new["tabs"][0]["title"] = "Alpha"          # retitle pins id, the diff unpins it
    new["tabs"][1]["children"].append({"id": "q", "type": "label", "position": [0, 0]})
    ops = assert_diff(old, new)
    assert {"op": "setTab", "tab": 0, "key": "id", "value": None} in ops
    added = copy.deepcopy(old)
    added["tabs"].append({"title": "C", "children": []})
    assert_diff(old, added, expressible=False)   # can't add an id-less tab by index


# ── schema corpus: small programmatic edits round-trip ───────────────────────

def _corpus():
    out = []
    for p in sorted(CORPUS_DIR.rglob("*.json")):
        try:
            doc = load(p)
        except ValueError:
            continue
        if isinstance(doc, dict) and isinstance(doc.get("tabs"), list) and doc["tabs"]:
            out.append(p)
    return out


CORPUS = _corpus()


def _corpus_edits(doc):
    """(kind, new) pairs: tint + span on the first top-level child, remove it, reverse the
    first tab's children, retitle the first tab, rename the layout, set/unset a key."""
    def first(d):
        for t in d["tabs"]:
            for k in t.get("children") or []:
                if isinstance(k, dict) and isinstance(k.get("id"), str):
                    return k, t
        return None, None

    def edit(fn):
        d = copy.deepcopy(doc)
        return d if fn(d) is not False else None

    def tint(d):
        k, _ = first(d)
        if k is None:
            return False
        k["tint"] = "#123456"

    def span(d):
        k, _ = first(d)
        if k is None:
            return False
        k["span"] = [3, 1]

    def remove(d):
        k, t = first(d)
        if k is None:
            return False
        t["children"].remove(k)

    def reorder(d):
        kids = d["tabs"][0].get("children")
        if not isinstance(kids, list) or len(kids) < 2:
            return False
        kids.reverse()

    def retitle(d): d["tabs"][0]["title"] = "Renamed / Ω"
    def rename(d): d["name"] = "Nouveau ✓"
    def unset(d): d.pop("version", None); d["accentColor"] = "#abcdef"

    for kind, fn in [("tint", tint), ("span", span), ("remove", remove), ("reorder", reorder),
                     ("retitle", retitle), ("rename", rename), ("layout", unset)]:
        new = edit(fn)
        if new is not None:
            yield kind, new


def test_corpus_is_present():
    assert len(CORPUS) >= 20


@pytest.mark.parametrize("path", CORPUS, ids=lambda p: str(p.relative_to(CORPUS_DIR)))
def test_corpus_diff_round_trip(path):
    doc = load(path)
    readonly = doc.get("schemaVersion", 1) > 2
    for kind, new in _corpus_edits(doc):
        ops = patch.diff(doc, new)
        if ops is None:
            continue
        assert same(patch.apply(doc, ops).document, new), (kind, ops)
    if not readonly and same(patch.apply(doc, []).document, doc):
        # (a sectioned `placements.<id>.default` alias re-lifts as top-level
        # position/span, like the Swift applier, so apply(doc, []) isn't identity there)
        assert patch.diff(doc, copy.deepcopy(doc)) == []


def test_corpus_diffs_are_mostly_expressible():
    tally: dict = {}
    for path in CORPUS:
        doc = load(path)
        for kind, new in _corpus_edits(doc):
            ok, total = tally.get(kind, (0, 0))
            tally[kind] = (ok + (patch.diff(doc, new) is not None), total + 1)
    for kind, (ok, total) in tally.items():
        assert ok / total >= 0.85, (kind, ok, total)


# ── applier details ──────────────────────────────────────────────────────────

def _base():
    return load(GOLDEN_DIR / "setprop-tint.json")["input"]


def test_aliases_decode_to_canonical_ops():
    d = patch.decode_op
    assert d({"op": "set", "id": "a", "key": "k", "value": 1})["op"] == "setProp"
    assert d({"op": "unset", "id": "a", "key": "k"}) == {"op": "setProp", "id": "a", "key": "k", "value": None}
    assert d({"op": "add", "tab": 0, "child": {"type": "label"}})["parent"] == 0
    assert d({"op": "move", "id": "a", "tab": "More"})["parent"] == "More"
    assert d({"op": "setLayout", "key": "name", "value": "N"}) == {"op": "layout", "set": {"name": "N"}, "unset": []}
    assert d({"op": "setLayout", "key": "name"}) == {"op": "layout", "set": {}, "unset": ["name"]}
    assert d({"op": "renameTab", "from": "Main", "to": "Home"}) == {
        "op": "setTab", "tab": "Main", "key": "title", "value": "Home"}
    with pytest.raises(patch.PatchError, match="unknown op"):
        d({"op": "explode"})
    with pytest.raises(patch.PatchError, match="op 1"):
        patch.decode_batch({"ops": [{"op": "remove", "id": "a"}, {"op": "remove"}]})


def test_placeholders_mint_ids_and_names():
    ops = [{"op": "add", "parent": "t_more", "control": {"type": "gauge", "id": "$g"}, "position": [0, 0]},
           {"op": "setProp", "id": "$g", "key": "label", "value": "Battery"},
           {"op": "add", "parent": "t_more", "control": {"type": "liveGroup"}},
           {"op": "addTab", "title": "Extra"}]
    out = patch.apply(_base(), ops, mint=counter_mint())
    assert out.minted == {"$g": "c_000001", "#2": "c_000002", "#3": "t_000003"}
    kids = out.document["tabs"][1]["children"]
    assert kids[0] == {"type": "gauge", "id": "c_000001", "name": "Gauge 1", "label": "Battery", "position": [0, 0]}
    assert kids[1]["name"] == "Live group 1"
    assert out.document["tabs"][2]["id"] == "t_000003"
    real = patch.apply(_base(), ops[:1]).minted["$g"]
    assert real.startswith("c_") and len(real) == 8


def test_base_and_atomicity():
    base = _base()
    before = copy.deepcopy(base)
    ok = patch.apply(base, {"ops": [{"op": "setProp", "id": "temp", "key": "tint", "value": "#fff"}],
                            "base": patch.layout_hash(base)})
    assert ok.document["tabs"][0]["children"][0]["tint"] == "#fff"
    with pytest.raises(patch.PatchError) as err:
        patch.apply(base, [{"op": "setProp", "id": "temp", "key": "tint", "value": "#fff"},
                           {"op": "remove", "id": "ghost"}])
    assert err.value.op_index == 1
    assert base == before
    with pytest.raises(patch.PatchError, match="changed since base"):
        patch.apply(base, [], base="sha256:" + "0" * 64)


def test_nested_addressing_and_refusals():
    base = _base()
    out = patch.apply(base, [{"op": "update", "id": "oil", "set": {"tint": "#0f0", "label": None}}]).document
    oil = out["tabs"][0]["children"][2]["children"][0]
    assert oil["tint"] == "#0f0" and "label" not in oil
    for bad, why in [({"op": "setProp", "id": "temp", "key": "id", "value": "x"}, "setProp"),
                     ({"op": "update", "id": "temp", "set": {"id": "x"}}, "renameId"),
                     ({"op": "layout", "set": {"tabs": []}}, "tab ops"),
                     ({"op": "move", "id": "engine", "parent": "engine"}, "into itself"),
                     ({"op": "resize", "id": "temp", "span": [0, 1]}, "span")]:
        with pytest.raises(patch.PatchError, match=why):
            patch.apply(base, [bad])


def test_readonly_newer_schema_is_refused():
    with pytest.raises(patch.PatchError, match="read-only"):
        patch.apply({"schemaVersion": 3, "tabs": []}, [])




