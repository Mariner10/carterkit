"""Layout-aware connectors for CAR-TER's iOS surfaces.

Use ``hub.surfaces``: no duplicated labels, control IDs, wire types or date epochs.
Remote refresh is explicit so telemetry-rate ``hub.push`` calls never consume
notification or ActivityKit budgets behind the caller's back.
"""
import time
import re

from .ambient import (activity_attributes, apple_date, canonical_layout_id,
                      content_state, glance_update, slot, surfaces_deregister_token,
                      surfaces_get_state, surfaces_publish, surfaces_register_token,
                      _scalar)

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
    ``snapshot`` and ``activity_state`` are pure preview helpers; every other
    method here makes an HTTP request to the validator host.

    Two routes reach the same surfaces from opposite directions. ``refresh`` and
    ``notify`` push a payload *at* the device, so something of ours must be alive
    to apply it. ``publish`` writes the relay's **retained** state and pokes every
    surface, so a widget iOS wakes tomorrow can pull current values with no app
    process at all — that is the one to reach for.
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

    # ── /surfaces: the relay's retained state + one push for every surface ────
    #
    # `refresh` above spends a notification budget to nudge a *running* app; these
    # go the other way. The relay holds the layout's latest values, so a widget
    # iOS wakes tomorrow morning still has something to render, and one `publish`
    # pokes widgets, Control Center and the Live Activity together.

    def _values_by_id(self, values):
        """Resolve `{handle-or-id: value}` to `{controlId: value}` — the wire keys
        the relay stores. Same resolution `refresh` uses, so the two agree about
        what a handle means."""
        if values is None:
            return None
        out = {}
        for target, value in values.items():
            control = self.hub._control(target)
            cid = control.get("id")
            if not cid:
                raise ValueError(f"control {target!r} has no id to publish under")
            _scalar(value)
            out[cid] = value
        return out

    def _controls_by_id(self, controls):
        """Glance-control ids (`glance.controls[].id`), not layout control ids —
        a Control Center tile is its own thing. A handle is still accepted, for
        the common case where the tile mirrors one control."""
        if controls is None:
            return None
        out = {}
        for target, value in controls.items():
            cid = target if isinstance(target, str) else getattr(target, "id", None)
            if not isinstance(cid, str) or not cid:
                raise ValueError(f"control key {target!r} must be a glance control id "
                                 f"or a Layout control handle")
            _scalar(value)
            out[cid] = value
        return out

    async def publish(self, values=None, *, controls=None, is_connected=True,
                      activity=None, force=False):
        """Publish this layout's state and poke every surface (POST /surfaces/publish).

        ONE call refreshes the widgets, the Control Center controls and the Live
        Activity, and leaves the values retained on the relay for whatever iOS
        wakes later::

            await hub.surfaces.publish({nozzle: 214.5, bed: 60}, activity=True)

        `values` is keyed by control handle or id (ids go on the wire); `controls`
        mirrors Control Center tile state keyed by `glance.controls[].id`.

        `activity` chooses whether the Live Activity is pushed too: omit it for
        widgets and controls only, pass ``True`` to let the relay build the content
        state from the merged values, ``"end"`` to finish the session, or a dict
        (`contentState`, `staleSeconds`, `priority`, `relevanceScore`, `event`) to
        say exactly what to send. :meth:`activity_state` builds a `contentState`
        from this layout's own hero/slots if you want the app's shape verbatim.

        Publishing at telemetry rate is safe. The relay's floors (widgets ≥ 60 s,
        controls ≥ 10 s, activity ≥ 2 s) skip the *push* inside a window but still
        merge the state, and report that as `suppressed`; the surface shows the
        newest value at its next wake either way. `force=True` asks for the
        higher-priority push where the floor allows it — it does not lift it."""
        if activity is True:
            activity = {}
        elif activity == "end":
            activity = {"event": "end"}
        elif activity is False:
            activity = None
        return await self.hub.client._ambient_call(
            surfaces_publish, layout_id=self.layout_id,
            values=self._values_by_id(values), controls=self._controls_by_id(controls),
            is_connected=is_connected, activity=activity, force=force)

    async def state(self):
        """Read back what the relay holds for this layout (GET /surfaces/state/…).

        `{layoutId, values, controls, isConnected, updatedAt}`, or **None** before
        anything has been published. This is the same state a widget pulls when
        iOS wakes it, so it answers "what would the Home Screen show right now"."""
        return await self.hub.client._ambient_call(surfaces_get_state,
                                                   layout_id=self.layout_id)

    async def register_token(self, *, kind, key, bundle_id, token):
        """Register a widget or Control Center push token for this layout.

        The device registers its own tokens; this exists for provisioning and
        tests. `kind` is `"widget"` or `"control"`, `key` the widget/control kind
        the token was issued for, and `bundle_id` the build that minted it — the
        APNs topic is `<bundleId>.push-type.<kind>`, so a mismatched bundle id is
        refused by APNs, not here."""
        return await self.hub.client._ambient_call(
            surfaces_register_token, layout_id=self.layout_id, kind=kind, key=key,
            bundle_id=bundle_id, token=token)

    async def deregister_token(self, *, kind, key, bundle_id, token):
        """Drop a registered surface token. Pass exactly what was registered;
        de-registering an unknown token succeeds."""
        return await self.hub.client._ambient_call(
            surfaces_deregister_token, layout_id=self.layout_id, kind=kind, key=key,
            bundle_id=bundle_id, token=token)
