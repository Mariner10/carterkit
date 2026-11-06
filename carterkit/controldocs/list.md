---
type: list
depth: complete
label: List
icon: list.bullet
category: controls
defaultSpan: [3, 4]
addIntent: show
pickerCategory: Readouts
friendlyName: Table
oneLiner: Rows of information
aliases: [rows, table, items, entries, feed, menu]
starterPreset: {"label": "Table"}
lookFormats: [{"id": "plain","name": "Plain","symbol": "textformat","set": {"formatValue": null}},{"id": "lastTime","name": "Last time","symbol": "clock.arrow.circlepath","set": {"formatValue": "relative:day"}},{"id": "date","name": "Date","symbol": "calendar","set": {"formatValue": "date"}}]
io:
  - emits: row
    when: tap
    title: When you tap a row
    type: id
    says: the tapped row's id
    example: "row-1"
    also: Only rows with a text id can be tapped; with no action set, a list bound to a My Data collection opens that row's entry sheet instead
    since: next
  - receives: rows
    role: show
    type: json
    shape: [{"id": "text?", "name": "text or number"}]
    from: [hub, mqtt, http, store]
    says: a list of rows, each with the values for its columns and an optional id
    reacts: rows are replaced by the new list, and the columns come from the rows' own keys unless you set them
    example: [{"id": "row-1", "name": "Item 1"}]
    since: next
  - sample: [{"id": "row-1", "name": "Item 1", "detail": "Example 1"}, {"id": "row-2", "name": "Item 2", "detail": "Example 2"}, {"id": "row-3", "name": "Item 3", "detail": "Example 3"}]
    next: [{"id": "row-1", "name": "Item 1", "detail": "Example 1"}, {"id": "row-2", "name": "Item 2", "detail": "Example 2"}, {"id": "row-3", "name": "Item 3", "detail": "Example 3"}, {"id": "row-4", "name": "Item 4", "detail": "Example 4"}]
