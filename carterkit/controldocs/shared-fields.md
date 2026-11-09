---
kind: shared-fields
title: Shared fields
fields:
  - name: confirm
    title: Show confirmation
    tab: action
    type: bool
    default: false
    summary: A short note with Undo after each tap
    description: After this control's local write lands, show a pill naming the change with an Undo button for 3 seconds (default off)
    does: Shows a pill naming the change with an Undo button for 3 seconds after each local write.
  - name: forecastRate
    title: Change per second
    tab: data
    simple: hide
    type: number
    min: -1000
    max: 1000
    step: 0.01
    description: Keep moving by this much per second from the last real reading (forecast "reach", no time needed)
    summary: How fast it is expected to change
    does: Keeps moving the shown value by this much per second, -1000 to 1000, from the last real reading.
  - name: forecastTarget
    title: Expected to reach
    tab: data
    type: number
    min: -1000000
    max: 1000000
    step: 1
    description: The value this one is expected to arrive at (with forecast "reach")
    summary: The number it should reach
    does: Moves the shown value toward this number, between -1,000,000 and 1,000,000, until a real reading replaces it.
  - name: forecastTimeFrom
    title: Arrival time from
    tab: data
    simple: hide
    type: string
    description: Id of the control whose value is the arrival time (epoch seconds or ISO-8601), for forecast "reach"
    summary: Which control says when it arrives
    does: Takes the arrival time from another control's value (epoch seconds or ISO date) so the guess lands on time.
  - name: iconMap
    tab: data
    type: object
    edit: map
    columns: [{"name": "value", "title": "Value", "type": "string", "edit": "inline", "required": true, "values": ["default"], "default": "value{n}"}, {"name": "symbol", "title": "Symbol", "type": "string", "edit": "symbol", "required": true, "default": "circle"}]
    description: Incoming value → SF Symbol name ("default" catches the rest)
    does: Swaps the glyph to the symbol listed for the incoming value, with default catching any other value.
    summary: Show different symbols for different values
themeFields:
  - name: accentColor
    summary: "The theme's highlight color"
    does: Tints the accents wherever no color is set directly.
    title: Accent color
    type: color
    default: #667eea
    description: Accent/tint color
  - name: borderColor
    title: Border color
    type: color
    default: #FFFFFF1A
    description: Border color
    summary: The outline around the control
    does: "Colors the card's outline."
  - name: borderWidth
    title: Border thickness
    min: 0
    max: 5
    step: 0.5
    type: number
    default: 1
    description: Border width
    summary: How thick the outline is
    does: Sets the outline width from 0 (none) to 5 points.
  - name: controlPadding
    title: Inner spacing
    min: 0
    max: 24
    step: 1
    type: number
    default: 8
    description: Internal padding
    summary: Breathing room inside the edge
    does: Adds 0 to 24 points between the control's edge and its content.
  - name: cornerRadius
    title: Corner roundness
    min: 0
    max: 30
    step: 1
    type: number
    default: 12
    description: Control corner radius
    summary: How rounded the corners are
    does: Rounds the control's corners from square (0) to 30 points.
  - name: foregroundColor
    title: Text color
    type: color
    default: #FFFFFF
    description: Primary text color
    summary: The main text color
    does: Colors the primary text on the control.
  - name: labelFontSize
    title: Title text size
    min: 8
    max: 24
    step: 1
    type: number
    default: 12
    description: Label text size
    summary: "How big the title is"
    does: "Sets the title text size from 8 to 24 points."
  - name: secondaryColor
    title: Second text color
    type: color
    default: #FFFFFF99
    description: Secondary text color
    summary: The color of the less important text
    does: Colors the quieter supporting text.
  - name: surfacePrimary
    title: Background color
    type: color
    default: #FFFFFF0F
    description: Background fill
    summary: The card's fill color
    does: Fills the card behind the control with this color.
  - name: surfaceSecondary
    title: Second background color
    type: color
    default: #FFFFFF0A
    description: Secondary surface fill
    summary: Second background color
    does: Fills the nested surface inside the card with this color.
  - name: tertiaryColor
    title: Faint text color
    type: color
    default: #FFFFFF4D
    description: Tertiary text and ink color
    summary: The faintest text color
    does: Colors the faintest text and ink.
