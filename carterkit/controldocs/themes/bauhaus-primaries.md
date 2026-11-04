---
type: theme-pack
label: Bauhaus Primaries
icon: square.on.circle
category: style
vibe: Bauhaus, flat, primary colours, poster, square
accent: #111111
colorScheme: light
lightDarkNotes: Pinned to light with scheme-neutral values in the base theme.
whenToUse: Print-like dashboards and design-led layouts that want flat tiles, ink rules and exactly three colours
specimen: layout-library/playbook/themes/bauhaus-primaries.specimen.json
themeFile: layout-library/playbook/themes/bauhaus-primaries.theme.json
tokens: {"accentColor":"#D62828","pageBackground":"#F4EFE6","surfacePrimary":"#FFFFFF","surfaceSecondary":"#F4EFE6","foregroundColor":"#111111","secondaryColor":"#111111A6","tertiaryColor":"#11111159","borderWidth":2,"borderColor":"#111111","cornerRadius":0,"controlPadding":8,"cardPadding":10,"fontFamily":"Futura","labelFontSize":12,"blurEnabled":false,"toggle":{"trackColor":"#D9D0BD","trackActiveColor":"#D62828","knobColor":"#FFFFFF","trackRadius":0,"knobRadius":0,"knobShadow":false},"slider":{"trackColor":"#E9E2D4","thumbColor":"#111111","trackRadius":0,"thumbRadius":0,"thumbShadow":false},"segmented":{"trackColor":"#E9E2D4","selectedColor":"#111111","textColor":"#111111A6","selectedTextColor":"#FFFFFF","trackRadius":0,"selectedRadius":0,"selectedShadow":false},"stepper":{"buttonColor":"#F2B705","iconColor":"#111111","buttonRadius":0}}
appearance: {"colorScheme":"light","statusBarStyle":"dark"}
---

# Bauhaus Primaries

A 1923 Weimar workshop poster, as a control panel: cream paper #F4EFE6, white and solid-primary tiles boxed in 2 pt #111111 rules, square corners, Futura for every word, and exactly three colours: red #D62828 to act, blue #1D4ED8 to inform, yellow #F2B705 to warn. Every card and every poster tile is flat. The only soft shapes left are the app's own header capsule and tab pill, listed under Known limits; switches are 2-option segmented controls, so even on/off is a flat ink chip. Themes are Pro-only: without Connect+ Pro a phone ignores the layout `theme` and draws the default look.

**When to use:** Print-like dashboards and design-led layouts that want flat tiles, ink rules and exactly three colours.

**Light and dark:** Pinned to light with scheme-neutral values in the base theme.

Apply it by copying the `tokens` object into the layout `theme` (see [[theming]]) and the `appearance` object into the layout `appearance`. Rules that still apply to it are in [[style-rules]]. Themes need Connect+ Pro on the phone; without it the default glass look is drawn.
