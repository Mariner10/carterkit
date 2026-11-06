---
type: theming
depth: complete
label: Theming
icon: paintbrush.pointed.fill
category: models
fields:
  - name: pageBackground
    type: color
    description: Page background
    summary: The solid colour behind the whole page
    does: Paints the page with one flat colour behind every control.
  - name: headerBackground
    type: color
    description: Header bar background
    summary: The colour of the top bar
    does: Fills the header bar with this colour in place of the default glass.
  - name: tabBarBackground
    type: color
    description: Tab bar background
    summary: The colour of the bottom tab bar
    does: Fills the tab bar strip with this colour.
  - name: tabBarTint
    type: color
    description: Tab bar selected tint
    summary: The colour of the selected tab
    does: Tints the selected tab icon and label; when unset the accent colour is used.
  - name: surfacePrimary
    type: color
    description: Card / control surface
    summary: The colour of cards and controls
    does: Fills cards and control backgrounds with this colour.
  - name: surfaceSecondary
    type: color
    description: Nested surface
    summary: The colour of things inside a card
    does: Fills surfaces nested inside a card, one level deeper than the card itself.
  - name: surfaceTertiary
    type: color
    description: Deepest surface
    summary: The colour of the deepest layer
    does: Fills the deepest nested surfaces, such as wells inside nested cards.
  - name: accentColor
    edit: color
    depth: surface
    type: color
    description: Primary accent
    summary: Your main highlight colour
    does: Colours gauges, toggles, sliders and other highlights, and the toggle, slider, stepper and progress tracks follow it unless they set their own.
  - name: foregroundColor
    type: color
    description: Primary text
    summary: The main text colour
    does: Draws primary text and icons in this colour; by default white in dark mode and black in light mode.
  - name: onAccent
    type: color
    description: Text/icon colour drawn on an accent fill
    summary: Text colour on top of accent fills
    does: Draws the text or icon on a filled accent button or band; unset, it picks white or black for the best contrast on each fill.
  - name: secondaryColor
    type: color
    description: Secondary text
    summary: The softer text colour
    does: Draws secondary text such as captions and sub-labels in this colour.
  - name: tertiaryColor
    type: color
    description: Tertiary text
    summary: The faintest text colour
    does: Draws the least prominent text, such as hints, in this colour.
  - name: borderColor
    type: color
    description: Border stroke
    summary: The colour of card outlines
    does: Strokes the outline of cards and controls in this colour.
  - name: statusOK
    type: color
    description: OK / success status colour
    summary: The good or success colour
    does: Colours success states such as a status light that is on, a good change and success log lines.
  - name: statusWarn
    type: color
    description: Warning status colour
    summary: The warning colour
    does: Colours warning states such as warn log lines and attention markers.
  - name: statusError
    type: color
    description: Error status colour
    summary: The error colour
    does: Colours error states such as a status light that is off, a bad change and error log lines.
  - name: statusInfo
    type: color
    description: Info status colour
    summary: The information colour
    does: Colours info log lines and other neutral notices.
  - name: scrimColor
    type: color
    description: Dimming scrim behind sheets and popups
    summary: The dimming colour behind pop-ups
    does: Dims the content behind chips, sheets and overlays; by default black at 35 percent in dark mode and white at 60 percent in light mode.
  - name: pageBackgroundGradient
    type: string[]
    description: Page background gradient (2+ colours)
    summary: A blend of colours behind the page
    does: Paints the page with a gradient running from top-left to bottom-right through the listed colours.
  - name: headerBackgroundGradient
    type: string[]
    description: Header background gradient (2+ colours)
    summary: A blend of colours in the top bar
    does: Fills the header bar with a gradient through the listed colours.
  - name: accentGradient
    type: string[]
    description: Accent gradient (2+ colours)
    summary: A blend of colours for highlights
    does: Fills accent areas with a gradient through the listed colours instead of one flat accent.
  - name: borderWidth
    min: 0
    max: 6
    step: 0.5
    type: number
    description: Border width
    summary: How thick card outlines are
    does: Sets the stroke width of card and control outlines, with 0 meaning no outline.
  - name: cornerRadius
    edit: scrub
    unit: pt
    depth: surface
    default: 12
    min: 0
    max: 40
    step: 1
    type: number
    description: Control/card corner radius
    summary: How round the corners are
    does: Rounds every card and control by this many points, and the smaller radii derive from it unless set.
  - name: controlPadding
    min: 0
    max: 32
    step: 1
    type: number
    description: Inner control padding
    summary: Space inside controls
    does: Sets the gap between a control's edge and its content, and the spacing rungs derive from it unless set.
  - name: cardPadding
    edit: scrub
    unit: pt
    depth: surface
    default: 12
    min: 0
    max: 32
    step: 1
    type: number
    description: Group card padding
    summary: Space inside group cards
    does: Sets the gap between a group card's edge and the controls inside it.
  - name: compactRadius
    min: 0
    max: 40
    step: 1
    type: number
    description: Radius for compact elements
    summary: Corner roundness for small bits
    does: Rounds small chips, badges and tick marks; unset, it is a third of the corner radius.
  - name: controlRadius
    min: 0
    max: 40
    step: 1
    type: number
    description: Radius for controls
    summary: Corner roundness for buttons and fields
    does: Rounds buttons, fields and inner controls; unset, it is two thirds of the corner radius.
  - name: cardRadius
    min: 0
    max: 40
    step: 1
    type: number
    description: Radius for group cards
    summary: Corner roundness for cards
    does: Rounds group cards and containers; unset, it follows the corner radius.
  - name: compactSpacing
    min: 0
    max: 32
    step: 1
    type: number
    description: Tight spacing
    summary: The tightest gap
    does: Sets small gaps inside a control; unset, it is half the control padding.
  - name: standardSpacing
    min: 0
    max: 48
    step: 1
    type: number
    description: Standard spacing
    summary: The normal gap
    does: Sets the default gap between the parts of a control; unset, it equals the control padding.
  - name: sectionSpacing
    min: 0
    max: 64
    step: 1
    type: number
    description: Spacing between sections
    summary: The big gap between sections
    does: Sets the gap between groups or sections; unset, it is twice the control padding.
  - name: emphasizedBorderWidth
    min: 0
    max: 8
    step: 0.5
    type: number
    description: Border width for emphasised elements
    summary: The thicker outline for emphasis
    does: Sets the stroke width used for emphasised lines such as chart outlines, heavier than the normal border.
  - name: labelFontSize
    min: 8
    max: 32
    step: 1
    type: number
    description: Label font size
    summary: Size of label text
    does: Sets the size of control labels in points.
  - name: valueFontSize
    min: 8
    max: 72
    step: 1
    type: number
    description: Value font size
    summary: Size of value text
    does: Sets the size of values shown on controls in points.
  - name: readoutFontSize
    min: 8
    max: 96
    step: 1
    type: number
    description: Big readout font size
    summary: Size of the big number
    does: Sets the size of the main readout in gauges and stat values in points.
  - name: captionFontSize
    min: 8
    max: 24
    step: 1
    type: number
    description: Caption font size
    summary: Size of small print
    does: Sets the size of captions and small print in points.
  - name: blurEnabled
    type: bool
    description: Glass material blur
    summary: Frosted-glass blur on or off
    does: Turns the blurred glass material behind cards on or off; off gives flat surfaces.
  - name: accent
    type: color
    description: Theme token. Accent colour; overrides the pack, loses to a control's own look
    summary: Pick one accent colour for the whole layout
    does: Sets the accent from a colour name or hex, over the theme pack but under a control's own look.
  - name: surface
    values: [glass, solid, paper]
    type: enum
    description: Theme token. Surface material
    summary: Glass, flat or paper cards
    does: Switches the card material for the whole layout.
    valueHelp: {"glass": "frosted translucent cards, the default look", "solid": "flat opaque grey cards with the blur turned off", "paper": "warm cream cards with the blur off and a hairline border"}
  - name: corners
    values: [sharp, soft, round]
    type: enum
    description: Theme token. Corner shape (4, 12 or 22 pt)
    summary: Sharp, soft or round corners
    does: Sets one corner shape for the whole layout, and the smaller radii follow it.
    valueHelp: {"sharp": "4 pt corners", "soft": "12 pt corners", "round": "22 pt corners"}
  - name: type
    values: [system, rounded, serif, mono]
    type: enum
    description: Theme token. Type face
    summary: The type style for the whole layout
    does: Switches every text to one type design, replacing a custom font family.
    valueHelp: {"system": "the normal system font", "rounded": "a rounded system font", "serif": "a serif font", "mono": "a monospaced font"}
  - name: density
    type: number
    min: 0.7
    max: 1.5
    step: 0.05
    description: Theme token. Padding scale
    summary: How roomy or tight things are
    does: Scales the control and card padding by this factor, so 0.7 is tighter and 1.5 is roomier.
  - name: fontFamily
    type: string
    description: Custom font family name (e.g. Times New Roman)
    summary: A custom font by name
    does: Draws text in the named font family instead of the system font.
  - name: fontDesign
    values: [default, rounded, serif, monospaced]
    type: enum
    description: Font design
    summary: The look of the system font
    does: Switches the system font between its default, rounded, serif and monospaced designs.
    valueHelp: {"default": "the normal system design", "rounded": "a rounded design", "serif": "a serif design", "monospaced": "a fixed-width design"}
  - name: valueFontWeight
    type: string
    description: Value font weight (e.g. semibold, bold)
    summary: How bold value text is
    does: Sets the weight of value text, for example semibold or bold.
  - name: toggle
    type: object
    description: Per-type toggle sub-theme; keys are the toggle group fields
    summary: Restyle every toggle
    does: Holds the toggle look keys that apply to all toggles in this scope.
  - name: slider
    type: object
    description: Per-type slider sub-theme; keys are the slider group fields
    summary: Restyle every slider
    does: Holds the slider look keys that apply to all sliders in this scope.
  - name: stepper
    type: object
    description: Per-type stepper sub-theme; keys are the stepper group fields
    summary: Restyle every stepper
    does: Holds the stepper look keys that apply to all steppers in this scope.
  - name: segmented
    type: object
    description: Per-type segmented sub-theme; keys are the segmented group fields
    summary: Restyle every segmented picker
    does: Holds the segmented look keys that apply to all segmented pickers in this scope.
  - name: progressBar
    type: object
    description: Per-type progressBar sub-theme; keys are the progressBar group fields
    summary: Restyle every progress bar
    does: Holds the progress bar look keys that apply to all progress bars in this scope.
  - name: light
    type: object
    description: Overrides applied last when the app is in light mode; keys are the schemeOverride group fields
    summary: Colours used only in light mode
    does: Applies these colour overrides last, only while the app is showing light mode.
  - name: dark
    type: object
    description: Overrides applied last when the app is in dark mode; keys are the schemeOverride group fields
    summary: Colours used only in dark mode
    does: Applies these colour overrides last, only while the app is showing dark mode.
  - name: palette
    type: object
    description: Named colours written once, referenced as $name in any colour field
    summary: Name your colours once
    does: Defines named colours that any colour field can reuse as a dollar-name reference.
    changes: [{in: next, note: "primary, secondary, tertiary and neutral are colour roles: a colour or a {light, dark} pair that controls' colour slots draw with"}]
  - name: primary
    group: palette
    type: color
    since: next
    description: Primary role colour, or a {light, dark} pair
    summary: Your main colour role
    does: Colours every slot that defaults to primary (a gauge arc, a button fill); unset, it is the accent colour.
  - name: secondary
    group: palette
    type: color
    since: next
    description: Secondary role colour, or a {light, dark} pair
    summary: A second colour for two-tone controls
    does: Colours slots and series entries that name secondary; unset, it is the primary colour.
  - name: tertiary
    group: palette
    type: color
    since: next
    description: Tertiary role colour, or a {light, dark} pair
    summary: A third colour for series and accents
    does: Colours slots and series entries that name tertiary; unset, it is the secondary colour.
  - name: neutral
    group: palette
    type: color
    since: next
    description: Neutral role colour, or a {light, dark} pair
    summary: The quiet colour for tracks and ticks
    does: Colours slots that default to neutral, such as tracks and grid lines at their own opacity; unset, it is the foreground colour.
  - name: pageBackground
    group: schemeOverride
    type: color
    description: Page background (scheme override)
    summary: The solid colour behind the whole page in this mode
    does: When the app is in this block's mode, paints the page with one flat colour behind every control.
  - name: headerBackground
    group: schemeOverride
    type: color
    description: Header bar background (scheme override)
    summary: The colour of the top bar in this mode
    does: When the app is in this block's mode, fills the header bar with this colour in place of the default glass.
  - name: tabBarBackground
    group: schemeOverride
    type: color
    description: Tab bar background (scheme override)
    summary: The colour of the bottom tab bar in this mode
    does: When the app is in this block's mode, fills the tab bar strip with this colour.
  - name: tabBarTint
    group: schemeOverride
    type: color
    description: Tab bar selected tint (scheme override)
    summary: The colour of the selected tab in this mode
    does: When the app is in this block's mode, tints the selected tab icon and label; when unset the accent colour is used.
  - name: surfacePrimary
    group: schemeOverride
    type: color
    description: Card / control surface (scheme override)
    summary: The colour of cards and controls in this mode
    does: When the app is in this block's mode, fills cards and control backgrounds with this colour.
  - name: surfaceSecondary
    group: schemeOverride
    type: color
    description: Nested surface (scheme override)
    summary: The colour of things inside a card in this mode
    does: When the app is in this block's mode, fills surfaces nested inside a card, one level deeper than the card itself.
  - name: surfaceTertiary
    group: schemeOverride
    type: color
    description: Deepest surface (scheme override)
    summary: The colour of the deepest layer in this mode
    does: When the app is in this block's mode, fills the deepest nested surfaces, such as wells inside nested cards.
  - name: accentColor
    group: schemeOverride
    type: color
    description: Primary accent (scheme override)
    summary: Your main highlight colour in this mode
    does: When the app is in this block's mode, colours gauges, toggles, sliders and other highlights, and the toggle, slider, stepper and progress tracks follow it unless they set their own.
  - name: foregroundColor
    group: schemeOverride
    type: color
    description: Primary text (scheme override)
    summary: The main text colour in this mode
    does: When the app is in this block's mode, draws primary text and icons in this colour; by default white in dark mode and black in light mode.
  - name: onAccent
    group: schemeOverride
    type: color
    description: Text/icon colour drawn on an accent fill (scheme override)
    summary: Text colour on top of accent fills in this mode
    does: When the app is in this block's mode, draws the text or icon on a filled accent button or band; unset, it picks white or black for the best contrast on each fill.
  - name: secondaryColor
    group: schemeOverride
    type: color
    description: Secondary text (scheme override)
    summary: The softer text colour in this mode
    does: When the app is in this block's mode, draws secondary text such as captions and sub-labels in this colour.
  - name: tertiaryColor
    group: schemeOverride
    type: color
    description: Tertiary text (scheme override)
    summary: The faintest text colour in this mode
    does: When the app is in this block's mode, draws the least prominent text, such as hints, in this colour.
  - name: borderColor
    group: schemeOverride
    type: color
    description: Border stroke (scheme override)
    summary: The colour of card outlines in this mode
    does: When the app is in this block's mode, strokes the outline of cards and controls in this colour.
  - name: statusOK
    group: schemeOverride
    type: color
    description: OK / success status colour (scheme override)
    summary: The good or success colour in this mode
    does: When the app is in this block's mode, colours success states such as a status light that is on, a good change and success log lines.
  - name: statusWarn
    group: schemeOverride
    type: color
    description: Warning status colour (scheme override)
    summary: The warning colour in this mode
    does: When the app is in this block's mode, colours warning states such as warn log lines and attention markers.
  - name: statusError
    group: schemeOverride
    type: color
    description: Error status colour (scheme override)
    summary: The error colour in this mode
    does: When the app is in this block's mode, colours error states such as a status light that is off, a bad change and error log lines.
  - name: statusInfo
    group: schemeOverride
    type: color
    description: Info status colour (scheme override)
    summary: The information colour in this mode
    does: When the app is in this block's mode, colours info log lines and other neutral notices.
  - name: scrimColor
    group: schemeOverride
    type: color
    description: Dimming scrim behind sheets and popups (scheme override)
    summary: The dimming colour behind pop-ups in this mode
    does: When the app is in this block's mode, dims the content behind chips, sheets and overlays; by default black at 35 percent in dark mode and white at 60 percent in light mode.
  - name: pageBackgroundGradient
    group: schemeOverride
    type: string[]
    description: Page background gradient (2+ colours) (scheme override)
    summary: A blend of colours behind the page in this mode
    does: When the app is in this block's mode, paints the page with a gradient running from top-left to bottom-right through the listed colours.
  - name: headerBackgroundGradient
    group: schemeOverride
    type: string[]
    description: Header background gradient (2+ colours) (scheme override)
    summary: A blend of colours in the top bar in this mode
    does: When the app is in this block's mode, fills the header bar with a gradient through the listed colours.
  - name: accentGradient
    group: schemeOverride
    type: string[]
    description: Accent gradient (2+ colours) (scheme override)
    summary: A blend of colours for highlights in this mode
    does: When the app is in this block's mode, fills accent areas with a gradient through the listed colours instead of one flat accent.
  - name: trackColor
    group: toggle
    type: color
    description: Track colour (off)
    summary: Toggle colour when off
    does: Fills the toggle's track while the switch is off.
  - name: trackActiveColor
    group: toggle
    type: color
    description: Track colour (on)
    summary: Toggle colour when on
    does: Fills the toggle's track while the switch is on; it follows the accent when unset.
  - name: trackRadius
    group: toggle
    min: 0
    max: 30
    step: 1
    type: number
    description: Track corner radius
    summary: How round the toggle track is
    does: Rounds the corners of the toggle's track.
  - name: trackHeight
    group: toggle
    min: 8
    max: 60
    step: 1
    type: number
    description: Track height
    summary: How tall the toggle is
    does: Sets the height of the toggle's track in points.
  - name: trackWidth
    group: toggle
    min: 20
    max: 100
    step: 1
    type: number
    description: Track width
    summary: How wide the toggle is
    does: Sets the width of the toggle's track in points.
  - name: knobColor
    group: toggle
    type: color
    description: Knob colour (off)
    summary: Knob colour when off
    does: Fills the sliding knob while the switch is off.
  - name: knobActiveColor
    group: toggle
    type: color
    description: Knob colour (on)
    summary: Knob colour when on
    does: Fades the knob to this colour as the switch moves to on.
  - name: knobRadius
    group: toggle
    min: 0
    max: 30
    step: 1
    type: number
    description: Knob corner radius
    summary: How round the knob is
    does: Rounds the corners of the toggle's knob.
  - name: knobSize
    group: toggle
    min: 8
    max: 50
    step: 1
    type: number
    description: Knob diameter
    summary: How big the knob is
    does: Sets the diameter of the toggle's knob in points.
  - name: knobShadow
    group: toggle
    type: bool
    description: Draw a shadow under the knob
    summary: Shadow under the knob
    does: Draws or hides a soft shadow beneath the toggle knob.
  - name: trackColor
    group: slider
    type: color
    description: Track colour
    summary: Slider track colour
    does: Fills the unfilled part of the slider's track.
  - name: trackActiveColor
    group: slider
    type: color
    description: Filled track colour
    summary: Slider filled colour
    does: Fills the part of the slider's track up to the thumb; it follows the accent when unset.
  - name: trackRadius
    group: slider
    min: 0
    max: 10
    step: 1
    type: number
    description: Track corner radius
    summary: How round the slider track is
    does: Rounds the corners of the slider's track.
  - name: trackHeight
    group: slider
    min: 2
    max: 20
    step: 1
    type: number
    description: Track height
    summary: How thick the slider track is
    does: Sets the height of the slider's track in points.
  - name: thumbColor
    group: slider
    type: color
    description: Thumb colour
    summary: Slider handle colour
    does: Fills the draggable thumb of the slider.
  - name: thumbRadius
    group: slider
    min: 0
    max: 20
    step: 1
    type: number
    description: Thumb corner radius
    summary: How round the handle is
    does: Rounds the corners of the slider's thumb.
  - name: thumbSize
    group: slider
    min: 8
    max: 40
    step: 1
    type: number
    description: Thumb diameter
    summary: How big the handle is
    does: Sets the diameter of the slider's thumb in points.
  - name: thumbShadow
    group: slider
    type: bool
    description: Draw a shadow under the thumb
    summary: Shadow under the handle
    does: Draws or hides a soft shadow beneath the slider thumb.
  - name: thumbBorderColor
    group: slider
    type: color
    description: Thumb border colour
    summary: Outline colour of the handle
    does: Strokes the edge of the slider thumb in this colour.
  - name: thumbBorderWidth
    group: slider
    min: 0
    max: 6
    step: 0.5
    type: number
    description: Thumb border width
    summary: Outline thickness of the handle
    does: Sets how thick the thumb's outline is; 0 draws none.
  - name: buttonColor
    group: stepper
    type: color
    description: Button fill colour
    summary: Stepper button colour
    does: Fills the plus and minus buttons; it follows the accent when unset.
  - name: buttonRadius
    group: stepper
    min: 0
    max: 30
    step: 1
    type: number
    description: Button corner radius
    summary: How round the stepper buttons are
    does: Rounds the corners of the plus and minus buttons.
  - name: buttonSize
    group: stepper
    min: 20
    max: 64
    step: 1
    type: number
    description: Button size
    summary: How big the stepper buttons are
    does: Sets the size of the plus and minus buttons in points.
  - name: iconColor
    group: stepper
    type: color
    description: Plus/minus icon colour
    summary: Colour of the plus and minus
    does: Draws the plus and minus symbols in this colour.
  - name: style
    group: stepper
    type: string
    description: Stepper style variant
    summary: Which stepper layout to use
    does: Names a stepper layout variant, horizontal unless set.
  - name: trackColor
    group: segmented
    type: color
    description: Track colour
    summary: Segmented picker background
    does: Fills the strip behind all the segments.
  - name: trackRadius
    group: segmented
    min: 0
    max: 30
    step: 1
    type: number
    description: Track corner radius
    summary: How round the strip is
    does: Rounds the corners of the strip behind the segments.
  - name: selectedColor
    group: segmented
    type: color
    description: Selected segment fill
    summary: Colour of the chosen segment
    does: Fills the pill behind the selected segment.
  - name: selectedRadius
    group: segmented
    min: 0
    max: 30
    step: 1
    type: number
    description: Selected segment corner radius
    summary: How round the chosen pill is
    does: Rounds the corners of the selected segment's pill.
  - name: selectedShadow
    group: segmented
    type: bool
    description: Draw a shadow under the selected segment
    summary: Shadow under the chosen segment
    does: Draws or hides a soft shadow beneath the selected segment's pill.
  - name: textColor
    group: segmented
    type: color
    description: Segment text colour
    summary: Text colour of unchosen segments
    does: Draws the labels of segments that are not selected.
  - name: selectedTextColor
    group: segmented
    type: color
    description: Selected segment text colour
    summary: Text colour of the chosen segment
    does: Draws the selected segment's label; unset, it picks black or white to suit the pill.
  - name: trackColor
    group: progressBar
    type: color
    description: Track colour
    summary: Progress bar background
    does: Fills the empty part of the progress bar.
  - name: trackActiveColor
    group: progressBar
    type: color
    description: Filled track colour
    summary: Progress bar fill colour
    does: Fills the completed part of the progress bar; it follows the accent when unset.
  - name: trackRadius
    group: progressBar
    min: 0
    max: 20
    step: 1
    type: number
    description: Track corner radius
    summary: How round the bar is
    does: Rounds the corners of the progress bar's track.
  - name: trackHeight
    group: progressBar
    min: 2
    max: 30
    step: 1
    type: number
    description: Track height
    summary: How thick the bar is
    does: Sets the height of the progress bar in points.
