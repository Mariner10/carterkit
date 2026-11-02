"""Tests for `carterkit new`."""
import json
import py_compile

import pytest

from carterkit import cli, scaffold


def test_new_creates_project(tmp_path, capsys):
    d = tmp_path / "demo"
    assert cli.main(["new", str(d)]) == 0
    hello = (d / "hello.py").read_text()
    assert "secrets" in hello and "Add Hub" in hello and "asyncio.sleep(2)" in hello
    py_compile.compile(str(d / "hello.py"), doraise=True)
    assert (d / "secrets" / ".gitignore").read_text().splitlines() == ["*", "!.gitignore"]
    s = json.loads((d / ".vscode" / "settings.json").read_text())
    assert s["python.analysis.typeCheckingMode"] == "basic"
    assert len((d / "README.md").read_text().strip().splitlines()) <= 4


def test_new_accepts_empty_dir(tmp_path):
    d = tmp_path / "x"
    d.mkdir()
    scaffold.scaffold(str(d))
    assert (d / "hello.py").exists()


def test_new_refuses_non_empty(tmp_path, capsys):
    d = tmp_path / "x"
    d.mkdir()
    (d / "keep.txt").write_text("hi")
    assert cli.main(["new", str(d)]) == 1
    assert not (d / "hello.py").exists()
    assert "not empty" in capsys.readouterr().err
    with pytest.raises(FileExistsError):
        scaffold.scaffold(str(d))


def test_hello_hint_without_credential(tmp_path):
    import subprocess, sys
    d = tmp_path / "demo"
    scaffold.scaffold(str(d))
    r = subprocess.run([sys.executable, str(d / "hello.py")], capture_output=True, text=True,
                       env={"PYTHONPATH": ".", "PATH": ""}, timeout=60)
    assert "Hubs -> Add Hub" in r.stdout
