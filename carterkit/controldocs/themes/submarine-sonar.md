---
type: theme-pack
label: Submarine Sonar
icon: dot.radiowaves.left.and.right
category: style
vibe: sonar, phosphor green, amber contact, instrument
accent: #00E5A0
colorScheme: dark
lightDarkNotes: Pinned to dark; theme.dark carries the scheme-sensitive colours. Sibling variants: submarine-sonar-daylight.
whenToUse: Network scans, monitoring and sensor consoles; amber means a contact; has a daylight variant
specimen: layout-library/playbook/themes/submarine-sonar.specimen.json
themeFile: layout-library/playbook/themes/submarine-sonar.theme.json
variants: layout-library/playbook/themes/submarine-sonar-daylight.theme.json
tokens: {"accentColor":"#00E5A0","cornerRadius":10,"fontDesign":"monospaced","borderWidth":1,"controlPadding":10,"cardPadding":10,"blurEnabled":false,"labelFontSize":11,"dark":{"pageBackground":"#001210","pageBackgroundGradient":["#001210","#00261F"],"surfacePrimary":"#00E5A00A","surfaceSecondary":"#00E5A006","borderColor":"#00E5A026","foregroundColor":"#C9FFF0","secondaryColor":"#00E5A0CC","tertiaryColor":"#00E5A0A6"},"toggle":{"trackColor":"#00E5A040","trackActiveColor":"#00E5A0","knobColor":"#C9FFF0"},"slider":{"trackColor":"#00E5A026","thumbColor":"#C9FFF0"},"segmented":{"trackColor":"#00E5A012","selectedColor":"#00E5A0","textColor":"#00E5A0CC","selectedTextColor":"#001210"}}
appearance: {"colorScheme":"dark","statusBarStyle":"light"}
---

# Submarine Sonar

A sonar console at 40 m: a green-black page from #001210 to #00261F, cards that are only 4% phosphor, one #00E5A0 accent for every live value, and amber #FFB000 reserved for exactly one meaning: a contact. Monospaced type and radius 10 make it read as an instrument, not an app. Themes are Pro-only: without Connect+ Pro a phone ignores the layout `theme` and draws the default look.

**When to use:** Network scans, monitoring and sensor consoles; amber means a contact; has a daylight variant.

**Light and dark:** Pinned to dark; theme.dark carries the scheme-sensitive colours. Sibling variants: submarine-sonar-daylight.

Apply it by copying the `tokens` object into the layout `theme` (see [[theming]]) and the `appearance` object into the layout `appearance`. Rules that still apply to it are in [[style-rules]]. Themes need Connect+ Pro on the phone; without it the default glass look is drawn.
