"""``carterkit new <name> [--template <kit>]``: write a starter project.

Without a template it is ``hello.py`` (a layout built in Python). A starter kit is a
``layout.json`` (the layout, ``carterkit validate`` clean), a ``hub.py`` that serves it
(``python hub.py``: pair by QR, push, handle, every save reaches the phone) and a
README; ``carterkit new --list`` names them.
"""
from __future__ import annotations

import os
import re
from importlib.resources import files

#: Files every project gets: (template file, destination relative to the project)
_COMMON = (
    ("secrets_gitignore", os.path.join("secrets", ".gitignore")),
    ("gitignore", ".gitignore"),
    ("vscode_settings.json", os.path.join(".vscode", "settings.json")),
)

#: The default project: (template file, destination)
_FILES = (("hello.py", "hello.py"), ("README.md", "README.md")) + _COMMON

#: Starter kits, in `--list` order: name -> what it shows. Each is
#: scaffold_templates/kits/<name>/ with these files.
KITS = {
    "paged-cards": "a card list the hub pages and searches; each card expands into a detail page",
    "confirm-delete": "a Delete that asks first (hub.confirm) before the hub removes anything",
    "live-dashboard": "a gauge, a sparkline and a readout fed live by the hub's broadcasts",
    "hub-form": "a form whose Send reaches the hub, which checks it and answers",
    "scaled-grid": "a 1x5 card drawing a 3x15 grid at 1/3 (grid.scale auto) and a hub sheet",
    "remote": "toggles and sliders whose state the hub owns and sends back",
}
KIT_FILES = ("layout.json", "hub.py", "README.md")


def list_lines() -> list[str]:
    """``carterkit new --list``: one line per kit."""
    width = max(len(k) for k in KITS)
    return [f"{name.ljust(width)}  {what}" for name, what in KITS.items()]


def scaffold(path: str, template: str | None = None) -> list[str]:
    """Create the project at `path` (from starter kit `template` when given); refuse a
    non-empty existing directory or an unknown kit. Returns the files written
    (relative paths)."""
    if template is not None and template not in KITS:
        raise ValueError(f"no starter kit {template!r}; pick one of: {', '.join(KITS)}")
    if os.path.isdir(path) and os.listdir(path):
        raise FileExistsError(f"{path} exists and is not empty; pick a new name")
    if os.path.exists(path) and not os.path.isdir(path):
        raise FileExistsError(f"{path} exists and is not a directory")
    name = os.path.basename(os.path.normpath(path))
    ident = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "hello"
    root = files("carterkit") / "scaffold_templates"
    if template is None:
        plan = [(root / tpl, dest) for tpl, dest in _FILES]
    else:
        kit = root / "kits" / template
        plan = [(kit / f, f) for f in KIT_FILES] + [(root / tpl, dest) for tpl, dest in _COMMON]
    written = []
    for src, dest in plan:
        text = src.read_text(encoding="utf-8")
        text = text.replace("__NAME__", name).replace("__ID__", ident)
        full = os.path.join(path, dest)
        os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)
        written.append(dest)
    return written
