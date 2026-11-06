#!/usr/bin/env python3
"""Vendor CAR-TER's tutorials into carterkit/tutorials at the commit pinned in its SOURCE.

CAR-TER/Tutorials is the one home for tutorial docs; carterkit renders them and never authors them.
SOURCE (same format as controldocs/SOURCE, see sync_controldocs.py) pins:
  repo / path / commit   the CAR-TER checkout and its Tutorials directory
  also-repo / also-path / also-commit / also-only
                         code tutorials CAR-TER does not host yet (comma list of files), taken from the
                         workspace pin until they move; a file CAR-TER has wins.
Writes index.json (every tutorial's frontmatter, so no YAML parser is needed at runtime).

  uv run --with pyyaml python scripts/sync_tutorials.py [--check]
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEST = HERE.parent / "carterkit" / "tutorials"


def _controldocs_sync():
    spec = importlib.util.spec_from_file_location(
        "sync_controldocs", HERE.parent / "carterkit" / "scripts" / "sync_controldocs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def want_files(cd, src: dict, work: Path) -> dict[str, bytes]:
    want = {}
    if src.get("also-repo"):
        also = {"repo": src["also-repo"], "path": src["also-path"], "commit": src["also-commit"]}
        keep = {n.strip() for n in src.get("also-only", "").split(",") if n.strip()}
        override = os.environ.pop("CARTER_REPO", None)   # CARTER_REPO points at CAR-TER only
        try:
            got = cd.fetch_pinned(also, work / "also")
        finally:
            if override:
                os.environ["CARTER_REPO"] = override
        want.update({n: b for n, b in got.items() if n in keep})
    want.update(cd.fetch_pinned(src, work))
    want["index.json"] = cd.frontmatter_index(want)
    return want


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if the vendored tree differs from the pin")
    ap.add_argument("--dest", type=Path, default=DEST)
    args = ap.parse_args(argv)
    cd = _controldocs_sync()
    src = cd.read_source(args.dest)
    with tempfile.TemporaryDirectory() as tmp:
        want = want_files(cd, src, Path(tmp))
    have = cd.local_files(args.dest)
    added = sorted(set(want) - set(have))
    removed = sorted(set(have) - set(want))
    changed = sorted(n for n in want if n in have and want[n] != have[n])
    if args.check:
        for tag, names in (("missing", added), ("extra", removed), ("differs", changed)):
            for n in names:
                print(f"{tag}: {n}")
        if added or removed or changed:
            print(f"tutorials differ from pin {src['commit'][:12]}", file=sys.stderr)
            return 1
        print(f"tutorials match pin {src['commit'][:12]}")
        return 0
    for n in removed:
        (args.dest / n).unlink()
    for n in added + changed:
        p = args.dest / n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(want[n])
    print(f"synced {len(want)} files at {src['commit'][:12]} (+{len(added)} ~{len(changed)} -{len(removed)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