---

The `theme` block on a [[layout-config|layout]] controls colors, fonts, spacing, and per-control-type styling. Every control resolves its appearance from the active theme, and any control can override it locally via its own `theme` field.

The live builder above re-themes a small demo layout as you change values — flip light/dark, pick an accent, and adjust the shape, then copy the generated `theme` block.

## Base Fields

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `accentColor` | color | `#667eea` | Primary accent (gauges, toggles, highlights) |
| `accentGradient` | color[] | — | 2+ color accent gradient |
| `foregroundColor` | color | auto | Primary text (auto: white in dark, black in light) |
| `onAccent` | color | auto | Text/icon colour drawn ON an accent or tint fill (filled buttons, solid stat-tile bands). Auto: white, or black when white would fall under 3:1 on that fill (so `#FFD60A` gets dark ink, `#0A84FF` white). Set it to force one ink everywhere |
| `secondaryColor` | color | auto | Secondary text |
| `tertiaryColor` | color | auto | Tertiary text |
| `surfacePrimary` | color | auto | Card / control surface |
| `surfaceSecondary` | color | auto | Nested surface |
| `surfaceTertiary` | color | auto | Deepest surface |
| `borderColor` | color | auto | Border stroke |
| `borderWidth` | number | `1` | Border width |
| `cornerRadius` | number | `12` | Control/card corner radius |
| `controlPadding` | number | `8` | Inner control padding |
| `cardPadding` | number | `12` | Group card padding |
| `blurEnabled` | bool | `true` | Glass material blur |
| `fontFamily` | string | — | Custom font (e.g. `"Times New Roman"`) |
| `fontDesign` | string | `default` | `default`, `rounded`, `serif`, `monospaced` |
| `labelFontSize` | number | `12` | Label text size |
| `valueFontSize` | number | `14` | Value text size |
| `valueFontWeight` | string | `semibold` | Value weight |
| `readoutFontSize` | number | `17` | Primary readout size (gauge and stat values) |
| `captionFontSize` | number | `11` | Caption and small-print size |
| `statusOK` | color | `#34C759` | Success: status light on, good delta, log `success` |
| `statusWarn` | color | `#FF9500` | Warning: log `warn`, attention states |
| `statusError` | color | `#FF453A` | Error: status light off, bad delta, log `error` |
| `statusInfo` | color | `#5AC8FA` | Info: log `info` |
| `scrimColor` | color | auto | Wash behind chips and overlays (dark: black 35%, light: white 60%) |

