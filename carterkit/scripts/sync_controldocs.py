#!/usr/bin/env python3
"""Vendor CAR-TER ControlDocs at the commit pinned in controldocs/SOURCE.

SOURCE is a text file of `key: value` / `key=value` lines (# comments ok):
  repo:   git URL or local path of the CAR-TER checkout
  commit: the pinned commit sha
  path:   directory inside the repo holding the docs (default ControlDocs)

Default: copy the pinned files into carterkit/controldocs.
--check: change nothing; exit 1 if the vendored tree differs from the pin.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

DEST = Path(__file__).resolve().parent.parent / "controldocs"
SOURCE_NAME = "SOURCE"


def read_source(dest: Path) -> dict:
    src = dest / SOURCE_NAME
    if not src.is_file():
        sys.exit(f"missing {src}")
    out = {"path": "ControlDocs"}
    for line in src.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for sep in (":", "="):
            if sep in line:
                k, v = line.split(sep, 1)
                out[k.strip().lower()] = v.strip()
                break
    for k in ("repo", "commit"):
        if not out.get(k):
            sys.exit(f"{src}: missing '{k}'")
    return out


def git(*args: str, cwd: str | None = None) -> bytes:
    return subprocess.run(["git", *args], cwd=cwd, check=True,
                          stdout=subprocess.PIPE).stdout


def fetch_pinned(src: dict, work: Path) -> dict[str, bytes]:
    """Return {filename: bytes} of the docs dir at the pinned commit."""
    repo = os.environ.get("CARTER_REPO") or src["repo"]
    if Path(repo).is_dir():
        gitdir = repo
    else:
        gitdir = str(work / "clone")
        git("clone", "--quiet", "--no-checkout", repo, gitdir)
    commit, sub = src["commit"], src["path"].strip("/")
    names = git("ls-tree", "-r", "--name-only", "-z", f"{commit}:{sub}",
                cwd=gitdir).decode().split("\0")
    return {n: git("show", f"{commit}:{sub}/{n}", cwd=gitdir)
            for n in names if n}


def local_files(dest: Path) -> dict[str, bytes]:
    return {str(p.relative_to(dest)): p.read_bytes()
            for p in sorted(dest.rglob("*"))
            if p.is_file() and p.name != SOURCE_NAME}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the vendored tree differs from the pin")
    ap.add_argument("--dest", type=Path, default=DEST,
                    help="vendored directory (default: carterkit/controldocs)")
    args = ap.parse_args(argv)

    src = read_source(args.dest)
    with tempfile.TemporaryDirectory() as tmp:
        want = fetch_pinned(src, Path(tmp))
    have = local_files(args.dest)

    added = sorted(set(want) - set(have))
    removed = sorted(set(have) - set(want))
    changed = sorted(n for n in want if n in have and want[n] != have[n])

    if args.check:
        for tag, names in (("missing", added), ("extra", removed),
                           ("differs", changed)):
            for n in names:
                print(f"{tag}: {n}")
        if added or removed or changed:
            print(f"controldocs differ from pin {src['commit'][:12]}",
                  file=sys.stderr)
            return 1
        print(f"controldocs match pin {src['commit'][:12]}")
        return 0

    for n in removed:
        (args.dest / n).unlink()
    for n in added + changed:
        p = args.dest / n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(want[n])
    print(f"synced {len(want)} files at {src['commit'][:12]} "
          f"(+{len(added)} ~{len(changed)} -{len(removed)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
