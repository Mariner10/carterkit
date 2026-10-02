"""Local store (carterkit 0.13): builders, lint, codegen/contract neutrality and the
fixture-parity run over the app's shared conformance fixtures."""
from __future__ import annotations

import copy
import glob
import json
import os
import sys
from pathlib import Path

import pytest

import carterkit
from carterkit import Layout, bind, codegen, local, validate
from carterkit.contract import extract_contract

sys.path.insert(0, str(Path(__file__).parent))
import local_eval as E  # noqa: E402

CAT = carterkit.controls(include_theme=True)
FIXTURE = Path(__file__).parent / "fixtures" / "local-store.json"
_DEFAULT_A4 = (Path(__file__).resolve().parents[2] / "local-store" / "CAR-TERTests"
               / "Fixtures" / "local-query")


def _layout():
    return json.loads(FIXTURE.read_text())


def _errors(layout):
    return [f for f in validate.validate_layout(layout, CAT) if f["severity"] == "error"]


def _details(layout, kind=None):
    return [f["detail"] for f in validate.validate_layout(layout, CAT)
            if kind is None or f["kind"] == kind]


def _one_control(sync=None, action=None, ctype="label", **src):
    """A layout with one local source (books: title/pages/finished/tags) and one control."""
    ch = {"type": ctype, "id": "x", "position": [0, 0]}
    if sync is not None:
        ch["sync"] = [sync]
    if action is not None:
        ch["action"] = action
    if ctype == "label":
        ch["label"] = "x"
    source = {"type": "local", "namespace": "t",
              "collections": {"books": {"fields": {"title": "string", "pages": "integer",
                                                   "finished": "date", "tags": "json",
                                                   "lent": "bool"}}}}
    source.update(src)
    return {"name": "T", "version": 1, "sources": {"db": source},
            "tabs": [{"title": "Main", "icon": "house.fill", "grid": {"columns": 4, "rows": 4},
                      "children": [ch]}]}


# ── builders (spec §9.2 / §5.1 / §6.1 shapes) ─────────────────────────────────

def test_bind_local_minimal_and_full():
    assert bind.local("books", aggregate="count") == {
        "method": "local", "collection": "books", "aggregate": "count"}
    full = bind.local("books", where={"finished": {"gte": "{{startOfYear}}"}},
                      group_by={"field": "finished", "bucket": "month"},
                      aggregate={"op": "sum", "field": "pages"}, order_by="-key",
                      limit=12, value_path="rows", source="db")
    assert full == {"method": "local", "collection": "books",
                    "where": {"finished": {"gte": "{{startOfYear}}"}},
                    "groupBy": {"field": "finished", "bucket": "month"},
                    "aggregate": {"op": "sum", "field": "pages"},
                    "orderBy": "-key", "limit": 12, "valuePath": "rows", "source": "db"}


def test_bind_local_op_shapes():
    assert bind.local_op("insert", "books", set={"title": "{{value}}"}) == {
        "method": "local", "op": "insert", "collection": "books", "set": {"title": "{{value}}"}}
    assert bind.local_op("delete", "books", id="{{selected}}") == {
        "method": "local", "op": "delete", "collection": "books", "id": "{{selected}}"}
    # select with no id clears the cursor: the key is emitted as null, not dropped.
    assert bind.local_op("select", "books") == {
        "method": "local", "op": "select", "collection": "books", "id": None}


def test_layout_source_local_shorthand_and_full():
    ui = Layout("Log", columns=4, rows=4)
    ui.source_local("db", {"books": {"title": "string", "pages": "integer"},
                           "notes": {"fields": {"text": "string"}, "shared": True}},
                    namespace="log", views={"all": {"from": "books"}}, week_starts_on="sunday")
    src = ui.layout["sources"]["db"]
    assert src == {"type": "local", "namespace": "log", "weekStartsOn": "sunday",
                   "collections": {"books": {"fields": {"title": "string", "pages": "integer"}},
                                   "notes": {"fields": {"text": "string"}, "shared": True}},
                   "views": {"all": {"from": "books"}}}


def test_builder_round_trip_lints_clean():
    with Layout("Log", columns=4, rows=4) as ui:
        ui.source_local("db", {"books": {"title": "string", "pages": "integer",
                                         "finished": "date"}},
                        namespace="log")
        with ui.tab("Main", icon="book"):
            ui.label("n", label="Books", sync=[bind.local("books", aggregate="count")])
            ui.button("add", label="Add",
                      action=bind.local_op("insert", "books",
                                           set={"title": "{{value}}", "finished": "{{today}}"}))
    assert _errors(ui.layout) == []
    assert "unused_source" not in {f["kind"] for f in validate.validate_layout(ui.layout, CAT)}


