"""Lint runtime dynamic-group payloads against observed traffic.

A group with ``dynamic="event"`` has its children replaced at runtime by a broadcast
whose ``msg_type`` equals that event and which carries a ``children`` array (see
group-def.md → *Dynamic Groups*). This module is the dynamic-content mirror of
``autowire.live_data_lint``: given a layout and the broadcasts a service actually
emits, it flags the failure modes that leave a dynamic group silently empty or broken:

  • the event never arrives (typo / wrong namespace / service not emitting it);
  • a matching broadcast carries no ``children`` array;
  • injected children won't render — unknown control type, bad enum, an id reused
    within the deck or taken from the layout (the app refuses the deck),
    or placement that overflows/overlaps the group's own grid;
  • a children-bearing broadcast that no dynamic group listens for (likely a typo).

`observed` is the decoded broadcast payloads as seen on the wire, e.g. what a
``CarterClient.on_broadcast`` handler receives, or `Fragment.payload(...)` dicts.
Pure (no I/O); findings share the shape used by `validate` so `format_findings` renders them.
"""
from __future__ import annotations

import hashlib as _hashlib
import json as _json

from . import canonical as _canonical
from . import validate as _validate

# Chunked-deck wire contract (group-def.md → *Chunked decks*). The relay drops frames
# over 256 KiB, and an E2EE room grows a frame by about a third (seal + base64), so a
# 160 KB plaintext budget per frame stays under the limit either way.
DECK_FRAME_BUDGET = 160_000
MAX_DECK_PARTS = 64          # the app accepts parts 2...64
MAX_REV_BYTES = 256          # the app drops a rev longer than this


def _frame_bytes(frame: dict) -> int:
    return len(_json.dumps(frame, ensure_ascii=False).encode("utf-8"))


def chunk_deck(event: str, children, *, max_bytes: int = DECK_FRAME_BUDGET,
               rev: str = None) -> list[dict]:
    """Split a dynamic-group deck into the broadcast frames the app reassembles.

    A deck that fits in `max_bytes` comes back as one plain ``{msg_type, children}``
    frame. A bigger one is packed, whole children in order, into frames that each carry
    ``rev`` (same for every part), ``part`` (1-based, ``1``...``parts``) and ``parts``.
    1-based numbering works on every app version that reassembles decks; 0-based only
    on 1.3+. `rev` defaults to a hash of the deck's content, so an identical re-push
    keeps the same rev. Raises ``ValueError`` when one child alone exceeds `max_bytes`,
    when the deck needs more than 64 parts, or when `rev` is longer than 256 bytes.
    """
    kids = list(getattr(children, "children", children) or [])
    whole = {"msg_type": event, "children": kids}
    if _frame_bytes(whole) <= max_bytes:
        return [whole]
    if rev is None:
        rev = _hashlib.sha256(_canonical.canonical_bytes(kids)).hexdigest()[:16]
    rev = str(rev)
    if len(rev.encode("utf-8")) > MAX_REV_BYTES:
        raise ValueError(f"rev is {len(rev.encode('utf-8'))} bytes; the app drops a rev over {MAX_REV_BYTES}")
    # Reserve room for the largest possible part header (part = parts = 64).
    overhead = _frame_bytes({"msg_type": event, "rev": rev, "part": MAX_DECK_PARTS,
                             "parts": MAX_DECK_PARTS, "children": []})
    slices: list[list] = []
    current: list = []
    used = overhead
    for child in kids:
        size = len(_json.dumps(child, ensure_ascii=False).encode("utf-8")) + 2  # ", " separator
        if overhead + size > max_bytes:
            raise ValueError(f"child '{child.get('id', '?') if isinstance(child, dict) else '?'}' "
                             f"is {size} bytes, over the {max_bytes}-byte frame budget; "
                             f"a deck can only split between children")
        if current and used + size > max_bytes:
            slices.append(current)
            current, used = [], overhead
        current.append(child)
        used += size
    if current:
        slices.append(current)
    if len(slices) == 1:   # only the header estimate pushed it over; send it whole
        return [whole]
    if len(slices) > MAX_DECK_PARTS:
        raise ValueError(f"deck needs {len(slices)} parts; the app accepts at most {MAX_DECK_PARTS}")
    total = len(slices)
    return [{"msg_type": event, "rev": rev, "part": i, "parts": total, "children": piece}
            for i, piece in enumerate(slices, start=1)]


