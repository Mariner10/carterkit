"""Vendored ControlDocs must equal the pinned CAR-TER ControlDocs.

``carterkit/controldocs/SOURCE`` pins the CAR-TER repo, path and a (short or full)
commit SHA as ``key: value`` lines. Every file vendored under
``carterkit/controldocs`` must be byte-identical to the file at that commit, and
no file may be missing or extra.

Overrides: ``CARTER_APP_REPO`` (local clone of CAR-TER) and
``CARTER_APP_CONTROLDOCS_REL`` (ControlDocs dir inside it).
"""
import os
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

KIT_ROOT = Path(__file__).resolve().parents[2]
VENDORED = KIT_ROOT / "carterkit" / "controldocs"
SOURCE = VENDORED / "SOURCE"
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True).stdout


def _parse_source():
    """Return the SOURCE pin as a dict of ``key: value`` / ``key=value`` pairs."""
    pin = {}
    for line in SOURCE.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        m = re.match(r"([A-Za-z_]+)\s*[:=]\s*(.+)$", line)
        if m:
            pin[m.group(1).lower()] = m.group(2).strip()
    commit = pin.get("commit", "")
    assert SHA_RE.match(commit), f"controldocs/SOURCE commit {commit!r} is not a 7-40 hex SHA"
    return pin


def _resolve(repo, commit):
    r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", f"{commit}^{{commit}}"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def _find_repo(pin):
    """Locate a git repo containing the pinned commit; return (top, full_sha) or None."""
    cands = []
    if os.environ.get("CARTER_APP_REPO"):
        cands.append(Path(os.environ["CARTER_APP_REPO"]).expanduser())
    for parent in KIT_ROOT.parents:
        cands += [parent / "CAR-TER", parent / "CAR-TER-workspace"]
    for p in cands:
        if (p / ".git").exists() and _resolve(p, pin["commit"]):
            top = _git(p, "rev-parse", "--show-toplevel").decode().strip()
            return top, _resolve(top, pin["commit"])
    url = pin.get("repo")
    if url:  # last resort: fetch the pinned repo into a temp bare clone
        tmp = Path(tempfile.mkdtemp(prefix="controldocs-pin-"))
        env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
        r = subprocess.run(["git", "clone", "-q", "--bare", url, str(tmp)],
                           capture_output=True, env=env, timeout=300)
        if r.returncode == 0 and _resolve(tmp, pin["commit"]):
            return str(tmp), _resolve(tmp, pin["commit"])
    return None


def _pinned_files(top, sha, rel):
    r = subprocess.run(["git", "-C", top, "ls-tree", "-r", "--name-only", f"{sha}:{rel}"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip(), f"no {rel} at {sha} in {top}"
    return {n: _git(top, "show", f"{sha}:{rel}/{n}") for n in r.stdout.split("\n") if n}


def test_vendored_controldocs_match_pinned_commit():
    assert SOURCE.is_file(), "carterkit/controldocs/SOURCE pin is missing"
    pin = _parse_source()
    found = _find_repo(pin)
    if found is None:
        pytest.skip(f"pinned commit {pin['commit']} not reachable (set CARTER_APP_REPO)")
    top, sha = found
    rel = os.environ.get("CARTER_APP_CONTROLDOCS_REL") or pin.get("path", "CAR-TER/ControlDocs")
    pinned = _pinned_files(top, sha, rel)
    vendored = {p.relative_to(VENDORED).as_posix(): p.read_bytes()
                for p in VENDORED.rglob("*") if p.is_file() and p.name != "SOURCE"}
    missing = sorted(set(pinned) - set(vendored))
    extra = sorted(set(vendored) - set(pinned))
    changed = sorted(n for n in set(pinned) & set(vendored) if pinned[n] != vendored[n])
    assert not (missing or extra or changed), (
        f"vendored ControlDocs drift from {sha}: "
        f"{len(changed)} differ {changed}, missing {missing}, extra {extra}")