# ── whitelists and the fixture layout ────────────────────────────────────────

def test_fixture_layout_lints_clean_and_cli_exit_codes(tmp_path):
    lay = _layout()
    assert _errors(lay) == []
    assert not [f for f in validate.validate_layout(lay, CAT) if f["kind"] == "unused_source"]
    broken = copy.deepcopy(lay)
    broken["tabs"][0]["children"][0]["sync"][0]["where"] = {"nope": 1}
    bad = tmp_path / "broken.json"
    bad.write_text(json.dumps(broken))
    from carterkit.cli import main
    assert main(["validate", str(FIXTURE)]) == 0
    assert main(["validate", str(bad)]) == 1


def test_local_source_type_accepted_and_unknown_type_still_rejected():
    lay = _one_control(sync=bind.local("books", aggregate="count"))
    assert "bad_sources" not in {f["kind"] for f in validate.validate_layout(lay, CAT)}
    lay["sources"]["db"]["type"] = "sqlite"
    assert any("'local'" in d for d in _details(lay, "bad_sources"))


def test_local_binding_without_a_source_is_an_error():
    lay = _one_control(sync=bind.local("books", aggregate="count"))
    del lay["sources"]
    assert any("no local source declared" in d for d in _details(lay, "bad_source"))


# ── lint negatives (acceptance list) ──────────────────────────────────────────

@pytest.mark.parametrize("stage, needle", [
    ({"where": {"genre": "sf"}}, "unknown field 'genre'"),
    ({"limit": 0}, "limit must be an integer from 1 to 1000"),
    ({"limit": 1001}, "limit must be an integer from 1 to 1000"),
    ({"where": {"title": {"like": "x"}}}, "unknown operator 'like'"),
    ({"where": {"tags": {"eq": 1}}}, "only 'exists' applies"),
    ({"where": {"pages": {"contains": "4"}}}, "contains needs a string field"),
    ({"where": {"lent": {"gt": True}}}, "supports eq/ne only"),
    ({"where": {"title": {"in": list(range(65))}}}, "at most 64 members"),
    ({"where": {"finished": {"gte": "{{startOfCentury}}"}}}, "unknown token"),
    ({"aggregate": {"op": "sum", "field": "title"}}, "needs a numeric field"),
    ({"aggregate": {"op": "count", "field": "title"}}, "count takes no field"),
    ({"aggregate": {"op": "median", "field": "pages"}}, "unknown op 'median'"),
    ({"groupBy": {"field": "title", "bucket": "month"}}, "bucket needs a date field"),
    ({"groupBy": {"field": "title", "width": 5}}, "width needs a numeric field"),
    ({"groupBy": {"field": "finished", "bucket": "day", "width": 1}}, "bucket and width are exclusive"),
    ({"groupBy": "title", "orderBy": "pages"}, "orders by 'key' or 'value' only"),
    ({"groupBy": "title", "aggregate": {"op": "first", "field": "title"}}, "not a group aggregate"),
    ({"orderBy": "-nope"}, "unknown field 'nope'"),
])
def test_stage_lint_errors(stage, needle):
    lay = _one_control(sync={"method": "local", "collection": "books", **stage})
    errs = [f["detail"] for f in _errors(lay)]
    assert any(needle in d for d in errs), errs


def test_where_depth_and_leaf_caps():
    deep = {"title": "a"}
    for _ in range(9):
        deep = {"and": [deep]}
    lay = _one_control(sync={"method": "local", "collection": "books", "where": deep})
    assert any("nests deeper than 8" in f["detail"] for f in _errors(lay))
    wide = {"and": [{"title": str(i)} for i in range(33)]}
    lay = _one_control(sync={"method": "local", "collection": "books", "where": wide})
    assert any("33 leaves" in f["detail"] for f in _errors(lay))


def test_sync_needs_collection_and_warns_on_wire_keys():
    lay = _one_control(sync={"method": "local", "aggregate": "count", "event": "broadcast"})
    details = _details(lay, "bad_sync")
    assert any("needs a 'collection'" in d for d in details)
    assert any("'event' means nothing" in d for d in details)
    lay = _one_control(sync=bind.local("ghosts", aggregate="count"))
    assert _details(lay, "unknown_collection")


