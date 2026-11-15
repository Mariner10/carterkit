"""Phone customization of hub-served UI: the overlay store, allow-list and apply.

A hub opts in with ``connection.customize`` (``"none"`` | ``"look"`` | ``"arrange"``, or
``{"mode": ..., "save": true}``). With ``save`` on, the phone sends one
``customize_save`` message after an editor save::

    {"msg_type": "customize_save", "layout": "<id>", "rev": 7,
     "overlay": {"patches": {"eq": {"look": {...}, "arrange": {...}}, ...},
                 "order": {"page": ["eq", "flat"]}}}

The hub keeps it, answers ``{"msg_type": "customize_ack", "layout", "rev"}``, and applies
the overlay to every layout / deck it sends afterwards, stamping
``connection.customize.rev`` so the phone can drop its retained copy. Applying is a *set*
on an allow-list of keys (never code, actions, wiring or ids), so applying twice equals
applying once. Spec: CAR-TER docs/superpowers/specs/2026-11-14-dynamic-lists-design.md, section 9.
"""
from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path
from typing import Any

MODES = ("none", "look", "arrange")
_LEVEL = {m: i for i, m in enumerate(MODES)}

#: Keys a ``look`` facet may set (spec 9.2). ``theme`` is a dict merged key by key.
LOOK_KEYS = frozenset({
    "accentColor", "color", "font", "fontSize", "fontWeight", "scale", "spacing",
    "itemSpacing", "cardPadding", "cornerRadius", "cardStyle", "rowStyle",
    "hideBackground", "theme", "edge", "edgeSize",
})
#: Keys an ``arrange`` facet may set.
ARRANGE_KEYS = frozenset({"position", "span", "hidden"})

MAX_BYTES = 256 * 1024
MAX_PATCHES = 2000


def parse_customize(value: Any) -> tuple[str, bool]:
    """``(mode, save)`` for a ``customize`` value; anything unrecognised is ``("none", False)``."""
    if isinstance(value, str):
        return (value, False) if value in MODES else ("none", False)
    if isinstance(value, dict):
        mode = value.get("mode", "none")
        return (mode if mode in MODES else "none"), value.get("save") is True
    return "none", False


def needs_connection(layout: dict | None) -> bool:
    """True when ``layout`` has no dial-back connection yet. A bare
    ``connection: {"customize": ...}`` (set by ``Layout.customize``) still needs one."""
    conn = (layout or {}).get("connection")
    return not (isinstance(conn, dict) and conn.get("url"))


def with_connection(layout: dict, block: dict) -> dict:
    """``layout`` with ``block`` as its connection, keeping a customize opt-in already there."""
    conn = layout.get("connection")
    keep = {"customize": conn["customize"]} if isinstance(conn, dict) and "customize" in conn else {}
    return dict(layout, connection={**block, **keep})


def layout_customize(layout: dict | None) -> tuple[str, bool]:
    conn = (layout or {}).get("connection")
    return parse_customize(conn.get("customize") if isinstance(conn, dict) else None)


def sanitize_overlay(overlay: Any) -> dict:
    """Keep only allow-listed keys. Returns ``{"patches": {...}, "order": {...}}``; raises
    ``ValueError`` for a document that is not an overlay or is over the size caps."""
    if not isinstance(overlay, dict):
        raise ValueError("overlay must be an object")
    patches_in = overlay.get("patches", {})
    if not isinstance(patches_in, dict):
        raise ValueError("overlay.patches must be an object")
    if len(patches_in) > MAX_PATCHES:
        raise ValueError(f"overlay has {len(patches_in)} patches; the cap is {MAX_PATCHES}")
    patches: dict = {}
    for key, facets in patches_in.items():
        if not isinstance(key, str) or not isinstance(facets, dict):
            continue
        out: dict = {}
        for facet, allowed in (("look", LOOK_KEYS), ("arrange", ARRANGE_KEYS)):
            body = facets.get(facet)
            if isinstance(body, dict):
                kept = {k: copy.deepcopy(v) for k, v in body.items() if k in allowed}
                if kept:
                    out[facet] = kept
        if out:
            patches[key] = out
    order: dict = {}
    order_in = overlay.get("order", {})
    if isinstance(order_in, dict):
        for scope, ids in order_in.items():
            if isinstance(scope, str) and isinstance(ids, list) and all(isinstance(i, str) for i in ids):
                order[scope] = list(ids)
    clean = {"patches": patches, "order": order}
    if len(json.dumps(clean)) > MAX_BYTES:
        raise ValueError(f"overlay is over the {MAX_BYTES // 1024} KB cap")
    return clean


# ── apply ────────────────────────────────────────────────────────────────────

def _flat(facets: dict, level: int) -> dict:
    flat: dict = {}
    if level >= _LEVEL["look"]:
        flat.update(facets.get("look") or {})
    if level >= _LEVEL["arrange"]:
        flat.update(facets.get("arrange") or {})
    return flat


def _set(node: dict, flat: dict) -> None:
    """Set patch fields on a control, group or itemTemplate (a set, so idempotent)."""
    for k, v in flat.items():
        v = copy.deepcopy(v)
        if k == "scale":
            grid = node.get("grid")
            if not isinstance(grid, dict):
                grid = node["grid"] = {}
            grid["scale"] = v
        elif k == "theme" and isinstance(v, dict):
            theme = node.get("theme")
            if not isinstance(theme, dict):
                theme = node["theme"] = {}
            theme.update(v)
        else:
            node[k] = v


