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
    resolved_frontmatter(content)    -> dict | None   the shape controldocs.schema.json checks
    parse_flow(text)                 -> list | dict | None   `[..]` / `{..}` (JSON or YAML flow)
    introduced(doc, field, value)    -> str   nearest `since` pin, else the doc's baseline
    parse_io(facts)                  -> dict   a doc's `io:` facts (emits / receives / sample)

Version pins (aif-xd1w8.1, control-def.md "Version pins"): docs, fields and enum values
carry `since` / `changes` / `deprecated` / `removed` / `alias`; a doc's `baseline` (absent
= DEFAULT_BASELINE) covers everything unpinned. A field's pinned values land in
`valueMeta` ({value: pins}); `values` stays the plain list.

io: facts (app bead aif-8whty.20; CAR-TER spec 2026-11-06-controls-explain-themselves.md):
a doc's top-level `io:` list says what the control sends (`emits:`), what it can show or
follow (`receives:`) and the editor's placeholder preview (`sample:`). parse_doc puts them
under "io" (only when the doc has the key); payloads keep their JSON types. Mirrors
ControlDocIO.swift.
"""

from __future__ import annotations

import json
import re
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


# ─── Flow values and version pins (app bead aif-xd1w8.1) ──────────────────────
#
# A `[..]` / `{..}` value is flow: JSON, or YAML flow with bare or quoted scalars
# (`[filled, { value: pill, since: next }]`). Every scalar comes back a string, as
# in the rest of the dialect. Mirrors ControlDocLoader.parseFlow.

DEFAULT_BASELINE = "2.0"
PIN_KEYS = ("since", "changes", "deprecated", "removed", "alias")
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "/": "/"}


def parse_flow(text: str):
    """A flow list/map as nested lists/dicts of strings, or None when malformed."""
    s, n = text, len(text)

    def ws(i):
        while i < n and s[i] in " \t":
            i += 1
        return i

    def scalar(i, stops):
        if i < n and s[i] in "\"'":
            q, i, out = s[i], i + 1, []
            while i < n and s[i] != q:
                if q == '"' and s[i] == "\\" and i + 1 < n:
                    e = s[i + 1]
                    if e == "u" and i + 6 <= n:
                        try:
                            out.append(chr(int(s[i + 2:i + 6], 16)))
                            i += 6
                            continue
                        except ValueError:
                            pass
                    out.append(_ESCAPES.get(e, "\\" + e))
                    i += 2
                    continue
                out.append(s[i])
                i += 1
            return ("".join(out), i + 1) if i < n else (None, i)
        j = i
        while j < n and s[j] not in stops:
            j += 1
        return s[i:j].strip(), j

    def value(i, stops):
        i = ws(i)
        if i < n and s[i] in "[{":
            return container(i)
        return scalar(i, stops)

    def container(i):
        close = "]" if s[i] == "[" else "}"
        out = [] if close == "]" else {}
        i = ws(i + 1)
        while i < n and s[i] != close:
            if close == "]":
                item, i = value(i, ",]")
                if item is None:
                    return None, i
                if item != "":
                    out.append(item)
            else:
                key, i = scalar(ws(i), ":,}")
                i = ws(i)
                if key is None or i >= n or s[i] != ":":
                    return None, i
                item, i = value(i + 1, ",}")
                if item is None:
                    return None, i
                out[key] = item
            i = ws(i)
            if i < n and s[i] == ",":
                i = ws(i + 1)
            elif i < n and s[i] != close:
                return None, i
        return (out, i + 1) if i < n else (None, i)

    i = ws(0)
    if i >= n or s[i] not in "[{":
        return None
    result, i = container(i)
    return result if result is not None and ws(i) == n else None


def _decode(value: str):
    """A raw frontmatter value as the resolved form: flow decoded, else the string
    with its double quotes trimmed (what both line parsers keep)."""
    v = value.strip().strip('"')
    if v[:1] in ("[", "{"):
        parsed = parse_flow(v)
        if parsed is not None:
            return parsed
    return v


def _version(v) -> Optional[str]:
    return v.strip().strip("\"'") or None if isinstance(v, str) else None


def _pins(get) -> dict:
    """The version pins `get(key)` yields (raw strings or decoded values), present ones only."""
    out: dict = {}
    for key in ("since", "deprecated", "removed"):
        v = _version(get(key))
        if v:
            out[key] = v
    raw = get("changes")
    changes = _decode(raw) if isinstance(raw, str) else raw
    if isinstance(changes, list):
        items = [{"in": _version(c.get("in")), "note": str(c.get("note", "")).strip()}
                 for c in changes if isinstance(c, dict)]
        items = [c for c in items if c["in"] and c["note"]]
        if items:
            out["changes"] = items
    alias = get("alias")
    if isinstance(alias, str) and alias.strip().strip("\"'"):
        out["alias"] = alias.strip().strip("\"'")
    return out


def _values(raw: str) -> tuple[list[str], dict[str, dict]]:
    """An enum's `values:` as (value list, {value: pins}); items are strings or
    `{value, since, changes, deprecated, removed, alias}` objects."""
    items = parse_flow(raw.strip())
    if not isinstance(items, list):
        return _parse_str_array(raw), {}
    values, meta = [], {}
    for item in items:
        if isinstance(item, str):
            values.append(item)
        elif isinstance(item, dict) and isinstance(item.get("value"), str):
            values.append(item["value"])
            pins = _pins(item.get)
            if pins:
                meta[item["value"]] = pins
    return values, meta


def introduced(doc: dict, field: Optional[dict] = None, value: Optional[str] = None) -> str:
    """The version that brought `doc` (or its `field`, or that field's enum `value`):
    the nearest `since` pin, else the doc's baseline."""
    pinned = [doc.get("since")]
    if field is not None:
        pinned.insert(0, field.get("since"))
        if value is not None:
            pinned.insert(0, (field.get("valueMeta") or {}).get(value, {}).get("since"))
    return next((p for p in pinned if p), doc.get("baseline") or DEFAULT_BASELINE)


def _make_field(raw: dict[str, str]) -> dict:
    field: dict = {"name": raw.get("name", ""), "type": raw.get("type", "string")}
    if "values" in raw:
        field["values"], value_meta = _values(raw["values"])
        if value_meta:
            field["valueMeta"] = value_meta
    field.update(_pins(raw.get))
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
    # The settings taxonomy (aif-8whty.19): a doc names a field's category only where the shared
    # lists are wrong for it, and `chip:` opens the control's own chip on the editor bar.
    for key in ("category", "chip"):
        if raw.get(key):
            field[key] = raw[key]
    return field


# ─── Shared fields: `- use: <name>` (app bead aif-fa4jj) ──────────────────────
#
# A field many docs share is written once in controldocs/shared-fields.md; a doc's
# `fields:` / `themeFields:` entry says `- use: <name>` (same section) plus optional
# overrides, and is expanded here exactly as the app's ControlDocLoader.FieldReader does.

SHARED_DOC = "shared-fields.md"
USE_OVERRIDES = ("default", "min", "max", "step", "does", "since", "summary",
                 "changes", "deprecated", "removed", "alias")
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
    block: Optional[str] = None  # a key written with no value: `- item` lines below are its list

    def flush():
        nonlocal current, use, overrides, block
        block = None
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
        elif trimmed.startswith("- ") and block is not None:
            # A block list (`values:` then `- filled` / `- { value: pill, since: next }`)
            # becomes the same flow text as `values: [filled, { value: pill, since: next }]`.
            item = trimmed[2:].strip()
            target = current if use is None else dict(overrides)
            prev = target.get(block, "")
            joined = f"{prev[:-1]}, {item}]" if prev.startswith("[") else f"[{item}]"
            if use is None:
                current[block] = joined
            else:
                overrides = [(k, v) for k, v in overrides if k != block] + [(block, joined)]
        elif ":" in trimmed:
            k, _, v = trimmed.partition(":")
            k, v = k.strip(), v.strip().strip('"')
            block = k if not v else None
            if use is not None:
                overrides.append((k, v))
            else:
                current[k] = v
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


def _top_level(front: list[str]) -> dict[str, str]:
    """Unindented `key: value` lines as raw strings (first one wins)."""
    out: dict[str, str] = {}
    for line in front:
        if line.strip() and not line.startswith((" ", "\t")) and ":" in line:
            key, _, value = line.partition(":")
            out.setdefault(key.strip(), value.strip())
    return out


def _block(lines: list[str], value=None):
    """The indented lines under a valueless top-level key: a list of `- item` (a flow
    value, a scalar, or a `k: v` map continued on the lines below), else a `k: v` map.
    `value` reads each value (default: `_decode`)."""
    read = value or _decode
    items: list = []
    mapping: dict = {}
    for line in lines:
        t = line.strip()
        if t.startswith("- ") or t == "-":
            t = t[2:].strip()
            if ":" in t and t[:1] not in "[{\"'":
                k, _, v = t.partition(":")
                items.append({k.strip(): read(v)})
            else:
                items.append(read(t))
        elif ":" in t:
            k, _, v = t.partition(":")
            target = items[-1] if items and isinstance(items[-1], dict) else mapping
            target[k.strip()] = read(v)
    return items if items else mapping


def _color_slots(front: list[str]) -> list[dict]:
    """The `colorSlots:` key (app aif-5g98i.1, theming.md "Colour roles"): a block list of
    `- slot:` maps or one flow line, as `[{slot, default, alias?, ...}]`. A `default` that is
    a list makes a series slot. Entries without a slot or a default are skipped. Mirrors
    ControlDocLoader.parseColorSlots."""
    collecting = False
    under: list[str] = []
    raw = None
    for line in front:
        if not line.startswith((" ", "\t")) and ":" in line:
            if collecting:
                break
            k, _, v = line.partition(":")
            if k.strip() != "colorSlots":
                continue
            collecting = True
            if v.strip():
                raw = _decode(v)
                break
        elif collecting and line.strip():
            under.append(line)
    if not collecting:
        return []
    if raw is None:
        raw = _block(under)
    out = []
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, dict) or not _version(item.get("slot")):
            continue
        default = item.get("default")
        if isinstance(default, list):
            default = [d.strip().strip("\"'") for d in default if isinstance(d, str) and d.strip()]
        elif isinstance(default, str):
            default = default.strip().strip("\"'")
        if not default:
            continue
        out.append({**item, "slot": _version(item["slot"]), "default": default})
    return out