@pytest.mark.parametrize("source_patch, needle", [
    ({"namespace": "shared"}, "namespace 'shared' is reserved"),
    ({"namespace": "-bad"}, "namespace must match"),
    ({"weekStartsOn": "tuesday"}, "weekStartsOn must be one of"),
    ({"collections": {"books": {"fields": {"title": "text"}}}}, "unknown type 'text'"),
    ({"collections": {"books": {"fields": {"id": "string"}}}}, "field 'id' is reserved"),
    ({"collections": {"books": {"fields": {"createdAt": "date", "title": "string"}}}},
     "field 'createdAt' is reserved"),
    ({"collections": {"Books": {"fields": {"title": "string"}}}}, "collection name 'Books' must match"),
    ({"collections": {"books": {"fields": {"Title": "string"}}}}, "field name 'Title' must match"),
    ({"collections": {}}, "non-empty 'collections'"),
    ({"views": {"a": {"from": "b"}, "b": {"from": "a"}}}, "cyclic 'from'"),
    ({"views": {"a": {"from": "nowhere"}}}, "unknown from 'nowhere'"),
    ({"views": {"books": {"from": "books"}}}, "collides with a collection"),
    ({"views": {"v": {"from": "books", "aggregate": "count"}}}, "'aggregate' is not allowed on a view"),
    ({"views": {"v": {"from": "books", "limit": 1001}}}, "view v: limit must be an integer"),
    ({"views": {"v": {"from": "books", "where": {"nope": 1}}}}, "view v: where.nope: unknown field"),
])
def test_source_lint_errors(source_patch, needle):
    lay = _one_control(sync=bind.local("books", aggregate="count"), **source_patch)
    errs = [f["detail"] for f in validate.validate_layout(lay, CAT)
            if f["kind"] == "bad_sources" and f["severity"] == "error"]
    assert any(needle in d for d in errs), errs


def test_view_nesting_cap():
    views = {"v0": {"from": "books"}}
    for i in range(1, 9):
        views[f"v{i}"] = {"from": f"v{i - 1}"}
    lay = _one_control(sync=bind.local("v8", aggregate="count"), views=views)
    assert any("nesting deeper than 8" in d for d in _details(lay, "bad_sources"))


def test_second_local_source_needs_namespace_and_no_duplicate_namespaces():
    lay = _one_control(sync=bind.local("books", aggregate="count", source="db"))
    del lay["sources"]["db"]["namespace"]
    lay["sources"]["other"] = {"type": "local", "collections": {"x": {"fields": {"a": "string"}}}}
    details = _details(lay, "bad_sources")
    assert sum("second local source needs an explicit 'namespace'" in d for d in details) == 2
    lay["sources"]["db"]["namespace"] = lay["sources"]["other"]["namespace"] = "same"
    assert any("already used by source" in d for d in _details(lay, "bad_sources"))


@pytest.mark.parametrize("action, needle", [
    ({"op": "truncate", "collection": "books"}, "op must be one of"),
    ({"op": "update", "collection": "books", "set": {"title": "x"}}, "update needs an 'id'"),
    ({"op": "upsert", "collection": "books", "set": {"title": "x"}}, "upsert needs an 'id'"),
    ({"op": "delete", "collection": "books"}, "delete needs an 'id'"),
    ({"op": "delete", "collection": "books", "id": "b1", "where": {"lent": True}}, "takes no 'where'"),
    ({"op": "insert", "collection": "books", "set": {"title": "x", "createdAt": "{{now}}"}},
     "set.createdAt: reserved field"),
    ({"op": "insert", "collection": "books", "set": {"genre": "sf"}}, "set.genre: unknown field"),
    ({"op": "insert", "collection": "books", "set": {"pages": "412"}}, "not a integer"),
    ({"op": "insert", "collection": "books", "set": {"pages": 1.5}}, "has a fraction"),
    ({"op": "insert", "collection": "books", "set": {"finished": "2026-02-30"}}, "not a valid date"),
    ({"op": "insert", "collection": "books"}, "needs a non-empty 'set'"),
    ({"op": "insert", "collection": "books", "id": "bad id!", "set": {"title": "x"}},
     "id must be 1–128 chars"),
    ({"op": "select", "collection": "books"}, "select needs an 'id'"),
    ({"op": "insert", "collection": "ghosts", "set": {"title": "x"}}, "unknown collection 'ghosts'"),
])
def test_op_lint_errors(action, needle):
    lay = _one_control(action={"method": "local", **action}, ctype="button")
    errs = [f["detail"] for f in _errors(lay) if f["kind"] == "bad_action"]
    assert any(needle in d for d in errs), errs


