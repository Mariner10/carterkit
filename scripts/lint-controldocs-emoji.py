#!/usr/bin/env python3
"""No emoji in the ControlDocs authoring fields (carter-re2l, mirrors the app's
CAR-TERTests/EmojiSymbolLintTests from carter-73q2.30, SPEC 3a: SF Symbols only).

Scans each doc's frontmatter authoring fields (label, icon, friendlyName, oneLiner,
starterPreset, starterVariants, lookFormats; the JSON ones string leaf by string leaf)
and fails on Extended_Pictographic code points, regional indicators (flags), the emoji
variation selector U+FE0F and the keycap combiner U+20E3. Doc BODIES and field
descriptions are out of scope: they legitimately use text arrows like U+2194.

Stdlib only, so sync-controldocs.sh can run it with any python.

Usage: scripts/lint-controldocs-emoji.py [controldocs dir]   (default: the vendored one)
Exit 0 = clean, 1 = offenders (one line each on stderr).
"""
import json
import re
import sys
from pathlib import Path

DEFAULT_DIR = Path(__file__).resolve().parents[1] / "carterkit" / "controldocs"

# Top-level frontmatter keys an editor shows the user (or seeds a control with).
TEXT_KEYS = ("label", "icon", "friendlyName", "oneLiner")
JSON_KEYS = ("starterPreset", "starterVariants", "lookFormats")

# Extended_Pictographic below the pictographic planes (Unicode 15.1 emoji-data.txt).
# The planes U+1F000-1FAFF and U+1FC00-1FFFD are taken whole, as the app's test does.
_BMP_PICTOGRAPHIC = (
    (0x00A9, 0x00A9), (0x00AE, 0x00AE), (0x203C, 0x203C), (0x2049, 0x2049),
    (0x2122, 0x2122), (0x2139, 0x2139), (0x2194, 0x2199), (0x21A9, 0x21AA),
    (0x231A, 0x231B), (0x2328, 0x2328), (0x2388, 0x2388), (0x23CF, 0x23CF),
    (0x23E9, 0x23F3), (0x23F8, 0x23FA), (0x24C2, 0x24C2), (0x25AA, 0x25AB),
    (0x25B6, 0x25B6), (0x25C0, 0x25C0), (0x25FB, 0x25FE), (0x2600, 0x2605),
    (0x2607, 0x2612), (0x2614, 0x2685), (0x2690, 0x2705), (0x2708, 0x2712),
    (0x2714, 0x2714), (0x2716, 0x2716), (0x271D, 0x271D), (0x2721, 0x2721),
    (0x2728, 0x2728), (0x2733, 0x2734), (0x2744, 0x2744), (0x2747, 0x2747),
    (0x274C, 0x274C), (0x274E, 0x274E), (0x2753, 0x2755), (0x2757, 0x2757),
    (0x2763, 0x2767), (0x2795, 0x2797), (0x27A1, 0x27A1), (0x27B0, 0x27B0),
    (0x27BF, 0x27BF), (0x2934, 0x2935), (0x2B05, 0x2B07), (0x2B1B, 0x2B1C),
    (0x2B50, 0x2B50), (0x2B55, 0x2B55), (0x3030, 0x3030), (0x303D, 0x303D),
    (0x3297, 0x3297), (0x3299, 0x3299),
)


def is_emoji_scalar(ch: str) -> bool:
    v = ord(ch)
    if v in (0xFE0F, 0x20E3):
        return True
    if 0x1F1E6 <= v <= 0x1F1FF:  # regional indicators
        return True
    if 0x1F000 <= v <= 0x1FAFF or 0x1FC00 <= v <= 0x1FFFD:
        return True
    return any(lo <= v <= hi for lo, hi in _BMP_PICTOGRAPHIC)


def emoji_scalars(text: str) -> list[str]:
    return [f"U+{ord(c):04X}" for c in text if is_emoji_scalar(c)]


def string_leaves(value, path: str = ""):
    """Every string leaf in a decoded JSON tree, with its key path."""
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from string_leaves(child, f"{path}.{key}")
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from string_leaves(child, f"{path}[{i}]")


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def authoring_strings(content: str):
    """`(field path, text)` for every authoring-field string in one doc's frontmatter."""
    if not content.startswith("---"):
        return
    front = content.split("---", 2)[1]
    for line in front.splitlines():
        m = re.match(r"^([A-Za-z]+):\s*(.*)$", line)  # top-level keys only
        if not m:
            continue
        key, raw = m.group(1), m.group(2)
        if key in TEXT_KEYS:
            yield key, _unquote(raw)
        elif key in JSON_KEYS:
            try:
                tree = json.loads(raw)
            except ValueError:
                yield key, raw  # not JSON: lint the raw text rather than skip it
                continue
            yield from ((key + path, text) for path, text in string_leaves(tree))


def offenders(content: str, name: str) -> list[str]:
    out = []
    for place, text in authoring_strings(content):
        hits = emoji_scalars(text)
        if hits:
            out.append(f"{name} {place}: {text!r} [{' '.join(hits)}]")
    return out


def lint_dir(docs_dir) -> list[str]:
    out = []
    for path in sorted(Path(docs_dir).glob("*.md")):
        out += offenders(path.read_text(encoding="utf-8"), path.name)
    return out


def main(argv) -> int:
    docs_dir = Path(argv[1]) if len(argv) > 1 else DEFAULT_DIR
    bad = lint_dir(docs_dir)
    for line in bad:
        print(f"emoji in ControlDocs authoring field: {line}", file=sys.stderr)
    if bad:
        print("SPEC 3a: no emoji in authoring fields; use an SF Symbol name for icons.", file=sys.stderr)
        return 1
    print(f"emoji lint: {len(list(Path(docs_dir).glob('*.md')))} docs clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