def dynamic_groups(layout: dict) -> list[dict]:
    """Every group carrying a `dynamic` event, anywhere in the layout (incl. nested):
    ``[{"id", "event", "columns", "rows", "where"}, ...]``."""
    out: list[dict] = []

    def walk(children, where):
        for ch in children or []:
            if not isinstance(ch, dict) or ch.get("type") != "group":
                continue
            spot = f"{where}/{ch.get('id', '?')}"
            if ch.get("dynamic"):
                g = ch.get("grid") or {}
                out.append({"id": ch.get("id"), "event": ch["dynamic"],
                            "columns": int(g.get("columns", 4)),
                            "rows": int(g.get("rows", 8)), "where": spot})
            walk(ch.get("children"), spot)

    for ti, tab in enumerate(layout.get("tabs", [])):
        walk(tab.get("children"), f"tab[{ti}]")
    return out


def fragment_id_findings(children, layout: dict, where: str = "deck") -> list[dict]:
    """Identity problems in a dynamic deck (or a dynamic tab's children) that the app
    refuses since carter-1o0: a missing/empty id, an id used twice in the fragment, or an
    id the layout already holds (`validate.identity_ids`, dynamic slot content excluded).
    Walks groups, container panels and long-press popups like the app's identity pass.
    `validate`-style `error` findings; [] when the fragment is clean."""
    if not isinstance(children, list):
        return []
    seen = {i: f"layout {w}" for i, w in _validate.identity_ids(layout or {}).items()}
    findings: list[dict] = []
    _validate._claim_ids(children, where, findings, seen)
    return findings


def dynamic_tab_events(layout: dict) -> set:
    """Events registered in the layout's `dynamicTabs`."""
    return {t.get("event") for t in (layout or {}).get("dynamicTabs") or []
            if isinstance(t, dict) and isinstance(t.get("event"), str)}


def _event_of(msg: dict):
    return msg.get("msg_type") or msg.get("event")


def lint_dynamic_traffic(layout: dict, observed, *, catalog: dict = None) -> list[dict]:
    """Lint a layout's dynamic groups against `observed` broadcast payloads (an iterable
    of decoded dicts). Returns `validate`-style findings."""
    import carterkit
    cat = catalog if catalog is not None else carterkit.controls(include_theme=True)

    msgs = [m for m in (observed or []) if isinstance(m, dict)]
    by_event: dict[str, list] = {}
    for m in msgs:
        ev = _event_of(m)
        if ev:
            by_event.setdefault(ev, []).append(m)

    groups = dynamic_groups(layout)
    layout_ids = _validate.identity_ids(layout)
    listened = {g["event"] for g in groups}
    findings: list[dict] = []

    for g in groups:
        spot, event = g["where"], g["event"]
        hits = by_event.get(event, [])
        if not hits:
            findings.append(_validate._f(
                "warn", "event_never_seen", spot,
                f"dynamic group listens for '{event}' but no matching broadcast was observed"))
            continue
        for mi, m in enumerate(hits):
            children = m.get("children")
            if not isinstance(children, list):
                findings.append(_validate._f(
                    "error", "missing_children", spot,
                    f"'{event}' broadcast #{mi} has no 'children' array — the group would clear"))
                continue
            # injected children render in the group's OWN grid
            _validate._grid_findings(children, g["columns"], g["rows"], spot, findings)
            # A deck id may not reuse one of the layout's own ids (carter-1o0): the
            # app refuses the whole deck, so it would never render.
            seen_ids = {i: f"layout {w}" for i, w in layout_ids.items()}
            for ch in children:
                _validate._validate_child(ch, cat, spot, findings, seen_ids)

    # dynamic tabs: the whole broadcast is the tab; the app refuses it on an id clash
    tab_events = dynamic_tab_events(layout)
    for ev in sorted(tab_events):
        for mi, m in enumerate(by_event.get(ev, [])):
            findings += fragment_id_findings(m.get("children"), layout,
                                             f"dynamicTab '{ev}' #{mi}")

    # mirror: a payload carrying children that no dynamic group consumes (usually a typo)
    for ev, ms in by_event.items():
        if ev not in listened and ev not in tab_events \
                and any(isinstance(m.get("children"), list) for m in ms):
            findings.append(_validate._f(
                "warn", "orphan_payload", f"event:{ev}",
                f"broadcast '{ev}' carries a 'children' array but no dynamic group listens for it"))
    return findings


def format_findings(findings: list[dict]) -> str:
    """Readable report (delegates to `validate.format_findings`)."""
    return _validate.format_findings(findings)
