---
type: theme-pack
label: Terminal Phosphor
icon: terminal.fill
category: style
vibe: CRT, green phosphor, monospaced, true black, 2 pt corners
accent: #33FF66
colorScheme: dark
lightDarkNotes: Pinned to dark; theme.dark carries the scheme-sensitive colours.
whenToUse: Server closets, logs, shells and developer tools
specimen: layout-library/playbook/themes/terminal-phosphor.specimen.json
themeFile: layout-library/playbook/themes/terminal-phosphor.theme.json
tokens: {"accentColor":"#33FF66","cornerRadius":2,"fontDesign":"monospaced","borderWidth":1,"controlPadding":10,"cardPadding":10,"blurEnabled":false,"tabBarTint":"#33FF66","labelFontSize":11,"dark":{"pageBackground":"#000000","surfacePrimary":"#33FF660F","surfaceSecondary":"#33FF6608","borderColor":"#33FF6633","foregroundColor":"#B8FFC8","secondaryColor":"#33FF6699","tertiaryColor":"#33FF664D"},"toggle":{"trackColor":"#33FF661F","trackActiveColor":"#33FF66","knobColor":"#B8FFC8"},"slider":{"trackColor":"#33FF661F","trackActiveColor":"#33FF66","thumbColor":"#B8FFC8"},"segmented":{"trackColor":"#33FF6614","selectedColor":"#33FF66","textColor":"#33FF6699","selectedTextColor":"#000000"},"stepper":{"buttonColor":"#33FF661F","iconColor":"#33FF66"}}
appearance: {"colorScheme":"dark","statusBarStyle":"light"}
---

# Terminal Phosphor

A green P1 phosphor CRT at 3 a.m. in the server closet: a true #000000 page, cards that are only 6% green glow behind a 20% green hairline, square 2 pt corners, monospaced everything, and one #33FF66 beam that carries every live value. Text is a paler #B8FFC8 so readouts never merge with the arcs. Amber #FFB000, the other classic phosphor, is the only warning colour. Themes are Pro-only: without Connect+ Pro a phone ignores the layout `theme` and draws the default look.

**When to use:** Server closets, logs, shells and developer tools.

**Light and dark:** Pinned to dark; theme.dark carries the scheme-sensitive colours.

Apply it by copying the `tokens` object into the layout `theme` (see [[theming]]) and the `appearance` object into the layout `appearance`. Rules that still apply to it are in [[style-rules]]. Themes need Connect+ Pro on the phone; without it the default glass look is drawn.