chips:
  - name: look
    title: Look
    icon: paintbrush.pointed
    order: 2
    categories: [look, motion, layout, feedback]
    tap: [style, "*Style", "*Mode", variant, indicator, cellShape, whiskers, renderingMode]
    petals: [own, "animation|containerAnimation|effect", "glowRadius|glow", haptic]
    petalTitles: {"animation": "Motion", "glowRadius": "Glow", "haptic": "Feel"}
    since: next
  - name: colour
    title: Colour
    icon: paintpalette
    order: 3
    categories: [colour]
    tap: [tint, accentColor, color]
    petals: [own]
    since: next
  - name: text
    title: Text
    icon: textformat
    order: 4
    categories: [text]
    tap: [label, title, text, name]
    petals: ["labelFontSize|labelSize", "valueFontSize|valueSize|fontSize", "fontWeight|weight", align, "maxLines|lines|minLines"]
    petalTitles: {"labelFontSize": "Title size", "valueFontSize": "Value size", "fontWeight": "Weight", "align": "Alignment", "maxLines": "Lines"}
    since: next
  - name: card
    title: Background
    icon: rectangle.on.rectangle
    order: 5
    categories: [card]
    tap: [backgroundColor]
    petals: [backgroundPadding, backgroundCornerRadius, backgroundBorderWidth, backgroundShadow, backgroundShadowOpacity]
    aliases: {"theme.cornerRadius": "backgroundCornerRadius", "theme.borderWidth": "backgroundBorderWidth", "theme.borderColor": "backgroundBorderColor", "theme.controlPadding": "backgroundPadding", "theme.cardPadding": "backgroundPadding", "theme.surfacePrimary": "backgroundColor"}
    always: true
    since: next
categories:
  - name: card
    title: Background
    fields: [hideBackground, background]
    theme: [borderColor, borderWidth, cornerRadius, surfacePrimary, surfaceSecondary, controlPadding, cardPadding, blurEnabled]
    since: next
  - name: text
    title: Text
    fields: [label, title, subtitle, placeholder, unit, emptyText, centerText, paletteLabel, hideLabel, hideValue, fontSize, fontWeight, weight, align, maxLines, minLines, lines, labelSize, valueSize, formatValue, format, valueMap, name, icon, onIcon, offIcon, minIcon, maxIcon]
    theme: [labelFontSize, valueFontSize]
    since: next
  - name: colour
    title: Colour
    fields: [tint, color, colors, colorMap, colorByValue, segments, palette, groupColors, logColors, statusColors, thresholds, colorBlend, glowColor]
    theme: [accentColor, foregroundColor, secondaryColor, tertiaryColor, trackColor, thumbColor, knobColor, selectedColor, selectedTextColor, textColor, buttonColor, iconColor, trackActiveColor]
    types: [color]
    suffixes: [Color, Tint]
    since: next
  - name: look
    title: Look
    fields: [style, lineCap, barCornerRadius, cellCornerRadius, sliceCornerRadius, sliceGap, cellGap, lineWidth, lineThickness, arcThickness, arcAngle, arcRotation, donutRatio, startAngle, pointSize, nodeSize, nodeWidth, nodeBorderWidth, edgeWidth, edgeOpacity, edgeCurved, curved, smooth, fillOpacity, ribbonOpacity, linkOpacity, cellShape, cellCorner, boxWidth, whiskers, variant, size, indicator, renderingMode, correctionLevel, sparklineFill, imageCornerRadius, imageShadow, rings, scale, trackCurvature, trackLength, cardinalSize, labelOffset, pad, sparklinePoints, bins, stacked, horizontal, percent, iconMap, flipAxis, explodeSelected, maxPoints, window]
    theme: [trackHeight, trackRadius, trackWidth, thumbRadius, thumbSize, knobRadius, buttonRadius, buttonSize, selectedRadius, knobShadow, selectedShadow, thumbShadow]
    prefixes: [show, hide]
    suffixes: [Style, Mode]
    since: next
  - name: motion
    title: Motion
    fields: [animation, containerAnimation, transition, glowRadius, glow, glowEnabled, pulse, tapEffect, spinDuration, spinTicks, effect, effectOptions, speed, loopCount, loopDelay, showParticles, particleSpeed, particleIntensity, particleAngle, damping, attractionForce, repulsionForce, centerForce, velocityDecay]
    since: next
  - name: feedback
    title: Feel
    fields: [haptic, sound]
    since: next
  - name: confirm
    title: Ask first
    home: binding
    fields: [confirm, ask]
    since: next
  - name: data
    title: Binding
    home: binding
    fields: [action, longPressAction, longPressGroup, snapshotAction, events, sync, valuePath, pageSize, forecast, forecastRate, forecastTarget, forecastTimeFrom, request, queryFrom, referencePath, replyPath, replyType, contentEvent, systemMessageEvents, sendMode, sendRate, debounce, historyCount, snapshot, snapshotMaxDimension, snapshotQuality, triggers, activeWhen, dynamic, visible, enabled, form, webRefreshInterval, defaultValue, continuous, repeatOnHold, clearOnSubmit, target]
    suffixes: [Action]
    groups: [data.series, paging]
    since: next
  - name: layout
    title: Layout
    fields: [span, position, landscape, regular, columns, rows, spacing, itemSpacing, controlHeight, aspect, aspectRatio, surfaceAspect, rowHeight, nodeSpacing, children]
    since: next
  - name: content
    title: Content
    home: control
    fields: [options, optionLabels, optionIcons, items, panels, listColumns, url, text, systemName, pucks, zones, scan, symbologies, itemTemplate, expand, trigger, mapConfig]
    since: next
  - name: behaviour
    title: Behaviour
    home: control
    fields: [min, max, step, editable, drag, draggable, drillDown, scrub, interactive, mapInteractive, webInteractive, webScrollEnabled, scrollable, searchable, sortKeys, sticky, wraps, discrete, autocorrect, autocorrectToggle, keyboard, sendButton, allowImages, allowReactions, allowReplies, allowClear, calendar, weekStartsOn, dateMin, dateMax, yMin, yMax, vMin, vMax, maxValue, criticalAbove, criticalBelow, reference, invertDelta, deltaMode, deadzone, tolerance, dwell, snap, maxZoom, zoomRange, mapZoom, torch, autoScroll, expandedIndex, flipTrigger, autoAdvance, loop, maxRows, variableMin, variableMax, weeks]
    since: next
  - name: internal
    title: Internal
    home: none
    fields: [type, id, theme, config, extensions, unsupportedType, field, role]
    since: next
