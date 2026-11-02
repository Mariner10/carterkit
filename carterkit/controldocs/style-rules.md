---
type: style-rules
label: Style Rules
icon: checkmark.seal.fill
category: style
scope: house packs (Midnight, Grouped) and any layout that does not name an art-direction pack; the art-direction packs in themes/ may break shape rules on purpose and say so in their own frontmatter
source: layout-library/playbook chapters 01, 03, 04, 05, 06, 08, 10, 11, 12, 13, 16
rules:
  - id: one-accent
    area: color
    check: Every control resolves to one accent hue; status colours (ok, warn, error, info) are excepted
    target: theme.accentColor, theme.light.accentColor, theme.dark.accentColor, control tint
    op: distinctAccentHues
    threshold: 1
    severity: error
    why: Two accents split the eye; the page carries hue and the accent marks only what is live or tappable (ch01, ch16 Restraint)
  - id: accent-same-both-schemes
    area: color
    check: The accent hue is identical in light and dark
    target: theme.light.accentColor == theme.dark.accentColor
    op: equals
    threshold: 0
    severity: warn
    why: Sub-themes are frozen before the scheme block lands, so a per-scheme accent leaves tracks on the old hue (ch02, ch12)
  - id: accent-not-foreground
    area: color
    check: accentColor differs from foregroundColor and reaches 3:1 on both pages
    target: theme.accentColor vs theme.foregroundColor and page stops
    op: contrastMin
    threshold: 3.0
    severity: error
    why: An accent equal to the ink makes stepper icons and filled-button labels vanish at 1.0:1 (ch03, ch16 one-star)
  - id: card-alpha-dark
    area: surface
    check: Dark surfacePrimary alpha byte, hex 0F to 24 (6% to 14%)
    target: theme.dark.surfacePrimary alpha
    op: alphaByteRange
    threshold: "0x0F-0x24"
    severity: warn
    why: Below 0F the card disappears, above 24 it becomes a slab; 28 to 3F scores 3 stars, 40 and up scores 2 (ch03, ch16)
  - id: card-border-width
    area: surface
    check: borderWidth 1 or less
    target: theme.borderWidth
    op: max
    threshold: 1
    severity: warn
    why: Heavier strokes read as decoration; hairlines at 10% (dark) or 12% (light) are the house edge (ch03, ch16)
  - id: corner-radius
    area: shape
    check: cornerRadius from 14 to 16 (house packs)
    target: theme.cornerRadius
    op: range
    threshold: "14-16"
    severity: info
    why: Matches the iOS glass chrome around the grid; art-direction packs may set 0 to 20 deliberately (ch01)
  - id: control-padding
    area: shape
    check: controlPadding 12 or less
    target: theme.controlPadding
    op: max
    threshold: 12
    severity: warn
    why: 16 and up shrinks the content area of a 56 pt cell and scores 2 stars on Restraint (ch01, ch16)
  - id: no-card-in-card
    area: surface
    check: A group card holds controls with hideBackground, not nested cards
    target: group children without hideBackground that draw their own surface
    op: noNestedCards
    threshold: 0
    severity: warn
    why: Double surfaces muddy the alpha ladder and break the one-hero rule (ch06, ch16 Restraint)
  - id: max-rows-iphone
    area: grid
    check: At most 10 rows per tab on iPhone
    target: tabs[].grid.rows
    op: max
    threshold: 10
    severity: error
    why: 10 rows is 648 pt in a 665 pt viewport; row 11 sits under the fold (ch05, ch06). iPad-first layouts may use 15
  - id: cell-height-64n-8
    area: grid
    check: A cell spanning n rows is n x rowHeight + (n - 1) x 8 pt tall, which is 64n - 8 at the default rowHeight 56
    target: control.span[0], grid.rowHeight
    op: cellHeight
    threshold: "rowSpan*rowHeight+(rowSpan-1)*8"
    severity: info
    why: The 8 pt gutter is fixed and not themeable; knowing the height before rendering is what lets a layout be sized in points (ch05)
  - id: group-rows
    area: grid
    check: A group has ceil((contentHeight + 8) / 64) rows or more
    target: group.span[0]
    op: minRows
    threshold: "ceil((content+8)/64)"
    severity: warn
    why: A group sized below its content clips or crushes its children (ch05)
  - id: one-row-outgrow
    area: grid
    check: A toggle, stepper, picker, statusLight or compact datePicker on the 56 pt grid spans 2 rows or more
    target: control.span[0] for those types
    op: min
    threshold: 2
    severity: warn
    why: These draw a card taller than 56 pt; at rowSpan 1 it grows into the gutter and touches its neighbour (ch05, ch07)
  - id: one-hero-per-tab
    area: composition
    check: One control per tab spans 3 to 5 rows; every other control is 3 rows or fewer
    target: tabs[].children[].span[0]
    op: maxHeroCount
    threshold: 1
    severity: warn
    why: Two heroes compete; demote one to a 2-row tile or move it to its own tab (ch08)
  - id: tab-count
    area: chrome
    check: 2 to 5 tabs, each with at least one control
    target: tabs
    op: range
    threshold: "2-5"
    severity: warn
    why: An empty tab or a tab promised and not delivered scores Truth 2 (ch13, ch16). A single-page layout may use one tab
  - id: header-title-format
    area: chrome
    check: headerTitle is WORD · QUALIFIER in capitals, 14 to 18 characters
    target: headerTitle
    op: lengthRange
    threshold: "14-18"
    severity: info
    why: Fits the roughly 222 pt left in the header capsule once the keep-awake sun takes its share (ch13)
  - id: light-dark-parity
    area: parity
    check: Either appearance.colorScheme is pinned, or both theme.light and theme.dark set pageBackground, surfacePrimary, foregroundColor and borderColor
    target: appearance.colorScheme, theme.light, theme.dark
    op: parityComplete
    threshold: 4
    severity: error
    why: A one-scheme page left on system renders black on black in the other mode (ch12, ch16 Parity)
  - id: text-contrast
    area: legibility
    check: Text under 24 pt reaches 4.5:1 against the card-over-page composite on every gradient stop, in both schemes
    target: foregroundColor, secondaryColor vs surfacePrimary over page stops
    op: contrastMin
    threshold: 4.5
    severity: error
    why: Ship bar is Legibility 4; the weakest gradient stop sets the ratio (ch16)
  - id: large-text-icon-contrast
    area: legibility
    check: Readouts of 24 pt and up, icons, knobs and gauge arcs reach 3:1
    target: accentColor, tertiaryColor (axis ticks) vs backdrop
    op: contrastMin
    threshold: 3.0
    severity: warn
    why: Tertiary draws chart axis text; at 40% alpha it was 2.3:1, so 65% to 70% is the floor (ch04, midnight pack)
  - id: dark-page-luminance
    area: color
    check: Dark-scheme page gradient stops have relative luminance under 15%
    target: theme.dark.pageBackgroundGradient
    op: maxLuminance
    threshold: 0.15
    severity: warn
    why: A bright stop washes out white ink; the page carries hue, kept dark (ch03)
  - id: caption-size
    area: type
    check: Caption text 11 to 12 pt
    target: theme.captionFontSize, theme.labelFontSize
    op: range
    threshold: "11-12"
    severity: info
    why: Span, not valueFontSize, sizes the hero numbers (ch04)
  - id: one-type-voice
    area: type
    check: One fontDesign or fontFamily per layout
    target: theme.fontDesign, theme.fontFamily
    op: singleValue
    threshold: 1
    severity: info
    why: Mixing voices reads as accident; rendered once and kept (ch04)
  - id: animation-profile-enum
    area: motion
    check: animation.profile is one of smooth, snappy, bouncy, gentle, instant
    target: control.animation.profile
    op: enum
    threshold: "smooth|snappy|bouncy|gentle|instant"
    severity: error
    why: A typo is fatal, the control drops its animation block (ch11, animations doc)
  - id: pulse-spread
    area: motion
    check: pulse.spread at most 0.1 (22 pt)
    target: pulse.spread
    op: max
    threshold: 0.1
    severity: warn
    why: A wider ring spills into neighbouring cards (ch11)
  - id: alarm-twin
    area: state
    check: Nominal and alarm looks are two twins at the same position and span with complementary visibility conditions; red only on the twin that shows a fault
    target: visibility conditions on controls sharing position and span
    op: complementaryTwins
    threshold: 2
    severity: info
    why: Styling never drives state; the value does (ch10)
  - id: ship-bar
    area: review
    check: Every rubric axis (Legibility, Rhythm, Restraint, Parity, Truth) scores 4 or more; the layout scores its lowest axis
    target: rubric scores
    op: minOfAxes
    threshold: 4
    severity: info
    why: One invisible button makes a one-star layout, however good the gauges look (ch16)
