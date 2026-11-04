"""Control catalog + example extraction — pure parsing of the ControlDocs markdown.

Mirrors the app's `ControlDocLoader` frontmatter parser (Swift) so the MCP and the
device agree on the field schema for every control. Deliberately does NOT use a real
YAML parser: the docs carry unquoted `#hex` defaults (e.g. `default: #667eea`) which
YAML would treat as comments, and some values omit quotes inconsistently. The
hand-rolled parser tolerates both.

Public surface (all pure; `docs_dir` is injected for testability):
    parse_doc(content, node_id, shared=None) -> dict | None   one doc's frontmatter + body +
                                     examples, `- use:` shared fields expanded
    load_shared(docs_dir)            -> {section: {name: raw}}   shared-fields.md
    use_errors(docs_dir)             -> [str]   `use:` lint (unknown names, other overrides)
    parse_all(docs_dir)              -> {node_id: doc}
    build_catalog(docs_dir, types)   -> {type: compact}   placeable-control schema
    get_examples(docs_dir, control)  -> [{"name", "json"}]
    find_example(docs_dir, control, name) -> {"name", "json"} | None
    resolve_doc(docs_dir, control)   -> doc | None   accepts node_id OR control type
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


# ─── Frontmatter parsing (mirrors ControlDocLoader.swift) ────────────────────


def _parse_str_array(value: str) -> list[str]:
    inner = value.strip().strip("[]")
    out = []
    for part in inner.split(","):
        s = part.strip().strip("\"'")
        if s:
            out.append(s)
    return out


def _parse_int_array(value: str) -> Optional[list[int]]:
    inner = value.strip().strip("[]")
    parts = []
    for part in inner.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            parts.append(int(part))
        except ValueError:
            return None
    return parts or None


def _parse_json(value: str, kind):
    """A one-line JSON frontmatter value (`starterPreset`, `starterVariants`), or
    None when it is missing, malformed, or not of `kind`."""
    try:
        parsed = json.loads(value)
    except ValueError:
        return None
    return parsed if isinstance(parsed, kind) else None


def _make_field(raw: dict[str, str]) -> dict:
    field: dict = {"name": raw.get("name", ""), "type": raw.get("type", "string")}
    if "values" in raw:
        field["values"] = _parse_str_array(raw["values"])
    if "default" in raw:
        field["default"] = raw["default"]
    if raw.get("description"):
        field["description"] = raw["description"]
    if raw.get("title"):
        # Friendly Simple-mode name ("Lowest value" for `min`), mirrored from the
        # Swift loader's authoredTitle (carter-1cz0). Absent = the app humanises
        # the key, so the catalog leaves it out rather than guessing.
        field["title"] = raw["title"]
    if raw.get("summary"):
        field["summary"] = raw["summary"]
    if raw.get("does"):
        field["does"] = raw["does"]
    if raw.get("valueHelp"):
        vh = _parse_json(raw["valueHelp"], dict)
        if vh:
            field["valueHelp"] = {str(k): str(v) for k, v in vh.items()}
    if raw.get("simple", "").lower() == "hide":
        # `simple: hide` — the lay path sets this field, so Simple mode leaves it
        # off every inspector tab (Swift simpleHidden, carter-1cz0).
        field["simpleHidden"] = True
    if raw.get("group"):
        # Per-field `group:` nests the field under a config object (e.g.
        # `sortboardConfig`) — mirrored from the Swift loader's makeField.
        field["group"] = raw["group"]
    return field


# ─── Shared fields: `- use: <name>` (app bead aif-fa4jj) ──────────────────────
#
# A field many docs share is written once in controldocs/shared-fields.md; a doc's
# `fields:` / `themeFields:` entry says `- use: <name>` (same section) plus optional
# overrides, and is expanded here exactly as the app's ControlDocLoader.FieldReader does.

SHARED_DOC = "shared-fields.md"
USE_OVERRIDES = ("default", "min", "max", "step", "does", "since")
_FIELD_SECTIONS = ("fields", "themeFields")
_BUNDLED_SHARED: Optional[dict] = None


def _read_fields(front: list[str], shared: dict) -> tuple[list[tuple[str, dict]], list[str]]:
    """Raw `fields:` / `themeFields:` entries as (section, {key: value}), `use:` expanded,
    plus the doc's use: lint errors."""
    entries: list[tuple[str, dict]] = []
    errors: list[str] = []
    section: Optional[str] = None
    current: dict[str, str] = {}
    use: Optional[str] = None
    overrides: list[tuple[str, str]] = []

    def flush():
        nonlocal current, use, overrides
        if section is not None:
            if use is None:
                if current:
                    entries.append((section, current))
            else:
                base = (shared.get(section) or {}).get(use)
                if base is None:
                    other = [s for s in _FIELD_SECTIONS if s != section and use in (shared.get(s) or {})]
                    hint = f" (it is shared under {other[0]}:)" if other else ""
                    errors.append(f"{section} use: {use} is not in {SHARED_DOC}{hint}")
                else:
                    merged = dict(base)
                    for k, v in overrides:
                        if k not in USE_OVERRIDES:
                            errors.append(f"{section} use: {use} overrides `{k}`; "
                                          f"allowed: {', '.join(USE_OVERRIDES)}")
                        elif base.get(k) == v:
                            errors.append(f"{section} use: {use} override `{k}` repeats the shared value")
                        merged[k] = v
                    entries.append((section, merged))
        current, use, overrides = {}, None, []

    for line in front:
        if not line.strip():
            continue
        if not line.startswith((" ", "\t")) and ":" in line:
            flush()
            key = line.partition(":")[0].strip()
            section = key if key in _FIELD_SECTIONS else None
            continue
        if section is None:
            continue
        trimmed = line.strip()
        if trimmed.startswith("- name:"):
            flush()
            current = {"name": trimmed[len("- name:"):].strip().strip("\"'")}
        elif trimmed.startswith("- use:"):
            flush()
            use = trimmed[len("- use:"):].strip().strip("\"'")
        elif ":" in trimmed:
            k, _, v = trimmed.partition(":")
            if use is not None:
                overrides.append((k.strip(), v.strip().strip('"')))
            else:
                current[k.strip()] = v.strip().strip('"')
    flush()
    return entries, errors


