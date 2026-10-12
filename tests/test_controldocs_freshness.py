"""The vendored ControlDocs match the app's ControlDocs (carter-mfzq).

The app repo's ``CAR-TER/ControlDocs`` is the source of truth; carterkit ships a
copy in ``carterkit/controldocs`` that ``scripts/sync-controldocs.sh`` refreshes by
hand. This test catches drift before a release instead of after it.

It only runs where the sibling app checkout exists (the CAR-TER workspace); CI and
sdist/wheel builds have no app repo and skip. Overrides:

- ``CARTER_APP_CONTROLDOCS``: path to the app's ControlDocs directory.
- ``CARTER_APP_CONTROLDOCS_REF``: compare against another git ref of the app repo
  (for example a release tag). Set it empty to compare the working tree.

The default compares the app repo's COMMITTED ``master`` (the kit tracks app trunk),
so another session's uncommitted app edits never count. A non-git sibling compares
its files; a git sibling without a ``master`` ref skips.
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


DEFAULT_REF = "master"


def _is_git(docs_dir):
    return subprocess.run(["git", "-C", str(docs_dir), "rev-parse", "--show-toplevel"],
                          capture_output=True).returncode == 0


def _ref_exists(docs_dir, ref):
    return subprocess.run(["git", "-C", str(docs_dir), "rev-parse", "--verify", "-q",
                           f"{ref}^{{commit}}"], capture_output=True).returncode == 0


def _resolve_ref(docs_dir, env=None):
    """The git ref to compare: env var if set (empty = working tree), else master
    when docs_dir is a git checkout, else None (working tree)."""
    env = os.environ if env is None else env
    if "CARTER_APP_CONTROLDOCS_REF" in env:
        return env["CARTER_APP_CONTROLDOCS_REF"] or None
    return DEFAULT_REF if _is_git(docs_dir) else None


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
    ref = _resolve_ref(app_dir)
    if ref and not _ref_exists(app_dir, ref):
        pytest.skip(f"app repo has no ref {ref!r} to compare against")
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


def _check(app_dir, ref=None):
    env = {k: v for k, v in os.environ.items()
           if k not in ("APP_REF", "CARTER_APP_CONTROLDOCS_REF")}
    env["APP_REPO"] = str(app_dir)
    if ref is not None:
        env["APP_REF"] = ref
    return subprocess.run(["bash", str(SCRIPT), "--check"], capture_output=True, text=True,
                          env=env)


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


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


def test_sync_script_check_reports_kit_only_docs(tmp_path):
    app = tmp_path / "ControlDocs"
    app.mkdir()
    names = sorted(_docs(VENDORED))
    for name in names[1:]:                      # the app "deleted" the first doc
        (app / name).write_bytes((VENDORED / name).read_bytes())
    res = _check(app)
    assert res.returncode == 1
    assert res.stdout.strip() == f"only in carterkit:      {names[0]}"


def test_check_against_a_git_ref_ignores_the_working_tree(tmp_path):
    """APP_REF / CARTER_APP_CONTROLDOCS_REF compare a committed app ref, so another
    session's uncommitted ControlDocs edits in the app checkout don't count."""
    repo = tmp_path / "app"
    docs = repo / "CAR-TER" / "ControlDocs"
    docs.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "master")
    vendored = _docs(VENDORED)
    for name, data in vendored.items():
        (docs / name).write_bytes(data)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "docs")

    first = sorted(vendored)[0]
    (docs / first).write_bytes(b"uncommitted edit\n")   # dirty working tree only

    assert _check(docs, ref="").returncode == 1            # APP_REF= : working tree drifts
    clean = _check(docs, ref="master")                   # committed ref: in sync
    assert clean.returncode == 0, clean.stdout + clean.stderr
    assert drift(_app_docs_at_ref(docs, "master"), vendored) == []

    bad = _check(docs, ref="no-such-ref")
    assert bad.returncode == 2
    assert "unknown app ref" in bad.stderr


def _app_repo(tmp_path, branch="master"):
    """A git app checkout with the vendored docs committed on `branch`."""
    repo = tmp_path / "app"
    docs = repo / "CAR-TER" / "ControlDocs"
    docs.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", branch)
    for name, data in _docs(VENDORED).items():
        (docs / name).write_bytes(data)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "docs")
    return docs


def test_default_ref_is_committed_master_and_ignores_a_dirty_tree(tmp_path, monkeypatch):
    docs = _app_repo(tmp_path)
    first = sorted(docs.glob("*.md"))[0]
    first.write_bytes(b"uncommitted edit\n")
    monkeypatch.delenv("CARTER_APP_CONTROLDOCS_REF", raising=False)
    monkeypatch.setenv("CARTER_APP_CONTROLDOCS", str(docs))
    assert _resolve_ref(docs) == "master"
    test_vendored_controldocs_match_the_app()          # passes: master matches
    monkeypatch.setenv("CARTER_APP_CONTROLDOCS_REF", "")   # empty = working tree
    assert _resolve_ref(docs) is None
    with pytest.raises(AssertionError):
        test_vendored_controldocs_match_the_app()


def test_missing_default_ref_skips(tmp_path, monkeypatch):
    docs = _app_repo(tmp_path, branch="trunk")
    monkeypatch.delenv("CARTER_APP_CONTROLDOCS_REF", raising=False)
    monkeypatch.setenv("CARTER_APP_CONTROLDOCS", str(docs))
    with pytest.raises(pytest.skip.Exception, match="master"):
        test_vendored_controldocs_match_the_app()


def test_non_git_sibling_uses_the_working_tree(tmp_path):
    plain = tmp_path / "ControlDocs"
    plain.mkdir()
    assert _resolve_ref(plain, env={}) is None


def test_check_defaults_to_master(tmp_path):
    docs = _app_repo(tmp_path)
    first = sorted(docs.glob("*.md"))[0]
    first.write_bytes(b"uncommitted edit\n")
    assert _check(docs).returncode == 0                  # no ref given: committed master
    assert _check(docs, ref="").returncode == 1          # APP_REF= : working tree
    env = {k: v for k, v in os.environ.items() if k != "APP_REF"}
    env.update(APP_REPO=str(docs), CARTER_APP_CONTROLDOCS_REF="")
    assert subprocess.run(["bash", str(SCRIPT), "--check"], env=env,
                          capture_output=True).returncode == 1
    assert _check(_app_repo(tmp_path / "x", branch="trunk")).returncode == 2


def test_help_prints_the_whole_header():
    out = subprocess.run(["bash", str(SCRIPT), "-h"], capture_output=True, text=True)
    assert out.returncode == 0
    assert "Exit codes:" in out.stdout and "tests/test_controldocs_freshness.py" in out.stdout
