---
type: local-store
label: Local Store
icon: internaldrive
category: system
fields:
  - name: type
    type: enum
    values: [local]
    description: Must be "local" — declared inside the layout's sources block
  - name: namespace
    type: string
    description: Scope for every non-shared collection (default the layout id, else its name); must match ^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$ and cannot be "shared"
  - name: collections
    type: object
    description: Collection name → { fields, shared?, mirror? }; fields maps a name to one of string number integer bool date json
  - name: views
    type: object
    description: View name → { from, where?, orderBy?, limit? }; a named row set over a collection or another view
  - name: weekStartsOn
    type: enum
    values: [monday, sunday]
    default: monday
    description: First day of the week for the week bucket and the startOfWeek token
---

# Local Store

An on-device database a layout owns: **typed collections** of records that live in
the app, with no server, no broker and no network. Controls read them through the
standard [[sync]] block (`method: "local"`) and write them through the standard
[[actions]] block (`method: "local"`), so a [[label]], [[chart]] or [[list]]
bound to the store behaves exactly as it does over MeshSocket, MQTT or HTTP —
only the wire differs. Every query is plain JSON: there is no SQL, no code and no
expression language in a layout.

Typical uses: a reading log, a habit or expense tracker, a parts inventory, a
scoreboard — anything that is the user's own data and should survive a relaunch,
a layout edit and even the layout's deletion.

## Definition

A local store is one more entry in the layout's top-level [[sources]] block:

```json
{ "sources": {
  "db": {
    "type": "local",
    "namespace": "book-logger",
    "weekStartsOn": "monday",
    "collections": {
      "books": {
        "fields": { "title": "string", "pages": "integer", "rating": "number",
                    "started": "date", "finished": "date", "notes": "string",
                    "tags": "json", "lent": "bool" }
      }
    },
    "views": {
      "finishedThisYear": { "from": "books",
                            "where": { "finished": { "gte": "{{startOfYear}}" } },
                            "orderBy": "-finished" },
      "topShelf": { "from": "finishedThisYear", "where": { "rating": { "gte": 4 } }, "limit": 20 }
    }
  }
} }
```

| Key | Required | Meaning |
|---|---|---|
| `type` | yes | `"local"`. |
| `namespace` | no | Scope for every non-shared collection. Defaults to the layout `id`, else its `name`. An explicit value must match `^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$`; the literal `shared` is reserved. A layout with a second `local` source must give it an explicit `namespace`. |
| `weekStartsOn` | no | `"monday"` (default, ISO weeks) or `"sunday"`. Feeds the `week` bucket and the `{{startOfWeek}}` token. |
| `collections` | yes | Map of collection name → declaration. Names match `^[a-z][A-Za-z0-9_]{0,47}$`; at most 32 per source. |
| `collections.*.fields` | yes | Map of field name → type (closed set below). Names match `^[a-z][A-Za-z0-9_]{0,63}$`; `id`, `createdAt`, `updatedAt` and `_hlc` are reserved; at most 64 fields. |
| `collections.*.shared` | no | `true` puts the collection in the device-wide `shared` namespace so other layouts can bind the same rows. |
| `collections.*.mirror` | no | Reserved for the studio change-notice; stored, not read by the store. |
| `views` | no | Map of view name → `{from, where?, orderBy?, limit?}`. `from` is a collection or another view (nesting up to 8 deep, cycles rejected). View names share the collection namespace and may not collide with one. A view never has `groupBy`/`aggregate`: it is a row set, and the binding aggregates it. |

A sync or action with no `source` resolves to the single `local` source, exactly
as MQTT/HTTP bindings do; name the source when a layout declares several. A
source that fails validation (bad name, unknown type, a stage naming an undeclared
field) is reported to the connection console and shown as a `failed` pipe; the
rest of the layout still renders.

## Collections and field types

Every record carries three reserved, store-managed fields — `id` (a string,
1–128 chars of `[A-Za-z0-9_.:-]`, minted by the store unless the action supplies
one), `createdAt` and `updatedAt` (ISO-8601 UTC instants) — plus the declared
fields. Every declared field is nullable; a field missing from a write is `null`.

| Type | Accepted on write | Delivered as |
|---|---|---|
| `string` | JSON string | string |
| `number` | JSON number | number |
| `integer` | JSON number with no fractional part | number |
| `bool` | JSON `true` / `false` only | bool |
| `date` | ISO-8601 string, one of the two forms below | string, normalized |
| `json` | any JSON value; stored canonical (sorted keys, no whitespace) | the decoded value |