def resolved_frontmatter(content: str, shared: Optional[dict] = None) -> Optional[dict]:
    """A doc's frontmatter in the resolved form controldocs.schema.json describes:
    every top-level key, `fields` / `themeFields` as their `use:`-expanded entries,
    `[..]` / `{..}` values flow-decoded, scalars as strings. Mirrors
    ControlDocLoader.resolvedFrontmatter. None when there is no frontmatter."""
    fm = _frontmatter(content)
    if fm is None:
        return None
    front = fm[0]
    is_shared = any(line.strip() == "kind: shared-fields" for line in front)
    entries, _ = _read_fields(front, {} if is_shared else (_bundled_shared() if shared is None else shared))
    out: dict = {}
    key: Optional[str] = None
    under: list[str] = []

    def close():
        if key is not None and key not in out and key not in _FIELD_SECTIONS:
            out[key] = _block(under) if under else ""

    for line in front:
        if not line.strip():
            continue
        if not line.startswith((" ", "\t")) and ":" in line:
            close()
            k, _, v = line.partition(":")
            key, under = k.strip(), []
            if key in _FIELD_SECTIONS:
                out[key] = [{n: _decode(x) for n, x in raw.items()} for s, raw in entries if s == key]
            elif v.strip() and key not in out:
                out[key] = _decode(v)
        elif key is not None:
            under.append(line)
    close()
    return out


