---
type: webView
label: Web View
icon: globe
category: controls
defaultSpan: [4, 4]
addIntent: show
pickerCategory: Media
friendlyName: Web page
oneLiner: A web page inside your app
aliases: [web, browser, webpage, url, site, embed]
depth: complete
starterPreset: {"label": "Web page","url": "https://example.com"}
fields:
  - name: url
    chip: Page
    type: string
    description: URL to load
    summary: The web page to show
    does: Loads this web address inside the control; a missing address shows a globe and "No URL". A live synced value that is a full URL replaces it.
  - name: label
    edit: inline
    depth: surface
    title: Title
    type: string
    description: Header label
    summary: The name shown above the page
    does: Shows this text above the page in the label font size (8-24 pt, default 12); with no label no header row appears.
  - name: webInteractive
    effect: behavior
    edit: part
    depth: hold
    title: Interactive
    type: bool
    default: true
    description: Allow user interaction
    summary: Whether you can tap and type in the page
    does: When off, touches pass through the page so it is display only; when on, links and forms work.
  - name: webScrollEnabled
    effect: behavior
    edit: part
    depth: hold
    title: Scrolling
    type: bool
    default: true
    description: Allow scrolling
    summary: Whether the page can be scrolled
    does: When off, the page stays at its top position and cannot be dragged; when on, you can scroll it.
  - name: webRefreshInterval
    min: 1
    max: 3600
    step: 1
    type: number
    description: Auto-refresh interval in seconds
    summary: How often the page reloads by itself
    does: Reloads the page every this many seconds (1 to 3600) while it is on screen; leave it unset for no automatic reload.
  - name: hideBackground
    edit: part
    depth: hold
    title: Background
    tab: style
    type: bool
    default: false
    description: Remove glass card background
    summary: Whether the card behind it is drawn
    does: Removes the glass card, fill and border so only the page sits on the layout.
themeFields:
  - use: cornerRadius
    summary: How round the card corners are
    does: Rounds the control's card corners from 0 to 30 pt (default 12).
  - name: controlPadding
    title: Inner spacing
    min: 0
    max: 24
    step: 1
    type: number
    default: 8
    description: Internal padding
    summary: The gap between card edge and page
    does: Sets the space inside the card around the page from 0 to 24 pt (default 8).
  - name: surfacePrimary
    title: Background color
    type: color
    default: #FFFFFF0F
    description: Background fill
    summary: The card's fill color
    does: Fills the card behind the page with this color, default a faint white wash.
  - name: secondaryColor
    title: Second text color
    type: color
    default: #FFFFFF99
    description: Secondary text color
    summary: The color of the title
    does: Colors the label above the page, default a soft white.
  - name: borderColor
    title: Border color
    type: color
    default: #FFFFFF1A
    description: Border color
    summary: The card's outline color
    does: Draws the card's outline in this color, default a faint white.
  - name: borderWidth
    title: Border thickness
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
    summary: How thick the outline is
    does: Sets the outline thickness from 0 to 5 pt (default 1).
  - name: labelFontSize
    title: Title text size
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
    summary: How big the title is
    does: Sets the label text size from 8 to 24 pt (default 12).
---

# Web View

An embedded web browser that renders a URL inline within the layout grid. Supports interactive browsing, scroll control, and periodic auto-refresh.

## Type
`"webView"`

## Relevant Fields
Inherits all [[shared-properties]]. Key fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | string | — | URL to load |
| `label` | string | falls back to `id` | Header label |
| `webInteractive` | bool | `true` | Allow user interaction |
| `webScrollEnabled` | bool | `true` | Allow scrolling |
| `webRefreshInterval` | number | — | Auto-refresh interval in seconds |
| `hideBackground` | bool | `false` | Remove glass card background |

## Examples

### Embedded dashboard
A scroll-locked dashboard that refreshes every 30 seconds.
```json
{
  "type": "webView",
  "id": "grafana",
  "position": [0, 0],
  "span": [4, 4],
  "label": "Metrics Dashboard",
  "url": "https://grafana.local/d/overview?kiosk",
  "webInteractive": true,
  "webScrollEnabled": false,
  "webRefreshInterval": 30
}
```

### Auto-refreshing status page
A read-only page that reloads itself every minute.
```json
{
  "type": "webView",
  "id": "status-page",
  "position": [0, 0],
  "span": [4, 3],
  "label": "Service status",
  "url": "https://example.com/status",
  "webInteractive": false,
  "webScrollEnabled": false,
  "webRefreshInterval": 60
}
```

### Plain page without a card
A browsable page with no frosted card or title row.
```json
{
  "type": "webView",
  "id": "docs-page",
  "position": [0, 4],
  "span": [4, 4],
  "url": "https://example.com",
  "hideBackground": true
}
```

## Related
- [[shared-properties]] — Base fields
