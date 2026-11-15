#!/usr/bin/env python3
"""Build the pure carterkit wheel plus one platform wheel per target carrying `carter-direct`.

    python3 scripts/build_direct_wheels.py --out dist [--only linux-amd64]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRECT = ROOT / "direct"

# name -> (GOOS, GOARCH, GOARM, wheel platform tag)
TARGETS = {
    "linux-arm64": ("linux", "arm64", "", "manylinux_2_17_aarch64"),
    "linux-arm": ("linux", "arm", "7", "manylinux_2_17_armv7l"),
    "linux-amd64": ("linux", "amd64", "", "manylinux_2_17_x86_64"),
    "darwin-arm64": ("darwin", "arm64", "", "macosx_11_0_arm64"),
    "darwin-amd64": ("darwin", "amd64", "", "macosx_10_15_x86_64"),
    "windows-amd64": ("windows", "amd64", "", "win_amd64"),
}


def find_go() -> str | None:
    w = shutil.which("go")
    if w:
        return w
    g = Path.home() / ".cache" / "carterkit-go" / "go" / "bin" / "go"
    return str(g) if g.is_file() else None


def ensure_go() -> str:
    go = find_go()
    if go:
        return go
    subprocess.run(["bash", str(DIRECT / "scripts" / "check.sh")], check=True)  # bootstraps Go
    go = find_go()
    if not go:
        sys.exit("go toolchain not available")
    return go


def write_notice(dest: Path) -> None:
    mods = []
    for line in (DIRECT / "go.sum").read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2 and not parts[1].endswith("/go.mod"):
            mods.append(f"{parts[0]} {parts[1]}")
        elif len(parts) >= 2:
            m = f"{parts[0]} {parts[1][:-len('/go.mod')]}"
            if m not in mods:
                mods.append(m)
    mods = sorted(set(mods))
    head = (
        "carter-direct bundles the following Go modules (from direct/go.sum).\n"
        "Pion modules (github.com/pion/*) and the RTSP client are MIT licensed:\n"
        "  Copyright (c) the respective Pion / RTSP client authors.\n"
        "  Permission is hereby granted, free of charge, to any person obtaining a copy of this\n"
        "  software and associated documentation files, to deal in the Software without restriction,\n"
        "  subject to inclusion of this notice. THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY\n"
        "  OF ANY KIND.\n"
        "Other modules (golang.org/x/*, github.com/google/uuid, ...) are BSD-3-Clause licensed by\n"
        "their authors; see each module's LICENSE file.\n\nModules:\n"
    )
    dest.write_text(head + "".join(f"  {m}\n" for m in mods))


def build_pure(out: Path) -> Path:
    before = set(out.glob("*.whl"))
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src"
        shutil.copytree(ROOT, src, ignore=shutil.ignore_patterns(
            ".git", "dist", "build", "*.egg-info", "__pycache__", "tests", ".venv", "bin"))
        shutil.rmtree(src / "carterkit" / "bin", ignore_errors=True)
        subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation",
                        "-q", "-w", str(out), str(src)], check=True)
    new = set(out.glob("*.whl")) - before
    if len(new) != 1:
        sys.exit(f"expected one pure wheel, got {new}")
    return new.pop()


def _record_line(name: str, data: bytes) -> str:
    h = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
    return f"{name},sha256={h},{len(data)}\n"


def platform_wheel(pure: Path, binary: Path, notice: Path, plat: str, exe: str, out: Path) -> Path:
    parts = pure.name[:-4].split("-")        # name-ver-pytag-abitag-plat
    new = out / ("-".join(parts[:2]) + f"-py3-none-{plat}.whl")
    with zipfile.ZipFile(pure) as zin, zipfile.ZipFile(new, "w", zipfile.ZIP_DEFLATED) as zout:
        record = None
        lines = []
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.endswith(".dist-info/RECORD"):
                record = item.filename
                continue
            if item.filename.endswith(".dist-info/WHEEL"):
                lines = [l for l in data.decode().splitlines() if not l.startswith(("Tag:", "Root-Is-Purelib"))]
                lines += ["Root-Is-Purelib: false", f"Tag: py3-none-{plat}"]
                data = ("\n".join(lines) + "\n").encode()
            zout.writestr(item, data)
            lines.append(_record_line(item.filename, data))
        extra = [(f"carterkit/bin/carter-direct{exe}", binary.read_bytes(), 0o755),
                 ("carterkit/NOTICE", notice.read_bytes(), 0o644)]
        for name, data, mode in extra:
            zi = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            zi.external_attr = (0o100000 | mode) << 16
            zi.compress_type = zipfile.ZIP_DEFLATED
            zout.writestr(zi, data)
            lines.append(_record_line(name, data))
        lines.append(f"{record},,\n")
        zout.writestr(record, "".join(lines))
    return new


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist")
    ap.add_argument("--only", help="one target, e.g. linux-amd64")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    names = [a.only] if a.only else list(TARGETS)
    for n in names:
        if n not in TARGETS:
            sys.exit(f"unknown target {n}; choose from {', '.join(TARGETS)}")
    go = ensure_go()
    notice = DIRECT / "NOTICE"
    write_notice(notice)
    pure = build_pure(out)
    print("built", pure.name)
    with tempfile.TemporaryDirectory() as tmp:
        for n in names:
            goos, goarch, goarm, plat = TARGETS[n]
            exe = ".exe" if goos == "windows" else ""
            binary = Path(tmp) / f"carter-direct-{n}{exe}"
            env = dict(os.environ, CGO_ENABLED="0", GOOS=goos, GOARCH=goarch)
            if goarm:
                env["GOARM"] = goarm
            subprocess.run([go, "build", "-trimpath", "-ldflags", "-s -w", "-o", str(binary),
                            "./cmd/carter-direct"], cwd=DIRECT, env=env, check=True)
            w = platform_wheel(pure, binary, notice, plat, exe, out)
            print("built", w.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
