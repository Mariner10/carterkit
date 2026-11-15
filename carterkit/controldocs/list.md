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
starterPreset: {"label": "Table", "listColumns": [{"key": "name", "label": "Name"}, {"key": "detail", "label": "Detail"}]}
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
    edit: rows
    columns: [{"name": "key", "title": "Data key", "type": "string", "edit": "inline", "required": true, "default": "field{n}"}, {"name": "label", "title": "Header", "type": "string", "edit": "inline", "required": true, "default": "Column {n}"}, {"name": "format", "title": "Format", "type": "string", "edit": "inline"}, {"name": "align", "title": "Align", "type": "string", "edit": "inline"}]
    description: "Column definitions: [{key, label, format, align}] (align: leading, trailing or numeric). Absent or empty: a store-bound list shows its collection's first fields, any other list its rows' own keys."
    summary: Which columns to show and how to display them
    does: "Sets the columns across each row: their order, header text and number or date format; with none, up to 3 columns are picked from the data."
  - name: emptyText
    edit: inline
    depth: surface
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
    edit: paging
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
    edit: key
    depth: hold
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
  - name: search
    edit: pick-control
    tab: advanced
    simple: hide
    type: string
    values: [builtin, none]
    default: none
    description: "Where the rows' search text comes from: builtin (the list draws its own small box above the rows), none (no box, no filtering), or the id of a text input with role: search. One box can drive several lists. Static and store rows are filtered on the phone (case and diacritic blind, 150 ms after typing stops); paged rows send the text as {{query}} and the hub matches. Absent: paging.queryFrom if set, else none. See [[#Search]]."
    summary: The search box this list follows
    does: "Filters the rows as you type in the named search box, or draws its own box when set to builtin."
    since: next
  - name: searchFields
    tab: advanced
    simple: hide
    under: search
    type: array
    description: "The row fields the phone-side search reads (default: every text and number field of the row). Ignored by paged lists, where the hub matches."
    summary: Which row fields the search looks in
    does: "Limits the search to these row fields, e.g. [\"name\", \"room\"]."
    since: next
  - name: itemTemplate
    chip: Rows
    edit: template
    depth: surface
    title: Row design
    tab: advanced
    type: object
    description: "A group definition ({grid, children}) drawn once per row; {{item.<field>}} in its children's text, values, images and payloads is replaced from that row. Absent: rows are columns. See [[#Item templates]]."
    summary: Draw each row from controls instead of columns
    does: "Lays out each row as its own small grid of controls, e.g. a name, a version and a button, filled in from that row's data."
  - name: axis
    since: next
    edit: look
    depth: hold
    under: itemTemplate
    title: Direction
    tab: style
    type: enum
    values: [vertical, horizontal]
    default: vertical
    description: "vertical: rows run down the list. horizontal: with an itemTemplate the list is a side strip, items scroll sideways, one template group each. See [[#Side strips]]."
    summary: Rows down, or a strip that scrolls sideways
    does: "Turns a templated list into a strip: every item is drawn from the itemTemplate side by side and you scroll them left and right."
    valueHelp: {"vertical": "rows run down the page", "horizontal": "items scroll sideways as a strip"}
    valueTitles: {"vertical": "Down", "horizontal": "Sideways"}
    valueSymbols: {"vertical": "list.bullet", "horizontal": "rectangle.split.3x1"}
  - name: snap
    since: next
    edit: look
    depth: hold
    under: axis
    title: Snap
    tab: style
    type: enum
    values: [none, item]
    default: none
    description: "Strip: where a scroll comes to rest. none: anywhere. item: an item's edge lines up with the strip's start."
    summary: Whether a scroll settles on an item
    does: "Makes a sideways strip settle with an item at its start, instead of stopping wherever it slows."
    valueHelp: {"none": "stops anywhere", "item": "settles on an item"}
    valueTitles: {"none": "Free", "item": "Item"}
    valueSymbols: {"none": "arrow.left.and.right", "item": "arrow.left.to.line"}
  - name: edge
    since: next
    edit: part
    depth: hold
    under: axis
    title: Soft edges
    tab: style
    type: enum
    values: [soft, none]
    default: soft
    description: "Strip: items soften toward the strip's ends (the scroller engine's helper). none: a hard edge."
    summary: Whether items fade at the ends of the strip
    does: "Softens the items that run off either end of the strip, or leaves them cut square."
    valueHelp: {"soft": "items soften at the ends", "none": "items are cut at the ends"}
    valueTitles: {"soft": "Soft", "none": "Hard"}
    valueSymbols: {"soft": "circle.lefthalf.filled", "none": "square"}
  - name: itemColumns
    since: next
    edit: scrub
    depth: hold
    under: axis
    title: Item width
    unit: columns
    tab: style
    min: 1
    max: 12
    step: 1
    type: number
    default: 1
    description: "Strip: an item's width in grid columns of the list's own width (default 1)."
    summary: How wide each strip item is
    does: "Sets how many of the list's columns one item takes; at least a finger wide."
  - name: valueFrom
    since: next
    simple: hide
    tab: data
    type: any
    description: "On a control inside a strip's itemTemplate: the item's value it starts at and follows when the hub patches that item, usually \"{{item.value}}\". A drag by the user wins for 600 ms."
    summary: The item value this control shows
    does: "Keeps this control (a slider) at its item's value, so the hub moving one item moves only that item's control."
  - name: itemSpacing
    edit: scrub
    depth: hold
    under: itemStyle
    title: Row gap
    unit: pt
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
    edit: look
    depth: hold
    under: itemTemplate
    title: Row look
    tab: style
    values: [plain, card]
    type: enum
    default: plain
    description: "plain: rows sit inside the list's card. card: each itemTemplate row draws its template group's own card (fill, corners, theme), so rows read as separate cards; pair it with hideBackground: true and an itemSpacing. See [[#Card rows]]."
    summary: Plain rows or a card per row
    does: "Gives every templated row a card of its own, styled by the template's theme, instead of lines inside one list card."
    valueHelp: {"plain": "rows sit inside the list's own card, as before", "card": "each templated row is its own card, styled by the template group"}
    valueTitles: {"plain": "Plain", "card": "Cards"}
    valueSymbols: {"plain": "list.bullet", "card": "rectangle.stack.fill"}
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
    valueTitles: {"rows": "Rows", "grid": "Grid"}
    valueSymbols: {"rows": "list.bullet", "grid": "square.grid.2x2.fill"}
  - name: rowStyle
    since: next
    title: Table look
    tab: style
    simple: hide
    type: enum
    edit: look
    depth: hold
    values: [inset, plain, dense]
    default: plain
    valueHelp: {"inset": "rounded section cards with hairlines inside, like Settings", "plain": "an edge-to-edge list with inset hairlines", "dense": "a data table: 36 pt rows, smaller type, full-width hairlines"}
    valueTitles: {"inset": "Inset", "plain": "Plain", "dense": "Dense"}
    valueSymbols: {"inset": "rectangle.grid.1x2", "plain": "list.bullet", "dense": "tablecells"}
    description: "inset: rounded section cards on the page like Settings. plain: an edge-to-edge list, hairlines inset 16 pt. dense: a data table with 36 pt rows. Default: dense for a column table (listColumns set), else plain. See [[#Table rows]]."
    summary: The look of the rows
    does: "Draws the rows as inset cards, a plain edge-to-edge list or a dense data table."
  - name: leadingIcon
    since: next
    title: Row icon
    tab: style
    simple: hide
    type: string
    description: "Row field holding an SF Symbol name, drawn at the leading edge of each row."
    summary: Which field is the row icon
    does: "Shows the SF Symbol named in that field at the start of every row."
  - name: leadingImage
    since: next
    title: Row image
    tab: style
    simple: hide
    type: string
    description: "Row field holding an image URL, drawn at the leading edge of each row (wins over leadingIcon)."
    summary: Which field is the row picture
    does: "Shows the picture at that URL at the start of every row."
  - name: titleField
    since: next
    title: Row title
    tab: style
    simple: hide
    type: string
    description: "Row field for the first line of each row. Default: the first column."
    summary: Which field is the row title
    does: "Prints that field as each row's title line."
  - name: subtitleField
    since: next
    title: Row subtitle
    tab: style
    simple: hide
    type: string
    description: "Row field for the second, secondary line of each row."
    summary: Which field is the row subtitle
    does: "Prints that field under each row's title in a smaller, quieter style."
  - name: trailingField
    since: next
    title: Row value
    tab: style
    simple: hide
    type: string
    description: "Row field shown at the trailing edge of each row, in monospaced digits."
    summary: Which field sits at the row's end
    does: "Prints that field at the end of each row, numbers lined up."
  - name: sectionField
    since: next
    title: Group by
    tab: style
    simple: hide
    type: string
    description: "Row field whose values group the rows under sticky section headers, in order of first appearance. Not used with paging or an itemTemplate."
    summary: Which field groups the rows
    does: "Splits the rows into sections headed by that field's value."
  - name: accessory
    since: next
    title: Row mark
    tab: style
    simple: hide
    edit: look
    depth: hold
    values: [none, chevron, checkmark, detail]
    type: enum
    description: "The mark at each row's trailing edge: none, chevron, checkmark or detail (an info mark). Default: chevron when the list has an action, else none."
    summary: What sits at each row's end
    does: "Adds a chevron, checkmark or info mark at the end of every row."
    valueHelp: {"none": "no mark", "chevron": "a chevron, the row opens something", "checkmark": "a checkmark", "detail": "an info mark"}
    valueTitles: {"none": "None", "chevron": "Chevron", "checkmark": "Check", "detail": "Info"}
    valueSymbols: {"none": "minus", "chevron": "chevron.right", "checkmark": "checkmark", "detail": "info.circle"}
  - name: showSubtitle
    since: next
    edit: switch
    depth: hold
    under: rowStyle
    title: Second column as subtitle
    tab: style
    simple: hide
    type: bool
    default: false
    description: "Column rows: the second column is the subtitle under the title instead of a second value at the end."
    summary: Put the second column under the title
    does: "Moves the second column to a quieter line under the first, instead of the end of the row."
  - name: header
    since: next
    edit: switch
    depth: hold
    under: rowStyle
    title: Column header row
    tab: style
    simple: hide
    type: bool
    default: true
    description: "Column tables (listColumns set): the sticky header row of column names. Default on."
    summary: Show the column names above the rows
    does: "Shows or hides the row of column names above a column table."