# ─── io: facts (app bead aif-8whty.20) ───────────────────────────────────────

IO_WHEN = ("change", "release", "tap", "hold", "submit", "pick", "detect", "lift", "drop", "settle", "land")
IO_TYPES = ("bool", "number", "string", "color", "date", "id", "json")
IO_SOURCES = ("hub", "mqtt", "http", "sensor", "store", "derive", "default")
IO_ROLES = ("show", "follow")
_IO_KINDS = ("emits", "receives", "sample")


def _io_facts(front: list[str]) -> Optional[list[dict]]:
    """The `- k: v` maps under a top-level `io:` with each value as written (stripped, not
    decoded), so payloads keep their JSON types. None when the doc has no `io:` key."""
    lines: Optional[list[str]] = None
    inside = False
    for line in front:
        if not line.strip():
            continue
        if not line.startswith((" ", "\t")) and ":" in line:
            inside = line.partition(":")[0].strip() == "io"
            if inside and lines is None:
                lines = []
        elif inside and lines is not None:
            lines.append(line)
    if lines is None:
        return None
    block = _block(lines, value=str.strip)
    return [f for f in block if isinstance(f, dict)] if isinstance(block, list) else []


def _io_text(raw) -> Optional[str]:
    if not isinstance(raw, str):
        return None
    v = _decode(raw)
    return v.strip() or None if isinstance(v, str) else None


