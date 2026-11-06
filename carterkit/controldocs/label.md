---
type: label
depth: complete
label: Label
icon: textformat
category: controls
defaultSpan: [1, 2]
addIntent: show
pickerCategory: Readouts
friendlyName: Text
oneLiner: A line of text, or a value with a caption
aliases: [text, title, heading, caption, readout, words]
addRank: 1
starterPreset: {"label": "Text","text": "Hello"}
lookFormats: [{"id": "plain","name": "Plain","symbol": "textformat","set": {"formatValue": null}},{"id": "number","name": "Number","symbol": "number","set": {"formatValue": "decimal"}},{"id": "lastTime","name": "Last time","symbol": "clock.arrow.circlepath","set": {"formatValue": "relative:day"}},{"id": "date","name": "Date","symbol": "calendar","set": {"formatValue": "date"}}]
lookPresets: [{"id": "plain","name": "Plain","symbol": "text.alignleft","set": {"style": null,"align": null}},{"id": "headline","name": "Headline","symbol": "textformat.size.larger","set": {"style": "headline","align": null}},{"id": "bigNumber","name": "Big number","symbol": "textformat.123","set": {"style": "large-mono","align": "center"}},{"id": "quiet","name": "Quiet","symbol": "textformat.size.smaller","set": {"style": "caption","align": null}}]
fields:
  - name: text
    edit: inline
    depth: surface
    title: Text
    type: string
    description: Static display text (overridden by sync)
    summary: Text to show until a connected value is available
    does: Sets the words on the label; a synced value replaces them as soon as one arrives.
  - name: label
    title: Other text
    type: string
    description: Alternative to text
    summary: A second place to put the words
    does: Shows this text when Text is empty; the label reads the same either way.
  - name: subtitle
    edit: inline
    depth: hold
    title: Second line
    type: string
    description: A quieter second line under the text (caption size, secondary color). In a list itemTemplate it takes {{item.<field>}}
    summary: A smaller gray line under the words
    does: Adds a compact second line in the caption size and the theme's secondary color; leave it empty for a single line.
  - name: lines
    edit: scrub
    depth: hold
    under: style
    title: Lines
    tab: style
    min: 0
    max: 10
    step: 1
    type: number
    default: 1
    description: Most lines the text may take (1 = truncate, N = wrap up to N, 0 = wrap freely). Also limits the subtitle
    summary: How many lines the words may use
    does: Keeps the text on one line, or lets it wrap onto up to 10 lines; 0 wraps as far as it needs.
  - name: icon
    edit: symbol
    depth: surface
    title: Symbol
    type: string
    description: SF Symbol before text
    summary: A small picture shown before the words
    does: Draws the named SF Symbol in front of the text, in the same color and size.
  - name: style
    edit: look
    title: Look
    tab: style
    type: enum
    values: [default, headline, title, caption, mono, large-mono, terminal]
    default: default
    description: Text style variant (terminal = ANSI terminal renderer)
    summary: How big and bold the text looks
    does: Switches the font between a small line, a headline, a title, a caption and monospaced or terminal looks.
    valueHelp: {"default": "small body text", "headline": "bold headline size", "title": "larger bold title", "caption": "small caption text", "mono": "body text in a monospaced font", "large-mono": "larger monospaced text, good for big numbers", "terminal": "a dark ANSI terminal view that keeps colors and columns"}
  - name: glowRadius
    edit: scrub
    depth: hold
    under: style
    title: Glow
    unit: pt
    tab: style
    min: 0
    max: 30
    step: 1
    type: number
    default: 0
    description: Soft glow behind the text in its own colour, in points (0 = none). Cross-control, same on every control
    summary: A soft halo behind the words
    does: Adds a blurred glow in the text color, 0 to 30 points wide; 0 turns it off.
  - name: tint
    edit: color
    title: Color
    tab: style
    type: color
    default: "#FFFFFF"
    description: Text and icon color
    summary: The color of the words and symbol
    does: Recolors the text and the symbol in front of it.
  - name: align
    edit: look
    depth: hold
    under: style
    title: Alignment
    tab: style
    type: enum
    values: [leading, center, trailing]
    default: leading
    description: Text alignment
    summary: Where the words sit across the label
    does: Moves the text to the left edge, the middle or the right edge of the label.
    valueHelp: {"leading": "text starts at the left edge", "center": "text is centered", "trailing": "text ends at the right edge"}
  - name: fontWeight
    edit: look
    depth: hold
    under: style
    title: Weight
    tab: style
    type: enum
    values: [ultraLight, thin, light, regular, medium, semibold, bold, heavy, black]
    default: regular
    description: Font weight laid over the text style
    summary: How thick the letter strokes are
    does: Makes the letters lighter or heavier, from ultra thin to black, on top of the chosen style.
    valueHelp: {"ultraLight": "hairline strokes", "thin": "very slim strokes", "light": "slim strokes", "regular": "normal strokes", "medium": "slightly heavier than normal", "semibold": "firm, between medium and bold", "bold": "heavy strokes", "heavy": "very heavy strokes", "black": "the heaviest strokes"}
  - name: forecast
    title: Look ahead
    tab: data
    type: enum
    values: [countdown, reach]
    description: "Look ahead beside the real reading: countdown = the value is a time and the widget counts down to it; reach = the value is expected to arrive at forecastTarget (at the time forecastTimeFrom holds) or to keep moving by forecastRate per second. A newer real value always replaces the guess; past its end the value reads stale."
    summary: Show as a countdown, or show where the value is expected to reach
    does: Lets the label keep ticking between real readings, marked as about, until a real value replaces it.
    valueHelp: {"countdown": "the value is a time and the label counts down to it", "reach": "the value is guessed to move toward a target number until the next real reading"}
  - use: forecastTarget
    does: Gives the number the guessed value drifts toward, from -1000000 to 1000000.
  - use: forecastTimeFrom
    summary: Which other control says when it arrives
    does: Uses that control's time value as the moment the guess reaches the target, so the guess lands on time.
  - use: forecastRate
    summary: How fast the guess keeps moving
    does: Moves the displayed number by this much every second after the last real reading, from -1000 to 1000.
  - name: unit
    title: Unit
    type: string
    description: "Measurement unit the value arrives in ([[values#Units]] name or symbol, e.g. celsius, km/h). A numeric value converts to the device locale; text values show as sent. Unknown strings show literally."
    summary: The measurement the number is in
    does: Converts a numeric value to the phone's own units, so celsius shows as degrees Fahrenheit in the US; text is shown as sent.
  - name: scrollable
    title: Scrolling log
    type: bool
    default: false
    description: Fixed-height scrolling terminal/log view that keeps the latest line in view (pair with controlHeight)
    summary: Turns the label into a log you can scroll
    does: Gives the label a fixed height that scrolls and stays on the newest line.
  - name: formatValue
    title: Number format
    simple: hide
    tab: data
    type: string
    description: Value display format (see formatValue table; relative / relative:day show a date as time-since)
    summary: How the value is written out
    does: Shows the value as a rounded number, a percent, a duration, a size, a date or a time since, instead of the raw text.
  - name: placeholder
    title: Text before any value
    type: string
    description: Shown by a relative-date label with no date yet (default "Never")
    summary: What to say before there is a date
    does: Shows this text (Never by default) on a time-since or date label that has no date yet.
  - name: valueMap
    title: Words for values
    tab: data
    type: object
    description: Incoming value → display text ("default" catches the rest)
    summary: Show different words for different values
    does: Replaces a raw incoming value such as 61 with the words you pick, with default catching the rest.
  - name: iconMap
    title: Symbols for values
    tab: data
    type: object
    description: Incoming value → SF Symbol name
    summary: Show different symbols for different values
    does: Swaps the symbol in front of the text to match the incoming value.
  - name: colorMap
    title: Colors for values
    tab: data
    type: object
    description: Incoming value → hex tint
    summary: Show different colors for different values
    does: Recolors the text to match the incoming value, for example green for running.
