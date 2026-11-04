---
type: theme-pack
label: Swiss Rail Departure Board
icon: tram.fill
category: style
vibe: departure board, Helvetica, navy, square, one red
accent: #0B1E3F
colorScheme: dark
lightDarkNotes: Pinned to dark; theme.dark carries the scheme-sensitive colours. Sibling variants: swiss-rail-board.daylight.
whenToUse: Schedules, queues and delay boards where red is reserved for delay and the one action; has a daylight variant
specimen: layout-library/playbook/themes/swiss-rail-board.specimen.json
themeFile: layout-library/playbook/themes/swiss-rail-board.theme.json
variants: layout-library/playbook/themes/swiss-rail-board.daylight.json
tokens: {"accentColor":"#FFFFFF","fontFamily":"Helvetica Neue","cornerRadius":2,"borderWidth":0,"controlPadding":10,"cardPadding":10,"labelFontSize":13,"valueFontWeight":"bold","blurEnabled":false,"dark":{"pageBackground":"#0B1E3F","surfacePrimary":"#FFFFFF0D","surfaceSecondary":"#FFFFFF08","borderColor":"#00000000","foregroundColor":"#FFFFFF","secondaryColor":"#FFFFFFB3","tertiaryColor":"#FFFFFF66"},"toggle":{"trackColor":"#FFFFFF26","trackActiveColor":"#FFFFFF","knobColor":"#FFFFFF","knobActiveColor":"#0B1E3F"},"slider":{"trackColor":"#FFFFFF26","trackActiveColor":"#FFFFFF","thumbColor":"#FFFFFF"},"segmented":{"trackColor":"#FFFFFF14","selectedColor":"#FFFFFF","textColor":"#FFFFFFB3","selectedTextColor":"#0B1E3F","trackRadius":2,"selectedRadius":2},"stepper":{"buttonColor":"#FFFFFF1A","iconColor":"#FFFFFF","buttonRadius":2}}
appearance: {"colorScheme":"dark","statusBarStyle":"light"}
---

# Swiss Rail Departure Board

A station departure board, not a dark app. One solid navy field, white type set in Helvetica Neue, square 2pt corners, no strokes, no glass, and exactly one colour that shouts: SBB red #EB0000, reserved for delays and the one action button at the foot of the board. The discipline is the look: if red appears anywhere else, the board stops meaning anything.

**When to use:** Schedules, queues and delay boards where red is reserved for delay and the one action; has a daylight variant.

**Light and dark:** Pinned to dark; theme.dark carries the scheme-sensitive colours. Sibling variants: swiss-rail-board.daylight.

Apply it by copying the `tokens` object into the layout `theme` (see [[theming]]) and the `appearance` object into the layout `appearance`. Rules that still apply to it are in [[style-rules]]. Themes need Connect+ Pro on the phone; without it the default glass look is drawn.