def test_insert_into_view_is_error_but_select_on_view_is_fine():
    lay = _one_control(action=bind.local_op("insert", "v", set={"title": "x"}), ctype="button",
                       views={"v": {"from": "books"}})
    assert any("'v' is a view" in d for d in _details(lay, "bad_action"))
    lay = _one_control(action=bind.local_op("select", "v", id="{{item}}"), ctype="button",
                       views={"v": {"from": "books"}})
    assert _details(lay, "bad_action") == []


def test_type_mismatch_in_where_is_a_warning_not_an_error():
    lay = _one_control(sync=bind.local("books", where={"pages": "412"}))
    found = [f for f in validate.validate_layout(lay, CAT) if f["kind"] == "bad_stage"]
    assert found and all(f["severity"] == "warn" for f in found)


# ── codegen and contract treat local as app-direct ────────────────────────────

def test_codegen_ignores_local_bindings():
    lay = _layout()
    c = codegen.analyze_layout(lay)
    assert c["actions"] == {} and c["emits"] == {} and c["pushes"] == []
    stub = codegen.generate_service_stub(lay)
    assert "books" not in stub and "hub.on(" not in stub


def test_contract_lists_local_as_app_direct():
    c = extract_contract(_layout())
    assert c["triggers"] == [] and c["feeds"] == []
    kinds = {(d["direction"], d["transport"]) for d in c["appDirect"]}
    assert kinds == {("in", "local"), ("out", "local")}
    addresses = {d["address"] for d in c["appDirect"]}
    assert "books" in addresses and "insert books" in addresses


# ── fixture parity over the app's conformance fixtures ────────────────────────

def _fixture_files():
    root = Path(os.environ.get("CARTER_LOCAL_FIXTURES") or _DEFAULT_A4)
    return sorted(glob.glob(str(root / "*.json")))


@pytest.mark.parametrize("path", _fixture_files() or [None])
def test_fixture_parity(path):
    if path is None:
        pytest.skip("no local-query fixtures (set CARTER_LOCAL_FIXTURES)")
    fx = json.loads(Path(path).read_text())
    store = E.Store(fx)
    fields_of = lambda c: local.fields_for(store.schema, c)  # noqa: E731
    failures = []
    for st in fx["stages"]:
        tag = f"{Path(path).name}.{st['name']}"
        exp = st["expected"]
        # 1) the static lint must agree with the fixture's verdict
        fields = fields_of(st["collection"])
        lint_errors = [m for sev, m in local.lint_stage(st["stage"], fields or {})
                       if sev == "error"] if fields else []
        if exp.get("error") == "unknown-collection":
            if fields is not None:
                failures.append(f"{tag}: lint resolved an unknown collection")
        elif exp.get("error") == "invalid-stage":
            if not lint_errors:
                failures.append(f"{tag}: lint accepted an invalid stage")
        elif lint_errors:
            failures.append(f"{tag}: lint rejected a valid stage: {lint_errors}")
        # 2) the pure evaluator must reproduce the expected result
        try:
            res = store.query(st["collection"], st["stage"])
        except E.InvalidStage as e:
            if exp.get("error") != "invalid-stage":
                failures.append(f"{tag}: evaluator raised {e}")
            continue
        except E.LimitExceeded as e:
            if exp.get("error") != "limit":
                failures.append(f"{tag}: evaluator raised limit: {e}")
            continue
        except E.UnknownCollection:
            if exp.get("error") != "unknown-collection":
                failures.append(f"{tag}: evaluator: unknown collection")
            continue
        if "error" in exp:
            failures.append(f"{tag}: expected {exp['error']}, got a result")
            continue
        failures.extend(f"{tag}: {d}" for d in E.compare(res, exp))
    # 3) rejected writes the lint can see statically (type/reserved/id shape)
    for coll, writes in (fx.get("rejected") or {}).items():
        for w in writes:
            op = {"method": "local", "op": "insert", "collection": coll, "set": w.get("fields") or {}}
            if "id" in w:
                op["id"] = w["id"]
                if w["id"] in {r["id"] for r in store.rows.get(coll, [])}:
                    continue            # a duplicate id is a runtime fact, not lintable
            if op["set"] and not any(sev == "error" for sev, _ in local.lint_op(op, store.schema)):
                failures.append(f"{Path(path).name}: lint accepted rejected write {w}")
    assert failures == [], "\n".join(failures)


# ── singleton collections + set / increment / decrement / toggle (carter-0gj.53) ──

def _singleton_layout(action, **coll):
    cdef = {"singleton": True, "fields": {"lastWatered": "date", "cups": "integer",
                                          "litres": "number", "on": "bool", "note": "string"},
            "defaults": {"cups": 0, "on": False}}
    cdef.update(coll)
    lay = _one_control(action=action, ctype="button")
    lay["sources"]["db"]["collections"]["fern"] = cdef
    lay["tabs"][0]["children"][0]["label"] = "Go"
    return lay


