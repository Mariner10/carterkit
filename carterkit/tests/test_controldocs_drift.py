"""Vendored ControlDocs must equal the pinned CAR-TER ControlDocs.

``carterkit/controldocs/SOURCE`` pins the CAR-TER repo and a commit SHA (any
``key: value`` / ``key=value`` / bare-token layout; the first 40-hex token is the
commit, the first URL or path-like token is the repo). Every file vendored under
``carterkit/controldocs`` must be byte-identical to the file at that commit, and
no file may be missing or extra.

Overrides: ``CARTER_APP_REPO`` (local clone of CAR-TER) and
``CARTER_APP_CONTROLDOCS_REL`` (ControlDocs dir inside it).
"""
import os
import re
import subprocess
from pathlib import Path

import pytest

KIT_ROOT = Path(__file__).resolve().parents[2]
VENDORED = KIT_ROOT / "carterkit" / "controldocs"
SOURCE = VENDORED / "SOURCE"
DOCS_REL = os.environ.get("CARTER_APP_CONTROLDOCS_REL", "CAR-TER/ControlDocs")
SHA_RE = re.compile(r"\b[0-9a-f]{40}\b")


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True).stdout


def _parse_source():
    text = SOURCE.read_text()
    sha = SHA_RE.search(text)
    assert sha, "controldocs/SOURCE has no 40-hex commit SHA"
    repo = None
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        for tok in re.split(r"[\s=]+", line):
            if "://" in tok or tok.startswith(("/", "~", "git@")):
                repo = tok
                break
        if repo:
            break
    return repo, sha.group(0)


def _local_repo(repo):
    env = os.environ.get("CARTER_APP_REPO")
    cands = [env] if env else []
    if repo and "://" not in repo and not repo.startswith("git@"):
        cands.append(repo)
    for parent in KIT_ROOT.parents:
        cands.append(parent / "CAR-TER")
    for c in cands:
        p = Path(c).expanduser()
        if (p / ".git").exists() or p.name.endswith(".git"):
            return p
    return None


def _pinned_files(repo, sha):
    top = _git(repo, "rev-parse", "--show-toplevel").decode().strip()
    candidates = [DOCS_REL, "CAR-TER/CAR-TER/ControlDocs", "ControlDocs"]
    for rel in dict.fromkeys(candidates):
        r = subprocess.run(["git", "-C", top, "ls-tree", "-r", "--name-only", f"{sha}:{rel}"],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return {n: _git(top, "show", f"{sha}:{rel}/{n}") for n in r.stdout.split("\n") if n}
    pytest.skip(f"no ControlDocs dir at {sha} in {top}")


def test_vendored_controldocs_match_pinned_commit():
    assert SOURCE.is_file(), "carterkit/controldocs/SOURCE pin is missing"
    repo_url, sha = _parse_source()
    repo = _local_repo(repo_url)
    if repo is None:
        pytest.skip("no local CAR-TER checkout (set CARTER_APP_REPO)")
    if subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{sha}^{{commit}}"],
                      capture_output=True).returncode != 0:
        pytest.skip(f"pinned commit {sha} not present in {repo}")
    pinned = _pinned_files(repo, sha)
    vendored = {p.relative_to(VENDORED).as_posix(): p.read_bytes()
                for p in VENDORED.rglob("*") if p.is_file() and p.name != "SOURCE"}
    missing = sorted(set(pinned) - set(vendored))
    extra = sorted(set(vendored) - set(pinned))
    changed = sorted(n for n in set(pinned) & set(vendored) if pinned[n] != vendored[n])
    assert not (missing or extra or changed), (
        f"vendored ControlDocs drift from {sha}: "
        f"{len(changed)} differ {changed}, missing {missing}, extra {extra}")