fields:
  - name: formatValue
    title: Date format
    simple: hide
    tab: data
    type: string
    description: "Default date format for columns with no `format` of their own: relative:day (4 days ago), relative, date, date:time. Applies to date text and epoch numbers; other text shows as is."
    summary: How dates in the rows are written
    does: "Dates in columns without their own format show as e.g. 4 days ago (relative:day) or a calendar date; other text is unchanged."
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label
    summary: The heading above the rows
    does: "Shows this text as the header line above the rows in the header text size."
  - name: listColumns
    title: Columns
    type: array
    description: "Column definitions: [{key, label, format}]. Absent or empty: a store-bound list shows its collection's first fields, any other list its rows' own keys."
    summary: Which columns to show and how to display them
    does: "Sets the columns across each row: their order, header text and number or date format; with none, up to 3 columns are picked from the data."
  - name: emptyText
    title: Empty message
    type: string
    description: "Line shown when the list has no rows. Default: \"No <label> yet\"."
    summary: What to show when there are no rows
    does: "Replaces the line shown when there are no rows, e.g. No books yet."
  - name: tint
    edit: color
    depth: surface
    title: Header color
    tab: style
    type: color
    default: "#FFFFFF"
    description: Header text color
    summary: The color of the heading
    does: "Paints the header label in this color."
  - name: hideLabel
    edit: part
    depth: hold
    title: Hide the title
    type: bool
    default: false
    description: Hide header label
    summary: Hide the heading line
    does: "Removes the header label so the rows start at the top of the card."
  - name: hideBackground
    edit: part
    depth: hold
    title: No background card
    tab: style
    type: bool
    default: false
    description: Remove glass card background
    summary: Remove the card behind the rows
    does: "Drops the frosted card fill so the rows sit directly on the screen background."
  - name: defaultValue
    title: Starting rows
    type: object[]
    description: Seed rows shown before the first sync (the same row objects a sync delivers)
    summary: Starting rows shown until new data arrives
    does: "Fills the list with these rows before the first sync, e.g. 3 sample rows, then new data replaces them."
  - use: confirm
    does: "After a tap writes locally, a pill naming the change appears for 3 seconds with an Undo button."
  - name: paging
    title: Load as you scroll
    tab: advanced
    simple: hide
    type: object
    description: "Rows fed by the hub a page at a time: {pageSize, request, replyType, replyPath, window, queryFrom}. Absent: the list shows the rows its sync delivers. See [[#Paging]]."
    summary: Load rows from the hub a page at a time as you scroll
    does: "Asks the hub for the first rows when the list appears and for more as you near the end, so a list of any length scrolls without the phone holding every row."
  - name: pageSize
    group: paging
    title: Rows per page
    tab: advanced
    simple: hide
    type: number
    min: 5
    max: 200
    step: 5
    default: 50
    description: "Rows asked for per request, sent as {{limit}} (5-200). A hub may send fewer."
    summary: How many rows each request asks for
    does: "Asks the hub for this many rows at a time, e.g. 50; the next request goes out when you are half a page from the last row."
  - name: request
    group: paging
    title: Page request
    tab: advanced
    simple: hide
    type: object
    description: "The action sent for each page (meshsocket; `method` may be left out), with {{cursor}}, {{offset}}, {{limit}}, {{query}} and {{req}} filled into its payload. See [[#Paging]]."
    summary: The message that asks the hub for rows
    does: "Sends this message for every page with the position, the page size and the search text filled in."
  - name: replyType
    group: paging
    title: Reply type
    tab: advanced
    simple: hide
    type: string
    description: "msg_type of the hub's page broadcasts. A page is {items (or rows), cursor?, total?, more?, offset?, query?, req?}; a frame of this type without items or rows is ignored."
    summary: Which hub messages carry the rows
    does: "Takes rows only from hub messages of this type and leaves every other message alone."
  - name: replyPath
    group: paging
    title: Page inside the reply
    tab: advanced
    simple: hide
    type: string
    description: "Dot path from the reply frame to the page object, e.g. result for {msg_type, req, result: {rows, total}}. Absent: the frame is the page."
    summary: Where the rows sit inside a reply
    does: "Reads the page from this part of each reply, e.g. result, instead of from the top of the message."
  - name: window
    group: paging
    title: Rows kept
    tab: advanced
    simple: hide
    type: number
    min: 20
    max: 5000
    step: 50
    default: 600
    description: "Most rows kept on the phone at once (at least 4 pages, at most 5000). Rows far from the screen are let go and asked for again when you scroll back."
    summary: How many rows the phone keeps at once
    does: "Keeps at most this many rows around the ones on screen, e.g. 600, and asks the hub again for rows you scroll back to."
  - name: queryFrom
    group: paging
    title: Search field
    tab: advanced
    simple: hide
    type: string
    description: "Id of a text input whose text is the search, sent as {{query}}. A change starts the list over after 250 ms without typing."
    summary: The field whose text filters the rows
    does: "Sends that field's text as the search with every request, and starts the list over from the top when the text changes."
  - name: itemTemplate
    chip: Rows
    edit: template
    depth: surface
    title: Row design
    tab: advanced
    simple: hide
    type: object
    description: "A group definition ({grid, children}) drawn once per row; {{item.<field>}} in its children's text, values, images and payloads is replaced from that row. Absent: rows are columns. See [[#Item templates]]."
    summary: Draw each row from controls instead of columns
    does: "Lays out each row as its own small grid of controls, e.g. a name, a version and a button, filled in from that row's data."
  - name: itemSpacing
    title: Row gap
    tab: style
    min: 0
    max: 64
    step: 1
    type: number
    default: 2
    description: "Points between rows (0-64, default 2), and between the cards of a card grid (itemLayout: grid)."
    summary: How far apart the rows sit
    does: "Opens up space between rows, so card-style rows stand apart from each other."
  - name: itemStyle
    title: Row look
    tab: style
    values: [plain, card]
    type: enum
    default: plain
    description: "plain: rows sit inside the list's card. card: each itemTemplate row draws its template group's own card (fill, corners, theme), so rows read as separate cards; pair it with hideBackground: true and an itemSpacing. See [[#Card rows]]."
    summary: Plain rows or a card per row
    does: "Gives every templated row a card of its own, styled by the template's theme, instead of lines inside one list card."
    valueHelp: {"plain": "rows sit inside the list's own card, as before", "card": "each templated row is its own card, styled by the template group"}
  - name: itemLayout
    edit: look
    depth: hold
    under: itemTemplate
    since: next
    title: Row layout
    tab: style
    values: [rows, grid]
    type: enum
    default: rows
    description: "rows: one templated row per line. grid: the itemTemplate rows as cards side by side, as many columns as keep each card 150 pt wide or more, at most 3 (2 on a phone-wide list, 3 on an iPad or in landscape, 1 on a list too narrow for two), itemSpacing apart; paging, search, row taps and itemStyle work as in rows. Needs an itemTemplate: column rows stay one per line. Any other value is rows. See [[#Card grid]]."
    summary: One row per line, or cards side by side
    does: "Lays the templated rows out as a grid of cards, 2 or 3 to a line by the list's width, scrolling and loading as the rows do."
    valueHelp: {"rows": "one templated row per line, as before", "grid": "templated rows as cards side by side, 2 or 3 columns by the list's width"}
