import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "build_direct_wheels.py"


def _have_go():
    return shutil.which("go") or (Path.home() / ".cache/carterkit-go/go/bin/go").is_file()


@pytest.mark.skipif(not _have_go(), reason="Go toolchain not available")
def test_build_linux_amd64_wheel(tmp_path):
    subprocess.run([sys.executable, str(SCRIPT), "--out", str(tmp_path), "--only", "linux-amd64"],
                   check=True, cwd=ROOT)
    wheels = sorted(tmp_path.glob("*.whl"))
    assert len(wheels) == 2
    plat = [w for w in wheels if "manylinux_2_17_x86_64" in w.name]
    pure = [w for w in wheels if w not in plat]
    assert len(plat) == 1 and len(pure) == 1
    assert not any(n.startswith("carterkit/bin/") for n in zipfile.ZipFile(pure[0]).namelist())
    z = zipfile.ZipFile(plat[0])
    names = z.namelist()
    assert "carterkit/bin/carter-direct" in names
    assert any(n.endswith("NOTICE") for n in names)
    notice = z.read("carterkit/NOTICE").decode()
    assert "github.com/pion/webrtc/v4" in notice
    assert "Permission is hereby granted" in notice      # MIT text in full, not a paraphrase
    assert "Go standard library" in notice and "The Go Authors" in notice
    assert "github.com/stretchr/testify" not in notice   # test-only, not linked
    assert (z.getinfo("carterkit/bin/carter-direct").external_attr >> 16) & 0o111
    # RECORD lists every file once with a hash (pip uninstall/upgrade read it)
    record = next(n for n in names if n.endswith(".dist-info/RECORD"))
    rows = [r.split(",") for r in z.read(record).decode().splitlines()]
    assert all(len(r) == 3 for r in rows)
    assert sorted(r[0] for r in rows) == sorted(names)
    assert all(r[1].startswith("sha256=") for r in rows if r[0] != record)
    # WHEEL keeps every header before the blank line that ends them
    wheel = z.read(next(n for n in names if n.endswith(".dist-info/WHEEL"))).decode()
    head = wheel.split("\n\n")[0]
    assert "Root-Is-Purelib: false" in head
    assert "Tag: py3-none-manylinux_2_17_x86_64" in head
    assert "Tag: py3-none-any" not in wheel


def test_find_sidecar_prefers_package_bin(tmp_path, monkeypatch):
    import carterkit.direct as d
    pkg = tmp_path / "carterkit"
    (pkg / "bin").mkdir(parents=True)
    exe = pkg / "bin" / "carter-direct"
    exe.write_text("x")
    monkeypatch.setattr(d, "__file__", str(pkg / "direct.py"))
    monkeypatch.delenv("CARTERKIT_DIRECT_BIN", raising=False)
    assert d.find_sidecar() == exe
    other = tmp_path / "other"
    other.write_text("y")
    monkeypatch.setenv("CARTERKIT_DIRECT_BIN", str(other))
    assert d.find_sidecar() == other