def test_singleton_ops_lint_clean():
    for action in (bind.local_op("set", "fern", set={"lastWatered": "{{now}}"}),
                   bind.local_op("increment", "fern", field="cups"),
                   bind.local_op("decrement", "fern", field="cups", by=2),
                   bind.local_op("increment", "fern", field="litres", by=0.25),
                   bind.local_op("toggle", "fern", field="on")):
        assert _errors(_singleton_layout(action)) == [], action
    assert bind.local_op("increment", "fern", field="cups", by=2) == {
        "method": "local", "op": "increment", "collection": "fern", "field": "cups", "by": 2}


def test_singleton_ops_reject_what_the_app_rejects():
    cases = {
        "needs a singleton collection": bind.local_op("increment", "books", field="pages"),
        "needs a 'field'": bind.local_op("toggle", "fern"),
        "toggle needs a bool field": bind.local_op("toggle", "fern", field="cups"),
        "needs a number or integer field": bind.local_op("increment", "fern", field="note"),
        "has a fraction": bind.local_op("increment", "fern", field="cups", by=0.5),
        "'by' must be a number": bind.local_op("increment", "fern", field="cups", by="x"),
        "unknown field": bind.local_op("toggle", "fern", field="nope"),
        "non-empty 'set'": bind.local_op("set", "fern"),
    }
    for needle, action in cases.items():
        details = " | ".join(_details(_singleton_layout(action)))
        assert needle in details, (needle, details)


def test_singleton_defaults_lint():
    ok = bind.local_op("toggle", "fern", field="on")
    assert _errors(_singleton_layout(ok)) == []
    bad = {"defaults need singleton": ({"singleton": False}, "'defaults' needs 'singleton': true"),
           "undeclared": ({"defaults": {"zzz": 1}}, "undeclared field 'zzz'"),
           "mistyped": ({"defaults": {"cups": "x"}}, "is not a integer"),
           "token": ({"defaults": {"lastWatered": "{{now}}"}}, "not a token")}
    for name, (over, needle) in bad.items():
        details = " | ".join(_details(_singleton_layout(ok, **over)))
        assert needle in details, (name, details)


# ── span aggregate (carter-73q2.31) ───────────────────────────────────────────

def test_span_aggregate_lint():
    f = {"started": "date", "finished": "date", "title": "string", "pages": "integer"}
    errs = lambda st: [m for sev, m in local.lint_stage(st, f) if sev == "error"]  # noqa: E731
    assert "span" in local.AGGREGATE_OPS
    assert errs({"aggregate": {"op": "span", "field": "finished"}}) == []
    assert errs({"aggregate": {"op": "span", "field": "started", "to": "finished"}}) == []
    assert errs({"where": {"title": "Dune"}, "aggregate": {"op": "span", "field": "started", "to": "finished"}}) == []
    assert any("needs a 'field'" in m for m in errs({"aggregate": "span"}))
    assert any("span needs a date field" in m for m in errs({"aggregate": {"op": "span", "field": "pages"}}))
    assert any("span.to needs a date field" in m
               for m in errs({"aggregate": {"op": "span", "field": "started", "to": "title"}}))
    assert any("unknown field 'nope'" in m for m in errs({"aggregate": {"op": "span", "field": "started", "to": "nope"}}))
    assert any("only for span" in m for m in errs({"aggregate": {"op": "max", "field": "started", "to": "finished"}}))
    assert any("not a group aggregate" in m
               for m in errs({"groupBy": "title", "aggregate": {"op": "span", "field": "started"}}))


def test_span_aggregate_in_a_layout_lints_clean():
    layout = _one_control(sync={"method": "local", "collection": "books",
                                "aggregate": {"op": "span", "field": "finished"}})
    assert _errors(layout) == []


# ── range buckets, fill, distinct over a bucket (carter-73q2.32) ──────────────