def _frontmatter(content: str) -> Optional[tuple[list[str], str]]:
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1:]).strip()
    return None


def parse_shared(content: str) -> dict[str, dict[str, dict]]:
    """{section: {name: raw entry}} from a shared-fields.md text (first definition wins)."""
    out: dict[str, dict[str, dict]] = {s: {} for s in _FIELD_SECTIONS}
    fm = _frontmatter(content)
    for section, raw in (_read_fields(fm[0], {})[0] if fm else []):
        if raw.get("name"):
            out[section].setdefault(raw["name"], raw)
    return out


def load_shared(docs_dir) -> dict[str, dict[str, dict]]:
    """The shared entries of `docs_dir`/shared-fields.md (empty when it is absent)."""
    path = Path(docs_dir) / SHARED_DOC
    return parse_shared(path.read_text()) if path.is_file() else parse_shared("")


def _bundled_shared() -> dict:
    global _BUNDLED_SHARED
    if _BUNDLED_SHARED is None:
        _BUNDLED_SHARED = load_shared(Path(__file__).resolve().parent / "controldocs")
    return _BUNDLED_SHARED


def use_errors(docs_dir) -> list[str]:
    """Every `use:` lint error under `docs_dir` (unknown names, other overrides, a shared
    entry that uses another), as "file: message"."""
    root = Path(docs_dir)
    shared = load_shared(root)
    out = []
    for f in sorted(root.rglob("*.md")):
        fm = _frontmatter(f.read_text())
        if fm is None:
            continue
        rel = f.relative_to(root).as_posix()
        errors = _read_fields(fm[0], {} if f.name == SHARED_DOC else shared)[1]
        if f.name == SHARED_DOC:
            errors = [f"a shared entry cannot use: another ({e})" for e in errors]
        out += [f"{rel}: {e}" for e in errors]
    return out