Content tokens only: app chrome (`chrome*`, `glassWave`) is not a layout key and stays with the app.

### Shape & Spacing Ladder

Controls draw from a small scale of radii and spacings rather than one-off numbers.
Every rung is optional. Unset, it derives from the base fields above, so a layout that
sets only `cornerRadius` or `controlPadding` keeps today's look.

| Field | Type | Default (derived) | Description |
|-------|------|-------------------|-------------|
| `compactRadius` | number | `cornerRadius / 3` (`4`) | Small chips, badges, tick marks |
| `controlRadius` | number | `cornerRadius * 2 / 3` (`8`) | Buttons, fields, inner controls |
| `cardRadius` | number | `cornerRadius` (`12`) | Cards and group containers |
| `compactSpacing` | number | `controlPadding / 2` (`4`) | Tight gaps inside a control |
| `standardSpacing` | number | `controlPadding` (`8`) | Default gap between control parts |
| `sectionSpacing` | number | `controlPadding * 2` (`16`) | Gap between groups or sections |
| `emphasizedBorderWidth` | number | `1.5` | The one emphasis stroke beyond `borderWidth` |

Colors are hex strings and may include alpha: `"#RRGGBB"` or `"#RRGGBBAA"`.

## Light & Dark Variants

Most palettes differ between modes. Put scheme-sensitive colors in `light` / `dark` sub-objects — they are applied **last**, on top of the base, for the active mode. Keep scheme-neutral values (accent, radius, fonts) in the base.