def test_range_fill_and_distinct_bucket_lint():
    f = {"started": "date", "finished": "date", "title": "string", "pages": "integer"}
    errs = lambda st: [m for sev, m in local.lint_stage(st, f) if sev == "error"]  # noqa: E731
    ok = [
        {"groupBy": {"range": ["started", "finished"], "bucket": "day"}},
        {"groupBy": {"range": ["started", "finished"], "bucket": "week", "fill": True},
         "aggregate": {"op": "sum", "field": "pages"}},
        {"groupBy": {"field": "finished", "bucket": "month", "fill": {"from": "{{startOfYear}}", "to": "{{today}}"}}},
        {"groupBy": {"field": "finished", "bucket": "day", "fill": False}},
        {"aggregate": {"op": "distinct", "field": "finished", "bucket": "day"}},
        {"groupBy": {"field": "finished", "bucket": "month"},
         "aggregate": {"op": "distinct", "field": "finished", "bucket": "day"}},
    ]
    for st in ok:
        assert errs(st) == [], st
    bad = {
        "range must be [fromField, toField]": {"groupBy": {"range": ["started"], "bucket": "day"}},
        "range needs a bucket": {"groupBy": {"range": ["started", "finished"]}},
        "range needs date fields": {"groupBy": {"range": ["title", "finished"], "bucket": "day"}},
        "range replaces field": {"groupBy": {"range": ["started", "finished"], "field": "started", "bucket": "day"}},
        "fill needs a date bucket": {"groupBy": {"field": "pages", "width": 10, "fill": True}},
        "fill: unknown key": {"groupBy": {"field": "finished", "bucket": "day", "fill": {"since": "2026-01-01"}}},
        "{{selected}} is not a date": {"groupBy": {"field": "finished", "bucket": "day", "fill": {"from": "{{selected}}"}}},
        "bucket is only for distinct": {"aggregate": {"op": "sum", "field": "pages", "bucket": "day"}},
        "distinct bucket needs a date field": {"aggregate": {"op": "distinct", "field": "pages", "bucket": "day"}},
    }
    for needle, st in bad.items():
        assert any(needle in m for m in errs(st)), (needle, errs(st))


def test_range_groupby_in_a_layout_lints_clean():
    layout = _one_control(sync={"method": "local", "collection": "books",
                                "groupBy": {"range": ["finished", "finished"], "bucket": "day", "fill": True}})
    assert _errors(layout) == []


# ── two-level groupBy + having (carter-73q2.36) ───────────────────────────────

_SERIES_FIELDS = {"date": "date", "exercise": "string", "weight": "number", "when": "date",
                  "plant": "string", "value": "integer", "blob": "json"}


def _stage_errors(st, fields=_SERIES_FIELDS):
    return [m for sev, m in local.lint_stage(st, fields) if sev == "error"]


def test_series_and_having_lint_clean():
    ok = [
        {"groupBy": [{"field": "date", "bucket": "week"}, "exercise"], "aggregate": {"op": "max", "field": "weight"}},
        {"groupBy": ["plant", "exercise"], "orderBy": "-key", "limit": 2},
        {"groupBy": [{"field": "date", "bucket": "week", "fill": True}, "exercise"]},
        {"groupBy": [{"field": "weight", "width": 1}, "exercise"]},
        {"groupBy": "plant", "aggregate": {"op": "max", "field": "when"}, "having": {"value": {"lt": {"daysAgo": 7}}}},
        {"groupBy": "plant", "having": {"value": {"gte": 2}}},
        {"groupBy": "plant", "aggregate": {"op": "sum", "field": "value"}, "having": {"value": {"gt": 300}}},
        {"groupBy": "plant", "having": {"key": {"in": ["fern", "basil"]}}, "orderBy": "-value"},
        {"groupBy": "plant", "having": {"or": [{"key": {"eq": "mint"}}, {"value": {"gt": 1}}]}},
        {"groupBy": [{"field": "date", "bucket": "week"}, "exercise"], "having": {"value": {"lt": 2}}},
        {"groupBy": {"field": "when", "bucket": "day", "fill": False}, "having": {"value": {"gt": 0}}},
    ]
    for st in ok:
        assert _stage_errors(st) == [], (st, _stage_errors(st))
        assert not any("unknown stage key" in m for _, m in local.lint_stage(st, _SERIES_FIELDS))