def _io_payload(raw):
    """A payload with its JSON types when it is strict JSON (`42`, `"#RRGGBB"`, `{"value": 3}`),
    else the dialect's reading (every scalar a string). None when empty."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        return json.loads(raw.strip())
    except ValueError:
        return _decode(raw)


def parse_io(facts: list[dict]) -> dict:
    """`io:` facts (raw `{key: text}` maps) as {"emits": [..], "receives": [..], "samples": [..],
    "sendsNothing", "showsNothing", "problems"}. An emits fact gets `field` (default `action`),
    a receives fact `role` (default `follow` when the doc emits its `value`, else `show`); pins
    as on fields. Unusable facts are skipped and named in `problems`. Mirrors ControlDoc.IO."""
    out: dict = {"emits": [], "receives": [], "samples": [], "sendsNothing": False,
                 "showsNothing": False, "problems": []}
    problems = out["problems"]
    receives = []
    for n, fact in enumerate(facts, 1):
        kinds = [k for k in _IO_KINDS if k in fact]
        if len(kinds) != 1:
            problems.append(f"io fact {n}: needs exactly one of emits / receives / sample, has {kinds}")
        elif kinds[0] == "emits":
            _io_emit(fact, n, out)
        elif kinds[0] == "receives":
            receives.append((n, fact))
        elif (value := _io_payload(fact["sample"])) is None:
            problems.append(f"io fact {n}: sample has no payload")
        else:
            sample = {"sample": value}
            for key in ("next", "for", "into"):
                v = _io_payload(fact.get(key)) if key == "next" else _io_text(fact.get(key))
                if v is not None:
                    sample[key] = v
            out["samples"].append(sample)
    emits_value = any(e["emits"] == "value" for e in out["emits"])
    for n, fact in receives:
        _io_receive(fact, n, out, emits_value)
    return out


def _io_optional(fact: dict, entry: dict, text_keys=(), payload_keys=()) -> None:
    for key in text_keys:
        if (v := _io_text(fact.get(key))) is not None:
            entry[key] = v
    for key in payload_keys:
        if (v := _io_payload(fact.get(key))) is not None:
            entry[key] = v
    entry.update(_pins(fact.get))


def _io_emit(fact: dict, n: int, out: dict) -> None:
    problems = out["problems"]
    eid = _io_text(fact["emits"])
    if not eid:
        problems.append(f"io fact {n}: emits has no id")
        return
    if eid == "none":
        out["sendsNothing"] = True
        return
    when, vtype, says = _io_text(fact.get("when")), _io_text(fact.get("type")), _io_text(fact.get("says"))
    if when not in IO_WHEN or vtype not in IO_TYPES or not says:
        problems.append(f"io emits {eid}: needs when (one of {', '.join(IO_WHEN)}), "
                        f"type (one of {', '.join(IO_TYPES)}) and says")
        return
    tokens = _decode(fact.get("tokens", ""))
    when_by = _decode(fact.get("whenBy", ""))
    entry = {"emits": eid, "when": when, "type": vtype, "says": says, "field": _io_text(fact.get("field")) or "action",
             "tokens": {k: v for k, v in tokens.items() if isinstance(v, str)} if isinstance(tokens, dict) else {},
             "whenBy": {}}
    for field, rule in (when_by.items() if isinstance(when_by, dict) else []):
        for value, target in (rule.items() if isinstance(rule, dict) else []):
            if target in IO_WHEN:
                entry["whenBy"].setdefault(field, {})[value] = target
            else:
                problems.append(f"io emits {eid}: whenBy {field}.{value} is not a when")
    _io_optional(fact, entry, ("title", "fallback", "also"), ("example", "hub"))
    out["emits"].append(entry)


def _io_receive(fact: dict, n: int, out: dict, emits_value: bool) -> None:
    problems = out["problems"]
    rid = _io_text(fact["receives"])
    if not rid:
        problems.append(f"io fact {n}: receives has no id")
        return
    if rid == "none":
        out["showsNothing"] = True
        return
    vtype, says, reacts = _io_text(fact.get("type")), _io_text(fact.get("says")), _io_text(fact.get("reacts"))
    role = _io_text(fact.get("role")) or ("follow" if emits_value else "show")
    if vtype not in IO_TYPES or vtype == "id" or not says or not reacts or role not in IO_ROLES:
        problems.append(f"io receives {rid}: needs type (not id), says, reacts and a role of show/follow")
        return
    raw_from = _decode(fact.get("from", ""))
    sources = [s for s in raw_from if s in IO_SOURCES] if isinstance(raw_from, list) else []
    if not sources or len(sources) != len(raw_from):
        problems.append(f"io receives {rid}: from needs a flow list of {', '.join(IO_SOURCES)}")
    entry = {"receives": rid, "role": role, "type": vtype, "from": sources, "says": says, "reacts": reacts}
    _io_optional(fact, entry, (), ("example", "shape"))
    out["receives"].append(entry)


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


# ─── The settings taxonomy (app bead aif-8whty.19) ───────────────────────────
#
# shared-fields.md's `chips:`, `categories:`, `internal:` and `canvas:`: every field of every control resolves to
# one category, every category has one home in the control editor (a shared chip, the control's own chip, the
# Binding view, the canvas, or none). Mirrors ControlDocLoader.taxonomy (SettingsTaxonomy.swift) and
# scripts/settings-taxonomy.py's `classify`.

TAXONOMY_CHIP_KEYS = ("tap", "petals", "categories")
TAXONOMY_CATEGORY_KEYS = ("fields", "theme", "groups", "suffixes", "prefixes", "types")


def _strings(value) -> list[str]:
    return [str(v).strip() for v in value] if isinstance(value, list) else []


def parse_taxonomy(content: str) -> dict:
    """The taxonomy sections of a shared-fields.md text: {chips, categories, internal, canvas}. Chips come sorted
    by `order` (an int), `always` is a bool, the name lists are lists of strings, and each entry keeps its version
    pins. Empty lists when the sections are absent."""
    fm = resolved_frontmatter(content, {}) or {}
    chips = []
    for raw in fm.get("chips") or []:
        if not isinstance(raw, dict) or not str(raw.get("name", "")).strip():
            continue
        chip = {"name": raw["name"], "title": raw.get("title", ""), "icon": raw.get("icon", ""),
                "order": int(raw["order"]) if str(raw.get("order", "")).isdigit() else 99,
                "always": raw.get("always") == "true",
                "petalTitles": raw["petalTitles"] if isinstance(raw.get("petalTitles"), dict) else {}}
        chip.update({k: _strings(raw.get(k)) for k in TAXONOMY_CHIP_KEYS})
        chip.update(_pins(raw.get))
        chips.append(chip)
    categories = []
    for raw in fm.get("categories") or []:
        if not isinstance(raw, dict) or not str(raw.get("name", "")).strip():
            continue
        cat = {"name": raw["name"], "title": raw.get("title", "")}
        if raw.get("home"):
            cat["home"] = raw["home"]
        cat.update({k: _strings(raw.get(k)) for k in TAXONOMY_CATEGORY_KEYS})
        cat.update(_pins(raw.get))
        categories.append(cat)
    return {"chips": sorted(chips, key=lambda c: c["order"]), "categories": categories,
            "internal": _strings(fm.get("internal")), "canvas": _strings(fm.get("canvas"))}


def load_taxonomy(docs_dir) -> dict:
    """The taxonomy of `docs_dir`/shared-fields.md (empty lists when it is absent)."""
    path = Path(docs_dir) / SHARED_DOC
    return parse_taxonomy(path.read_text() if path.is_file() else "")


def _matches(pattern: str, name: str) -> bool:
    """`*Config` matches a name ending so, `show*` one starting so, anything else the name itself."""
    if pattern.startswith("*"):
        return len(name) >= len(pattern) and name.endswith(pattern[1:])
    if pattern.endswith("*"):
        return len(name) >= len(pattern) and name.startswith(pattern[:-1])
    return pattern == name


def taxonomy_home(taxonomy: dict, category: str) -> str:
    """A category's home: the shared chip that lists it, else its `home:` (control, binding, none)."""
    for chip in taxonomy["chips"]:
        if category in chip["categories"]:
            return chip["name"]
    for cat in taxonomy["categories"]:
        if cat["name"] == category:
            return cat.get("home", "none")
    return "none"