```json
{
"theme": {
  "accentColor": "#5AC8FA",
  "cornerRadius": 16,
  "fontDesign": "rounded",
  "dark": {
    "pageBackgroundGradient": ["#0A0F1E", "#0E1A33"],
    "surfacePrimary": "#FFFFFF12",
    "foregroundColor": "#FFFFFF",
    "borderColor": "#FFFFFF1F"
  },
  "light": {
    "pageBackgroundGradient": ["#EAF0FB", "#D7E3F4"],
    "surfacePrimary": "#FFFFFFF2",
    "foregroundColor": "#0B1220",
    "borderColor": "#0B122014"
  }
}
}
```

A `light` / `dark` block accepts: `pageBackground`, `pageBackgroundGradient`, `headerBackground`, `headerBackgroundGradient`, `tabBarBackground`, `tabBarTint`, `surfacePrimary/Secondary/Tertiary`, `foregroundColor`, `onAccent`, `secondaryColor`, `tertiaryColor`, `borderColor`, `accentColor`, `accentGradient`, `statusOK`, `statusWarn`, `statusError`, `statusInfo`, `scrimColor`.

> The whole app stays in lockstep with the device color scheme — see [[appearance]] for `colorScheme`.

**System layouts carry both palettes.** With `colorScheme: system` (or none) the layout follows the device, so a palette written for one scheme breaks contrast in the other. The editor keeps such a layout balanced: scheme-sensitive colours live in `light` and `dark`, both blocks colour the same slots, and in each the text clears 4.5:1 on the page and the accent 3:1 (a missing palette is derived from the other, same hue with the lightness flipped). A layout that sets no page colours keeps the built-in palettes, which already flip. Layouts pinned to `dark` or `light` are not touched.