---

# Style rules

Machine-checkable rules distilled from the 16-chapter playbook. Each rule in the frontmatter names the thing it checks (`check`), the layout path it reads (`target`), the comparison (`op`), the limit (`threshold`), how loud a breach is (`severity`), and the reason (`why`) with the playbook chapter it comes from.

Use them in this order when you build a layout:

1. Choose the pack in [[theming]] and the `themes/` docs, then keep to **one accent** in both schemes (`one-accent`, `accent-same-both-schemes`).
2. Hold the surfaces to the house ladder: card alpha `0F` to `24` in dark, `borderWidth` 1 or less, `cornerRadius` 14 to 16, `controlPadding` 12 or less.
3. Size the grid in points: a cell `n` rows tall is `64n - 8` at the default `rowHeight` of 56, and an iPhone tab holds 10 rows at most.
4. Design both schemes, or pin `appearance.colorScheme` (`light-dark-parity`).
5. Check contrast on every gradient stop (`text-contrast`), then score the five rubric axes (`ship-bar`).

The art-direction packs (Bauhaus, Terminal Phosphor, Swiss Rail Board and the rest) break the shape rules on purpose: square corners, 2 pt radius, no glass. They keep the other rules. Their frontmatter lists the values they set so a checker can tell a deliberate choice from a drift.
