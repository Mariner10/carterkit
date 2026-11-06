---
kind: profiles
title: Editor profiles
profiles:
  - name: all
    title: Everything
    since: next
    categories: [card, text, colour, look, motion, feedback, confirm, data, layout, content, behaviour]
    json: true
  - name: simple
    title: Simple
    since: next
    extends: all
    json: false
  - name: first-look
    title: First look
    since: next
    categories: [text, colour, card]
    petals: 2
    rows: false
  - name: binding-only
    title: Wiring
    since: next
    categories: [data]
    chips: []
    binding: [emits, receives]
---

# Editor profiles

An editor profile is a filter over a control's editable fields. It says which part of the control editor to draw
right now: the bar's chips, each chip's petals and tray rows, and the Binding view's cards all come from the
control's doc, and a profile cuts that doc down before any view reads it. A tutorial step sets one so the editor
shows only what the step teaches; the Simple setting uses `simple`. The design is
`docs/superpowers/specs/2026-11-06-editor-profiles.md`.

A profile only hides. It never adds a field, never changes a value and never edits a layout: everything it hides
keeps its value and still renders on the phone; only the editor stops offering it.

## The keys

Every key is optional except a named profile's `name`, `title` and `since`.

| Key | What it does |
|---|---|
| `name` | The id a tutorial step or a `carter://edit?…&profile=` link names. Links take named profiles only. |
| `title` | What the editor calls it. |
| `extends` | Start from this named profile's fields. Without it a profile starts from nothing and shows exactly what it names. |
| `categories` | Show every field of these settings categories (shared-fields.md `categories:`; never `internal`). |
| `chips` | Show every field homed on these chips: the shared `look`, `colour`, `text`, `card`, and `control` for the control's own chip. |
| `fields` | Show these fields: `<control>.<field>` (`gauge.min`, only on a gauge) or a field's bare name (`label`, on every control that has one). |
| `hide` | Remove these field ids, after everything above. |
| `petals` | At most this many petals on a chip (0 to 5; 0 means tap only). |
| `rows` | `false` hides every chip's tray rows (petals and taps stay). |
| `binding` | The Binding view cards it shows: `emits`, `receives`, `ask`, `feel`, `wiring`. Omitted with a visible `data` field: every card. |
| `add` | The control types the new-control picker offers. Omitted: every control. |
| `canvas` | The canvas verbs it allows: `place`, `move`, `resize`, `delete`, `pages`. Omitted: every verb. |
| `json` | Edit JSON and Show the wiring. Off unless the profile says `json: true`. |

Internal fields (shared-fields.md `internal:` and the `internal` category) never show, whatever a profile names.

## The named profiles

- **Everything** (`all`): every category, Edit JSON included. Today's editor, and the default.
- **Simple** (`simple`): everything but Edit JSON and the fields a doc marks `simple: hide`. The Simple setting.
- **First look** (`first-look`): the Text, Colour and Background fields, two petals a chip, no tray rows. For
  tutorials that style a control.
- **Wiring** (`binding-only`): the data fields and the Binding view's send and receive cards, no chips. For
  tutorials that connect a control.

A tutorial that needs something else writes its profile inline in the step. Once three tutorials write the same
inline profile, it becomes a named one here.

## Checks

`ControlDocProfileTests` and carterkit's `catalog.profile_lint` read this file: every id a profile names must be a
taxonomy category, a chip, a field of that control (or a field name some control has), a Binding card, a canvas
verb or a control type, and every named profile shows at least one field on every control it can reach.
`scripts/gen-capabilities.py` refuses to write `capabilities.json` while a profile is wrong, and lists the
category, chip and profile ids there for the tutorial lint.