def field_category(taxonomy: dict, raw: dict, theme: bool = False, containers=frozenset()) -> str:
    """The category of one raw field entry (`theme`: a themeFields entry; `containers`: the objects the doc's
    grouped fields nest under), by the rules in shared-fields.md "The editor's chips and categories"."""
    name, typ = raw.get("name", ""), raw.get("type", "string")
    cats = taxonomy["categories"]
    if raw.get("category"):
        return raw["category"]
    if theme:
        return next((c["name"] for c in cats if name in c["theme"]), "colour" if typ == "color" else "look")
    if raw.get("effect") == "deprecated" or raw.get("deprecated") or raw.get("removed"):
        return "internal"
    if raw.get("group"):
        hit = next((c["name"] for c in cats if raw["group"] in c["groups"]), None)
        if hit:
            return hit
    if typ == "object" and name in containers and not raw.get("edit"):
        return "internal"
    hit = next((c["name"] for c in cats if name in c["fields"]), None)
    if hit:
        return hit
    for c in cats:
        if typ in c["types"] or any(name.endswith(x) for x in c["suffixes"]) or any(name.startswith(x) for x in c["prefixes"]):
            return c["name"]
    if typ == "bool":
        return "behaviour"
    if typ == "number":
        return "look" if raw.get("tab") == "style" or raw.get("edit") in ("scrub", "look") else "behaviour"
    if typ == "enum":
        return "look" if raw.get("edit") == "look" or raw.get("tab") == "style" else "behaviour"
    return "content"