themeFields:
  - name: cardPadding
    title: Card padding
    type: number
    min: 0
    max: 32
    step: 1
    default: 12
    description: Card item padding
    summary: The room inside each card item
    does: Pads the inside of every item when itemStyle is card, from 0 to 32 points.
  - name: cornerRadius
    title: Corner roundness
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
    summary: How round the card corners are
    does: "Rounds the card corners from 0 (square) to 30 points."
  - use: controlPadding
    summary: Space between the card edge and the rows
    does: "Adds 0 to 24 points of space inside the card around the rows."
  - use: surfacePrimary
    summary: The fill color of the card
    does: "Paints the card background in this color, usually a faint translucent tone."
  - use: foregroundColor
    summary: The color of the row text
    does: "Colors the text in the rows with this color."
  - use: borderColor
    does: "Draws the card outline in this color."
  - use: borderWidth
    does: "Sets the outline thickness from 0 (none) to 5 points."
---

# List

A tabular data display that renders rows of structured data with configurable columns. Rows are populated via sync and can be formatted per column.

## Type
`"list"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `label` | string | falls back to `id` | Header label |
| `listColumns` | array | — | Column definitions: `[{key, label, format}]`. Absent or empty: worked out from the data — see [[#Columns when none are given]] |
| `listColumns[].key` | string | required | Field to read from each row. A **dot path** reaches into nested rows — see [[#Column keys]] |
| `listColumns[].label` | string | required | Column header text |
| `listColumns[].format` | string | — | Number format for numeric cells, or a date format (`relative`, `relative:day`, `date`, `date:time`) for date strings / epoch numbers (same formats as [[label]]) |
| `action` | [[actions\|ActionDefinition]] | — | Fired on a row tap with `{{value}}` = the row's `id` — see [[#Row taps]] |
| `confirm` | bool | `false` | "Show confirmation": after each local write, a 3-second pill naming the change, with Undo. See [[actions#Confirmation and Undo]] |
| `tint` | color | `"#FFFFFF"` | Header text color |
| `hideLabel` | bool | `false` | Hide header label |
| `hideBackground` | bool | `false` | Remove glass card background |
| `defaultValue` | object[] | — | Seed rows shown before the first sync, the same row objects a sync delivers. See [[control-def#defaultValue per type]] |
| `paging` | object | — | Rows fed by the hub a page at a time as the list scrolls — see [[#Paging]] |
| `itemTemplate` | [[group-def\|GroupDefinition]] | — | Each row drawn from controls bound to `{{item.<field>}}` — see [[#Item templates]] |
| `itemSpacing` | number | `2` | Points between rows (0-64) |
| `itemStyle` | `"plain"` or `"card"` | `"plain"` | `card`: each templated row draws its template group's own card — see [[#Card rows]] |
| `itemLayout` | `"rows"` or `"grid"` | `"rows"` | `grid`: templated rows as cards side by side, 2-3 columns by the list's width — see [[#Card grid]] |

## Column keys

A `key` is looked up flat on the row first, so `"key": "name"` reads `row.name` and a
row whose field name genuinely contains a dot still works.

If there's no flat match and the key contains dots, it's walked as a **dot path**:

- `"properties.title"` → `row.properties.title`
- `"geometry.coordinates.0"` → an integer segment indexes an array

That's what makes a nested public feed usable without a server in between: rows from
a GeoJSON `features[]` keep their data under `properties`, and a path key reads it
directly. A key that resolves to nothing renders as `—`.

## Columns when none are given

A list with no `listColumns` (or an empty array) still shows its rows:

- **Bound to a [[local-store]]** (a `method: "local"` sync that neither groups nor
  aggregates): the collection's fields, as declared in the layout's `sources` (or by
  the running store, for a shared collection) — the field that names a row first, then
  the field it sorts by, then the rest in declared order (`order`, else by name). Labels
  are the fields' friendly names, numbers format as numbers, and raw-data (`json`)
  fields are left out. At most 3 columns.
- **Anything else** (a grouped store binding, a web or hub feed): the rows' own keys,
  plain values by name first. At most 3 columns.

An empty store shows the empty-state line (`emptyText`, else "No <label> yet", else
"No rows yet"), never a configuration error. Write `listColumns` to choose the columns,
their order, labels and formats yourself; the editor writes them when it binds a list to
a store.

## Row taps

With an `action`, each row whose data carries an `id` becomes tappable and fires the
action with `{{value}}` = that row's `id`. Rows from a [[local-store]] binding always
carry one, so a checklist ticks the tapped row with
`{"method": "local", "op": "update", "collection": "items", "id": "{{value}}", "set": {"done": true}}`
or removes it with `op: "delete"`. To edit a row elsewhere on the screen, select it:
`{"method": "local", "op": "select", "collection": "books", "id": "{{value}}"}` moves the
selection cursor, and every control bound with `"where": {"id": "{{selected}}"}` refills
with the tapped row. Rows without an `id` aren't tappable. Without an `action` the list
stays read-only.

## Paging

A list with `paging` asks its hub for rows a page at a time instead of holding the whole
set, so a catalogue of tens of thousands of rows scrolls and searches smoothly. Its `sync`
is not needed (rows come from the replies).

**Requests.** The list sends `paging.request` (a meshsocket action, normally a
`broadcast_request`) when it first appears, and again when the user is half a page from
the last loaded row. Its payload is filled in with:

| Token | Value |
|-------|-------|
| `{{offset}}` | Index of the first row asked for (0 for the first page) |
| `{{limit}}` | `pageSize` |
| `{{cursor}}` | The `cursor` the hub sent with the page that ended at `{{offset}}`; `null` for the first page and for hubs that page by offset |
| `{{query}}` | The search text (`""` for none) |
| `{{req}}` | A request id, unique per request |

An exact token keeps its type (`"offset": "{{offset}}"` sends a number). A request with no
reply after 8 seconds is sent again while the list is on screen.

**Replies.** The hub answers with a broadcast whose `msg_type` is `paging.replyType`. The
page is the frame itself, or the object `paging.replyPath` names in it:

```json
{ "msg_type": "catalogue_page", "req": "…", "items": [{ "id": "a1", "name": "…" }],
  "cursor": "…", "total": 48211, "more": true, "offset": 0, "query": "" }
