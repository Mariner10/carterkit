"""``carterkit new <name>``: write a starter project."""
from __future__ import annotations

import os
import re
from importlib.resources import files

#: (template file, destination relative to the project)
_FILES = (
    ("hello.py", "hello.py"),
    ("README.md", "README.md"),
    ("secrets_gitignore", os.path.join("secrets", ".gitignore")),
    ("vscode_settings.json", os.path.join(".vscode", "settings.json")),
)


def scaffold(path: str) -> list[str]:
    """Create the project at `path`; refuse a non-empty existing directory.
    Returns the files written (relative paths)."""
    if os.path.isdir(path) and os.listdir(path):
        raise FileExistsError(f"{path} exists and is not empty; pick a new name")
    if os.path.exists(path) and not os.path.isdir(path):
        raise FileExistsError(f"{path} exists and is not a directory")
    name = os.path.basename(os.path.normpath(path))
    ident = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "hello"
    src = files("carterkit") / "scaffold_templates"
    written = []
    for tpl, dest in _FILES:
        text = (src / tpl).read_text(encoding="utf-8")
        text = text.replace("__NAME__", name).replace("__ID__", ident)
        full = os.path.join(path, dest)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)
        written.append(dest)
    return written