def _narrow(level: int, node: dict) -> int:
    """The nearest ``customize`` wins but never widens the ceiling."""
    if "customize" in node:
        mode, _ = parse_customize(node["customize"])
        return min(level, _LEVEL[mode])
    return level


def _reorder(children: list, ids: list) -> None:
    pos = {cid: i for i, cid in enumerate(ids)}
    keyed = [(pos.get(c.get("id") if isinstance(c, dict) else None, len(ids)), n, c)
             for n, c in enumerate(children)]
    children[:] = [c for _, _, c in sorted(keyed, key=lambda t: (t[0], t[1]))]


def _apply_children(children: Any, patches: dict, order: dict, level: int, scope: str,
                    parent: str | None) -> None:
    if not isinstance(children, list):
        return
    if level >= _LEVEL["arrange"] and scope in order:
        _reorder(children, order[scope])
    for ch in children:
        if not isinstance(ch, dict):
            continue
        cid = ch.get("id")
        clevel = _narrow(level, ch)
        if isinstance(cid, str):
            keys = [cid] + ([f"{parent}/{cid}"] if parent else [])
            for key in keys:
                if key in patches:
                    _set(ch, _flat(patches[key], clevel))
        _apply_node(ch, patches, order, clevel)


def _apply_node(ch: dict, patches: dict, order: dict, level: int) -> None:
    cid = ch.get("id") if isinstance(ch.get("id"), str) else None
    tpl = ch.get("itemTemplate")
    if isinstance(tpl, dict) and cid:
        tlevel = _narrow(level, tpl)
        if f"{cid}#item" in patches:
            _set(tpl, _flat(patches[f"{cid}#item"], tlevel))
        for sub in tpl.get("children") or []:
            if isinstance(sub, dict) and isinstance(sub.get("id"), str):
                key = f"{cid}#item/{sub['id']}"
                if key in patches:
                    _set(sub, _flat(patches[key], tlevel))
    if isinstance(ch.get("children"), list):
        _apply_children(ch["children"], patches, order, level, cid or "", cid)
    for panel in ch.get("panels") or []:
        if isinstance(panel, dict):
            _apply_children(panel.get("children"), patches, order, level, cid or "", cid)


def apply_overlay(layout: dict, overlay: dict | None, rev: int | None = None) -> dict:
    """A copy of ``layout`` with the overlay applied and ``connection.customize.rev``
    stamped. A layout that does not opt in (``customize`` absent or ``none``) is returned
    unchanged, so a script that never enables the feature is untouched."""
    mode, save = layout_customize(layout)
    if mode == "none" or not overlay:
        return layout
    clean = sanitize_overlay(overlay)
    out = copy.deepcopy(layout)
    level = _LEVEL[mode]
    patches, order = clean["patches"], clean["order"]
    for tab in out.get("tabs") or []:
        if isinstance(tab, dict):
            _apply_children(tab.get("children"), patches, order, level, "page", None)
    if rev is not None:
        conn = out.setdefault("connection", {})
        conn["customize"] = {"mode": mode, "save": save, "rev": int(rev)}
    return out


def apply_to_children(children: list, overlay: dict | None, mode: str, owner: str | None = None) -> list:
    """Overlay a runtime deck: ``children`` of dynamic group ``owner`` (patch keys
    ``<owner>/<child id>`` and the child's own id). Returns a patched copy."""
    if mode == "none" or not overlay or not isinstance(children, list):
        return children
    clean = sanitize_overlay(overlay)
    out = copy.deepcopy(children)
    _apply_children(out, clean["patches"], clean["order"], _LEVEL[mode], owner or "", owner)
    return out


# ── store ────────────────────────────────────────────────────────────────────

class OverlayStore:
    """The default storage: one JSON file ``{"layout", "rev", "overlay"}`` beside the script."""

    def __init__(self, path: str | os.PathLike):
        self.path = Path(path)

    @staticmethod
    def beside_script() -> "OverlayStore":
        import sys
        main = getattr(sys.modules.get("__main__"), "__file__", None)
        if main:
            p = Path(main)
            return OverlayStore(p.with_name(p.name + ".customize.json"))
        return OverlayStore(Path.cwd() / "carterkit.customize.json")

    def load(self, layout_id: str | None = None) -> tuple[dict | None, int]:
        """``(overlay, rev)``; ``(None, 0)`` when absent, unreadable or for another layout."""
        try:
            doc = json.loads(self.path.read_text())
        except (OSError, ValueError):
            return None, 0
        if not isinstance(doc, dict) or (layout_id and doc.get("layout") != layout_id):
            return None, 0
        try:
            return sanitize_overlay(doc.get("overlay")), int(doc.get("rev") or 0)
        except (ValueError, TypeError):
            return None, 0

    def save(self, layout_id: str, rev: int, overlay: dict) -> None:
        doc = {"v": 1, "layout": layout_id, "rev": int(rev), "overlay": overlay}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), prefix=self.path.name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(doc, f, indent=2)
            os.replace(tmp, self.path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