```

- `items` (or `rows`): the rows, in order, from `offset`. Required; a frame of this type
  without them is not a page (an error reply, another method's reply) and is ignored.
- `req`: echo `{{req}}` (on the page or on the frame). With it, only the reply to a request
  still waiting is taken: a reply to an older search, or to another list sharing the
  `replyType`, is dropped. Without it, a page whose `query` differs from the current search
  is dropped, and the page goes to the oldest waiting request (or to `offset`, when echoed).
- `offset`: where the rows go; default, the requested `{{offset}}`.
- The end of the list is the first of: `more: false`; `total` reached; a `cursor` of `null`;
  none of these and fewer rows than `{{limit}}`. An empty page ends the list where it starts.
  `total` also tells VoiceOver how many rows there are.

**Search.** `paging.queryFrom` names a text input (a search field) in the layout. When its
text changes, the list waits 250 ms without typing, then drops its rows and asks for the
first page of the new search; the hub does the matching.

**Window.** The phone keeps at most `paging.window` rows (default 600) around the rows on
screen. Rows far away are let go but keep their place, so the scroll position holds; when
the user scrolls back to one, the list asks again for the page that held it (with that
page's `{{cursor}}` and `{{offset}}`). A loading row shows while a page is on its way, the
row count at the end, and `emptyText` when the search matches nothing. Row taps send the
row `id` as usual (see [[#Row taps]]).

The rows of a paged list live only on the phone for the layout on screen: switching tabs
keeps them; a new connection or a layout change starts over.

## Item templates

`itemTemplate` draws every row from controls instead of columns. It is a group definition
([[group-def]]): a `grid` (default 4 columns × 1 row, 56 pt rows) and `children` placed on
it; `id` and `position` may be left out. In the children's text, values, images, colors and
action payloads, `{{item.<field>}}` is replaced from the row (a dot path reaches nested
fields: `{{item.meta.author}}`), and an exact token keeps its type, so
`"defaultValue": "{{item.percent}}"` feeds a gauge a number.

- The row is the template's grid: one row of a 4-column grid is 56 pt tall. Set the grid's
  `rowHeight` to `"auto"` ([[grid-dimensions#rowHeight]]) and rows take their content's
  height instead, so a one-row card (icon, a label with a `subtitle`, a button) stays compact.
- Children read the row, not live values: each shows what its fields and `defaultValue`
  say for that row; inputs in a row don't keep what is typed. Buttons fire their actions,
  with the row's fields already in the payload and `{{value}}` left for the tap.
- A tap elsewhere on the row sends the row `id` through the list's `action`, as for column
  rows.
- Ids are scoped to the row (`<id>@<row id>`), so they need not be unique in the layout.
  A child that doesn't decode once filled in (a text field where a number belongs) is
  left out of that row.
- Text from the row is shown as written but never becomes a token itself (`{{` in a row's
  data can't pull in a secret).

Without `itemTemplate`, rows are columns (`listColumns`), paged or not.

## Card rows

With `"itemStyle": "card"` every templated row is a container of its own: the template group's
card (the theme's surface, corners and border, or the template's own `theme`), padded like any
group, instead of a line inside the list's card. Turn the list's own card off with
`"hideBackground": true` and set an `itemSpacing` so the cards stand apart. A template with
`"hideBackground": true` draws no card even here. Placeholder rows of a paged list take the
card's height too.

### Expanding a row

An `expand` block on the `itemTemplate` ([[group-def#Expand]]) lets each row grow, from where it
sits, into a full-screen (or sheet) container with a corner close. Its `{"ref": …}` entries name
the template's child ids and move that row's own controls to new cells; its other entries are
controls only the expanded row has. `{{item.<field>}}` is filled in from the row in all of them
and in `title`. The row's tap still sends its `id`; a row with an `expand` opens it on a tap no child claims (trigger `tap`, the default) or a hold.
The expanded row shows the row as it was when opened.

## Card grid

With `"itemLayout": "grid"` the templated rows sit side by side as cards instead of one per line,
in as many columns as keep every card at least 150 pt wide, at most 3: a list as wide as a phone
screen gets 2, a wider one (an iPad, a phone in landscape) 3, and a list too narrow for two cards
keeps one per line. The columns follow the list's width as it changes (rotation, Split View).

- Cards fill the grid left to right, then top to bottom, in row order; `itemSpacing` is the gap
  both across and down. Design the `itemTemplate` for a card (2 columns × 3 rows, say) rather
  than a full-width row.
- Each card is the template's own grid, as tall as its rows. With the template grid's
  `rowHeight: "auto"` a card takes its content's height: the cards of one line start level, and
  the line is as tall as its tallest card.
- Everything else is the list as it always is: `paging` asks for the same pages at the same
  points (a card's arrival on screen counts as its row's), keeps the same `window`, and searches
  the same way; the loading line, the row count and `emptyText` span the grid under the last
  cards. A tap sends the card's `id`, `itemStyle: "card"` draws each card's background, and an
  `expand` grows a card from where it sits.
- VoiceOver reads the cards line by line, left to right, each one element that speaks its
  controls, as a templated row does.

Without an `itemTemplate` the setting does nothing: column rows stay one per line. Any value other
than `"grid"` lays the rows out one per line.

## Examples

### Package cards that expand
Shows templated rows drawn as separate cards that each grow into a full-screen page. Intended effect: a scrolling column of package cards (icon, name, version, Install); tapping a card (anywhere but the Install button) or holding it grows that card to full screen with a bigger icon, the name beside it and the notes below.
```json
{
  "type": "list",
  "id": "packages",
  "position": [0, 0],
  "span": [6, 4],
  "hideBackground": true,
  "itemStyle": "card",
  "itemSpacing": 10,
  "itemTemplate": {
    "grid": { "columns": 4, "rows": 1 },
    "children": [
      { "type": "image", "id": "icon", "position": [0, 0], "systemName": "shippingbox" },
      { "type": "label", "id": "name", "position": [0, 1], "span": [1, 2], "text": "{{item.name}} {{item.version}}" },
      { "type": "button", "id": "install", "position": [0, 3], "label": "Install",
        "action": { "method": "meshsocket", "event": "install", "payload": { "id": "{{item.id}}" } } }
    ],
    "expand": {
      "title": "{{item.name}}",
      "grid": { "columns": 4, "rows": 5 },
      "children": [
        { "ref": "icon", "position": [0, 0], "span": [2, 2] },
        { "ref": "name", "position": [0, 2], "span": [1, 2] },
        { "ref": "install", "position": [1, 2], "span": [1, 2] },
        { "type": "label", "position": [2, 0], "span": [3, 4], "text": "{{item.notes}}" }
      ]
    }
  },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "packages" }, "valuePath": "items" }]
}
```

### Card grid catalogue
Shows `itemLayout: "grid"` on a paged, searchable list with card rows. Intended effect: a catalogue of any size scrolls as a grid of cards, 2 to a line on a phone and 3 on an iPad, each card an icon over a name and a detail line; the hub sends 40 cards at a time as you scroll, typing in the `gallery-search` text input searches on the hub, and tapping a card sends its id.
```json
{
  "type": "list",
  "id": "gallery",
  "position": [1, 0],
  "span": [7, 4],
  "hideBackground": true,
  "itemStyle": "card",
  "itemLayout": "grid",
  "itemSpacing": 10,
  "emptyText": "Nothing matches",
  "action": { "method": "meshsocket", "event": "broadcast_request", "payload": { "msg_type": "item_open", "id": "{{value}}" } },
  "paging": {
    "pageSize": 40,
    "replyType": "gallery_page",
    "queryFrom": "gallery-search",
    "request": { "method": "meshsocket", "event": "broadcast_request",
                 "payload": { "msg_type": "gallery_pages", "offset": "{{offset}}", "limit": "{{limit}}",
                              "query": "{{query}}", "req": "{{req}}" } }
  },
  "itemTemplate": {
    "grid": { "columns": 2, "rows": 3 },
    "children": [
      { "type": "image", "id": "icon", "position": [0, 0], "span": [2, 2], "systemName": "shippingbox" },
      { "type": "label", "id": "name", "position": [2, 0], "span": [1, 2], "label": "{{item.detail}}", "text": "{{item.name}}" }
    ]
  }
}
```

The hub answers `gallery_pages` exactly as for rows (see [[#Paging]]); the grid changes only how the cards are laid out.

### Device status list
Shows a list fed live from a hub, with a number column. Intended effect: three columns of device name, status and ping that refresh whenever the hub broadcasts.
```json
{
  "type": "list",
  "id": "device-list",
  "position": [0, 0],
  "span": [2, 4],
  "label": "Connected Devices",
  "listColumns": [
    { "key": "name", "label": "Name" },
    { "key": "status", "label": "Status" },
    { "key": "latency", "label": "Ping", "format": "number" }
  ],
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "device_list" }, "valuePath": "devices" }]
}
```

The server broadcasts `{"msg_type": "device_list", "devices": [{"name": "…", "status": "…", "latency": 12}, …]}`; `valuePath` picks the row array out of the frame.

### Nested feed rows (USGS GeoJSON, no server)
Shows dot-path column keys reading nested feed data. Intended effect: the last hour of earthquakes with magnitude, place and depth, refreshed every 5 minutes.
```json
{
  "type": "list",
  "id": "quake-list",
  "position": [2, 0],
  "span": [3, 4],
  "label": "Recent quakes",
  "listColumns": [
    { "key": "properties.mag", "label": "M", "format": "number" },
    { "key": "properties.place", "label": "Place" },
    { "key": "geometry.coordinates.2", "label": "Depth", "format": "number" }
  ],
  "sync": [{ "method": "http", "url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson", "interval": 300, "valuePath": "features" }]
}
```

`valuePath` picks the row array out of the document; each column key then reaches
into that row.
### Last-time look with starting rows
Shows the Last time look (`formatValue: "relative:day"`) together with seed rows, a custom empty message and a hidden title. Intended effect: rows appear at once with dates like "4 days ago", and show "Nothing watered yet" if the data is cleared.
```json
{
  "type": "list",
  "id": "watering-log",
  "position": [0, 4],
  "span": [2, 3],
  "label": "Watering",
  "hideLabel": true,
  "formatValue": "relative:day",
  "emptyText": "Nothing watered yet",
  "listColumns": [
    { "key": "plant", "label": "Plant" },
    { "key": "when", "label": "Last watered" }
  ],
  "defaultValue": [
    { "plant": "Fern", "when": "2026-10-30" },
    { "plant": "Basil", "when": "2026-11-02" }
  ]
}
```

The Plain look leaves `formatValue` unset, and the Date look sets it to `"date"` so the same column shows a calendar date; the JSON is otherwise identical. A per-column `format` always wins over `formatValue`.

### Tap a row to tick it (local store)
Shows a row tap bound to a local collection, with the confirmation pill. Intended effect: tapping a task marks it done, a pill with Undo appears for 3 seconds, and the row updates.
```json
{
  "type": "list",
  "id": "todo-list",
  "position": [2, 4],
  "span": [3, 4],
  "label": "To do",
  "confirm": true,
  "hideBackground": true,
  "action": { "method": "local", "op": "update", "collection": "items", "id": "{{value}}", "set": { "done": true } },
  "sync": [{ "method": "local", "collection": "items" }]
}
```

### Tap a row to select it
Shows the select binding that moves the selection cursor. Intended effect: tapping a book fills every control bound with `"where": {"id": "{{selected}}"}` with that book, so a form elsewhere can edit it.
```json
{
  "type": "list",
  "id": "book-list",
  "position": [0, 8],
  "span": [3, 4],
  "label": "Books",
  "action": { "method": "local", "op": "select", "collection": "books", "id": "{{value}}" },
  "sync": [{ "method": "local", "collection": "books" }]
}
```

### Paged catalogue with a row design
Shows `paging` with a search field and an `itemTemplate`. Intended effect: a catalogue of any size scrolls with rows of name, detail and version, the hub sends 50 rows at a time, typing in the `catalogue-search` text input searches on the hub, and tapping a row sends its id.
```json
{
  "type": "list",
  "id": "catalogue",
  "position": [1, 0],
  "span": [7, 4],
  "label": "Catalogue",
  "emptyText": "Nothing matches",
  "action": { "method": "meshsocket", "event": "broadcast_request", "payload": { "msg_type": "item_open", "id": "{{value}}" } },
  "paging": {
    "pageSize": 50,
    "replyType": "catalogue_page",
    "queryFrom": "catalogue-search",
    "request": { "method": "meshsocket", "event": "broadcast_request",
                 "payload": { "msg_type": "catalogue_pages", "offset": "{{offset}}", "limit": "{{limit}}",
                              "cursor": "{{cursor}}", "query": "{{query}}", "req": "{{req}}" } }
  },
  "itemTemplate": {
    "grid": { "columns": 4, "rows": 1 },
    "children": [
      { "type": "label", "id": "name", "position": [0, 0], "span": [1, 3], "label": "{{item.detail}}", "text": "{{item.name}}" },
      { "type": "label", "id": "version", "position": [0, 3], "label": "Version", "text": "{{item.version}}" }
    ]
  }
}
```

The hub answers `catalogue_pages` with `{"msg_type": "catalogue_page", "req": "<the req>", "items": [...], "total": 48211, "more": true}`. A hub that wraps its replies, like `{"msg_type": "daemon-reply", "req": "…", "result": {"rows": [...], "offset": 0, "more": true}}`, sets `"replyType": "daemon-reply"` and `"replyPath": "result"`.

The list has no look that switches it to another control type, and no long-press or detail view.

## Editor notes
Edit row (on the list's pose) edits `itemTemplate` as one row: its first row is the template, a group you move,
resize, add to and take controls out of, with the group's own chips (title, columns, rows, background, theme);
every row below follows at once, each filled from its own item. A stepper cycles sample items from the hub page
the list is on, else its synced or starting rows, else placeholders named after the template's fields. Each
control shows the `{{item.<field>}}` it reads above it. On a list drawn as columns the first edit creates a
template from its columns. Holding Edit row offers Row layout (`itemLayout`: rows or a card grid); the row pose
still draws the rows below the edited one a line each.
`hideBackground`, `hideLabel` and `tint` (header color) change only the card and header, so with `hideLabel` on, the Header color field changes nothing on screen.

## Related
- [[shared-properties]] — Base fields
- [[sync]] — Real-time data sync