Writes **reject, never coerce**: a `number` given `"42"` fails, a `bool` given
`1` fails, an `integer` given `1.5` fails, and a write naming an undeclared or
reserved field fails as a whole (one transaction, all or nothing). The failure
is a connection-console line and a `failed` pipe, never an alert.

## Dates

A `date` field is stored as text in one of two normalized forms:

- **Instant** — `YYYY-MM-DDTHH:MM:SS.SSSZ`, always UTC with milliseconds. Any
  ISO-8601 instant with an offset is accepted and converted.
- **Calendar date** — `YYYY-MM-DD`, no zone. A "finished on" is a date, not an
  instant, and never shifts a day when the phone travels.

Both forms compare and sort correctly with `gt`/`gte`/`lt`/`lte` because they
share the `YYYY-MM-DD` prefix, so a calendar-date token such as
`{{startOfYear}}` filters an instant column with no conversion. The `{{today}}`
and `{{startOf…}}` tokens are calendar dates; `{{now}}` is an instant. "Since the
start of today" is `{"gte": "{{today}}"}` and includes everything written today.

## Views

A view is a named, reusable row set: `{ "from", "where"?, "orderBy"?, "limit"? }`.
`from` names a collection or another view, so views stack (`topShelf` over
`finishedThisYear` over `books`). A binding or a `select` action names a view
wherever it would name a collection; the binding's own stage (including
`aggregate`/`groupBy`) is applied on top of the view's rows. Insert, update,
upsert and delete target collections only, never views.

## Query stages

A binding's query is the object `{ where?, groupBy?, aggregate?, orderBy?, limit? }`
written directly on the [[sync]] entry beside `collection`. Each stage is JSON;
field names must be declared on the collection (or be `id`, `createdAt`,
`updatedAt`), and values are matched by type — a mismatch is simply "no match",
never a coercion.

### where

An object whose keys are field names mapping to an operator object, or the
combinators `and` / `or` holding an array of `where` objects. A bare value is
shorthand for `eq`; sibling keys are `and`-ed. Depth is capped at 8 and a
`where` may hold at most 32 leaves. `{}` matches every row.

| Operator | Form | Meaning |
|---|---|---|
| `eq` | `{"rating": 5}` or `{"rating": {"eq": 5}}` | equals; `null` never matches; a value of the wrong type matches nothing |
| `ne` | `{"rating": {"ne": 5}}` | not equal; a `null` row counts as "not 5" |
| `gt` `gte` `lt` `lte` | `{"rating": {"gte": 4}}` | ordered compare on numbers, strings and dates |
| `in` | `{"tag": {"in": ["a", "b"]}}` | any of at most 64 values; an empty list matches nothing |
| `contains` | `{"title": {"contains": "dun"}}` | case-sensitive substring; `string` fields only |
| `exists` | `{"notes": {"exists": true}}` | field is (or, with `false`, is not) `null`; the only operator allowed on a `json` field |
| `and` / `or` | `{"or": [{"lent": true}, {"rating": {"lt": 2}}]}` | combine nested `where` objects |

### aggregate

Collapses the matched rows to one value. Either the bare string
`"aggregate": "count"` or the object `"aggregate": {"op": "sum", "field": "pages"}`
(the object form is required whenever a `field` is needed).

| Op | Field | Result |
|---|---|---|
| `count` | none | number of matched rows |
| `sum` | `number`/`integer` | total; `0` for no rows |
| `avg` | `number`/`integer` | mean; `null` for no rows |
| `min` / `max` | `number`/`integer`/`date`/`string` | smallest / largest value |
| `distinct` | any non-`json` field | number of distinct values |
| `first` / `last` | any non-`json` field | that field of the first / last row under `orderBy` (default `createdAt`, then `id`) |

### groupBy

Buckets the matched rows and (with `aggregate`, default `count`) produces one
value per bucket. Three forms:

- `"groupBy": "genre"` — exact values of a field.
- `"groupBy": {"field": "finished", "bucket": "month"}` — a `date` field by
  `day`, `week`, `month` or `year`. Keys are `YYYY-MM-DD` (day and week, the week
  keyed by its first day per `weekStartsOn`), `YYYY-MM` or `YYYY`. Calendar dates
  bucket as written; instants bucket in the device's current zone. A `null` date
  lands in the `null` bucket, listed last.
