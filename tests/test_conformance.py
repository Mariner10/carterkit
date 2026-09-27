"""Shared layout conformance fixtures (carter-c1n.11): the kit's `validate_layout` must
agree with the device's `LayoutDecoder` on every case.

The fixtures have ONE home, the app repo:
    CAR-TER/CAR-TERTests/Fixtures/layout-conformance/{accept,repair,reject}/<name>.json
each with a `<name>.expect.json` sidecar (schema: that folder's README.md). The device
runner (LayoutConformanceTests.swift) and the MCP runner read the same files, so there is
no vendored copy to go stale. Point CARTER_CONFORMANCE_DIR at the folder, or keep the
workspace layout (this repo beside CAR-TER/). Without either (e.g. GitHub CI) this module
skips.

This runner reads the sidecar's `kit` block: verdict "ok" (no error findings) or "error",
plus kinds that must appear. `pending.kit` names the bead that will make a case pass; it
runs as xfail(strict=True), so the day it passes the suite fails and the bead flips it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import carterkit

BUCKETS = ("accept", "repair", "reject")
_REL = Path("CAR-TER") / "CAR-TERTests" / "Fixtures" / "layout-conformance"


def conformance_dir() -> Path | None:
    env = os.environ.get("CARTER_CONFORMANCE_DIR")
    if env:
        return Path(env)
    for parent in Path(__file__).resolve().parents:
        if (parent / _REL).is_dir():
            return parent / _REL
    return None


ROOT = conformance_dir()


def _cases():
    if ROOT is None or not ROOT.is_dir():
        return []
    out = []
    for bucket in BUCKETS:
        for p in sorted((ROOT / bucket).glob("*.json")):
            if not p.name.endswith(".expect.json"):
                out.append(p)
    return out


CASES = _cases()
CATALOG = carterkit.controls(include_theme=True)


def judge(findings: list[dict], expect: dict) -> list[str]:
    """Mismatches between findings and a sidecar's kit (or mcp) block; [] = conforms."""
    errors = {f["kind"] for f in findings if f["severity"] == "error"}
    warns = {f["kind"] for f in findings if f["severity"] == "warn"}
    problems = []
    verdict = "error" if errors else "ok"
    if verdict != expect["verdict"]:
        problems.append(f"verdict {verdict} (errors {sorted(errors)}), expected {expect['verdict']}")
    missing = set(expect.get("errors", [])) - errors
    if missing:
        problems.append(f"missing error kinds {sorted(missing)} (got {sorted(errors)})")
    missing = set(expect.get("warns", [])) - warns
    if missing:
        problems.append(f"missing warn kinds {sorted(missing)} (got {sorted(warns)})")
    return problems


def findings_for(path: Path) -> list[dict]:
    try:
        layout = json.loads(path.read_text())
    except ValueError as e:
        return [{"severity": "error", "kind": "not_json", "where": "root", "detail": str(e)}]
    return carterkit.validate_layout(layout, CATALOG)


def test_fixture_folder_found():
    if ROOT is None:
        pytest.skip("conformance fixtures not found: set CARTER_CONFORMANCE_DIR")
    assert len(CASES) >= 40, f"fixture set thinned or missing under {ROOT}"
    for bucket in BUCKETS:
        assert any(p.parent.name == bucket for p in CASES), f"no fixtures in {bucket}/"


@pytest.mark.parametrize("path", CASES, ids=[f"{p.parent.name}/{p.stem}" for p in CASES])
def test_kit_matches_sidecar(path: Path):
    expect = json.loads(path.with_name(path.stem + ".expect.json").read_text())
    kit = expect["kit"]
    if path.parent.name != "accept":
        assert kit["verdict"] == "error", "repair/ and reject/ cases must be kit errors"
    problems = judge(findings_for(path), kit)
    pending = expect.get("pending", {}).get("kit")
    if pending:
        if problems:
            pytest.xfail(f"pending {pending}: {problems}")
        pytest.fail(f"pending {pending} now passes: delete its pending.kit line")
    assert not problems, f"{path.parent.name}/{path.stem}: {problems}"