def parse_doc(content: str, node_id: str, shared: Optional[dict] = None) -> Optional[dict]:
    """Parse one control doc into {node_id,type,label,icon,category,defaultSpan,
    fields,themeFields,body,examples}. Returns None if it lacks a type+label
    (matches the Swift loader, which skips non-control prose-only docs).
    `shared` resolves `- use:` entries; None uses the bundled shared-fields.md."""
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None

    front = lines[1:end]
    body = "\n".join(lines[end + 1:]).strip()

    meta: dict = {
        "node_id": node_id,
        "type": "",
        "label": "",
        "icon": "",
        "category": "",
        "defaultSpan": None,
        # Lay-user Add sheet keys (app bead carter-m7s.18). `starterPreset` is the
        # small config a NEW control is seeded from on every insert path — never
        # `sync`/`action` (examples stay docs). One-line JSON in the frontmatter.
        "addIntent": None,
        "friendlyName": None,
        "oneLiner": None,
        "addRank": None,
        "starterPreset": None,
        "starterVariants": [],
        "fields": [],
        "themeFields": [],
    }

    entries, errors = _read_fields(front, _bundled_shared() if shared is None else shared)
    for section, raw in entries:
        meta[section].append(_make_field(raw))
    if errors:
        meta["useErrors"] = errors

    for line in front:
        if not line.strip():
            continue
        top_level = not line.startswith((" ", "\t")) and ":" in line
        if top_level:
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip()
            if key == "type":
                meta["type"] = value
            elif key == "label":
                meta["label"] = value
            elif key == "icon":
                meta["icon"] = value
            elif key == "category":
                meta["category"] = value
            elif key == "defaultSpan":
                meta["defaultSpan"] = _parse_int_array(value)
            elif key == "since":
                # First app version that knows this control ("1.3"); absent = every
                # supported app. Read by validate's target-app lint (layout-config.md
                # "Requires and fallback").
                meta["since"] = value.strip("\"'") or None
            elif key == "addIntent":
                meta["addIntent"] = value if value in ("show", "change", "organize") else None
            elif key in ("friendlyName", "oneLiner"):
                meta[key] = value.strip('"')
            elif key == "addRank":
                meta["addRank"] = int(value) if value.isdigit() else None
            elif key == "starterPreset":
                meta["starterPreset"] = _parse_json(value, dict)
            elif key == "starterVariants":
                meta["starterVariants"] = _parse_json(value, list) or []

    if not meta["type"] or not meta["label"]:
        return None
    # Fields tagged `group: fooConfig` live nested under that key in the JSON
    # (the app decodes them as a config object). Synthesize the umbrella field
    # when the doc doesn't declare it explicitly (heatmap does; the drag pack
    # doesn't), so validators accept the nested key authors actually write.
    declared = {f.get("name") for f in meta["fields"]}
    for grp in dict.fromkeys(f["group"] for f in meta["fields"] if f.get("group")):
        if grp not in declared:
            meta["fields"].append(
                {"name": grp, "type": "object",
                 "description": "grouped config object (see grouped fields)"})
    meta["body"] = body
    meta["examples"] = extract_examples(body)
    return meta


# ─── Example extraction (the `## Examples` section) ──────────────────────────


def extract_examples(body: str) -> list[dict]:
    """Pull named JSON snippets from a doc's `## Examples` section: each `### Title`
    followed by a ```json fenced block becomes {"name", "json"}. Only the Examples
    section is scanned, so unrelated json blocks (e.g. a "## Segments" sample) are
    ignored."""
    lines = body.split("\n")
    start = None
    for i, l in enumerate(lines):
        if l.strip().lower() == "## examples":
            start = i + 1
            break
    if start is None:
        return []
    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    section = lines[start:end]

    examples: list[dict] = []
    title: Optional[str] = None
    seen: dict[str, int] = {}
    i = 0
    while i < len(section):
        l = section[i]
        if l.startswith("### "):
            title = l[4:].strip().strip("`")
            i += 1
            continue
        if l.strip().startswith("```json"):
            j = i + 1
            buf = []
            while j < len(section) and not section[j].strip().startswith("```"):
                buf.append(section[j])
                j += 1
            name = title or f"Example {len(examples) + 1}"
            if name in seen:
                seen[name] += 1
                name = f"{name} ({seen[name]})"
            else:
                seen[name] = 1
            examples.append({"name": name, "json": "\n".join(buf).strip()})
            i = j + 1
            continue
        i += 1
    return examples