## Page & Chrome

| Key | Type | Description |
|-----|------|-------------|
| `pageBackground` | color | Solid page background |
| `pageBackgroundGradient` | color[] | Page gradient (top-leading → bottom-trailing) |
| `tabBarBackground` | color | Tab bar fill |
| `tabBarTint` | color | Tab bar icon tint |

Header chrome lives in [[appearance]] (`appearance.header`), not the theme.

## Per-Type Sub-Themes

Fine-tune a whole control family. Each is an object under the theme:

| Sub-theme | Notable keys |
|-----------|--------------|
| `toggle` | `trackColor`, `trackActiveColor`, `knobColor`, `trackWidth`, `trackHeight`, `knobSize`, `knobShadow` |
| `slider` | `trackColor`, `trackActiveColor`, `thumbColor`, `thumbSize`, `thumbBorderColor`, `trackHeight` |
| `stepper` | `buttonColor`, `iconColor`, `buttonSize`, `style` |
| `segmented` | `trackColor`, `selectedColor`, `textColor`, `selectedTextColor` |
| `progressBar` | `trackColor`, `trackActiveColor`, `trackHeight` |

```json
{
"theme": {
  "toggle": { "trackActiveColor": "#34C759", "knobShadow": true },
  "slider": { "thumbColor": "#FFFFFF", "trackActiveColor": "#5AC8FA" }
}
}
```

