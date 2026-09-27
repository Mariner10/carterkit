"""The sectioned document (schemaVersion 2) — controldocs/document-contract.md.

A child's facets may live inline on the child (the v1 form this kit writes) OR in
top-level sections keyed by control/group id: ``placements`` (position, span,
landscape, regular), ``styles`` (theme, tint, icon, …) and ``connectivity`` (sync,
action, longPressAction). Top-level ``appearance`` is the app-shell block, not a
section. Mirrors the app's ``LayoutSections.swift``:

- a section entry overrides the same facet written inline;
- the id namespace is a tab's ``children`` and, recursively, group ``children``; the
  first holder of an id wins;
- an entry for an unknown id (or one that isn't an object) is dropped;
- keys in an entry that aren't that section's facets stay in the section (lossless).

``to_inline(layout)`` / ``to_sectioned(layout)`` are pure: they return new dicts.
"""
from __future__ import annotations

import copy

#: section -> the child keys it may hold (order = move order).
SECTIONS: dict[str, tuple[str, ...]] = {
    "placements": ("position", "span", "landscape", "regular"),
    "styles": ("theme", "tint", "icon", "hideLabel", "hideValue", "hideBackground", "animation"),
    "connectivity": ("sync", "action", "longPressAction"),
}
SCHEMA_VERSION = 2
_MAX_WALK = 64


def is_sectioned(layout) -> bool:
    return isinstance(layout, dict) and any(k in layout for k in SECTIONS)


def _is_group(child: dict) -> bool:
    return child.get("type") == "group"


def _first_holders(layout: dict) -> dict:
    """id -> the first child dict holding it, in document order (tab by tab, depth-first)."""
    out: dict = {}

    def walk(kids, depth):
        for child in kids:
            if not isinstance(child, dict):
                continue
            cid = child.get("id")
            if isinstance(cid, str) and cid and cid not in out:
                out[cid] = child
            if depth < _MAX_WALK and _is_group(child) and isinstance(child.get("children"), list):
                walk(child["children"], depth + 1)

    for tab in layout.get("tabs") or []:
        if isinstance(tab, dict) and isinstance(tab.get("children"), list):
            walk(tab["children"], 0)
    return out


def section_issues(layout) -> list[tuple[str, str]]:
    """(where, why) for every unusable section entry — what a load would drop."""
    if not is_sectioned(layout):
        return []
    ids = _first_holders(layout)
    issues = []
    for name in SECTIONS:
        if name not in layout:
            continue
        section = layout[name]
        if not isinstance(section, dict):
            issues.append((f"root.{name}", f"'{name}' must be an object keyed by control/group id"))
            continue
        for cid in sorted(section):
            if cid not in ids:
                issues.append((f"root.{name}.{cid}",
                               f"no control or group has id '{cid}' — the app drops this entry"))
            elif not isinstance(section[cid], dict):
                issues.append((f"root.{name}.{cid}", "a section entry must be an object"))
    return issues


def _write(doc: dict, sections: dict) -> None:
    for name, entries in sections.items():
        kept = {cid: e for cid, e in entries.items() if e}
        if kept:
            doc[name] = kept
        else:
            doc.pop(name, None)
    if is_sectioned(doc):
        doc["schemaVersion"] = SCHEMA_VERSION
    elif doc.get("schemaVersion") == SCHEMA_VERSION:
        del doc["schemaVersion"]


def to_inline(layout: dict) -> dict:
    """Fold every section onto its child (sections win), dropping unusable entries.
    Residual non-facet keys stay in their section; with none left, the sections and
    ``schemaVersion: 2`` go away."""
    doc = copy.deepcopy(layout)
    if not is_sectioned(doc):
        return doc
    holders = _first_holders(doc)
    sections: dict = {}
    for name in SECTIONS:
        if name not in doc:
            continue
        raw = doc[name]
        if not isinstance(raw, dict):
            del doc[name]
            continue
        sections[name] = {cid: dict(e) for cid, e in raw.items()
                          if cid in holders and isinstance(e, dict)}
    for name, entries in sections.items():
        for cid, entry in entries.items():
            if name == "placements" and isinstance(entry.get("default"), dict):
                alias = dict(entry["default"])
                for key in ("position", "span"):
                    if key in alias:
                        value = alias.pop(key)
                        entry.setdefault(key, value)
                if alias:
                    entry["default"] = alias
                else:
                    del entry["default"]
            child = holders[cid]
            for facet in SECTIONS[name]:
                if facet in entry:
                    child[facet] = entry.pop(facet)
    _write(doc, sections)
    return doc


def to_sectioned(layout: dict) -> dict:
    """Move every facet a child carries inline into its section entry and declare
    ``schemaVersion: 2``. An existing entry's value wins. Children without an id, and
    later holders of a duplicate id, keep their facets inline."""
    doc = copy.deepcopy(layout)
    sections: dict = {}
    for name in SECTIONS:
        if isinstance(doc.get(name), dict):
            sections[name] = {cid: dict(e) for cid, e in doc[name].items() if isinstance(e, dict)}
    for cid, child in _first_holders(doc).items():
        for name, facets in SECTIONS.items():
            for facet in facets:
                if facet not in child:
                    continue
                value = child.pop(facet)
                entry = sections.setdefault(name, {}).setdefault(cid, {})
                entry.setdefault(facet, value)
    _write(doc, sections)
    return doc


def inline_view(layout):
    """``layout`` itself when it is inline (no copy), else ``to_inline(layout)`` — for
    readers that walk children for their bindings/placements."""
    return to_inline(layout) if is_sectioned(layout) else layout
