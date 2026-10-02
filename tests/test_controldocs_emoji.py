"""No emoji in the vendored ControlDocs authoring fields (carter-re2l).

Mirrors the app's CAR-TERTests/EmojiSymbolLintTests (carter-73q2.30, SPEC 3a). The
detector lives in scripts/lint-controldocs-emoji.py so sync-controldocs.sh can run it
on every re-vendor; this suite runs it over the shipped snapshot and pins its scope."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("lint_controldocs_emoji", ROOT / "scripts" / "lint-controldocs-emoji.py")
lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lint)

DOCS = sorted((ROOT / "carterkit" / "controldocs").glob("*.md"))


def _doc(front: str, body: str = "# Body\n") -> str:
    return f"---\n{front}\n---\n{body}"


@pytest.mark.parametrize("path", DOCS, ids=[p.stem for p in DOCS])
def test_vendored_doc_has_no_emoji_in_authoring_fields(path):
    assert lint.offenders(path.read_text(encoding="utf-8"), path.name) == []


def test_lint_dir_and_cli_pass_on_vendored_docs():
    assert DOCS, "no vendored ControlDocs found"
    assert lint.lint_dir(ROOT / "carterkit" / "controldocs") == []
    assert lint.main(["lint"]) == 0


@pytest.mark.parametrize("text, expected", [
    ("Bell \U0001F514", ["U+1F514"]),            # pictographic plane
    ("Flag \U0001F1FA\U0001F1F8", ["U+1F1FA", "U+1F1F8"]),  # regional indicators
    ("Heart ❤️", ["U+2764", "U+FE0F"]),  # BMP pictograph + variation selector
    ("Keycap 1️⃣", ["U+FE0F", "U+20E3"]),
    ("Sun ☀", ["U+2600"]),
    ("Star ⭐", ["U+2B50"]),
])
def test_detector_flags_emoji(text, expected):
    assert lint.emoji_scalars(text) == expected


@pytest.mark.parametrize("text", [
    "Slide to pick a number", "0-100 #1 *note*", "Turn → here", "180° arc",
    "0–1 — dash", "été café", "• bullet",
])
def test_detector_allows_plain_text(text):
    assert lint.emoji_scalars(text) == []


def test_injected_emoji_in_every_authoring_field_fails():
    doc = _doc(
        "type: x\n"
        "label: Lamp \U0001F4A1\n"
        "icon: ☀️\n"
        'friendlyName: "Party \U0001F389"\n'
        "oneLiner: Go \U0001F680\n"
        'starterPreset: {"label": "Hot \U0001F525","min": 0}\n'
        'starterVariants: [{"friendlyName": "Ok ✅","oneLiner": "fine","preset": {"label": "Flag \U0001F1EF\U0001F1F5"}}]\n'
        'lookFormats: [{"title": "Star ⭐"}]'
    )
    places = [line.split(":")[0] for line in lint.offenders(doc, "x.md")]
    assert places == [
        "x.md label", "x.md icon", "x.md friendlyName", "x.md oneLiner",
        "x.md starterPreset.label", "x.md starterVariants[0].friendlyName",
        "x.md starterVariants[0].preset.label", "x.md lookFormats[0].title",
    ]


def test_bodies_and_field_descriptions_are_out_of_scope():
    doc = _doc(
        "type: x\nlabel: Plain\nfields:\n"
        "  - name: label\n    description: \"Arrow ↔ and sun ☀\"",
        body="# Body\nBoth ways ↔, emoji \U0001F514 in prose.\n",
    )
    assert lint.offenders(doc, "x.md") == []


def test_non_json_preset_is_linted_raw():
    doc = _doc("type: x\nstarterPreset: not json \U0001F514")
    assert lint.offenders(doc, "x.md") == ["x.md starterPreset: 'not json \U0001F514' [U+1F514]"]


def test_cli_fails_on_injected_fixture(tmp_path, capsys):
    (tmp_path / "ok.md").write_text(_doc("type: ok\nlabel: Fine"), encoding="utf-8")
    (tmp_path / "bad.md").write_text(_doc("type: bad\nfriendlyName: Bell \U0001F514"), encoding="utf-8")
    assert lint.main(["lint", str(tmp_path)]) == 1
    err = capsys.readouterr().err
    assert "bad.md friendlyName" in err and "ok.md" not in err
