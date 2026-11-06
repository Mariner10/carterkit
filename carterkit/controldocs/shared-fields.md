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