def is_internal(taxonomy: dict, raw: dict, theme: bool = False) -> bool:
    """On the `internal:` list: no editor home, on purpose (a plain name a top-level key, a `*` pattern any)."""
    if theme:
        return False
    name = raw.get("name", "")
    return any(_matches(p, name) if "*" in p else (not raw.get("group") and p == name) for p in taxonomy["internal"])


# ─── Editor profiles (app bead aif-qs8b0.11.1) ───────────────────────────────
#
# controldocs/profiles.md: named editor profiles, each a filter over a control's fields by taxonomy category,
# chip or field id, so a tutorial step's editor shows only what it teaches (CAR-TER
# docs/superpowers/specs/2026-11-06-editor-profiles.md). Read by the same line parser as shared-fields.md; mirrors
# ControlDocLoader.profiles (EditorProfile.swift). carterkit renders profiles; it never authors them.

PROFILES_DOC = "profiles.md"
BASE_PROFILE = "all"
SIMPLE_PROFILE = "simple"
CONTROL_CHIP = "control"
PROFILE_LISTS = ("categories", "chips", "fields", "hide", "binding", "add", "canvas")
PROFILE_FLAGS = ("rows", "json")
PROFILE_KEYS = ("name", "title", "extends", "petals", *PROFILE_LISTS, *PROFILE_FLAGS, *PIN_KEYS)
PROFILE_BINDING = ("emits", "receives", "ask", "feel", "wiring")
PROFILE_CANVAS = ("place", "move", "resize", "delete", "pages")
PROFILE_MAX_PETALS = 5
_PROFILE_NAME = re.compile(r"^[a-z][a-z0-9-]*$")


def parse_profile(raw: dict) -> dict:
    """One profile (a profiles.md entry, or a tutorial step's inline mapping) in its parsed shape: `name`, `title`,
    `extends` when written, each list key it writes as a list of strings, `petals` an int, `rows` / `json` bools,
    its version pins, and `unknownKeys` when it writes a key no profile has. A value of the wrong kind is kept as
    written, for `profile_errors` to report."""
    p: dict = {"name": str(raw.get("name") or "").strip(), "title": str(raw.get("title") or "").strip()}
    if str(raw.get("extends") or "").strip():
        p["extends"] = str(raw["extends"]).strip()
    for key in PROFILE_LISTS:
        if key in raw:
            v = raw[key]
            p[key] = _strings(v) if isinstance(v, list) else [s for s in [str(v).strip()] if s]
    if "petals" in raw:
        v = raw["petals"]
        if isinstance(v, int) and not isinstance(v, bool):
            p["petals"] = v
        else:
            p["petals"] = int(str(v).strip()) if str(v).strip().isdigit() else v
    for key in PROFILE_FLAGS:
        if key in raw:
            v = raw[key]
            p[key] = v if isinstance(v, bool) else {"true": True, "false": False}.get(str(v).strip(), v)
    p.update(_pins(raw.get))
    unknown = sorted(k for k in raw if k not in PROFILE_KEYS)
    if unknown:
        p["unknownKeys"] = unknown
    return p


def parse_profiles(content: str) -> list[dict]:
    """The named profiles of a profiles.md text, in file order (empty when it has none)."""
    fm = resolved_frontmatter(content, {}) or {}
    return [parse_profile(raw) for raw in fm.get("profiles") or [] if isinstance(raw, dict)]


def load_profiles(docs_dir) -> list[dict]:
    """The named profiles of `docs_dir`/profiles.md (empty when it is absent)."""
    path = Path(docs_dir) / PROFILES_DOC
    return parse_profiles(path.read_text()) if path.is_file() else []


def profile_manifest(taxonomy: dict, profiles: list[dict]) -> dict:
    """The ids capabilities.json lists for profiles: every category, every chip (the shared ones in bar order, then
    `control`), and each named profile's name, title and since."""
    return {"categories": [c["name"] for c in taxonomy["categories"]],
            "chips": [c["name"] for c in taxonomy["chips"]] + [CONTROL_CHIP],
            "profiles": [{"name": p["name"], "title": p["title"], "since": p.get("since") or DEFAULT_BASELINE}
                         for p in profiles]}


