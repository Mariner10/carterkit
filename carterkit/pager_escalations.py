"""Pure selector: which beads deserve a page on Carter's phone (aif-9079).

Carter's rule: page only for real escalations, a question bead filed for him or a
stalled P0; nothing else. No I/O: feed it ``bd list --json`` rows.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from carterkit.pager import SUMMARY_MAX, _clip

STALL_AFTER = timedelta(hours=2)
_QUESTION_STATUSES = {"open", "blocked", "in_progress"}


def _parse(ts):
    if not isinstance(ts, str) or not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _is_question(bead) -> bool:
    labels = set(bead.get("labels") or [])
    return ("question" in labels and bead.get("status") in _QUESTION_STATUSES
            and "cap:supervised" not in labels and "for:orchestrator" not in labels)


def _is_stalled_p0(bead, now, stall_after) -> bool:
    if bead.get("priority") != 0 or bead.get("status") in ("closed", "deferred"):
        return False
    stamps = [t for t in (_parse(bead.get("updated_at")), _parse(bead.get("heartbeat_at"))) if t]
    return bool(stamps) and now - max(stamps) > stall_after


def page_text(bead, reason) -> str:
    tag = "Question" if reason == "question" else "Stalled P0"
    return _clip(f"{tag} {bead.get('id', '?')}: {bead.get('title', '')}", SUMMARY_MAX)


def escalations(beads, now=None, stall_after=STALL_AFTER):
    """Return [{id, priority, reason, text}] sorted by (priority, id)."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    out = []
    for b in beads or []:
        if not isinstance(b, dict) or b.get("status") == "closed":
            continue
        reason = ("question" if _is_question(b)
                  else "stalled-p0" if _is_stalled_p0(b, now, stall_after) else None)
        if reason:
            pr = b.get("priority")
            out.append({"id": b.get("id"), "priority": pr, "reason": reason,
                        "text": page_text(b, reason)})
    out.sort(key=lambda e: (e["priority"] if isinstance(e["priority"], int) else 99,
                            str(e["id"])))
    return out
