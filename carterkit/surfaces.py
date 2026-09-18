"""Layout-aware connectors for CAR-TER's iOS surfaces.

Use ``hub.surfaces``: no duplicated labels, control IDs, wire types or date epochs.
Remote refresh is explicit so telemetry-rate ``hub.push`` calls never consume
notification or ActivityKit budgets behind the caller's back.
"""
import time
import re

from .ambient import (activity_attributes, apple_date, canonical_layout_id,
                      content_state, glance_update, slot, _scalar)

_KINDS = {"gauge": "gauge", "progressRing": "ring", "statusLight": "light",
          "sparkline": "number", "slider": "number", "stepper": "number",
          "toggle": "bool", "label": "text", "picker": "text", "segmentedControl": "text"}
_RANK = {"gauge": 0, "progressRing": 1, "statusLight": 2, "sparkline": 3,
         "slider": 4, "stepper": 5, "toggle": 6, "label": 7, "picker": 7, "segmentedControl": 7}


def _label(control):
    if control.get("label") is not None:
        return control["label"]
    cid = control["id"]
    noise = {"label", "value", "chip", "ring", "gauge", "light", "spark"}
    words = [word for word in re.split(r"[-_.]+", cid) if word and word.lower() not in noise]
    return " ".join(word[:1].upper() + word[1:] for word in (words or [cid]))


class LayoutSurfaces:
    """A hub's notifications, widgets, Control Center state and Live Activities.

    The layout must declare a stable ``id`` or have been loaded from a filename.
    ``snapshot`` and ``activity_state`` are pure preview helpers; only ``refresh``,
    ``notify`` and ``start/update/end_activity`` make HTTP requests.
    """
    def __init__(self, hub):
        self.hub = hub

    @property
    def layout_id(self):
        return canonical_layout_id(self.hub.layout, filename=self.hub._layout_filename)

    def _projection(self, values=None):
        layout = self.hub.layout or {}
        config = layout.get("glance") or {}
        if config.get("enabled") is False:
            raise ValueError("this layout disables glance surfaces")
        known = dict(self.hub.client._control_state)
        for target, value in (values or {}).items():
            control = self.hub._control(target)
            _scalar(value)
            known[control["id"]] = value
        candidates = []
        for order, control in enumerate(self.hub._index.values()):
            kind = control.get("type")
            if kind not in _KINDS:
                continue
            synced = any(s.get("type") == "listen" for s in control.get("sync") or [])
            if kind == "label" and not synced:
                continue
            candidates.append((_RANK[kind] - (10 if synced else 0), order, control["id"]))
        ranked = [cid for _, _, cid in sorted(candidates)]
        hero = config.get("hero")
        secondary = config.get("slots")
        if hero is None:
            hero = next((cid for cid in ranked if cid not in (secondary or [])), None)
        if not secondary:
            secondary = [cid for cid in ranked if cid != hero][:3]
        if len(secondary) > 3:
            raise ValueError("glance.slots supports at most 3 controls")
        tint = config.get("tint", layout.get("accentColor"))

        def make_slot(cid):
            control = self.hub._control(cid)
            kind = _KINDS.get(control.get("type"))
            if kind is None:
                raise ValueError(f"control {cid!r} is not a scalar glance reading")
            value = known.get(cid, control.get("defaultValue"))
            extra = {k: control[k] for k in ("min", "max", "formatValue", "statusColors", "tint") if k in control}
            if tint and "tint" not in extra:
                extra["tint"] = tint
            return slot(cid, _label(control), kind, value, **extra)

        state_values = {}
        for cid, value in known.items():
            if cid not in self.hub._index or self.hub._index[cid].get("type") not in _KINDS:
                continue
            _scalar(value)
            state_values[cid] = value
        controls = {}
        claimed = set()
        for definition in config.get("controls") or []:
            claimed.add(definition.get("control"))
            claimed.add(definition["id"])
            if definition.get("kind") == "toggle":
                value = known.get(definition.get("control"))
                if isinstance(value, bool):
                    controls[definition["id"]] = value
        for cid, value in state_values.items():
            control = self.hub._index[cid]
            action = control.get("action") or {}
            if cid not in claimed and control.get("type") == "toggle" and action.get("method") == "meshsocket":
                if isinstance(value, bool):
                    controls[cid] = value
        return dict(title=config.get("title") or layout.get("headerTitle") or layout.get("name") or "CAR-TER",
                    icon=config.get("icon") or "square.grid.2x2", tint=tint,
                    hero=make_slot(hero) if hero else None,
                    slots=[make_slot(cid) for cid in dict.fromkeys(secondary) if cid != hero],
                    values=state_values, controls=controls)

    def snapshot(self, values=None, *, is_connected=True):
        """Preview the exact widget/control payload; no network or state mutation."""
        return glance_update(layout_id=self.layout_id, is_connected=is_connected,
                             **self._projection(values))

    def activity_state(self, values=None, *, is_connected=True, hero_history=None):
        """Preview ActivityKit content using the correct Apple reference-date epoch."""
        projection = self._projection(values)
        return content_state(hero=projection["hero"], slots=projection["slots"],
                             is_connected=is_connected, updated_at=apple_date(time.time()),
                             hero_history=hero_history)

    async def refresh(self, values=None, *, is_connected=True):
        """Send one best-effort silent refresh for widgets, values and toggles."""
        return await self.hub.client.notify("", "", layout_id=self.layout_id,
            glance=self.snapshot(values, is_connected=is_connected), silent=True, encrypt=False)

    async def notify(self, title, body, *, values=None, include_glance=False, **options):
        """Send an account alert that opens this layout, optionally with fresh data.

        ``actions`` accepts ``notification_action(..., callback=...)``; callbacks
        receive the original frame and inline reply in ``frame['userText']``.
        """
        if "layout_id" in options:
            raise ValueError("layout_id is derived from this hub's layout")
        if include_glance or values is not None:
            if "glance" in options:
                raise ValueError("choose values/include_glance or an explicit glance payload")
            options["glance"] = self.snapshot(values)
        return await self.hub.client.notify(title, body, layout_id=self.layout_id, **options)

    def on_notification(self, handler):
        """Register a catch-all response handler; usable as a decorator.

        Unlike per-send callbacks, this can be re-registered after a hub restart.
        """
        return self.hub.client.on_notif_action(handler)

    async def start_activity(self, values=None, *, alert_title=None, alert_body=None, **options):
        projection = self._projection(values)
        attributes = activity_attributes(layout_id=self.layout_id, title=projection["title"],
            icon=projection["icon"], tint=projection["tint"], started_at=apple_date(time.time()))
        return await self.hub.client.push_live_activity(layout_id=self.layout_id, event="start",
            content_state=self.activity_state(values), attributes=attributes,
            alert_title=alert_title, alert_body=alert_body, **options)

    async def update_activity(self, values=None, *, is_connected=True, hero_history=None, **options):
        options.setdefault("priority", 5)
        return await self.hub.client.push_live_activity(layout_id=self.layout_id, event="update",
            content_state=self.activity_state(values, is_connected=is_connected, hero_history=hero_history), **options)

    async def end_activity(self, values=None, **options):
        return await self.hub.client.push_live_activity(layout_id=self.layout_id, event="end",
            content_state=self.activity_state(values, is_connected=False), **options)
