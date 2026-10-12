"""Layout-aware connectors for CAR-TER's iOS surfaces.

Use ``hub.surfaces``: no duplicated labels, control IDs, wire types or date epochs.
Remote refresh is explicit so telemetry-rate ``hub.push`` calls never consume
notification or ActivityKit budgets behind the caller's back.
"""
import asyncio
import logging
import math
import time
import re

from .ambient import (activity_attributes, apple_date, canonical_layout_id,
                      content_state, glance_update, slot, surfaces_deregister_token,
                      surfaces_get_state, surfaces_publish, surfaces_register_token,
                      _scalar)

_log = logging.getLogger(__name__)
_warned_no_tokens = set()  # layout ids already warned about, per process

_KINDS = {"gauge": "gauge", "progressRing": "ring", "statusLight": "light",
          "sparkline": "number", "slider": "number", "stepper": "number",
          "toggle": "bool", "label": "text", "picker": "text", "segmentedControl": "text"}
_RANK = {"gauge": 0, "progressRing": 1, "statusLight": 2, "sparkline": 3,
         "slider": 4, "stepper": 5, "toggle": 6, "label": 7, "picker": 7, "segmentedControl": 7}


#: `glance.live.activity.remoteCadence` per `live.tier` (seconds); `fresh` is the default.
_TIER_REMOTE_CADENCE = {"realtime": 2, "fresh": 5, "periodic": 30}
_MIN_LIVE_EVERY = 2.0  # the relay's Live Activity floor
_MAX_STALE_AFTER = 86400


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) \
        and math.isfinite(v) else None


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
        self._received = {}      # control id -> unix seconds the hub last received it
        self._live = None        # keep_live state, or None while it is off
        self._last_ms = {}       # control id -> last valuesAt sent (kept monotonic)
        self._sleep = asyncio.sleep  # injectable for tests

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

    # ── freshness: the app's own rule, so a hub-driven surface agrees with it ──

    def stale_after(self, target):
        """Resolved `staleAfter` seconds for a control, or None (never stale).

        Same order as the app: the control's sync `staleAfter`, then the layout's
        `liveness.staleAfter`, then 3x the poll interval of an `http` sync. 0 opts
        out; values over a day are clamped."""
        control = self.hub._control(target)
        syncs = [e for e in control.get("sync") or [] if isinstance(e, dict)]
        value = next((_num(e["staleAfter"]) for e in syncs
                      if _num(e.get("staleAfter")) is not None), None)
        if value is None:
            value = _num(((self.hub.layout or {}).get("liveness") or {}).get("staleAfter"))
        if value is None:
            polls = [_num(e.get("interval")) for e in syncs if e.get("method") == "http"]
            polls = [p for p in polls if p]
            value = 3 * polls[0] if polls else None
        if value is None or value <= 0:
            return None
        return min(value, _MAX_STALE_AFTER)

    def _stamp(self, entry):
        """Add `receivedAt` (reference-date seconds) and `staleAfter` to a slot."""
        out = dict(entry)
        cid = out["controlId"]
        if cid in self._received:
            out["receivedAt"] = apple_date(self._received[cid])
        stale = self.stale_after(cid)
        if stale is not None:
            out["staleAfter"] = stale
        return out

    def snapshot(self, values=None, *, is_connected=True):
        """Preview the exact widget/control payload; no network or state mutation."""
        return glance_update(layout_id=self.layout_id, is_connected=is_connected,
                             **self._projection(values))

    def activity_state(self, values=None, *, is_connected=True, hero_history=None):
        """Preview ActivityKit content using the correct Apple reference-date epoch."""
        projection = self._projection(values)
        hero = projection["hero"]
        return content_state(hero=self._stamp(hero) if hero else None,
                             slots=[self._stamp(e) for e in projection["slots"]],
                             is_connected=is_connected, updated_at=apple_date(time.time()),
                             hero_history=hero_history)

    def activity_payload(self, values=None, *, is_connected=True, hero_history=None, **options):
        """`activity=` argument for :meth:`publish`: :meth:`activity_state` plus
        `staleSeconds` following the lead slot (hero, else the first slot) so a
        hub-driven island goes stale by the source's own deadline."""
        state = self.activity_state(values, is_connected=is_connected,
                                    hero_history=hero_history)
        out = {"contentState": state, **options}
        lead = state.get("hero") or next(iter(state["slots"]), None)
        if lead and lead.get("staleAfter") and "staleSeconds" not in out:
            out["staleSeconds"] = max(1, math.ceil(lead["staleAfter"]))
        return out

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
                      activity=None, force=False, values_at=None):
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
        higher-priority push where the floor allows it — it does not lift it.

        The reply is the relay's dict plus **`no_tokens`**: True when nothing was
        pushed, pruned or suppressed and there is no error, i.e. no device has
        registered a widget / Control Center / Live Activity token (the phone never
        opened CAR-TER). A warning is logged once per layout per process until a
        later publish reaches a surface."""
        if activity is True:
            activity = {}
        elif activity == "end":
            activity = {"event": "end"}
        elif activity is False:
            activity = None
        result = await self.hub.client._ambient_call(
            surfaces_publish, layout_id=self.layout_id,
            values=self._values_by_id(values), controls=self._controls_by_id(controls),
            is_connected=is_connected, activity=activity, force=force,
            values_at=values_at)
        return self._flag_no_tokens(result)

    # ── keep_live: opt-in background publishing so surfaces outlive the app ──

    def _remote_cadence(self):
        live = ((self.hub.layout or {}).get("glance") or {}).get("live") or {}
        cadence = _num((live.get("activity") or {}).get("remoteCadence"))
        if cadence is None:
            cadence = _TIER_REMOTE_CADENCE.get(live.get("tier"), 5)
        return max(cadence, _MIN_LIVE_EVERY)

    def keep_live(self, every=None, *, activity=False, send_values_at=True):
        """Opt in: keep the relay's retained surface state current from this hub.

        After this, every ``hub.push`` of a glance-watched control schedules ONE
        debounced publish per `every` seconds (default: the layout's
        ``glance.live`` remote cadence; floor 2 s) carrying the changed values,
        ``valuesAt`` (this hub's receipt time per key, unix ms, monotonic) and
        ``isConnected=True``. Widgets, Control Center and the Live Activity then
        keep updating with CAR-TER closed and go stale only when the hub stops.
        ``activity=True`` also pushes the Live Activity (spends its budget).
        ``send_values_at=False`` omits ``valuesAt`` for a relay that predates it.

        Without this call nothing is ever published behind your back. Call from
        a running event loop; :meth:`stop_live` (or ``hub.close()``) ends it and
        publishes ``isConnected=False`` once."""
        every = self._remote_cadence() if every is None else max(float(every), _MIN_LIVE_EVERY)
        self._live = {"every": every, "activity": bool(activity),
                      "values_at": bool(send_values_at), "pending": {}, "task": None}
        return self

    def _note_push(self, control, value):
        cid = control.get("id")
        if control.get("type") not in _KINDS or not cid:
            return
        now = time.time()
        self._received[cid] = now
        live = self._live
        if live is None:
            return
        live["pending"][cid] = (value, now)
        task = live["task"]
        if task is None or task.done():
            live["task"] = asyncio.get_running_loop().create_task(self._flush_later(live))

    async def _flush_later(self, live):
        await self._sleep(live["every"])
        await self._flush(live)

    async def _flush(self, live, *, is_connected=True):
        pending, live["pending"] = live["pending"], {}
        if not pending and is_connected:
            return None
        values = {}
        stamps = {}
        for cid, (value, at) in pending.items():
            values[cid] = value
            ms = int(at * 1000)
            if cid in self._last_ms:
                ms = max(ms, self._last_ms[cid] + 1)
            self._last_ms[cid] = stamps[cid] = ms
        activity = None
        if live["activity"]:
            activity = self.activity_payload(values, is_connected=is_connected)
        try:
            return await self.publish(values or None, is_connected=is_connected,
                                      activity=activity,
                                      values_at=stamps if live["values_at"] and stamps else None)
        except Exception:
            _log.warning("surfaces: keep_live publish failed", exc_info=True)
            return None

    async def stop_live(self):
        """Turn :meth:`keep_live` off: ONE final publish with any pending values and
        ``isConnected=False``. A no-op when keep_live is off."""
        live, self._live = self._live, None
        if live is None:
            return None
        task = live["task"]
        if task is not None and not task.done():
            task.cancel()
        return await self._flush(live, is_connected=False)

    def _flag_no_tokens(self, result):
        if not isinstance(result, dict):
            return result
        suppressed = result.get("suppressed") or {}
        no_tokens = (not result.get("widgets") and not result.get("controls")
                     and not result.get("activity") and not result.get("pruned")
                     and not any(suppressed.values()) and not result.get("error"))
        result["no_tokens"] = no_tokens
        if not no_tokens:
            if not result.get("error"):
                _warned_no_tokens.discard(self.layout_id)
        elif self.layout_id not in _warned_no_tokens:
            _warned_no_tokens.add(self.layout_id)
            _log.warning("surfaces: no widget/Control Center/Live Activity token is "
                         "registered for layout %s; open CAR-TER on the device once so "
                         "they register", self.layout_id)
        return result

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