def test_series_and_having_lint_rejects_what_the_app_rejects():
    # LocalSeriesTests.testBadArrayGroupByIsRejected + testClosedGrammarRejects…
    bad = [
        ({"groupBy": ["plant"]}, 'must be [primary, "seriesField"]'),
        ({"groupBy": ["plant", "exercise", "date"]}, 'must be [primary, "seriesField"]'),
        ({"groupBy": [["plant", "exercise"], "date"]}, "nests at most two levels"),
        ({"groupBy": ["plant", {"field": "exercise"}]}, 'must be [primary, "seriesField"]'),
        ({"aggregate": "count", "having": {"value": {"gt": 1}}}, "having needs a groupBy"),
        ({"groupBy": "plant", "having": {"plant": {"eq": "fern"}}}, "compares 'key' or 'value' only"),
        ({"groupBy": {"field": "when", "bucket": "day", "fill": True}, "having": {"value": {"gt": 0}}},
         "does not combine with fill"),
        ({"groupBy": {"field": "when", "bucket": "day", "fill": {}}, "having": {"value": {"gt": 0}}},
         "does not combine with fill"),
        ({"groupBy": "plant", "having": {"value": {"gt": {"daysAgo": 7}}}}, "daysAgo compares a date value"),
        ({"groupBy": "plant", "aggregate": {"op": "max", "field": "when"},
          "having": {"value": {"lt": {"daysAgo": -1}}}}, "daysAgo must be a whole number"),
        ({"groupBy": "plant", "aggregate": {"op": "max", "field": "when"},
          "having": {"value": {"lt": {"daysAgo": 1.5}}}}, "daysAgo must be a whole number"),
        ({"groupBy": [{"range": ["when", "when"], "bucket": "day"}, "plant"]}, "range groupBy takes no series"),
        ({"groupBy": {"range": ["when", "when"], "bucket": "day"}, "having": {"value": {"gt": 1}}},
         "having does not combine with a range"),
        ({"groupBy": ["plant", "when"], "orderBy": "-value"}, "series query orders by 'key' only"),
        ({"groupBy": ["plant", "nope"]}, "unknown series field 'nope'"),
        ({"groupBy": ["plant", "blob"]}, "cannot group a json field"),
        ({"groupBy": "plant", "having": {"value": {"like": 1}}}, "unknown operator 'like'"),
    ]
    for st, needle in bad:
        errs = _stage_errors(st)
        assert any(needle in m for m in errs), (st, needle, errs)


def test_series_and_having_ride_a_layout_sync():
    sync = bind.local("books", group_by=[{"field": "finished", "bucket": "month"}, "title"],
                      aggregate={"op": "max", "field": "pages"})
    assert _errors(_one_control(sync=sync, ctype="chart")) == []
    sync = bind.local("books", group_by="title", aggregate={"op": "max", "field": "finished"},
                      having={"value": {"lt": {"daysAgo": 7}}})
    assert sync["having"] == {"value": {"lt": {"daysAgo": 7}}}
    assert _errors(_one_control(sync=sync)) == []
    lay = _one_control(sync={"method": "local", "collection": "books", "having": {"value": {"gt": 1}}})
    assert any("having needs a groupBy" in d for d in [f["detail"] for f in _errors(lay)])


def _series_store(lifts=(), waterings=()):
    """LocalSeriesTests' store: today is Monday 2026-09-28 in New York."""
    return E.Store({
        "schema": {"type": "local", "namespace": "fixture", "collections": {
            "lifts": {"fields": {"date": "date", "exercise": "string", "weight": "number"}},
            "waterings": {"fields": {"when": "date", "plant": "string", "value": "integer"}}}},
        "timeZone": "America/New_York", "now": "2026-09-28T12:00:00.000Z", "weekStartsOn": "monday",
        "records": {
            "lifts": [{"id": i, "fields": {"date": d, "exercise": e, "weight": w}} for i, d, e, w in lifts],
            "waterings": [{"id": i, "fields": {"when": d, "plant": p, "value": 250}} for i, d, p in waterings]},
    })


_LIFTS = [("a", "2026-09-07", "squat", 100), ("b", "2026-09-09", "squat", 110), ("c", "2026-09-08", "bench", 70),
          ("d", "2026-09-15", "bench", 75), ("e", "2026-09-22", "squat", 120)]
_WATERINGS = [("w1", "2026-09-10", "fern"), ("w2", "2026-09-25", "fern"),
              ("w3", "2026-09-15T14:00:00.000Z", "cactus"), ("w4", "2026-09-21", "basil"),
              ("w5", "2026-09-21T03:30:00.000Z", "mint")]
_WEEKLY_MAX = {"groupBy": [{"field": "date", "bucket": "week"}, "exercise"], "aggregate": {"op": "max", "field": "weight"}}


def _cells(res):
    assert res["shape"] == "groups"
    fmt = lambda v: "-" if v is None else str(int(v))  # noqa: E731
    return [f"{g['key']}/{g['series']}={fmt(g['value'])}" for g in res["groups"]]


def _keys(res):
    return [g["key"] for g in res["groups"]]


