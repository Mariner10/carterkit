"""Palette tokens: `theme.palette` + `"$name"` colour refs (carter-m7s.16).

Mirrors the app's `LayoutPalette` (CAR-TER/Services/LayoutPalette.swift): a layout
names its colours once in `theme.palette`, and any colour field may hold `"$name"`
instead of a hex. The app resolves refs at load; the saved document keeps them.

The lint here keeps authors (carterkit, the MCP, the designer) on tokens:
- `palette_literal` (warn): a raw colour equal to a palette token's colour; use `$name`.
- `unknown_token` (warn): a `$name` the palette doesn't define; the app drops the field
  and it falls back to its inherited default.
- `bad_palette` (warn): a palette entry the app ignores (non-string, a `$ref`, a bad name).

A string is in a colour position when its key names a colour (`tint`, `*Color`,
`*Background`, `*Gradient`, `colors`, `fill`, `stroke`), when it is an element of an
array under such a key, or when it sits under a `theme` object or `appearance.header`.
Wire blocks and the palette itself are skipped. See ControlDocs/theming.md.
"""

from __future__ import annotations

import re
from typing import Iterator

REF_PREFIX = "$"
MAX_TOKENS = 64
_MAX_DEPTH = 64
_REF_RE = re.compile(r"^\$([A-Za-z_][A-Za-z0-9_-]{0,63})$")
_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]{0,63}$")
_COLOR_FRAGMENTS = ("color", "colour", "tint", "background", "gradient", "fill", "stroke")
SKIPPED_KEYS = frozenset({
    "sync", "action", "longPressAction", "connection", "sources", "alerts",
    "publishers", "extensions", "state", "sensorSetup", "pollGroups", "dynamicTabs",
})


def ref_name(value) -> str | None:
    """`"$name"` -> `name` when the string has the ref shape, else None."""
    if not isinstance(value, str):
        return None
    m = _REF_RE.match(value)
    return m.group(1) if m else None


def is_color_key(key: str) -> bool:
    k = key.lower()
    return any(f in k for f in _COLOR_FRAGMENTS)


def _palette(layout, problems: list | None = None) -> dict[str, str]:
    theme = layout.get("theme") if isinstance(layout, dict) else None
    entries = theme.get("palette") if isinstance(theme, dict) else None
    if not isinstance(entries, dict):
        return {}
    out: dict[str, str] = {}
    for name in sorted(entries, key=str):
        value = entries[name]
        where = f"theme.palette.{name}"
        if not isinstance(value, str) or value.startswith(REF_PREFIX):
            why = "palette values must be literal colours; the app ignores this entry"
        elif not isinstance(name, str) or not _NAME_RE.match(name):
            why = "token names are letters, digits, _ and -; the app ignores this entry"
        elif len(out) >= MAX_TOKENS:
            why = f"palette holds more than {MAX_TOKENS} tokens; the app ignores this entry"
        else:
            out[name] = value
            continue
        if problems is not None:
            problems.append((where, why))
    return out


def palette(layout: dict) -> dict[str, str]:
    """The tokens the app would honour: `{name: colour}`."""
    return _palette(layout)


def color_strings(layout: dict) -> Iterator[tuple[str, str]]:
    """Every `(where, string)` in a colour position, the palette excluded."""
    stack = [(layout, "", None, False, 0)]
    while stack:
        node, where, key, in_color, depth = stack.pop()
        if isinstance(node, str):
            if in_color:
                yield where, node
        elif isinstance(node, dict) and depth < _MAX_DEPTH:
            for k, v in node.items():
                if not isinstance(k, str) or k in SKIPPED_KEYS or (k == "palette" and key == "theme"):
                    continue
                color = (in_color or k == "theme" or (k == "header" and key == "appearance")
                         or is_color_key(k))
                stack.append((v, f"{where}.{k}" if where else k, k, color, depth + 1))
        elif isinstance(node, list) and depth < _MAX_DEPTH:
            for i, item in enumerate(node):
                stack.append((item, f"{where}[{i}]", key, in_color, depth + 1))


def _norm(color: str) -> str | None:
    """Comparable form of a hex colour: `#RRGGBB` / `#RRGGBBAA` (opaque alpha folded)."""
    h = color.strip().lstrip("#").upper()
    if not re.fullmatch(r"[0-9A-F]{6}|[0-9A-F]{8}", h):
        return None
    return h[:6] if len(h) == 8 and h.endswith("FF") else h


def resolve(layout: dict) -> dict:
    """A copy of `layout` with every known `$name` replaced by its colour and every
    unknown ref in a colour position dropped (the app's load-time behaviour)."""
    tokens = palette(layout)

    def walk(node, key, in_color, depth):
        if isinstance(node, str):
            name = ref_name(node) if in_color else None
            if name is None:
                return node
            return tokens.get(name, _DROP)
        if isinstance(node, dict) and depth < _MAX_DEPTH:
            out = {}
            for k, v in node.items():
                if k in SKIPPED_KEYS or (k == "palette" and key == "theme"):
                    out[k] = v
                    continue
                color = (in_color or k == "theme" or (k == "header" and key == "appearance")
                         or is_color_key(k))
                r = walk(v, k, color, depth + 1)
                if r is not _DROP:
                    out[k] = r
            return out
        if isinstance(node, list) and depth < _MAX_DEPTH:
            return [r for r in (walk(i, key, in_color, depth + 1) for i in node) if r is not _DROP]
        return node

    return walk(layout, None, False, 0)


_DROP = object()


def palette_findings(layout: dict) -> list[tuple[str, str, str]]:
    """`(kind, where, detail)` warnings for the palette lint (see module doc)."""
    problems: list = []
    tokens = _palette(layout, problems)
    out = [("bad_palette", where, why) for where, why in problems]
    by_color: dict[str, list[str]] = {}
    for name, value in tokens.items():
        n = _norm(value)
        if n is not None:
            by_color.setdefault(n, []).append(name)
    for where, value in color_strings(layout):
        name = ref_name(value)
        if name is not None:
            if name not in tokens:
                out.append(("unknown_token", where,
                            f"'{value}' is not in theme.palette; the app drops it and the "
                            f"field falls back to its default"))
            continue
        n = _norm(value)
        if n is not None and n in by_color:
            refs = " or ".join(f"'${m}'" for m in sorted(by_color[n]))
            out.append(("palette_literal", where,
                        f"'{value}' is palette token {refs}; use the token so a palette "
                        f"edit recolours it"))
    out.sort(key=lambda f: (f[1], f[0]))
    return out