- `"groupBy": {"field": "pages", "width": 100}` — a `number`/`integer` field into
  ranges; the key is the bucket's lower edge as a number.

`bucket` and `width` are exclusive. A grouped query returns at most 500 groups.

### orderBy and limit

`orderBy` is a string or array of strings: `"title"` ascending, `"-finished"`
descending. In a row query any declared field, `id`, `createdAt` or `updatedAt`
is orderable; in a grouped query only `key` and `value` (default `key`
ascending). Ordering is stable (`id` is always the final tiebreak) and `null`
sorts last. A row query with no `orderBy` orders by `id`.

`limit` is an integer from 1 to 1000. It applies to the rows of a row query and
to the buckets of a grouped query.

## Tokens

A string that is *exactly* one of these tokens is replaced before the query runs
or the write lands (`"{{today}}T"` is a literal). In a `where`, tokens become
bound values, never query text.

| Token | Value | Form |
|---|---|---|
| `{{now}}` | the current moment | instant, UTC |
| `{{today}}` | start of today in the device's zone | calendar date |
| `{{startOfWeek}}` `{{startOfMonth}}` `{{startOfYear}}` | start of the current period (week per `weekStartsOn`) | calendar date |
| `{{selected}}` | the collection's selection cursor (see `select` below), or `null` when nothing is selected | string id |

A `where` that compares against an empty `{{selected}}` matches nothing, so a
form bound to the selection goes blank on deselect. A time-zone or calendar-day
change re-evaluates every binding that used a token. In actions, `{{value}}` and
the control's other tokens ([[actions]]) are available beside these.

## Delivery shapes

The stage decides the payload a binding receives, and the store supplies a
default `valuePath` so the minimal form works with every existing receiver.

| Stage | Payload | Default `valuePath` | Typical receivers |
|---|---|---|---|
| `aggregate`, no `groupBy` | `{"value": 3}` (`null` for `avg` of nothing) | `value` | [[label]], [[gauge]], [[progress-ring]], any scalar control; a [[sparkline]] appends each new value |
| `groupBy` (+ `aggregate`, default `count`) | `{"categories": ["2026-01", "2026-02"], "series": [{"name": "count", "values": [4, 7]}], "rows": [{"key": "2026-01", "value": 4}]}` | whole payload | [[chart]] / [[pie-chart]] / [[heatmap]] read `categories` + `series`; a [[list]] uses `valuePath: "rows"`; a sparkline uses `series.0.values` |
| rows (no `aggregate`) | `{"rows": [{"id": "…", "createdAt": "…", "updatedAt": "…", "title": "Dune", "pages": 412}], "count": 1, "total": 3, "first": {…} or null}` | `rows` | [[list]] (`listColumns[].key` reads a field), [[log-console]], or a form control naming `first.title` |

Rows are flat: the declared fields sit beside `id`, `createdAt` and `updatedAt`.
`count` is the rows delivered, `total` the rows in the collection or view. A
`valuePath` that starts with a declared field is shorthand for `first.<field>`,
so `{"where": {"id": "{{selected}}"}, "valuePath": "title"}` fills a [[text-input]]
with the selected row's title.

A declared field wins over the payload keys: if a collection declares a field
named `count`, `total`, `rows` or `first`, the bare `valuePath` (`"count"`) reads
that field off the first row, not the payload's value. The payload keys are always
reachable by a `$` spelling that no field can take: `$rows`, `$count`, `$total`
and `$first` (`"$count"` is the row count, `"$first.title"` the first row's
title). Without a colliding field, `"count"` and `"$count"` mean the same thing.
The lint and the app console warn about a field that shadows a payload key.

When nothing matches, `first` is `null` and the
control keeps its last value. `filter` applies to the payload object as on every
other transport but is rarely useful here.

## Ops

An action with `method: "local"` names an `op`, a `collection` and, per op, an
`id` and/or a `set` object of declared field → value. Tokens are substituted into
`set` and `id` first, then values are validated exactly like a delivery (reject,
never coerce). `set` may not name `id`, `createdAt` or `updatedAt`. A bound
control refreshes as soon as the write commits.