themeFields:
  - name: secondaryColor
    title: Subtitle color
    type: color
    description: Subtitle colour
    summary: The softer colour of the subtitle line
    does: Colours the subtitle under the label text; defaults to the theme's secondary text colour.
  - use: controlPadding
    summary: The breathing room inside the label
    does: Pushes the text in from the edges by 0 to 24 points.
  - name: cornerRadius
    edit: scrub
    depth: hold
    under: style
    unit: pt
    title: Corner roundness
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius (card behind the text, when a background is set)
    summary: How round the label's corners are
    does: Rounds the card behind the text from square at 0 to very round at 30 points.
  - use: surfacePrimary
    summary: The fill behind the text
    does: Paints the card behind the label in this color.
  - use: borderColor
    does: Colors the line drawn around the label.
  - name: borderWidth
    edit: scrub
    depth: hold
    under: style
    unit: pt
    title: Border thickness
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
    summary: How thick the outline is
    does: Draws the border from 0 to 5 points thick; 0 hides it.
  - use: foregroundColor
    summary: The main color of the words
    does: Sets the color the text is drawn in when no Color is chosen.
---

# Label

A read-only text display. Shows static text or synced dynamic text. Stores a `.string` value when synced.

## Type
`"label"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `text` | string | — | Static display text (overridden by sync) |
| `label` | string | — | Alternative to `text` |
| `subtitle` | string | — | A quieter second line under the text (caption size, theme secondary color); in a list `itemTemplate` it takes `{{item.<field>}}`. Empty = no second line |
| `lines` | number | `1` | Most lines the text may take: `1` truncates, `N` wraps up to N, `0` wraps freely. Also limits the subtitle. Unset keeps the style's own limit (headline/title 2, mono unlimited) |
| `icon` | string | — | SF Symbol before text |
| `style` | string | `"default"` | See [[style-properties#Label Styles]] |
| `tint` | string | white | Text and icon color (terminal: default text colour over the dark backdrop) |
| `glowRadius` | number | `0` | Soft glow behind the text in its own colour, 0–30 pt (the same attribute on every control that has it) |
| `align` | string | `"leading"` | `"leading"`, `"center"`, `"trailing"` |
| `fontWeight` | string | `"regular"` | `ultraLight` … `black`, laid over the style |
| `unit` | string | — | Measurement unit of a numeric value ([[values#Units]]); shown converted to the device locale (`"celsius"` → °F in the US). A `valueMap` hit or non-numeric text shows as sent. Unknown strings are a literal suffix |
| `forecast` | enum | — | `"countdown"` (the value is a time; count down to it) or `"reach"` (expected to arrive at `forecastTarget`). Shown on widgets and Live Activities, marked "about"; the next real value replaces it, and past its end the value reads stale |
| `forecastTarget` | number | — | With `"reach"`: the value it is expected to arrive at |
| `forecastTimeFrom` | string | — | With `"reach"`: id of the control whose value is the arrival time (epoch seconds or ISO-8601) |
| `forecastRate` | number | — | With `"reach"`: change per second from the last real reading (instead of a target and time) |
| `scrollable` | bool | `false` | Fixed-height scrolling terminal/log view (pair with `controlHeight`) |
| `formatValue` | string | — | Value display format (see formatValue table below) |
| `placeholder` | string | `"Never"` | With `relative` / `relative:day`: the text shown while there is no date |
| `valueMap` | object | — | Incoming value → display text — see [[#Value maps]] |
| `iconMap` | object | — | Incoming value → SF Symbol name |
| `colorMap` | object | — | Incoming value → hex tint |

## Value maps

A feed you don't control emits codes — a WMO weather code, a device state, an alarm
level — and the label should read as words, not `61`. `valueMap`, `iconMap`, and
`colorMap` say what each value looks like, declaratively:

```json
"valueMap": { "0": "Clear", "3": "Overcast", "61": "Rain", "default": "—" },
"iconMap":  { "0": "sun.max.fill", "3": "cloud.fill", "61": "cloud.rain.fill" },
"colorMap": { "61": "#0A84FF" }
```

- **Keys match the stringified value**, so `0`, `"0"`, `true`, and `"rain"` all work
  from the same map. `true`/`false` also match `yes`/`no`/`on`/`off`/`1`/`0`, and a
  number matches whether it arrives as `61` or `61.00`. Key lookup falls back to a
  case-insensitive match.
- **`"default"`** is the catch-all for any value with no entry.
- **No match and no `"default"`** ⇒ the label degrades gracefully: the raw value for
  `valueMap`, the control's own `icon`/`tint` for `iconMap`/`colorMap`. It never
  blanks out.
- A `valueMap` hit is the text as written — `formatValue` is not applied on top.
- The maps apply to the **synced** value; before the first sync the static `text`
  placeholder still shows.

The same three fields work on [[image]], where `valueMap` maps to an image URL.

## Format Values

| Value | Output | Example |
|-------|--------|---------|
| `"decimal"` | `"72"` or `"3.5"` | Rounds to integer |
| `"decimal:N"` | `"3.14"` | Fixed N decimal places (e.g., `"decimal:2"`) |
| `"percent"` | `"80%"` | Integer percentage |
| `"time"` | `"3:45"` | Minutes:seconds from total seconds |
| `"duration"` | `"1h 23m"` | Human-readable duration from seconds |
| `"bytes"` | `"1.2 GB"` | Auto-scaled byte units |
| `"bps"` | `"54 Mbps"` | Auto-scaled bits-per-second |
| `"suffix:X"` | `"72°F"` | Append custom suffix (e.g., `"suffix:°F"`) |
| `"relative"` | `"4 days ago"`, `"in 2 hours"` | A **date** shown as time-since / time-until — see [[#Relative dates]] |
| `"relative:day"` | `"Today"`, `"Yesterday"`, `"4 days ago"` | Whole local calendar days |
| `"date"` | `"Sep 26, 2026"` | A **date** shown as the date itself (locale medium style); no date → `placeholder` |
| `"date:time"` | `"Sep 26, 2026 at 2:03 PM"` | The date and the time |
| `"none"` | (hidden) | No value display |

## Look formats

In the editor's Look card, Text offers four **Format** chips, declared in this doc's
`lookFormats` frontmatter: **Plain** (no `formatValue`), **Number** (`"decimal"`),
**Last time** (`"relative:day"`) and **Date** (`"date"`). A chip only writes
`formatValue`; everything else stays as authored.

"Last time" is a Text format, not a separate control: the Add sheet offers one
**Text** choice, and showing a remembered time on a Text (Wire › a time value)
picks the **Last time** format for it, so the Look card shows that chip selected.

## Relative dates

`formatValue: "relative"` and `"relative:day"` turn a label bound to a date into a
time-since readout that **advances on its own** — "Fern: last watered 4 days ago"
becomes "5 days ago" tomorrow with no server, poll or data event.

- **Accepted values:** an ISO-8601 instant (`"2026-09-22T08:15:00Z"`, fractional
  seconds and offsets allowed — the `{{now}}` encoding), a date-only string
  (`"2026-09-22"`, read as that day in the device's **local** calendar), or an epoch
  number (seconds; milliseconds when larger than 10^11).
- **`relative`** picks the largest sensible unit: "Now" (under a minute), "5 minutes
  ago", "In 2 hours", "4 days ago".
- **`relative:day`** counts whole **local** calendar days: "Today", "Yesterday",
  "Tomorrow", "4 days ago", "In 2 days". Something done at 23:30 reads "Yesterday"
  at 00:30, whatever the UTC date says.
- **No date yet** (absent, `null`, empty, unparseable, or epoch `0`) shows
  `placeholder` — `"Never"` by default, localized. It is never blank, `"0"` or a
  1970 date.
- Before the first sync, a static `text` holding a date is formatted the same way.
- Text is localized (e.g. German "Vor 4 Tagen", "Gestern").
- The label refreshes itself once a minute with its own timer; nothing is written
  back to the control's value. Widget slots bound to the same control show the
  same text, refreshed whenever the widget reloads its timeline.

## Styles

| Value | Font |
|-------|------|
| `"default"` | `.subheadline` |
| `"headline"` | `.headline.bold` |
| `"title"` | `.title2.bold` |
| `"caption"` | `.caption` |
| `"mono"` | `.subheadline` monospaced |
| `"large-mono"` | `.title3` monospaced medium |
| `"terminal"` | Monospaced **ANSI terminal** — see [Terminal style](#terminal-style) |

## Terminal style

`style: "terminal"` (and, as a shortcut, **`mono`/`large-mono` + `scrollable`**) renders the
text as a real terminal instead of a plain mono label — purpose-built for piping a captured
shell/tmux pane to the phone:

- **ANSI styling** — colour (16 / 256 / truecolor), **bold**, dim, *italic*, underline, and
  reverse are parsed from the escape codes and rendered. Plain text (no escapes) renders
  normally.
- **Pane-matched scaling** — the font auto-scales so the source's column width exactly fills
  the view, so box-drawing and ASCII line up like the real pane. If a server prepends a
  `CSI 8;rows;cols t` size report, that column count is used; otherwise the widest line is.
- **Dark backdrop** — drawn on its own dark background (independent of the app theme) so
  ANSI colours have the contrast they were designed for.
- **Pinch to zoom** — pinch to scale the text past the fitted size; **double-tap** snaps back
  to fit. Content wider/taller than the view scrolls both ways.
- **Sizing** — set `controlHeight` for the on-screen height; `fontSize` caps the fitted font
  before zoom. Keeps the latest line in view and auto-scrolls on update.

Feed it like any synced label (a `.string` value); see the
[tmux-bridge](https://carterbeaudoin.net/CAR-TER) server for a complete example.

## Examples

### Time since (plant watering)
Shows a remembered date as a time-since readout that advances by itself; with no date yet it says the placeholder.

```json
{ "type": "label", "id": "fern-watered", "label": "Fern — last watered", "icon": "leaf.fill",
  "formatValue": "relative:day", "placeholder": "Not watered yet",
  "sync": [{ "method": "meshsocket", "event": "broadcast", "filter": { "msg_type": "fern" }, "valuePath": "lastWatered" }] }