internal: [type, id, theme, extensions, config, grid, paging, "*Config"]
canvas: [span, position, landscape, regular, children]
---

# Shared fields

A field that many controls describe the same way is written once, here, and each control doc points at it.
This file is the one place its type, range, default, title, hints and help live.

## Using a shared field

Inside a doc's `fields:` or `themeFields:`, write `- use: <name>` in place of the whole entry:

```
themeFields:
  - use: borderColor
  - use: cornerRadius
    does: Rounds the board's corners from square (0) to 30 points.
```

- `use:` looks the name up in the same section of this file: a `themeFields:` entry uses a shared theme key,
  a `fields:` entry uses a shared control field.
- The lines under `use:` override the shared entry. Only `default`, `min`, `max`, `step`, `summary`, `does`
  (when the effect on this control differs) and the version pins (`since`, `changes`, `deprecated`, `removed`,
  `alias`; control-def.md "Version pins") may be overridden. Any other key is a lint error, and so is an
  override that repeats the shared value.
- An unknown name is a lint error, and the field is left out of that doc.
- Both parsers expand `use:` when they load: the app's `ControlDocLoader` and carterkit's
  `catalog.parse_doc`. Every consumer (the inspector, the editor, carterkit, the MCP) sees the full field,
  exactly as if the doc had written it out.

## Adding or changing a shared field

Edit the entry here and every doc that uses it changes with it. To add one, write the full entry in the right
section, then run `scripts/migrate-shared-fields.py`: it lists every copy, and with `--write` it turns the
copies that already match (apart from the allowed overrides) into `use:` lines. A copy that differs anywhere
else is reported, never merged: the wording is the author's call. `--candidates 3` lists the fields copied
into three or more docs that have no shared entry yet.

This file has no `type:` or `label:`, so no parser treats it as a control.

## The editor's chips and categories

`chips:`, `categories:`, `internal:` and `canvas:` are the settings taxonomy
(docs/superpowers/specs/2026-11-06-settings-taxonomy.md): every field of every control resolves to one
category, and every category has one home in the control editor. Both parsers read them (the app's
`ControlDocLoader.taxonomy`, carterkit's `catalog.parse_taxonomy`), and `scripts/settings-taxonomy.py` reads the
same lists, so there is one copy.

- **A field's category** is the first that matches: its own `category:` (only where the lists are wrong for that
  control), a `theme:` list (a theme token; an unlisted colour token is `colour`, any other `look`), `internal`
  when it is deprecated or a container whose grouped leaves carry the editors, a `groups:` list, a `fields:`
  list, then the patterns (`suffixes:`, `prefixes:`, `types:`, in the order the categories are written). Left
  over, a bool is `behaviour`, a number or enum is `look` when it is a Style-tab or `scrub` / `look` field and
  `behaviour` otherwise, and anything else is `content`.
- **The bar** is at most five chips in a fixed order: the control chip, then the shared chips by `order`. A shared
  chip shows when the control has a field of one of its `categories` (`always: true` shows it on every control).
  `tap:` names the field the chip opens on (a `*` matches any prefix or suffix); the rest are rows in the chip's
  tray, drawn from each field's type. `petals:` are the hold petals, five at most: a name (or `a|b`, the first one
  the control has) is a shared petal, `own` the control's own petal fields (its `depth: hold` hints first) in the
  slots the shared ones leave. `petalTitles:` names a shared petal the same on every control. `aliases:` maps a
  doc field to the chip's field it is another name for: a control's `theme.cornerRadius` is the Background chip's
  Corners petal, so it lives there and never takes a row (aif-8whty.5).
- **The control chip** holds the `content` and `behaviour` fields (`home: control`). The doc names it on its first
  field, `chip: Range`; that field is the chip's tap.
- **Other homes.** `home: binding` fields are edited in the Binding view, `canvas:` fields on the canvas (place and
  size), and a `part` bool in the parts tray. `internal:` lists what has no editor on purpose (identity keys and
  containers); `ControlDocHintTests` and `EveryFieldHasAHomeTests` fail on any other field without a home.