def _profile_entries(taxonomy: dict, doc: dict, common: Optional[dict]) -> list[dict]:
    """Every field a profile can show on the resolved control doc `doc`, then the `common` (control-def) fields it
    does not have, in doc order: {path, name, group, theme, category, chip, internal, simpleHidden}. `path` is the
    capability path (`min`, `chartConfig.columns`, `theme.accentColor`); `chip` is the field's home on the bar: a
    shared chip, `control` (the doc's `chip:` field and the control-homed categories), or None (the Binding view,
    the canvas, the internal list)."""
    chips = {c["name"] for c in taxonomy["chips"]}
    out: list[dict] = []
    seen: set[str] = set()
    for d in (doc, common or {}):
        plain = [f for f in d.get("fields") or [] if isinstance(f, dict)]
        containers = frozenset(str(f["group"]).split(".")[0] for f in plain if f.get("group"))
        for section, theme in (("fields", False), ("themeFields", True)):
            for raw in d.get(section) or []:
                if not isinstance(raw, dict) or not str(raw.get("name") or "").strip():
                    continue
                name, group = str(raw["name"]).strip(), str(raw.get("group") or "").strip()
                path = ("theme." if theme else "") + (f"{group}." if group else "") + name
                if path in seen:
                    continue
                seen.add(path)
                category = field_category(taxonomy, raw, theme=theme, containers=containers)
                internal = category == "internal" or is_internal(taxonomy, raw, theme=theme)
                canvas = not theme and not group and name in taxonomy["canvas"]
                home = taxonomy_home(taxonomy, category)
                chip = (CONTROL_CHIP if raw.get("chip") else None) if canvas or internal else (
                    CONTROL_CHIP if raw.get("chip") or home == "control" else home if home in chips else None)
                out.append({"path": path, "name": name, "group": group or None, "theme": theme,
                            "category": category, "chip": chip, "internal": internal,
                            "simpleHidden": str(raw.get("simple") or "").strip().lower() == "hide"})
    return out



def _names_field(field_id: str, typ: str, entry: dict) -> bool:
    """A profile's field id names this entry: `<type>.<path>` on that control only, a bare name on every control."""
    if "." in field_id:
        head, _, rest = field_id.partition(".")
        return head == typ and rest == entry["path"]
    return field_id == entry["name"] and (entry["theme"] or not entry["group"])


def profile_fields(profile: dict, profiles: list[dict], taxonomy: dict, doc: dict,
                   common: Optional[dict] = None) -> list[str]:
    """The field paths `profile` shows on the resolved control doc `doc` (plus the `common` control-def fields), in
    doc order: the spec's rules 1 to 3. Start from the `extends` profile's set (named in `profiles`), else nothing;
    add the fields of `categories`, the fields homed on `chips` and the `fields` ids; remove `hide`, then every
    internal field. `simple` also hides every field its doc marks `simple: hide`. An unknown id names nothing."""
    named = {p["name"]: p for p in profiles if p.get("name")}
    typ = str(doc.get("type") or "").strip()
    entries = _profile_entries(taxonomy, doc, common)

    def visible(p: dict, chain: tuple) -> set[str]:
        shown: set[str] = set()
        parent = named.get(p.get("extends") or "")
        if parent is not None and parent["name"] not in chain:
            shown = visible(parent, chain + (parent["name"],))
        cats, chips = set(p.get("categories") or []), set(p.get("chips") or [])
        ids, hide = p.get("fields") or [], p.get("hide") or []
        for e in entries:
            if e["category"] in cats or (e["chip"] and e["chip"] in chips) or any(_names_field(i, typ, e) for i in ids):
                shown.add(e["path"])
        for e in entries:
            if e["internal"] or any(_names_field(i, typ, e) for i in hide) or (
                    p.get("name") == SIMPLE_PROFILE and e["simpleHidden"]):
                shown.discard(e["path"])
        return shown

    shown = visible(profile, (profile.get("name") or "",))
    return [e["path"] for e in entries if e["path"] in shown]


