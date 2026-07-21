"""Parity acceptance: the kit's validator must accept EVERY layout the app renders.

The app ships and renders all bundled SampleLayouts and every published template today;
if the kit's validator errors on any of them, the kit is wrong (not the file). This is
the definition of "up to spec." Skipped when the app repo (and docs-site) aren't adjacent,
so the test is a no-op on a standalone carterkit checkout / CI.

A WARNING INVENTORY is printed and soft-asserted so drift surfaces instead of hiding under
"warnings allowed": only a known-benign set of warning kinds may appear over the bundled
corpus, so a NEW warning kind fails loudly and gets reviewed.
"""
from __future__ import annotations

import collections
import glob
import json
import os
from pathlib import Path

import pytest

import carterkit

_ROOT = Path(__file__).resolve().parents[2]
_SAMPLES = _ROOT / "CAR-TER" / "CAR-TER" / "SampleLayouts"
_TEMPLATES = _ROOT / "carter-docs-site" / "CAR-TER" / "templates"

# Warning kinds the app's own bundled corpus is allowed to emit. Both are honest lint the
# app tolerates at runtime: a non-canonical enum value (app falls back to default) and a
# `mode:"request"` broadcast (fires fine, just awaits a reply that never comes). A NEW kind
# appearing here means real drift to review — hence the soft assertion.
_ALLOWED_WARNING_KINDS = {"bad_enum", "bad_action"}


def _layout_files(directory: Path) -> list[str]:
    return [p for p in sorted(glob.glob(str(directory / "*.json")))
            if os.path.basename(p) != "index.json"]


def _corpus() -> list[str]:
    files: list[str] = []
    if _SAMPLES.is_dir():
        files += _layout_files(_SAMPLES)
    if _TEMPLATES.is_dir():
        files += _layout_files(_TEMPLATES)
    return files


pytestmark = pytest.mark.skipif(
    not _SAMPLES.is_dir(),
    reason="app repo (CAR-TER/CAR-TER/SampleLayouts) not adjacent — parity corpus unavailable")


def test_every_bundled_layout_validates_without_errors(capsys):
    files = _corpus()
    assert files, "no layout files found in the parity corpus"

    failures: dict[str, list[str]] = {}
    warning_inventory: dict[str, dict] = {}
    warning_kinds: collections.Counter = collections.Counter()

    for path in files:
        name = os.path.basename(path)
        layout = json.loads(Path(path).read_text())
        findings = carterkit.validate_layout(layout)
        errors = [f for f in findings if f["severity"] == "error"]
        warns = [f for f in findings if f["severity"] == "warn"]
        if errors:
            failures[name] = [f"{f['kind']}@{f['where']}: {f['detail']}" for f in errors]
        if warns:
            by_kind = collections.Counter(f["kind"] for f in warns)
            warning_inventory[name] = dict(by_kind)
            warning_kinds.update(by_kind)

    # Emit the warning inventory for the CP report (file → {kind: count}).
    with capsys.disabled():
        print(f"\n[parity] validated {len(files)} layouts "
              f"({'samples+templates' if _TEMPLATES.is_dir() else 'samples only'})")
        print(f"[parity] warning kinds over corpus: {dict(warning_kinds)}")
        for fname in sorted(warning_inventory):
            print(f"[parity]   {fname}: {warning_inventory[fname]}")

    assert not failures, "kit rejects layouts the app renders:\n" + "\n".join(
        f"  {k}:\n    " + "\n    ".join(v) for k, v in failures.items())

    # Soft drift guard: only known-benign warning kinds may appear on the app's own corpus.
    unexpected = set(warning_kinds) - _ALLOWED_WARNING_KINDS
    assert not unexpected, (
        f"unexpected warning kind(s) over the bundled corpus (drift to review): {unexpected}; "
        f"inventory={warning_inventory}")


def test_templates_present_and_valid_when_adjacent():
    if not _TEMPLATES.is_dir():
        pytest.skip("carter-docs-site templates not adjacent")
    files = _layout_files(_TEMPLATES)
    assert files, "templates directory present but empty"
    for path in files:
        layout = json.loads(Path(path).read_text())
        errors = [f for f in carterkit.validate_layout(layout) if f["severity"] == "error"]
        assert not errors, f"{os.path.basename(path)} errors: {errors}"
