---
type: document-contract
label: Document Contract
icon: doc.badge.gearshape
category: models
fields:
  - name: schemaVersion
    min: 1
    max: 2
    type: number
    description: Grammar version of the document (optional; absent = 1). Bumped only when an older app would misread the file
  - name: version
    min: 1
    max: 9999
    type: number
    description: The author's revision label (the Layout Hub's "Revision"); never gates anything
  - name: format
    type: string
    description: Always the string carter; written on export only, never required
  - name: extensions
    type: object
    description: Reverse-DNS keyed tool data, top level and per control/group; preserved, never interpreted, 64 KB cap
  - name: provenance
    type: object
    description: Where this document came from (immediate parents, package)
  - name: requires
    type: object
    description: What the document needs from the app; features are name@N strings
---

The rules every `.carter` layout document obeys — the one place the app, carterkit,
the MCP and the on-device designer read them from. [[layout-config]] describes the
fields that draw a layout; this page describes the envelope around them: which
grammar a file speaks, where tools may keep their own data, what is reserved, how
things are identified, the size limits, and where binary content may live.

## Versions

Two different numbers, never confused:

| Field | Meaning | Who sets it |
|-------|---------|-------------|
| `schemaVersion` | The **grammar** the file is written in. Optional; absent means `1`. | The writer (app, kit, MCP) — never a person |
| `version` | The author's **revision label** ("Revision" in the Layout Hub). Any positive integer. | The author |

`version` never gates anything: an app must never refuse, migrate or downgrade a
file because of it (people bump it freely, and real files already hold any number).

**Bump policy.** `schemaVersion` goes up only when an older app would **misread**
the document — read it and show something different from what the author wrote.
Additive fields never bump it: an older app ignores a field it doesn't know, and
the file still says what it says. Today there are two grammars:

| `schemaVersion` | Grammar |
|-----------------|---------|
| `1` (or absent) | The inline form: every control carries its own position, span, theme and sync |
| `2` | The sectioned form (see [Sectioned document](#sectioned-document)) |

An app that meets a `schemaVersion` above the newest one it knows opens the file
**read-only** (it renders what it can and never writes the file back), so an
older phone can't flatten a newer author's work.

`format: "carter"` marks an exported file. Writers emit it on export only; no
reader requires it. The document type (UTI) `net.carterbeaudoin.carter-layout`
is **frozen** — it will not change with a domain switch.

## Extensions

`extensions` is where a tool keeps data the app doesn't understand. It may appear
at the top level of the layout and on any control or group:

```json
{
  "name": "Greenhouse",
  "version": 3,
  "extensions": {
    "editor": { "canvasZoom": 1.5 },
    "com.example.plantdb": { "catalogRef": "ficus-lyrata" }
  },
  "tabs": [{ "title": "Plants", "icon": "leaf", "children": [
    { "type": "gauge", "id": "c_7f3a9e", "name": "Soil moisture", "position": [0, 0],
      "extensions": { "com.example.plantdb": { "sensorModel": "SM-2" } } }
  ]}]
}
```

- **Keys are reverse-DNS** names of the tool that owns them (`com.example.tool`).
  A tool reads and writes only its own key.
- **Preserved, never interpreted.** The app carries every `extensions` block
  through load, edit, save, share and export untouched, and never changes
  behavior because of one. Nothing in it may be required to render the layout.
- **64 KB cap** per `extensions` block, measured as compact UTF-8 JSON. A strict
  load (wire push, import, room join, model output) refuses a larger block; a
  disk load drops it and lists the repair in the Layout Hub. carterkit's
  validator reports it as an error.
- `extensions.editor` is reserved for the app's own editor state (the one key that
  is not reverse-DNS); it is left out of the document digest (see
  [Provenance](#provenance-and-reserved-keys)).

A key the app doesn't model and that is **not** inside `extensions` is a
*core-key guess*: the app still tolerates it, but carterkit and the MCP warn
(`unknown_field`) and suggest moving it into `extensions` — a future version of
the grammar may give that name a meaning.

## Provenance and reserved keys

`provenance` (top level, optional) records where the document came from — its
**immediate** parents only, never the whole family tree:

```json
"provenance": {
  "parents": [
    { "id": "5C1E…", "relation": "copy", "digest": "sha256:…",
      "source": { "kind": "template", "ref": "plant-care", "version": "3" } }
  ],
  "package": { "id": "com.example.plants", "version": "1.2.0", "params": { "zones": 4 } }
}
```

`relation` is one of `copy`, `package`, `remix`, `import`; `source.kind` is one of
`template`, `package`, `file`. More than one parent is allowed (a remix).

**Digest.** A document's digest is SHA-256 over the RFC 8785 (JCS) canonical JSON
of the credential-stripped document, **minus** `provenance`, `attestations` and
`extensions.editor`, written `sha256:<hex>`. The app and
carterkit share golden fixtures for it.

**Reserved top-level keys** — do not author them; a later grammar defines them:
`revision`, `attestations`. No metrics or usage counters ever go in a document.

## Identity

Ids are the stable keys for stored values, `sync` targeting, visibility
references, glance tiles, sections and edits. Display text is never identity.

- **Layout `id` = the installation.** A layout's top-level `id` names this
  installed copy and its data. Copy, Make It Mine and copy-to-edit **re-mint** it
  (and record the original in `provenance`). Importing a file whose `id` is already
  installed asks **Update** (keep the data) or **Install a copy** (new id, new
  data). Joining a shared room keeps the room's `id`.
- **Control and group ids** are unique among all of the layout's controls and
  groups. Ids the app creates are opaque: `c_` + 6 lowercase hex for controls
  (`c_7f3a9e`), `g_` for groups and pages, `t_` for tabs. Hand-written and
  carterkit slugs (`"pump-speed"`) stay valid forever and are never rewritten.
  Nothing parses an id or shows it to people.
- **`name`** (controls and groups) is the readable label the editor shows —
  `name`, else `label`, else the type. Names may repeat; renaming never moves data.
- **`label`** is display text on the control. Changing it changes nothing else.
- **Renaming an id** goes through the editor's `renameId` operation, which
  rewrites every reference (visibility, glance, sections) in the same edit.
  Never rename an id by hand-editing one place.
- **Tabs** may carry an optional `id`; without one the tab's `title` is its id,
  so give a tab an `id` before renaming it.
- **Every new kind of entity** added to the grammar gets an `id` from day one.
- Duplicate or empty ids are repaired on disk loads (a later duplicate becomes
  `id~2`, an empty one `type-N`) and refused by strict loads and carterkit.

## Units

A control that shows a measurement carries **one** `unit` field, and it is a real
measurement unit (Foundation unit names: `celsius`, `fahrenheit`, `kph`, `mph`,
`percent`, `kilowattHours`, …), not display text. The app converts and formats the
value for the reader's locale — the author writes `"unit": "celsius"` once and an
American sees °F. A `unit` string the app doesn't recognize is shown literally, so
`"unit": "pots"` still reads "12 pots". There is no separate display-unit field.
Controls adopt `unit` one at a time (the stat tile first); until a control's own
doc lists it, the field is ignored there.

## Requirements

`requires` says what a document needs from the app. Features are `name@N`
strings — a capability name plus an optional version, e.g.
`"requires": { "features": ["local.store@2", "sensors"] }` (`sensors` = `sensors@1`).
An app missing a requirement shows one update banner and still renders what it
can. `requires` is the author's soft gate; `schemaVersion` is the grammar marker
and decides whether the app may write the file.

## Sectioned document

`schemaVersion: 2` lets a document keep a control's facets **out of line**, in
top-level sections keyed by control or group id, instead of on the control:

| Section | Holds, per id |
|---------|---------------|
| `placements` | `position`, `span` (the default presentation), plus optional `landscape` and `regular` variants — each `{position, span}` or `{hidden: true}`. `default: {position, span}` is accepted as an alias of the flat keys (the flat keys win) |
| `styles` | `theme`, `tint`, `icon`, `hideLabel`, `hideValue`, `hideBackground`, `animation` |
| `connectivity` | `sync`, `action`, `longPressAction` |

```json
{
  "schemaVersion": 2,
  "name": "Greenhouse", "version": 4,
  "tabs": [{ "id": "t_a01b2c", "title": "Plants", "icon": "leaf",
             "children": [{ "type": "gauge", "id": "c_7f3a9e", "name": "Soil moisture" }] }],
  "placements": { "c_7f3a9e": { "position": [0, 0], "span": [2, 2],
                                "landscape": { "position": [0, 2], "span": [2, 1] } } },
  "styles": { "c_7f3a9e": { "tint": "#34C759" } },
  "connectivity": { "c_7f3a9e": { "sync": [{ "method": "meshsocket", "event": "broadcast", "filter": { "msg_type": "soil" }, "valuePath": "moisture" }] } }
}
```

- Top-level `appearance` is the app-shell block ([[appearance]]), not a section.
- **One model.** The app folds the sections onto the children before it decodes,
  so the renderer, the editor and LayoutOps never know which form a file used.
  The same layout inline or sectioned decodes to an identical model.
- **Precedence:** a section entry overrides the same facet written inline.
- **Ids** are the identity namespace: a tab's `children` and, recursively, group
  `children` (container panels and long-press groups are not addressable). If two
  children share an id, the entry applies to the first.
- An id in a section that matches no control or group, or an entry that isn't an
  object, is a lint error; every load repairs it by dropping the entry.
- **Lossless:** a key inside an entry that isn't one of that section's facets
  stays in the section untouched (it is never copied onto the control).
- `landscape` renders when the page has compact height (an iPhone on its side),
  `regular` on an iPad-width page; the default `position`/`span` renders
  everywhere else. The same two keys are also accepted inline on a child. Rules
  (reflow, obstacles, `hidden`) are in [[grid-dimensions#Landscape and iPad]].
- The inline form stays valid forever — carterkit, the MCP and hand-written
  layouts keep writing it. The on-device editor keeps a sectioned file sectioned
  when it saves it, and (behind a flag, off for now) will write every save in the
  sectioned form, so an app that only knows `schemaVersion` 1 opens those files
  read-only.

## Limits

The single table every layer reads. The app's sanitizer and renderer and
carterkit's validator take these numbers from here (the app's unit tests and
carterkit's loader both parse this table), so a layout the kit accepts is a
layout the device renders. A strict load (wire, import, join, model output)
refuses a document past a limit; a disk load clamps or trims it and lists the
repair in the Layout Hub.

| Limit | Value | Applies to |
|-------|-------|------------|
| `maxTabs` | 24 | Tabs per layout |
| `maxControls` | 2000 | Controls per layout (groups not counted) |
| `maxNestingDepth` | 8 | Groups/containers enclosing a control (a tab's own children are 0). Deeper content is refused, or trimmed with a "Nested too deeply" placeholder |
| `maxStringBytes` | 4096 | Any string value |
| `maxDataImageBytes` | 524288 | A `data:image/…` URL in a `url` / `baseURL` field |
| `maxExtensionsBytes` | 65536 | One `extensions` block, compact UTF-8 JSON |
| `maxPosition` | 256 | Each `position` coordinate (0…256) |
| `maxSpan` | 64 | Each `span` value (1…64) |
| `maxGridColumns` | 64 | `grid.columns` |
| `maxGridRows` | 512 | `grid.rows` |
| `minTimerSeconds` | 0.25 | `interval`, `autoAdvance`, `webRefreshInterval` (`autoAdvance` / `webRefreshInterval` 0 = off) |
| `minSendRateSeconds` | 0.02 | Joystick `sendRate` (an event throttle) |
| `minPublisherIntervalSeconds` | 0.05 | Sensor `publishers[].interval` |
| `maxBufferPoints` | 5000 | `sparklinePoints`, `minLines`, `maxLines`, `historyCount` |
| `maxWireBytes` | 2097152 | A pushed, imported, joined or model-written document |
| `maxFileBytes` | 8388608 | A layout file loaded from disk |

## Assets

- **No blobs in documents.** The only inline binary a document may carry is a
  `data:image/…` URL in a `url` / `baseURL` field, up to `maxDataImageBytes`.
  Anything else base64-encoded (fonts, audio, other `data:` URLs, long base64
  strings) is refused as an oversized string and flagged by carterkit as
  `inline_blob`. Host the file and link it by `https://` URL.
- `backgroundImage.asset` names an image **bundled in the app**; it cannot point
  at a file of your own.
- The `asset://` URL scheme is **reserved** for a future package asset store.
  No runner resolves it today and strict loads refuse it — don't author it.

## Related

- [[layout-config]] — the top-level fields that draw a layout
- [[control-def]] — controls, including `name` and `extensions`
- [[group-def]] — groups
- [[appearance]] — the app-shell appearance block
