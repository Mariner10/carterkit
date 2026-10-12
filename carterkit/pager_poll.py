"""Poll ``bd list --json`` and page each new escalation (aif-ddg0).

Pages carry no Approve/Deny buttons (those are for permission requests; question
answers are aif-1dtx). Deduped by bead id. A page is withdrawn when its bead drops out of
``escalations()`` for any reason (closed, answered, relabelled for:orchestrator ...):
the id is forgotten, so a bead that escalates again is paged again. The hub has no
recall for a delivered push, so withdrawal is bookkeeping + a log line.
"""
from __future__ import annotations

import asyncio
import json
import logging
import subprocess

from carterkit.pager_escalations import escalations

log = logging.getLogger("carterkit.pager")
DEFAULT_INTERVAL = 120.0


def bd_list_json(timeout=60):
    """Rows of ``bd list --json --all`` (status filter is the selector's job)."""
    out = subprocess.run(["bd", "list", "--json", "--all", "--limit", "0"],
                         capture_output=True, text=True, timeout=timeout, check=True).stdout
    rows = json.loads(out)
    return rows if isinstance(rows, list) else []


class EscalationPoller:
    def __init__(self, hub, *, fetch=bd_list_json, interval=DEFAULT_INTERVAL, now=None):
        self.hub = hub
        self.fetch = fetch
        self.interval = interval
        self.now = now
        self.paged: dict[str, str] = {}      # bead id -> reason
        self.withdrawn: list[str] = []
        self._task = None

    async def poll_once(self) -> list:
        """One pass; returns the escalations newly paged."""
        rows = await asyncio.to_thread(self.fetch)
        current = {e["id"]: e for e in escalations(rows, now=self.now)}
        for bead_id in [i for i in self.paged if i not in current]:
            del self.paged[bead_id]
            self.withdrawn.append(bead_id)
            log.info("pager: escalation %s no longer needs a page", bead_id)
        fresh = []
        for bead_id, esc in current.items():
            if bead_id in self.paged:
                continue
            try:
                await self.hub.notify(esc["text"], esc["reason"],
                                      notif_id=f"esc-{bead_id}"[:64],
                                      interruption="time-sensitive")
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001 — retried next poll
                log.warning("pager: escalation push for %s failed: %s", bead_id, e)
                continue
            self.paged[bead_id] = esc["reason"]
            fresh.append(esc)
        return fresh

    async def _loop(self):
        while True:
            try:
                await self.poll_once()
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001 — bd down: try again next tick
                log.warning("pager: escalation poll failed: %s", e)
            await asyncio.sleep(self.interval)

    def start(self):
        self._task = asyncio.get_running_loop().create_task(self._loop())
        return self

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
