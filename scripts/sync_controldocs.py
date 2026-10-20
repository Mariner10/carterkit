#!/usr/bin/env python3
"""Vendor CAR-TER ControlDocs at the commit pinned in carterkit/controldocs/SOURCE.

Reads the SOURCE pin (repo, path, branch, commit), fetches that commit (or reads a
local checkout given via --source / CARTER_CONTROLDOCS_SOURCE), and copies the
*.md docs into carterkit/controldocs.

  sync_controldocs.py            copy the pinned docs over the vendored set
  sync_controldocs.py --check    change nothing; list drift, exit 1 if the vendored
                                 copy differs from the pinned source

Exit codes: 0 in sync / vendored, 1 drift (--check), 2 usage or source error.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

DEST = Path(__file__).resolve().parent.parent / "carterkit" / "controldocs"


def read_pin(dest: Path) -> dict:
    pin = {}
    for line in (dest / "SOURCE").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and ":" in line:
            k, v = line.split(":", 1)
            pin[k.strip()] = v.strip()
    for key in ("repo", "path", "commit"):
        if not pin.get(key):
            raise SystemExit(f"SOURCE pin missing '{key}'")
    return pin


def git(*args: str, cwd=None) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def fetch_pinned(pin: dict, tmp: str) -> Path:
    """Clone the pinned repo into tmp and check out the pinned commit."""
    git("clone", "--quiet", "--no-checkout", pin["repo"], tmp)
    git("checkout", "--quiet", pin["commit"], cwd=tmp)
    docs = Path(tmp) / pin["path"]
    if not docs.is_dir():
        raise SystemExit(f"path {pin['path']} not found at {pin['commit']}")
    return docs


def local_source(src: Path, pin: dict, tmp: str) -> Path:
    """A local checkout: export the pinned commit if it is git, else use files."""
    if (src / ".git").exists() or (src / "HEAD").exists():
        git("clone", "--quiet", "--no-checkout", str(src), tmp)
        git("checkout", "--quiet", pin["commit"], cwd=tmp)
        docs = Path(tmp) / pin["path"]
        if docs.is_dir():
            return docs
    return src


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the vendored copy differs from the pinned source")
    ap.add_argument("--source", default=os.environ.get("CARTER_CONTROLDOCS_SOURCE"),
                    help="local checkout (or ControlDocs dir) instead of cloning the pinned repo")
    ap.add_argument("--dest", default=str(DEST), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    dest = Path(args.dest)

    try:
        pin = read_pin(dest)
        with tempfile.TemporaryDirectory() as tmp:
            clone = os.path.join(tmp, "src")
            docs = (local_source(Path(args.source), pin, clone) if args.source
                    else fetch_pinned(pin, clone))
            src = {p.name: p.read_bytes() for p in sorted(docs.glob("*.md"))}
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 2
    if not src:
        print("no *.md docs found in source", file=sys.stderr)
        return 2

    have = {p.name: p.read_bytes() for p in sorted(dest.glob("*.md"))}
    if args.check:
        drift = 0
        for name, data in src.items():
            if name not in have:
                print(f"missing from carterkit: {name}"); drift += 1
            elif have[name] != data:
                print(f"differs:                {name}"); drift += 1
        for name in have:
            if name not in src:
                print(f"only in carterkit:      {name}"); drift += 1
        if drift:
            print(f"carterkit/controldocs drifted from pin {pin['commit']} "
                  f"({drift} files); run {sys.argv[0]} to re-vendor", file=sys.stderr)
            return 1
        print(f"carterkit/controldocs matches pin {pin['commit']}")
        return 0

    for name in have:
        (dest / name).unlink()
    for name, data in src.items():
        (dest / name).write_bytes(data)
    print(f"vendored {len(src)} docs into {dest.name}/ at {pin['commit']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
