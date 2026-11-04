---
type: theme-pack
label: Glass Cockpit
icon: airplane
category: style
vibe: avionics, flight display, monospaced, three hues
accent: #00D1FF
colorScheme: dark
lightDarkNotes: Pinned to dark; theme.light and theme.dark are both set for the scheme-sensitive colours.
whenToUse: Telemetry and vehicle panels where cyan is now, magenta is commanded and amber is caution
specimen: layout-library/playbook/themes/glass-cockpit.specimen.json
themeFile: layout-library/playbook/themes/glass-cockpit.theme.json
tokens: {"accentColor":"#00D1FF","cornerRadius":4,"fontDesign":"monospaced","borderWidth":1,"controlPadding":10,"cardPadding":10,"blurEnabled":false,"tabBarTint":"#00D1FF","labelFontSize":12,"dark":{"pageBackground":"#05070A","pageBackgroundGradient":["#05070A","#0B1017"],"surfacePrimary":"#FFFFFF0A","surfaceSecondary":"#FFFFFF05","borderColor":"#FFFFFF14","foregroundColor":"#FFFFFF","secondaryColor":"#FFFFFFB3","tertiaryColor":"#FFFFFF4D"},"light":{"pageBackground":"#05070A","pageBackgroundGradient":["#05070A","#0B1017"],"surfacePrimary":"#FFFFFF0A","surfaceSecondary":"#FFFFFF05","borderColor":"#FFFFFF14","foregroundColor":"#FFFFFF","secondaryColor":"#FFFFFFB3","tertiaryColor":"#FFFFFF4D"},"toggle":{"trackColor":"#FFFFFF26","trackActiveColor":"#00D1FF","knobColor":"#FFFFFF"},"slider":{"trackColor":"#FFFFFF1A","trackActiveColor":"#00D1FF","thumbColor":"#FFFFFF"},"segmented":{"trackColor":"#FFFFFF0F","selectedColor":"#00D1FF","textColor":"#FFFFFF99","selectedTextColor":"#05070A"},"stepper":{"buttonColor":"#00D1FF1F","iconColor":"#00D1FF"}}
appearance: {"colorScheme":"dark","statusBarStyle":"light"}
---

# Glass Cockpit

An avionics primary flight display in your pocket: a #05070A page that is almost black but never #000000, neutral white-glass cards at 4%, 1 pt hairlines at 8%, radius 4, monospaced everything, and exactly three hues with three jobs. Cyan #00D1FF is what the aircraft is doing now. Magenta #FF3DF5 is what you told it to do: targets, waypoints, setpoints. Amber #FFB000 is caution. Themes are Pro-only: without Connect+ Pro a phone ignores the layout `theme` and draws the default look.

**When to use:** Telemetry and vehicle panels where cyan is now, magenta is commanded and amber is caution.

**Light and dark:** Pinned to dark; theme.light and theme.dark are both set for the scheme-sensitive colours.

Apply it by copying the `tokens` object into the layout `theme` (see [[theming]]) and the `appearance` object into the layout `appearance`. Rules that still apply to it are in [[style-rules]]. Themes need Connect+ Pro on the phone; without it the default glass look is drawn.