```

### Static info label
Shows fixed text with no sync; the simplest label, it reads exactly as written.

```json
{
  "type": "label",
  "id": "temp-display",
  "position": [0, 0],
  "span": [1, 2],
  "text": "Current: 72°F"
}
```

### Synced label with icon
Shows a live value behind a small gray symbol; the dash stays until the first value arrives.

```json
{
  "type": "label",
  "id": "track-artist",
  "position": [1, 2],
  "span": [1, 2],
  "text": "—",
  "icon": "person.fill",
  "tint": "#AAAAAA",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "player_state" }, "valuePath": "artist" }]
}
```

### Name with a subtitle
Shows a name with a smaller gray line under it, two compact lines in one label; in a list row the second line comes from the item.

```json
{ "type": "label", "id": "pkg", "position": [0, 1], "span": [1, 2], "text": "{{item.name}}", "subtitle": "{{item.version}} · {{item.author}}" }
```

### Wrapping text
Shows a long description over up to three lines instead of cutting it off after one.

```json
{ "type": "label", "id": "blurb", "position": [0, 0], "span": [2, 4], "text": "A longer description that should wrap onto several lines.", "lines": 3 }
```

### Headline style
Shows a live value in the bold headline size, useful for a title that changes.

```json
{
  "type": "label",
  "id": "track-title",
  "position": [0, 2],
  "span": [1, 2],
  "text": "No Track",
  "style": "headline",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "player_state" }, "valuePath": "title" }]
}
```

### Terminal snapshot (live pane)
Shows a captured shell pane as a scrolling dark terminal with colors kept, pinned to the newest line.

```json
{
  "type": "label",
  "id": "pane-snapshot",
  "position": [1, 0],
  "span": [5, 4],
  "style": "terminal",
  "scrollable": true,
  "controlHeight": 360,
  "text": "(waiting for pane…)",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "snapshot" }, "valuePath": "text" }]
}
```

### Weather code → words, no server
Turns a numeric weather code into centered words with a matching symbol, and an em dash for any unknown code.

```json
{
  "type": "label",
  "id": "wx-text",
  "position": [0, 0],
  "span": [1, 2],
  "text": "…",
  "style": "headline",
  "align": "center",
  "valueMap": { "0": "Clear", "1": "Mainly clear", "2": "Partly cloudy", "3": "Overcast", "45": "Fog", "51": "Drizzle", "61": "Rain", "71": "Snow", "80": "Showers", "95": "Thunderstorm", "default": "—" },
  "iconMap": { "0": "sun.max.fill", "1": "sun.max.fill", "2": "cloud.sun.fill", "3": "cloud.fill", "45": "cloud.fog.fill", "51": "cloud.drizzle.fill", "61": "cloud.rain.fill", "71": "cloud.snow.fill", "80": "cloud.heavyrain.fill", "95": "cloud.bolt.rain.fill" },
  "sync": [{ "method": "http", "url": "https://api.open-meteo.com/v1/forecast?latitude=42.36&longitude=-71.06&current=weather_code", "interval": 900, "valuePath": "current.weather_code" }]
}
```

### Boolean state as words and colour
Shows true as green Running and false as gray Stopped, with a matching symbol for each.

```json
{
  "type": "label",
  "id": "pump-state",
  "position": [1, 0],
  "span": [1, 2],
  "text": "—",
  "align": "center",
  "valueMap": { "true": "Running", "false": "Stopped" },
  "iconMap": { "true": "bolt.fill", "false": "bolt.slash" },
  "colorMap": { "true": "#30D158", "false": "#8E8E93" },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "pump" }, "valuePath": "running" }]
}
```

### Number with a unit
Shows a Celsius reading converted to the phone's units, so a US phone reads it in degrees Fahrenheit.

```json
{ "type": "label", "id": "outside-temp", "position": [0, 0], "span": [1, 2], "text": "…", "unit": "celsius", "formatValue": "decimal", "style": "large-mono", "align": "center",
  "sync": [{ "method": "http", "url": "https://api.open-meteo.com/v1/forecast?latitude=42.36&longitude=-71.06&current=temperature_2m", "interval": 900, "valuePath": "current.temperature_2m" }] }
