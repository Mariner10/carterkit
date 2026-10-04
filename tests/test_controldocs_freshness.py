"""The vendored ControlDocs match the app's ControlDocs (carter-mfzq).

The app repo's ``CAR-TER/ControlDocs`` is the source of truth; carterkit ships a
copy in ``carterkit/controldocs`` that ``scripts/sync-controldocs.sh`` refreshes by
hand. This test catches drift before a release instead of after it.

It only runs where the sibling app checkout exists (the CAR-TER workspace); CI and
sdist/wheel builds have no app repo and skip. Overrides:

- ``CARTER_APP_CONTROLDOCS``: path to the app's ControlDocs directory.
- ``CARTER_APP_CONTROLDOCS_REF``: compare against a git ref of the app repo (for
  example a release tag) instead of its working tree.
"""
import os
import subprocess
from pathlib import Path

import pytest

KIT_ROOT = Path(__file__).resolve().parents[1]
VENDORED = KIT_ROOT / "carterkit" / "controldocs"
APP_REL = Path("CAR-TER") / "CAR-TER" / "ControlDocs"   # <workspace>/CAR-TER/CAR-TER/ControlDocs


def _find_app_docs():
    override = os.environ.get("CARTER_APP_CONTROLDOCS")
    if override:
        return Path(override).expanduser()
    # The kit is <workspace>/carterkit, or a worktree under <workspace>/.worktrees/.
    for parent in KIT_ROOT.parents:
        candidate = parent / APP_REL
        if candidate.is_dir():
            return candidate
    return None


def _app_docs_at_ref(docs_dir, ref):
    """{name: bytes} for the *.md docs in docs_dir at git ref."""
    top = subprocess.run(["git", "-C", str(docs_dir), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True, check=True).stdout.strip()
    rel = Path(docs_dir).resolve().relative_to(Path(top).resolve()).as_posix()
    names = subprocess.run(["git", "-C", top, "ls-tree", "--name-only", f"{ref}:{rel}"],
                           capture_output=True, text=True, check=True).stdout.split()
    return {n: subprocess.run(["git", "-C", top, "show", f"{ref}:{rel}/{n}"],
                              capture_output=True, check=True).stdout
            for n in names if n.endswith(".md")}


def _docs(directory):
    return {p.name: p.read_bytes() for p in Path(directory).glob("*.md")}


def drift(app, kit):
    """Sorted human-readable drift lines between two {name: bytes} maps."""
    lines = []
    for name in sorted(set(app) | set(kit)):
        if name not in kit:
            lines.append(f"missing from carterkit: {name}")
        elif name not in app:
            lines.append(f"only in carterkit:      {name}")
        elif app[name] != kit[name]:
            lines.append(f"differs:                {name}")
    return lines


def test_drift_lists_every_kind_of_difference():
    app = {"a.md": b"1", "b.md": b"2", "c.md": b"3"}
    kit = {"a.md": b"1", "b.md": b"X", "d.md": b"4"}
    assert drift(app, kit) == [
        "differs:                b.md",
        "missing from carterkit: c.md",
        "only in carterkit:      d.md",
    ]
    assert drift(app, dict(app)) == []


def test_vendored_controldocs_match_the_app():
    app_dir = _find_app_docs()
    if app_dir is None or not app_dir.is_dir():
        pytest.skip("sibling CAR-TER app repo not found (CI / package build)")
    ref = os.environ.get("CARTER_APP_CONTROLDOCS_REF")
    app = _app_docs_at_ref(app_dir, ref) if ref else _docs(app_dir)
    lines = drift(app, _docs(VENDORED))
    source = f"{app_dir} @ {ref}" if ref else str(app_dir)
    assert not lines, (
        f"carterkit/controldocs drifted from {source} ({len(lines)} files); "
        "re-vendor with scripts/sync-controldocs.sh:\n  " + "\n  ".join(lines))


def test_skips_without_the_sibling_app_repo(monkeypatch, tmp_path):
    monkeypatch.setenv("CARTER_APP_CONTROLDOCS", str(tmp_path / "absent"))
    with pytest.raises(pytest.skip.Exception):
        test_vendored_controldocs_match_the_app()


SCRIPT = KIT_ROOT / "scripts" / "sync-controldocs.sh"


def _check(app_dir):
    return subprocess.run(["bash", str(SCRIPT), "--check"], capture_output=True, text=True,
                          env={**os.environ, "APP_REPO": str(app_dir)})


def test_sync_script_check_mode(tmp_path):
    app = tmp_path / "ControlDocs"
    app.mkdir()
    for name, data in _docs(VENDORED).items():
        (app / name).write_bytes(data)
    clean = _check(app)
    assert clean.returncode == 0, clean.stdout + clean.stderr

    first = sorted(app.glob("*.md"))[0]
    first.write_bytes(first.read_bytes() + b"\n")
    (app / "zz-new.md").write_text("new\n")
    dirty = _check(app)
    assert dirty.returncode == 1
    assert f"differs:                {first.name}" in dirty.stdout
    assert "missing from carterkit: zz-new.md" in dirty.stdout
    # --check never touches the vendored copy.
    assert not (VENDORED / "zz-new.md").exists()
