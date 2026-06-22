"""Lint runtime dynamic-group payloads against observed traffic.

A group with ``dynamic="event"`` has its children replaced at runtime by a broadcast
whose ``msg_type`` equals that event and which carries a ``children`` array (see
group-def.md → *Dynamic Groups*). This module is the dynamic-content mirror of
``autowire.live_data_lint``: given a layout and the broadcasts a service actually
emits, it flags the failure modes that leave a dynamic group silently empty or broken:

  • the event never arrives (typo / wrong namespace / service not emitting it);
  • a matching broadcast carries no ``children`` array;
  • injected children won't render — unknown control type, bad enum, id collision,
    or placement that overflows/overlaps the group's own grid;
  • a children-bearing broadcast that no dynamic group listens for (likely a typo).

`observed` is the decoded broadcast payloads as seen on the wire, e.g. what a
``CarterClient.on_broadcast`` handler receives, or `Fragment.payload(...)` dicts.
Pure (no I/O); findings share the shape used by `validate` so `format_findings` renders them.
"""
from __future__ import annotations

from . import validate as _validate


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
            seen_ids: dict[str, str] = {}
            for ch in children:
                _validate._validate_child(ch, cat, spot, findings, seen_ids)

    # mirror: a payload carrying children that no dynamic group consumes (usually a typo)
    for ev, ms in by_event.items():
        if ev not in listened and any(isinstance(m.get("children"), list) for m in ms):
            findings.append(_validate._f(
                "warn", "orphan_payload", f"event:{ev}",
                f"broadcast '{ev}' carries a 'children' array but no dynamic group listens for it"))
    return findings


def format_findings(findings: list[dict]) -> str:
    """Readable report (delegates to `validate.format_findings`)."""
    return _validate.format_findings(findings)
