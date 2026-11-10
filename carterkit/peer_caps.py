"""Filter a layout to what the paired phone's app version supports.

The phone's ``studio.event`` hello carries ``appVersion`` and ``manifestHash`` (CAR-TER
aif-xd1w8.4). The vendored ``capabilities.json`` pins every field with ``since``: a
version, or ``next`` (unreleased: no shipped app has it). A hub keeps only fields with
``since <= appVersion``. Without a known version nothing is filtered."""
from __future__ import annotations

import copy
from typing import Optional

from .validate import capabilities_manifest, _is_app_version, _version_newer


def field_supported(cap_id: str, app_version: Optional[str]) -> bool:
    """True when the phone at ``app_version`` supports capability ``cap_id``.

    Unknown version or unknown capability: supported (never strip what we cannot judge)."""
    if not _is_app_version(app_version):
        return True
    caps = capabilities_manifest().get("capabilities")
    entry = caps.get(cap_id) if isinstance(caps, dict) else None
    since = entry.get("since") if isinstance(entry, dict) else None
    if since is None:
        return True
    if since == "next":
        return False
    if not _is_app_version(since):
        return True
    return not _version_newer(since, app_version)


def manifest_matches(manifest_hash: Optional[str]) -> bool:
    """True when the phone's manifest hash equals the vendored one (no filtering needed)."""
    return bool(manifest_hash) and manifest_hash == capabilities_manifest().get("hash")


def filter_control(ctrl: dict, app_version: Optional[str]) -> list:
    """Strip, in place, the top-level fields of ``ctrl`` (and nested controls) the phone
    cannot read. Returns the dropped ``type.field`` ids."""
    dropped: list = []
    ctype = ctrl.get("type")
    if isinstance(ctype, str):
        for key in list(ctrl):
            if key in ("type", "id"):
                continue
            cap = f"{ctype}.{key}"
            if not field_supported(cap, app_version):
                del ctrl[key]
                dropped.append(cap)
    for child in ctrl.get("children") or []:
        if isinstance(child, dict):
            dropped += filter_control(child, app_version)
    for panel in ctrl.get("panels") or []:
        if isinstance(panel, dict):
            for child in panel.get("children") or []:
                if isinstance(child, dict):
                    dropped += filter_control(child, app_version)
    return dropped


def filter_layout(layout: dict, app_version: Optional[str],
                  manifest_hash: Optional[str] = None) -> tuple:
    """(filtered copy, dropped ids). Returns the layout untouched when the version is
    unknown or the phone's manifest hash matches ours."""
    if not _is_app_version(app_version) or manifest_matches(manifest_hash):
        return layout, []
    out = copy.deepcopy(layout)
    dropped: list = []
    for tab in out.get("tabs") or []:
        for ch in tab.get("children") or []:
            if isinstance(ch, dict):
                dropped += filter_control(ch, app_version)
    return out, dropped