## Per-Control Overrides

Any control can override the theme for itself via its `theme` field — same keys as above plus its family's per-type keys. See [[control-def]]. A [[group-def|group]] takes the same `theme` object and hands it to everything inside it.

## Palette Tokens

Name your colours once in `theme.palette`, then write `"$name"` in any colour field instead of a hex. Recolouring the layout ("make it blue") is then a one-key edit: change the palette entry and every field that refers to it follows.

```json
{
"theme": {
  "palette": { "brand": "#0A84FF", "leaf": "#34C759", "ink": "#101418" },
  "accentColor": "$brand",
  "pageBackgroundGradient": ["$ink", "#1C2230"],
  "dark": { "foregroundColor": "$leaf" }
}
}
```

```json
{ "type": "gauge", "id": "c_soil", "tint": "$leaf", "theme": { "trackColor": "$ink" } }
```

- **Where refs work**: any string in a colour position — a key that names a colour (`tint`, `accentColor`, `*Color`, `*Background`, `*Gradient`, `colors`, `fill`, `stroke`), each element of an array under such a key, anything inside a `theme` object (layout, [[group-def|group]] or control, including `light`/`dark` and the per-type sub-themes), and the [[appearance]] `header` fills. A ref in the [[document-contract|`styles` section]] resolves exactly like one written inline.
- **Never rewritten**: labels, text and other non-colour strings, and the wire blocks (`sync`, `action`, `longPressAction`, `connection`, `sources`, `alerts`, `publishers`, `extensions`). A label of `"$brand"` stays `"$brand"`.
- **Palette values** are literal colours (the same hex forms as everywhere else). A value that is itself a `$ref`, is not a string, or has a name other than letters, digits, `_` and `-` is ignored with a warning. Up to 64 tokens.
- **Unknown tokens** (`"$nope"`) never crash and never render black: the field is dropped with a warning ("Repaired on load" in the Layout Hub) and falls back to whatever it would inherit.
- **Resolution happens at load**. The saved file keeps the `$name` refs, so editors (the designer, carterkit, the MCP) edit tokens, not the hexes behind them. Children pushed at runtime into a `dynamic` group or tab resolve against the active layout's palette the same way, with the same unknown-token fallback.
- **Lint**: carterkit's `validate_layout` and the MCP warn when a raw colour equals a palette token and suggest the `$name`.