| `op` | Requires | Effect |
|---|---|---|
| `insert` | `set` | New row with a store-minted id (or the given `id`; a duplicate is an error). |
| `update` | `id`, `set` | Merge `set` into the row; a missing row is an error. |
| `upsert` | `id`, `set` | Replace the whole row (fields absent from `set` become `null`), or insert it. |
| `delete` | `id` | Remove the row; a missing row is a no-op with a console note. Deleting the selected row clears the cursor. |
| `select` | `id` (or `null`) | Move the collection's selection cursor; no table write. Every binding that used `{{selected}}` for that collection re-delivers. |

Delete is by `id` only: a layout cannot wipe a collection with a `where`. Errors
surface as a connection-console line and a `failed` pipe (with the reason as its
detail) until the next successful op; there is never an alert. The studio mirror
sees only `{op, collection}` of a local action, never the values written.

## What survives

Records belong to the user, not the layout. Deleting or replacing a layout —
including every studio re-push — never drops a table; a re-imported layout with the
same `namespace` re-attaches to its rows. Changing a field's type is refused (the
source shows a `failed` pipe) rather than silently converting data. Adding a field
adds a nullable column; removing one from the declaration leaves the column in
place, hidden. The selection cursor persists across relaunch. Records, the cursor
and query results are never part of the layout document, so a `.carter` export,
a studio read or an invite bundle carries the schema only.

## What the header shows

A local source is a **Data Pipe** (`Local`, keyed by namespace) beside any MQTT or
HTTP pipes: grey with `no bindings` when nothing reads it, amber `loading` while
the first results arrive, green with `<n> records · <m> bindings` while serving,
red with the sanitized reason after a schema, stage or write error. A layout with
only a local source has no socket, so the header dot takes the pipe's colour.

## Limits

| Limit | Value |
|---|---|
| Collections per source | 32 |
| Fields per collection | 64 |
| Rows per collection | 50 000 (an insert past the cap fails) |
| Groups per grouped query | 500 |
| `limit` | 1 … 1000 |
| `where` | depth 8, 32 leaves, 64 members per `in` |
| View nesting | 8 deep |
| `id` | 1–128 chars of `[A-Za-z0-9_.:-]` |

Not a stage: no computed fields, no joins across collections, no expressions,
no `having`, no projections (rows always deliver every declared field). Anything
beyond this is a bridge's job.

## Examples

### A reading log source

```json
{
  "sources": {
    "db": {
      "type": "local",
      "namespace": "book-logger",
      "collections": {
        "books": {
          "fields": { "title": "string", "pages": "integer", "rating": "number",
                      "finished": "date", "tags": "json", "lent": "bool" }
        }
      }
    }
  }
}
```

### A shared collection with a view

```json
{
  "sources": {
    "home": {
      "type": "local",
      "weekStartsOn": "sunday",
      "collections": {
        "chores": { "fields": { "name": "string", "done": "date", "who": "string" }, "shared": true }
      },
      "views": {
        "thisWeek": { "from": "chores", "where": { "done": { "gte": "{{startOfWeek}}" } }, "orderBy": "-done" }
      }
    }
  }
}
```

## Binding examples

Reading, on a control's `sync` entry:

```json
[
  { "method": "local", "collection": "books", "aggregate": "count" },
  { "method": "local", "collection": "books", "aggregate": { "op": "sum", "field": "pages" },
    "where": { "finished": { "gte": "{{startOfYear}}" } } },
  { "method": "local", "collection": "books", "groupBy": { "field": "finished", "bucket": "month" } },
  { "method": "local", "collection": "books", "orderBy": "-createdAt", "limit": 50 },
  { "method": "local", "collection": "books", "where": { "id": "{{selected}}" }, "valuePath": "first.title" }
]
```

Writing, on a control's `action`:

```json
[
  { "method": "local", "op": "insert", "collection": "books",
    "set": { "title": "{{value}}", "pages": 0, "finished": "{{today}}" } },
  { "method": "local", "op": "update", "collection": "books", "id": "{{selected}}",
    "set": { "rating": "{{value}}" } },
  { "method": "local", "op": "delete", "collection": "books", "id": "{{selected}}" },
  { "method": "local", "op": "select", "collection": "books", "id": "b-42" }
]
```

## Related

- [[sync]] — the inbound binding; `collection` and the stage fields
- [[actions]] — the outbound op; `op`, `collection`, `id`, `set`
- [[sources]] — where the store is declared beside MQTT and HTTP
- [[list]] — the natural receiver for rows
- [[chart]] — the natural receiver for grouped results
