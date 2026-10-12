import asyncio
from datetime import datetime, timezone

from carterkit.pager_poll import EscalationPoller

NOW = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)


class Hub:
    def __init__(self, fail=False):
        self.notifies, self.fail = [], fail

    async def notify(self, title, body, **kw):
        if self.fail:
            raise RuntimeError("down")
        self.notifies.append((title, body, kw))


def q(id, **kw):
    d = {"id": id, "title": "t", "status": "open", "priority": 2, "labels": ["question"],
         "updated_at": NOW.isoformat()}
    d.update(kw)
    return d


def run(c):
    return asyncio.run(c)


def test_pages_once_without_buttons():
    rows = [q("a-1")]
    hub = Hub()
    p = EscalationPoller(hub, fetch=lambda: rows, now=NOW)
    assert len(run(p.poll_once())) == 1
    assert run(p.poll_once()) == []
    assert len(hub.notifies) == 1
    assert "actions" not in hub.notifies[0][2]


def test_withdraws_when_closed_or_answered_then_repages():
    rows = [q("a-1")]
    p = EscalationPoller(Hub(), fetch=lambda: rows, now=NOW)
    run(p.poll_once())
    rows[0] = q("a-1", status="closed")
    run(p.poll_once())
    assert p.withdrawn == ["a-1"] and not p.paged
    rows[0] = q("a-1", labels=["question", "for:orchestrator"])
    run(p.poll_once())
    assert p.withdrawn == ["a-1"] and not p.paged
    rows[0] = q("a-1")
    assert len(run(p.poll_once())) == 1


def test_answered_question_dropping_out_withdraws():
    rows = [q("a-1")]
    p = EscalationPoller(Hub(), fetch=lambda: rows, now=NOW)
    run(p.poll_once())
    rows[0] = q("a-1", labels=["question", "for:orchestrator"])
    run(p.poll_once())
    assert p.withdrawn == ["a-1"]


def test_failed_push_retried():
    hub = Hub(fail=True)
    p = EscalationPoller(hub, fetch=lambda: [q("a-1")], now=NOW)
    assert run(p.poll_once()) == [] and not p.paged
    hub.fail = False
    assert len(run(p.poll_once())) == 1