Starting palettes: the playbook theme packs in `layout-library/playbook/themes/<slug>.theme.json` (24 packs of `{theme, appearance, accentColor}`) are the presets; copy one's `theme` and name its colours. Each of the 19 packs has a doc in `ControlDocs/themes/<slug>.md` whose frontmatter carries its vibe words, accent, light/dark notes, when to use, specimen reference and the `tokens` object to copy. The numeric style rules (one accent, card alpha `0F`-`24`, `cornerRadius` 14-16, `controlPadding` 12 or less, 10 rows on iPhone, the `64n - 8` cell height, light/dark parity) are in [[style-rules]].

## Colour roles

Four names in `palette` are **roles**: `primary`, `secondary`, `tertiary` and `neutral`. A control's doc lists the colours it draws as **colour slots** (a gauge's `arc` and `track`, a chart's `series`), each with a default role, and a layout repaints a slot through the control's `colors` key. Change a role and every slot that follows it changes with it.

```json
{
"theme": {
  "palette": {
    "primary": "#0A84FF",
    "secondary": { "light": "#C2410C", "dark": "#FF9F0A" },
    "neutral": { "light": "#334155", "dark": "#CBD5E1" }
  }
}
}
```

```json
{ "type": "gauge", "id": "c_cpu", "colors": { "arc": "secondary", "track": "neutral@0.2" } }
```