```

### Fixed decimals and percent
Shows a battery fraction as a whole percent; swap the format for `decimal:2` to get two decimal places instead.

```json
{ "type": "label", "id": "battery", "position": [0, 2], "span": [1, 2], "text": "—", "icon": "battery.75percent", "formatValue": "percent",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "power" }, "valuePath": "battery" }] }
```

### Date and time
Shows a stored instant as a readable date with the time, such as Sep 26, 2026 at 2:03 PM, in the phone's language.

```json
{ "type": "label", "id": "last-backup", "position": [1, 0], "span": [1, 2], "text": "—", "formatValue": "date:time", "placeholder": "No backup yet",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "backup" }, "valuePath": "finishedAt" }] }
```

### Big centered number (look presets)
Shows a number in the large monospaced style, centered and heavy, the way the Big number look does.

```json
{ "type": "label", "id": "big-count", "position": [1, 2], "span": [1, 2], "text": "0", "style": "large-mono", "align": "center", "fontWeight": "bold", "tint": "#30D158",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "counter" }, "valuePath": "count" }] }
```

### Quiet caption
Shows small, light text for a footnote that should not compete with the readings around it.

```json
{ "type": "label", "id": "footnote", "position": [2, 0], "span": [1, 4], "text": "Updated every 15 minutes", "style": "caption", "fontWeight": "light", "tint": "#8E8E93", "align": "trailing" }
```

### Glowing readout
Shows a value with a soft 8-point halo in its own color, for a lit-display feel.

```json
{ "type": "label", "id": "glow-temp", "position": [2, 4], "span": [1, 2], "text": "72°", "style": "title", "tint": "#0A84FF", "glowRadius": 8, "align": "center" }
```

### Countdown to a time
Shows the time left until a moment that arrives as a time value, ticking down on its own between readings.

```json
{ "type": "label", "id": "next-bus", "position": [3, 0], "span": [1, 2], "text": "—", "icon": "bus", "forecast": "countdown", "formatValue": "time",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "bus" }, "valuePath": "arrivesAt" }] }
```

### Expected to reach a number
Shows a charge percent that keeps climbing toward 100 at the time another control reports, marked as about, until a real reading replaces it.

```json
{ "type": "label", "id": "ev-charge", "position": [3, 2], "span": [1, 2], "text": "—", "formatValue": "percent", "forecast": "reach", "forecastTarget": 100, "forecastTimeFrom": "ev-done-at",
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "ev" }, "valuePath": "charge" }] }
```

### Drifting by a rate
Shows a tank level that keeps falling by 0.05 per second from the last reading when no end time is known.

```json
{ "type": "label", "id": "tank-level", "position": [3, 4], "span": [1, 2], "text": "—", "formatValue": "decimal:1", "forecast": "reach", "forecastRate": -0.05,
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "tank" }, "valuePath": "level" }] }
```

### Words for a code
Shows a device state code as plain words, with the default catching anything unexpected.

```json
{ "type": "label", "id": "door-state", "position": [4, 0], "span": [1, 2], "text": "—", "valueMap": { "0": "Closed", "1": "Open", "default": "Unknown" }, "colorMap": { "1": "#FF9F0A" },
  "sync": [{ "method": "meshsocket", "type": "listen", "event": "broadcast", "filter": { "msg_type": "door" }, "valuePath": "state" }] }
```

## Behavior
- When synced, the `text` field serves as a placeholder until the first sync value arrives
- Text updates animate with a smooth numeric content transition
- Labels have no action — they are display-only
- `valueMap`/`iconMap`/`colorMap` translate the synced value on the way to the screen —
  see [[#Value maps]]

## Related
- [[shared-properties]] — Base fields
- [[image]] — the same value maps, mapping to symbols and image URLs
- [[style-properties#Label Styles]] — Style variants
- [[sync]] — Live value updates
