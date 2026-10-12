from datetime import datetime, timedelta, timezone

from carterkit.pager import SUMMARY_MAX
from carterkit.pager_escalations import escalations

NOW = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)


def ago(h):
    return (NOW - timedelta(hours=h)).isoformat()


def bead(id, **kw):
    d = {"id": id, "title": "t " + id, "status": "open", "priority": 2, "labels": [],
         "updated_at": ago(0)}
    d.update(kw)
    return d


def ids(rows):
    return [(e["id"], e["reason"]) for e in escalations(rows, now=NOW)]


def test_question_pages():
    assert ids([bead("q", labels=["question"], status="blocked")]) == [("q", "question")]


def test_question_exclusions():
    rows = [bead("c", labels=["question"], status="closed"),
            bead("d", labels=["question"], status="deferred"),
            bead("s", labels=["question", "cap:supervised"]),
            bead("o", labels=["question", "for:orchestrator"]),
            bead("plain")]
    assert ids(rows) == []


def test_stalled_p0():
    rows = [bead("p", priority=0, updated_at=ago(3))]
    assert ids(rows) == [("p", "stalled-p0")]


def test_heartbeat_keeps_p0_fresh():
    assert ids([bead("p", priority=0, updated_at=ago(5), heartbeat_at=ago(1))]) == []


def test_fresh_and_untimed_p0_do_not_page():
    rows = [bead("f", priority=0, updated_at=ago(1)),
            bead("m", priority=0, updated_at=None),
            bead("u", priority=0, updated_at="garbage"),
            bead("x", priority=0, status="deferred", updated_at=ago(9)),
            bead("y", priority=0, status="closed", updated_at=ago(9))]
    assert ids(rows) == []


def test_both_rules_once_as_question_sorted():
    rows = [bead("b", priority=0, labels=["question"], updated_at=ago(9)),
            bead("a", priority=0, updated_at=ago(9)),
            bead("c", priority=1, labels=["question"])]
    assert ids(rows) == [("a", "stalled-p0"), ("b", "question"), ("c", "question")]


def test_text_clipped():
    out = escalations([bead("q", labels=["question"], title="x" * 500)], now=NOW)
    assert len(out[0]["text"]) == SUMMARY_MAX and out[0]["text"].endswith("…")
