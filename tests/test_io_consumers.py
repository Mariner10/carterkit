"""Consumers of a doc's `io:` block: `carterkit doc` Sends/Receives/Sample, validate io warnings."""
from carterkit import cli, validate_layout
from carterkit import catalog as cat, controldocs_dir


def _lay(ch):
    return {"version": 1, "tabs": [{"title": "T", "icon": "x", "children": [ch]}]}


def _io(layout):
    cg = cat.build_catalog(controldocs_dir(), include_theme=True)
    return [f for f in validate_layout(layout, cg) if f["kind"].startswith("io_")]


def test_doc_shows_io_section(capsys):
    assert cli.main(["doc", "slider"]) == 0
    out = capsys.readouterr().out
    assert "## Sends" in out and "the number you slid to" in out
    assert "## Receives" in out and "## Sample" in out and "40 then 70" in out


def test_doc_without_io_has_no_section(capsys):
    assert cli.main(["doc", "form"]) == 0
    assert "## Sends" not in capsys.readouterr().out


def test_unemitted_action_warns():
    f = _io(_lay({"type": "slider", "id": "s", "longPressAction": {"event": "x"}}))
    assert [(x["severity"], x["kind"]) for x in f] == [("warn", "io_unemitted")]


def test_emitted_action_is_clean():
    assert _io(_lay({"type": "slider", "id": "s", "action": {"event": "x"}})) == []


def test_doc_without_io_never_warns():
    assert _io(_lay({"type": "form", "id": "l", "longPressAction": {"event": "x"}})) == []


def test_sync_shape_mismatch_warns():
    sync = {"method": "local", "collection": "c"}
    f = _io(_lay({"type": "slider", "id": "s", "sync": [sync]}))
    assert [x["kind"] for x in f] == ["io_sync_shape"]
    ok = dict(sync, aggregate="count")
    assert _io(_lay({"type": "slider", "id": "s", "sync": [ok]})) == []