def test_eval_series_grid_matches_the_app():
    store = _series_store(_LIFTS)
    assert _cells(store.query("lifts", _WEEKLY_MAX)) == [
        "2026-09-07/bench=70", "2026-09-07/squat=110", "2026-09-14/bench=75", "2026-09-14/squat=-",
        "2026-09-21/bench=-", "2026-09-21/squat=120"]
    st = {"groupBy": [{"field": "date", "bucket": "week"}, "exercise"], "orderBy": "-key", "limit": 2}
    assert _cells(store.query("lifts", st)) == [
        "2026-09-21/bench=0", "2026-09-21/squat=1", "2026-09-14/bench=1", "2026-09-14/squat=0"]
    filled = _series_store([("a", "2026-09-07", "squat", 100), ("b", "2026-09-08", "bench", 60),
                            ("c", "2026-09-22", "squat", 105)])
    st = {"groupBy": [{"field": "date", "bucket": "week", "fill": True}, "exercise"]}
    assert _cells(filled.query("lifts", st)) == [
        "2026-09-07/bench=1", "2026-09-07/squat=1", "2026-09-14/bench=0", "2026-09-14/squat=0",
        "2026-09-21/bench=0", "2026-09-21/squat=1"]


def test_eval_having_matches_the_app():
    store = _series_store(waterings=_WATERINGS)
    last = {"groupBy": "plant", "aggregate": {"op": "max", "field": "when"}, "having": {"value": {"lt": {"daysAgo": 7}}}}
    assert _keys(store.query("waterings", last)) == ["cactus", "mint"]
    last["having"] = {"value": {"lte": {"daysAgo": 7}}}
    assert _keys(store.query("waterings", last)) == ["basil", "cactus", "mint"]
    q = lambda st: _keys(store.query("waterings", st))  # noqa: E731
    assert q({"groupBy": "plant", "having": {"value": {"gte": 2}}}) == ["fern"]
    assert q({"groupBy": "plant", "aggregate": {"op": "sum", "field": "value"}, "having": {"value": {"gt": 300}}}) == ["fern"]
    assert q({"groupBy": "plant", "having": {"key": {"in": ["fern", "basil"]}}, "orderBy": "-value"}) == ["fern", "basil"]
    assert q({"groupBy": "plant", "having": {"or": [{"key": {"eq": "mint"}}, {"value": {"gt": 1}}]}}) == ["fern", "mint"]


def test_eval_having_on_series_cells_leaves_gaps():
    store = _series_store(_LIFTS)
    st = dict(_WEEKLY_MAX, having={"value": {"gte": 100}})
    assert _cells(store.query("lifts", st)) == ["2026-09-07/squat=110", "2026-09-21/squat=120"]
    st = {"groupBy": [{"field": "date", "bucket": "week"}, "exercise"], "having": {"value": {"lt": 2}}}
    assert _cells(store.query("lifts", st)) == [
        "2026-09-07/bench=1", "2026-09-07/squat=-", "2026-09-14/bench=1", "2026-09-14/squat=-",
        "2026-09-21/bench=-", "2026-09-21/squat=1"]
    st = {"groupBy": [{"field": "date", "bucket": "week"}, "exercise"], "having": {"value": {"gte": 1}},
          "aggregate": {"op": "sum", "field": "weight"}}
    assert _cells(store.query("lifts", st)) == [
        "2026-09-07/bench=70", "2026-09-07/squat=210", "2026-09-14/bench=75", "2026-09-14/squat=-",
        "2026-09-21/bench=-", "2026-09-21/squat=120"]


def test_eval_series_keeps_the_first_twelve_series_whole():
    lifts = [(f"r{k}-{e}", "2026-09-01", f"s{e:02d}", k) for k in range(40) for e in range(20)]
    res = _series_store(lifts).query("lifts", {"groupBy": [{"field": "weight", "width": 1}, "exercise"]})
    series = list(dict.fromkeys(g["series"] for g in res["groups"]))
    assert series == [f"s{e:02d}" for e in range(12)]
    assert len({g["key"] for g in res["groups"]}) == 40 and len(res["groups"]) == 40 * 12
    assert all(g["value"] == 1 for g in res["groups"])


def test_eval_rejects_the_closed_grammar_combinations():
    store = _series_store(_LIFTS, _WATERINGS)
    for st in [{"aggregate": "count", "having": {"value": {"gt": 1}}},
               {"groupBy": "plant", "having": {"plant": {"eq": "fern"}}},
               {"groupBy": {"field": "when", "bucket": "day", "fill": True}, "having": {"value": {"gt": 0}}},
               {"groupBy": "plant", "having": {"value": {"gt": {"daysAgo": 7}}}},
               {"groupBy": [{"range": ["when", "when"], "bucket": "day"}, "plant"]},
               {"groupBy": ["plant", "when"], "orderBy": "-value"},
               {"groupBy": ["plant", "nope"]}]:
        with pytest.raises(E.InvalidStage):
            store.query("waterings", st)