def profile_errors(profiles: list[dict], taxonomy: dict, docs: dict, common: Optional[dict] = None) -> list[str]:
    """Problems with the named `profiles` (parse_profiles) against the taxonomy and the resolved control docs
    `docs` ({type: resolved frontmatter}, the controls a profile can name): a bad or repeated name, no `all`, an
    unknown key, an `extends` that names no profile (or loops), a category, chip, field id, Binding card, canvas
    verb or control type no list holds, `internal` named, `petals` outside 0-5, `rows` / `json` not a bool.
    Empty = clean."""
    errors: list[str] = []
    categories = {c["name"] for c in taxonomy["categories"]}
    chips = {c["name"] for c in taxonomy["chips"]} | {CONTROL_CHIP}
    paths = {typ: {e["path"] for e in _profile_entries(taxonomy, d, common)} for typ, d in docs.items()}
    bare = {e["name"] for d in [*docs.values(), common or {}] for e in _profile_entries(taxonomy, d, None)
            if e["theme"] or not e["group"]}
    named = {p["name"]: p for p in profiles if p.get("name")}
    seen: set[str] = set()
    if profiles and BASE_PROFILE not in named:
        errors.append(f"profiles: no `{BASE_PROFILE}` profile (the one an unknown name falls back to)")
    for i, p in enumerate(profiles):
        name = p.get("name") or ""
        where = f"profiles.{name}" if name else f"profiles[{i}]"
        if not _PROFILE_NAME.match(name):
            errors.append(f"{where}: a profile needs a lowercase `name` (a-z, 0-9, -)")
        elif name in seen:
            errors.append(f"{where}: the name is used twice")
        seen.add(name)
        if not p.get("title"):
            errors.append(f"{where}: no `title`")
        for key in p.get("unknownKeys") or []:
            errors.append(f"{where}: unknown key `{key}` (a profile has {', '.join(PROFILE_KEYS)})")
        ext, chain = p.get("extends"), [name]
        while ext:
            if ext not in named:
                errors.append(f"{where}: extends `{ext}`, which is not a named profile")
                break
            if ext in chain:
                errors.append(f"{where}: extends loops ({' -> '.join(chain + [ext])})")
                break
            chain.append(ext)
            ext = named[ext].get("extends")
        for c in p.get("categories") or []:
            if c == "internal":
                errors.append(f"{where}: categories names `internal`; a profile never shows internal fields")
            elif c not in categories:
                errors.append(f"{where}: unknown category `{c}` (shared-fields.md categories:)")
        for c in p.get("chips") or []:
            if c not in chips:
                errors.append(f"{where}: unknown chip `{c}` (shared-fields.md chips:, or `{CONTROL_CHIP}`)")
        for key in ("fields", "hide"):
            for fid in p.get(key) or []:
                if "." in fid:
                    typ, _, rest = fid.partition(".")
                    if typ not in paths:
                        errors.append(f"{where}: {key} `{fid}` names no control `{typ}`")
                    elif rest not in paths[typ]:
                        errors.append(f"{where}: {key} `{fid}` is not a field of {typ}")
                elif fid not in bare:
                    errors.append(f"{where}: {key} `{fid}` is no control's field (write <control>.<field>)")
        for key, allowed in (("binding", PROFILE_BINDING), ("canvas", PROFILE_CANVAS), ("add", tuple(sorted(docs)))):
            for v in p.get(key) or []:
                if v not in allowed:
                    errors.append(f"{where}: unknown {key} `{v}`" + (
                        "" if key == "add" else f" ({', '.join(allowed)})"))
        if "petals" in p and not (isinstance(p["petals"], int) and not isinstance(p["petals"], bool)
                                  and 0 <= p["petals"] <= PROFILE_MAX_PETALS):
            errors.append(f"{where}: petals is {p['petals']}; a chip has 0 to {PROFILE_MAX_PETALS}")
        for key in PROFILE_FLAGS:
            if key in p and not isinstance(p[key], bool):
                errors.append(f"{where}: {key} is {p[key]}; write true or false")
    return errors


def profile_lint(docs_dir) -> list[str]:
    """`profile_errors` for `docs_dir`/profiles.md against its shared-fields.md taxonomy and its placeable control
    docs (control-def.md the common fields). Empty when the docs have no profiles.md."""
    docs_dir = Path(docs_dir)
    profiles = load_profiles(docs_dir)
    if not profiles and not (docs_dir / PROFILES_DOC).is_file():
        return []
    taxonomy = load_taxonomy(docs_dir)
    shared = load_shared(docs_dir)
    docs: dict = {}
    common = None
    for f in sorted(docs_dir.glob("*.md")):
        resolved = resolved_frontmatter(f.read_text(encoding="utf-8"), shared)
        if not isinstance(resolved, dict) or "kind" in resolved:
            continue
        typ = str(resolved.get("type") or "").strip()
        if typ == "control-def":
            common = resolved
        elif typ and str(resolved.get("category") or "").strip() in PLACEABLE_CATEGORIES:
            docs.setdefault(typ, resolved)
    if not profiles:
        return [f"{PROFILES_DOC}: no profiles"]
    return profile_errors(profiles, taxonomy, docs, common)


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
    # Version pins (aif-xd1w8.1): `baseline:` (absent = 2.0, the release pins start
    # from), and the doc's own since/changes/deprecated/removed/alias.
    top = _top_level(front)
    meta["baseline"] = _version(top.get("baseline")) or DEFAULT_BASELINE
    meta.update(_pins(top.get))
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
    facts = _io_facts(front)
    if facts is not None:
        meta["io"] = parse_io(facts)
    slots = _color_slots(front)
    if slots:
        meta["colorSlots"] = slots
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
    if doc.get("colorSlots"):
        out["colorSlots"] = doc["colorSlots"]
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
