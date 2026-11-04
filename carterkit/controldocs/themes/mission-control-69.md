---
type: theme-pack
label: Mission Control '69
icon: antenna.radiowaves.left.and.right
category: style
vibe: Apollo era, amber console, backlit bezel, monospaced
accent: #EDE6D6
colorScheme: dark
lightDarkNotes: Pinned to dark; theme.dark carries the scheme-sensitive colours.
whenToUse: Release dashboards, ops consoles and status boards with a flight-director feel
specimen: layout-library/playbook/themes/mission-control-69.specimen.json
themeFile: layout-library/playbook/themes/mission-control-69.theme.json
tokens: {"accentColor":"#F2A900","cornerRadius":4,"fontDesign":"monospaced","borderWidth":1,"controlPadding":8,"cardPadding":10,"blurEnabled":false,"labelFontSize":11,"valueFontWeight":"bold","tabBarTint":"#F2A900","dark":{"pageBackground":"#1B1D1A","pageBackgroundGradient":["#1B1D1A","#23251F"],"surfacePrimary":"#F2A9000A","surfaceSecondary":"#F2A90006","borderColor":"#F2A90033","foregroundColor":"#EDE6D6","secondaryColor":"#EDE6D699","tertiaryColor":"#EDE6D64D"},"toggle":{"trackColor":"#EDE6D61F","trackActiveColor":"#F2A900","knobColor":"#EDE6D6"},"slider":{"trackColor":"#EDE6D61F","trackActiveColor":"#F2A900","thumbColor":"#EDE6D6","thumbBorderColor":"#F2A900"},"segmented":{"trackColor":"#EDE6D614","selectedColor":"#F2A900","textColor":"#EDE6D699","selectedTextColor":"#1B1D1A"},"stepper":{"buttonColor":"#F2A90026","iconColor":"#F2A900"}}
appearance: {"colorScheme":"dark","statusBarStyle":"light"}
---

# Mission Control '69

An Apollo-era flight-director console for software releases. The page is warm grey #1B1D1A lifting to #23251F, like painted steel under incandescent light. Every card is a 4% amber wash with a 20% amber hairline, so the panels read as backlit bezels, not glass. Amber #F2A900 is the console lamp: action, primary series, the selected stage. GO green #7FB800 means exactly one thing: a station has said go. Type is monospaced everywhere, and every label is set in capitals like a stencilled panel legend. Themes are a Pro-only feature.

**When to use:** Release dashboards, ops consoles and status boards with a flight-director feel.

**Light and dark:** Pinned to dark; theme.dark carries the scheme-sensitive colours.

Apply it by copying the `tokens` object into the layout `theme` (see [[theming]]) and the `appearance` object into the layout `appearance`. Rules that still apply to it are in [[style-rules]]. Themes need Connect+ Pro on the phone; without it the default glass look is drawn.
