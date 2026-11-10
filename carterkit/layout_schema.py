"""The layout document as a JSON Schema (draft 2020-12), generated from the ControlDocs catalog.

Published as ``carterkit/schema.json``; regenerate with ``python3 -m carterkit.layout_schema``
(``--check`` exits 1 when the committed file is stale; tests/test_schema.py does the same).

Deliberately lenient where the app is lenient: unknown keys are allowed, enum values are
listed as ``examples`` (the app falls back to the default for a non-canonical value), and
per-control fields are described (``x-carter-type``) but not type-enforced.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from . import catalog, controldocs_dir

SCHEMA_PATH = Path(__file__).with_name("schema.json")
DIALECT = "https://json-schema.org/draft/2020-12/schema"


def _field_schema(f: dict) -> dict[str, Any]:
    """Documentation, not enforcement: the app coerces loosely (a number field may carry a
    string, an array a JSON-encoded string, any field a `{{binding}}`), so the doc type rides
    along as `x-carter-type` and only the structural keys are typed."""
    out: dict[str, Any] = {}
    if f.get("type"):
        out["x-carter-type"] = f["type"]
    if f.get("description"):
        out["description"] = f["description"]
    if f.get("type") == "enum" and f.get("values"):
        out["examples"] = list(f["values"])
    return out


def _control_schema(doc: dict) -> dict[str, Any]:
    props = {}
    for f in doc["fields"] + doc["themeFields"]:
        if f.get("name"):
            props[f["name"]] = _field_schema(f)
    return {"if": {"properties": {"type": {"const": doc["type"]}}, "required": ["type"]},
            "then": {"properties": props}}


def get_layout_json_schema(docs_dir=None) -> dict[str, Any]:
    docs = catalog.parse_all(docs_dir or controldocs_dir())
    types = sorted({d["type"] for d in docs.values() if d.get("type")})
    by_type = {}
    for d in docs.values():
        if d.get("type"):
            by_type.setdefault(d["type"], d)
    control = {
        "type": "object",
        "required": ["type"],
        "properties": {
            "type": {"type": "string", "examples": types},
            "id": {"type": "string"},
            "position": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
            "span": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
            "children": {"type": "array", "items": {"$ref": "#/$defs/control"}},
        },
        "allOf": [_control_schema(by_type[t]) for t in types],
    }
    tab = {
        "type": "object",
        "properties": {
            "title": {"type": "string"}, "icon": {"type": "string"}, "grid": {"type": "object"},
            "children": {"type": "array", "items": {"$ref": "#/$defs/control"}},
        },
    }
    return {
        "$schema": DIALECT,
        "$id": "https://carter.app/schema/layout.schema.json",
        "title": "CAR-TER layout",
        "type": "object",
        "required": ["name", "version", "tabs"],
        "properties": {
            "name": {"type": "string"},
            "version": {"type": "integer"},
            "headerTitle": {"type": "string"},
            "accentColor": {"type": "string"},
            "tabs": {"type": "array", "items": {"$ref": "#/$defs/tab"}},
        },
        "$defs": {"tab": tab, "control": control},
    }


def render(docs_dir=None) -> str:
    return json.dumps(get_layout_json_schema(docs_dir), indent=2, sort_keys=True) + "\n"


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    text = render()
    if "--check" in args:
        if not SCHEMA_PATH.exists() or SCHEMA_PATH.read_text() != text:
            print("carterkit/schema.json is stale; run: python3 -m carterkit.layout_schema", file=sys.stderr)
            return 1
        return 0
    SCHEMA_PATH.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
