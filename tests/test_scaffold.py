"""Tests for `carterkit new`."""
import json
import py_compile

import pytest

from carterkit import cli, scaffold


def test_new_creates_project(tmp_path, capsys):
    d = tmp_path / "demo"
    assert cli.main(["new", str(d)]) == 0
    hello = (d / "hello.py").read_text()
    assert "secrets" in hello and "Scan the QR" in hello and "asyncio.sleep(2)" in hello
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


def test_hello_without_credential_prints_the_qr_and_waits(tmp_path):
    import subprocess, sys
    d = tmp_path / "demo"
    scaffold.scaffold(str(d))
    import os
    env = {"PYTHONPATH": os.getcwd(), "PATH": "", "CARTERKIT_HOST": "127.0.0.1",
           "CARTERKIT_PAIR_TIMEOUT": "1"}
    r = subprocess.run([sys.executable, str(d / "hello.py")], capture_output=True, text=True,
                       env=env, cwd=str(d), timeout=60)
    assert (d / ".carterkit" / "session.json").is_file()     # the pairing lives in the project
    assert ".carterkit/" in (d / ".gitignore").read_text()
    assert "Scan this with the CAR-TER app" in r.stdout
    assert "Hubs -> Add Hub" not in r.stdout
    assert "No phone joined" in r.stdout and r.returncode == 1


# ─── starter kits (carterkit new --template) ────────────────────────────────

KIT_NAMES = list(scaffold.KITS)


def test_list_names_every_kit(capsys):
    assert cli.main(["new", "--list"]) == 0
    out = capsys.readouterr().out
    assert len(KIT_NAMES) >= 6
    for name in KIT_NAMES:
        assert name in out


def test_every_kit_is_packaged():
    from importlib.resources import files
    root = files("carterkit") / "scaffold_templates" / "kits"
    assert sorted(p.name for p in root.iterdir() if p.is_dir()) == sorted(KIT_NAMES)


@pytest.mark.parametrize("kit", KIT_NAMES)
def test_template_writes_the_kit(tmp_path, capsys, kit):
    d = tmp_path / "my-kit"
    assert cli.main(["new", str(d), "--template", kit]) == 0
    assert "python hub.py" in capsys.readouterr().out
    for f in ("layout.json", "hub.py", "README.md", ".gitignore", ".vscode/settings.json",
              "secrets/.gitignore"):
        assert (d / f).is_file(), f
    assert not (d / "hello.py").exists()
    text = "".join((d / f).read_text() for f in ("layout.json", "hub.py", "README.md"))
    assert "__NAME__" not in text and "__ID__" not in text
    assert json.loads((d / "layout.json").read_text())["id"] == "my-kit"
    readme = (d / "README.md").read_text()
    assert readme.startswith("# my-kit") and "python hub.py" in readme and "Change first" in readme
    py_compile.compile(str(d / "hub.py"), doraise=True)


@pytest.mark.parametrize("kit", KIT_NAMES)
def test_kit_layout_validates_clean(tmp_path, capsys, kit):
    d = tmp_path / "k"
    scaffold.scaffold(str(d), template=kit)
    assert cli.main(["validate", str(d / "layout.json")]) == 0
    assert "No issues found" in capsys.readouterr().out


def test_unknown_template_refused(tmp_path, capsys):
    d = tmp_path / "x"
    assert cli.main(["new", str(d), "--template", "nope"]) == 1
    assert "no starter kit 'nope'" in capsys.readouterr().err and not d.exists()
    with pytest.raises(ValueError):
        scaffold.scaffold(str(d), template="nope")


def test_new_without_name_or_list_is_usage_error(capsys):
    assert cli.main(["new"]) == 2
    assert "--list" in capsys.readouterr().err