- **A role's value** is a colour, or `{ "light": colour, "dark": colour }` for the two schemes (one side alone covers both). Role values are literal colours, like every palette value.
- **Where palettes go**: the layout's `theme.palette`, a tab's `palette` (same object, for that page), a [[group-def|group]]'s or a control's `theme.palette`. The nearest level that names a role wins, role by role. A group or control that sets its own `accentColor` but no `palette.primary` gets primary back from that accent.
- **Unset roles** keep today's look: `primary` is the accent colour, `secondary` is `primary`, `tertiary` is `secondary`, and `neutral` is the foreground colour. A layout without roles draws exactly what it drew before roles existed.
- **A slot value** in `colors` (and a slot's default in its doc) is a role, a role at an opacity (`neutral@0.12`), a theme colour key (`accentColor`, `foregroundColor`, `secondaryColor`, `tertiaryColor`, `surfacePrimary`, `surfaceSecondary`, `surfaceTertiary`, `borderColor`, `trackColor`, `statusOK`, `statusWarn`, `statusError`, `statusInfo`, `scrimColor`, opacity allowed too), a `$name` token or a colour. A value that does not resolve falls back to the slot's default.
- **Series**: a series slot takes an ordered list, `"colors": { "series": ["primary", "secondary", "#FF9F0A"] }`, or the bare list `"colors": ["primary", "secondary"]`. Series colours go to series in order.
- **Old keys still work**: each slot names the existing key that also sets it (its `alias`, such as `tint`). A slot draws its `colors` entry first, then the old key, then its default.
- **`$name` is not a role**: `"$primary"` reads a plain `primary` colour at load, once for both schemes. A role written as `{light, dark}` is not a token, so write `primary` (no `$`) in `colors` to follow the scheme.

Control docs declare their slots in frontmatter (`colorSlots:`, see [[control-def]] "Colour slots"). `ResolvedTheme.resolve(slot:of:)` is the one resolver; the controls move onto their slots in stages.

## Cascade

What a control finally draws with, from lowest to highest priority. This is the order `ResolvedTheme` and `GridRenderer` actually apply (pinned by the app's `PaletteTokenTests.cascadeTable`):

| # | Level | Where | Notes |
|---|-------|-------|-------|
| 1 | Built-in defaults | — | Dark glass palette, accent `#667eea` |
| 2 | Light palette | [[appearance]] `colorScheme` | When the layout renders light: black ink, light page `#F2F2F7`, light tracks. Never overrides a key the theme sets |
| 3 | Layout theme | `theme` | The base keys above. Per-type sub-themes (`toggle`, `slider`, `stepper`, `progressBar`) follow the accent unless they set their own colours |
| 4 | Scheme override | `theme.light` / `theme.dark` | Applied last at the layout level, for the active mode only. Its `accentColor` also becomes the accent the per-type tracks follow in that mode (a sub-theme's own colours still win) |
| 5 | Group theme | group `theme` | Applied over 4 for the group's label, card and every child, recursively through nested groups |
| 6 | Control theme | control `theme` | Applied over 5 for that control. An `accentColor` here also re-points the toggle / slider / stepper / progress tracks that were following the accent |
| 7 | Control tint | control `tint` | Most controls draw their accent as `tint ?? theme accent`, so `tint` beats even the control's own `theme.accentColor` |

Two colour settings are **not** part of the cascade:
- The top-level [[layout-config]] `accentColor` tints the layout's card in the library, the layout switcher and the [[glance]] fallback. It does not colour controls inside the layout; set `theme.accentColor` for that.
- [[appearance]] holds the colour **scheme** and the header fills, not control colours.

Theming levels 3–6 are Pro features: without Pro the layout renders with the default glass theme (level 1–2) and the `theme` fields are ignored. `tint` always applies.

## Examples

### One-accent dark layout
Sets a single accent, rounder corners and a rounded font, with a dark page gradient that only applies in dark mode.
```json
{
  "theme": {
    "accentColor": "#5AC8FA",
    "cornerRadius": 16,
    "fontDesign": "rounded",
    "dark": {
      "pageBackgroundGradient": ["#0A0F1E", "#0E1A33"],
      "foregroundColor": "#FFFFFF"
    }
  }
}
```

### Palette tokens
Names colours once in `palette` so changing one entry recolours every field that uses it.
```json
{
  "theme": {
    "palette": { "brand": "#0A84FF", "ink": "#101418" },
    "accentColor": "$brand",
    "pageBackgroundGradient": ["$ink", "#1C2230"]
  }
}
```

### Colour roles
Gives the layout a blue primary and a scheme-aware orange secondary; the Home tab's own palette makes primary green on that page, and one gauge's arc follows the secondary role.
```json
{
  "theme": {
    "palette": {
      "primary": "#0A84FF",
      "secondary": { "light": "#C2410C", "dark": "#FF9F0A" }
    }
  },
  "tabs": [
    {
      "title": "Home",
      "icon": "house",
      "grid": { "columns": 4, "rows": 6 },
      "palette": { "primary": "#34C759" },
      "children": [
        { "type": "gauge", "id": "c_cpu", "position": [0, 0], "span": [2, 2], "label": "CPU", "colors": { "arc": "secondary" } }
      ]
    }
  ]
}
```

### Quick tokens
Uses the short theme tokens to switch to paper cards, sharp corners, a serif face and a tighter density.
```json
{
  "theme": {
    "accent": "orange",
    "surface": "paper",
    "corners": "sharp",
    "type": "serif",
    "density": 0.85
  }
}
```

### Per-type sub-themes
Restyles every toggle, slider and progress bar in one place.
```json
{
  "theme": {
    "toggle": { "trackActiveColor": "#34C759", "knobShadow": false },
    "slider": { "thumbColor": "#FFFFFF", "trackHeight": 6 },
    "progressBar": { "trackActiveColor": "#5AC8FA", "trackHeight": 10 }
  }
}
```

## Related
- [[style-rules]] — Machine-checkable style rules from the playbook
- [[appearance]] — Color scheme, header, status bar, background image
- [[layout-config]] — Where `theme` lives
- [[control-def]] — Per-control `theme` overrides
- [[group-def]] — Group `theme` overrides and theme surfaces on group cards
- [[document-contract]] — The `styles` section, where per-control `theme`/`tint` may live