# ─── Catalog assembly ────────────────────────────────────────────────────────

# Categories whose docs describe controls that can be placed in a layout grid.
# "layout" covers the structural placeables (divider, spacer) — real grid
# citizens the app renders, previously missing from the catalog so typed
# builders rejected them and servers had to inject raw dicts.
PLACEABLE_CATEGORIES = {"controls", "display", "layout", "input"}


def parse_all(docs_dir) -> dict[str, dict]:
    """Parse every `*.md` doc in the directory. Keyed by node_id (filename stem)."""
    out: dict[str, dict] = {}
    shared = load_shared(docs_dir)
    for f in sorted(Path(docs_dir).glob("*.md")):
        doc = parse_doc(f.read_text(), f.stem, shared)
        if doc:
            out[doc["node_id"]] = doc
    return out


def _compact(doc: dict, include_theme: bool = False) -> dict:
    out: dict = {
        "type": doc["type"],
        "node_id": doc["node_id"],
        "label": doc["label"],
        "category": doc["category"],
    }
    if doc.get("defaultSpan"):
        out["defaultSpan"] = doc["defaultSpan"]
    if doc.get("since"):
        out["since"] = doc["since"]
    for key in ("addIntent", "friendlyName", "oneLiner", "addRank", "starterPreset"):
        if doc.get(key) is not None:
            out[key] = doc[key]
    if doc.get("starterVariants"):
        out["starterVariants"] = doc["starterVariants"]
    if doc.get("fields"):
        out["fields"] = doc["fields"]
    if include_theme and doc.get("themeFields"):
        out["themeFields"] = doc["themeFields"]
    if doc.get("examples"):
        out["examples"] = [e["name"] for e in doc["examples"]]
    return out


def build_catalog(docs_dir, types: Optional[list[str]] = None,
                  include_theme: bool = False) -> dict[str, dict]:
    """Compact, machine-readable schema for placeable controls, keyed by control
    `type` (the value used in a layout). `types` filters to specific control types;
    `include_theme` adds the per-control theme override fields."""
    docs = parse_all(docs_dir)
    catalog: dict[str, dict] = {}
    wanted = set(types) if types else None
    for doc in docs.values():
        t = doc["type"]
        if wanted is not None:
            if t not in wanted and doc["node_id"] not in wanted:
                continue
        elif doc["category"] not in PLACEABLE_CATEGORIES:
            continue
        catalog[t] = _compact(doc, include_theme=include_theme)
    return catalog


def resolve_doc(docs_dir, control: str) -> Optional[dict]:
    """Find a doc by node_id (e.g. 'color-picker') or control type (e.g. 'colorPicker')."""
    docs = parse_all(docs_dir)
    if control in docs:
        return docs[control]
    for doc in docs.values():
        if doc["type"] == control:
            return doc
    return None


def get_examples(docs_dir, control: str) -> list[dict]:
    doc = resolve_doc(docs_dir, control)
    return doc["examples"] if doc else []


def find_example(docs_dir, control: str, name: str) -> Optional[dict]:
    """Match an example by exact or case-insensitive-prefix name."""
    examples = get_examples(docs_dir, control)
    for ex in examples:
        if ex["name"] == name:
            return ex
    low = name.lower()
    for ex in examples:
        if ex["name"].lower().startswith(low):
            return ex
    return None


def example_as_obj(example: dict) -> Optional[dict]:
    """Parse an example's JSON snippet into a dict (None if it doesn't parse)."""
    try:
        obj = json.loads(example["json"])
        return obj if isinstance(obj, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None
