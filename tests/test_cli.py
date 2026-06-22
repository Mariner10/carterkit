"""Tests for the carterkit CLI."""

import json

import carterkit
from carterkit import cli


def test_catalog_json(capsys):
    assert cli.main(["catalog", "--json"]) == 0
    cat = json.loads(capsys.readouterr().out)
    assert "gauge" in cat and "button" in cat


def test_catalog_table(capsys):
    assert cli.main(["catalog"]) == 0
    assert "gauge" in capsys.readouterr().out


def test_doc(capsys):
    assert cli.main(["doc", "gauge"]) == 0
    assert "# Gauge" in capsys.readouterr().out


def test_doc_unknown(capsys):
    assert cli.main(["doc", "frobnicator"]) == 1


def test_examples_list(capsys):
    assert cli.main(["examples", "button"]) == 0
    assert "•" in capsys.readouterr().out


def test_version(capsys):
    assert cli.main(["version"]) == 0
    assert capsys.readouterr().out.strip() == carterkit.__version__


def test_validate_clean(tmp_path):
    b = carterkit.LayoutBuffer.blank(columns=4, rows=4)
    b.add_control(carterkit.build.gauge(id="cpu", min=0, max=100), default_span=[2, 2])
    f = tmp_path / "layout.json"
    f.write_text(json.dumps(b.layout))
    assert cli.main(["validate", str(f)]) == 0


def test_gen_emits_meshsocket_service(tmp_path, capsys):
    b = carterkit.LayoutBuffer.blank(columns=4, rows=4)
    b.add_control(carterkit.build.button(id="go"))
    f = tmp_path / "layout.json"
    f.write_text(json.dumps(b.layout))
    assert cli.main(["gen", str(f)]) == 0
    assert "from meshsocket import MeshSocket" in capsys.readouterr().out