themeFields:
  - name: cardPadding
    unit: pt
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
    unit: pt
    title: Corner roundness
    type: number
    min: 0
    max: 30
    step: 1
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
colorSlots:
  - slot: title
    default: neutral
    alias: tint
    since: next
    summary: The color of the heading
    does: Colors the list's heading, softened to 70%; until set it follows the neutral role, the text color.
  - slot: text
    default: neutral
    since: next
    summary: The color of the row text
    does: Colors the cells, and the column names above them at 75%; until set it follows the neutral role, the text color.
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
| `itemTemplate` | [[group-def\|GroupDefinition]] | — | Each row drawn from controls bound to `{{item.<field>}}` — see [[#Item templates]]. Being a group definition it takes `customize` (see [[group-def]]): none, look or arrange for the generated rows, one patch keyed `<list id>#item`; it only narrows `connection.customize` |
| `itemSpacing` | number | `2` | Points between rows (0-64) |
| `itemStyle` | `"plain"` or `"card"` | `"plain"` | `card`: each templated row draws its template group's own card — see [[#Card rows]] |
| `itemLayout` | `"rows"` or `"grid"` | `"rows"` | `grid`: templated rows as cards side by side, 2-3 columns by the list's width — see [[#Card grid]] |
| `rowStyle` | `"inset"`, `"plain"` or `"dense"` | dense with `listColumns`, else plain | The Table look — see [[#Table rows]] |
| `leadingIcon` / `leadingImage` | string | — | Row field holding an SF Symbol name / an image URL |
| `titleField` / `subtitleField` / `trailingField` | string | first column / — / — | Row fields for the title, subtitle and trailing value |
| `accessory` | `"none"`, `"chevron"`, `"checkmark"`, `"detail"` | chevron when tappable | Mark at the row's trailing edge |
| `sectionField` | string | — | Rows grouped under sticky headers by this row field |
| `showSubtitle` | bool | `false` | Column rows: the second column becomes the subtitle |
| `header` | bool | `true` with `listColumns` | Column tables: the sticky header row |
| `listColumns[].align` | `"leading"`, `"trailing"`, `"numeric"` | numeric for all-number columns, else leading | Column alignment; `numeric` aligns trailing in monospaced digits |

## Table rows

A row without an `itemTemplate` is drawn as: **leading** (icon or image) — **title** with a smaller
**subtitle** under it — **trailing** value(s) and an optional mark (chevron, checkmark, info).
Type is the app's proportional scale with monospaced digits, so figures line up; rows are at least
44 pt (36 pt dense) and a 0.5 pt hairline starts at the title's leading edge, none after the last row.
The rows soften where they leave the list ([[grid-dimensions]] `edge`).

- **Named fields.** `titleField`, `subtitleField`, `trailingField`, `leadingIcon`, `leadingImage` name the row
  fields to use. With none named, columns map on: the first column is the title, the second the
  subtitle when `showSubtitle` is on (else a trailing value), every further column a trailing value.
  Nothing is dropped.
- **Sections.** `sectionField` groups rows under headers (sticky) by that field's value, in order of
  first appearance; rows without a value sit under no header.
- **Column tables.** With `listColumns` and none of the fields above, the rows are an aligned table:
  a sticky header row (`header: false` hides it), each column `leading`, `trailing` or `numeric`
  (`align`; absent: numeric when every cell is a number). It uses the `dense` look unless `rowStyle` says otherwise.
- **Looks.** `rowStyle` `inset` draws section cards on the page like Settings, `plain` an edge-to-edge
  list, `dense` a data table. `inset` needs synced rows: a paged list draws it plain.
- Paging, search, row taps and `itemTemplate` rows (and cards) work as before.

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
stays read-only, unless the list is bound to a My Data collection: then a tap opens that row's entry sheet.

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

## Side strips

`axis: "horizontal"` with an `itemTemplate` makes the list a side strip on the scroller engine: the items
scroll sideways, one template group each, about `itemColumns` of the list's columns wide. It sits on the page
with no card unless `hideBackground` is `false`. `snap` is `none` or `item`; `edge` is `soft` (default) or `none`.

- **Per-item values.** Put the control in the template with `"valueFrom": "{{item.value}}"` (and the same token
  as its `defaultValue`). Its action carries the item: `"id": "{{item.id}}"` in the payload, and `{{value}}`
  for the control's own value, so moving one slider sends that item's id and value.
- **The hub sets one item.** Rows come from `rows`, a synced value, or `paging`. A frame with `"patch": true`
  and `items: [{"id": "band-3", "value": 0.4}]` merges by `id` into the rows held and moves only that item;
  an id not held is added (at `index`, else the end), and `"remove": ["band-3"]` takes items out. Added and
  removed items fade in and out; there is no bounce. A slider the user dragged keeps their value for 600 ms.
- Items without an `id` can be drawn but not patched.

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

### Search

`search` ties a list to a search box: `builtin` (its own box), `none`, or the id of a text input with
`role: search`. The same box can be named by any number of lists. Static and store rows are filtered
on the phone, ignoring case and accents, over `searchFields` (default: every text and number field);
the filter waits 150 ms after typing stops and keeps row order. A paged list never filters locally:
the text goes into the page request as `{{query}}` and the hub does the matching, exactly like
`paging.queryFrom`, which keeps working and is read as `search: <id>` when `search` is absent. A box
inside a `form` still drives its lists.

## Examples

### Settings-style rows
Shows a titled list with icons, subtitles and values. Intended effect: rounded cards per group, each row an icon, a name with a quieter line under it and a value at the end.
```json
{"type": "list", "id": "devices", "label": "Devices", "rowStyle": "inset", "sectionField": "room",
 "leadingIcon": "icon", "titleField": "name", "subtitleField": "state", "trailingField": "level",
 "defaultValue": [
  {"id": "a", "room": "Living room", "icon": "lamp.floor.fill", "name": "Floor lamp", "state": "On", "level": 80},
  {"id": "b", "room": "Living room", "icon": "tv.fill", "name": "TV", "state": "Standby", "level": 0},
  {"id": "c", "room": "Bedroom", "icon": "fan.fill", "name": "Fan", "state": "Off", "level": 0}]}
```

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

### Two lists, one search box
Shows one `role: search` text input driving a table. Intended effect: typing in the box narrows the rows to those whose name or room contains the text; clearing it brings every row back.
```json
{ "type": "textInput", "id": "find", "position": [0, 0], "span": [1, 4], "role": "search" }
```
```json
{ "type": "list", "id": "devices", "position": [1, 0], "span": [4, 4], "search": "find", "searchFields": ["name", "room"],
  "listColumns": [ { "key": "name", "label": "Name" }, { "key": "room", "label": "Room" } ] }
```

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

### EQ side strip fed by a hub
Shows a side strip with a vertical slider and a label per band. Intended effect: ten bands scroll sideways with no card; dragging band 3 sends `{"msg_type": "eq_band", "id": "band-3", "value": …}`, and the hub moves one band by sending `{"msg_type": "eq_bands", "patch": true, "items": [{"id": "band-3", "value": 0.4}]}`.
```json
{
  "type": "list",
  "id": "eq",
  "position": [0, 0],
  "span": [4, 4],
  "axis": "horizontal",
  "snap": "none",
  "itemColumns": 1,
  "hideBackground": true,
  "paging": { "pageSize": 20, "replyType": "eq_bands",
              "request": { "method": "meshsocket", "event": "broadcast_request",
                           "payload": { "msg_type": "eq_bands_get", "req": "{{req}}" } } },
  "itemTemplate": {
    "grid": { "columns": 1, "rows": 4 },
    "children": [
      { "type": "slider", "id": "band", "position": [0, 0], "span": [3, 1], "orientation": "vertical",
        "min": 0, "max": 1, "defaultValue": "{{item.value}}", "valueFrom": "{{item.value}}",
        "action": { "method": "meshsocket", "event": "broadcast_request",
                    "payload": { "msg_type": "eq_band", "id": "{{item.id}}", "value": "{{value}}" } } },
      { "type": "label", "id": "name", "position": [3, 0], "span": [1, 1], "text": "{{item.name}}" }
    ]
  }
}
```

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
