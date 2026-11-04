---
type: theme-pack
label: Cellar Candlelight
icon: wineglass.fill
category: style
vibe: candlelit, claret, brass, serif, smoke
accent: #C8A165
colorScheme: dark
lightDarkNotes: Pinned to dark; theme.dark carries the scheme-sensitive colours.
whenToUse: Wine cellars, humidor and pantry monitoring, slow evening dashboards
specimen: layout-library/playbook/themes/cellar-candlelight.specimen.json
themeFile: layout-library/playbook/themes/cellar-candlelight.theme.json
tokens: {"accentColor":"#C8A165","cornerRadius":12,"fontFamily":"Didot","borderWidth":1,"controlPadding":12,"cardPadding":12,"blurEnabled":false,"labelFontSize":14,"foregroundColor":"#F3E7D3","secondaryColor":"#F3E7D3B3","tertiaryColor":"#F3E7D380","dark":{"pageBackground":"#140A0A","pageBackgroundGradient":["#140A0A","#241012"],"surfacePrimary":"#F3E7D30D","surfaceSecondary":"#F3E7D308","borderColor":"#C8A16526","foregroundColor":"#F3E7D3","secondaryColor":"#F3E7D3B3","tertiaryColor":"#F3E7D380","tabBarTint":"#C8A165"},"toggle":{"trackColor":"#C8A16526","trackActiveColor":"#C8A165","knobColor":"#F3E7D3"},"slider":{"trackColor":"#C8A16526","trackActiveColor":"#C8A165","thumbColor":"#F3E7D3"},"segmented":{"trackColor":"#C8A1651A","selectedColor":"#C8A165","textColor":"#F3E7D3B3","selectedTextColor":"#140A0A"},"stepper":{"buttonColor":"#C8A16526","iconColor":"#C8A165"}}
appearance: {"colorScheme":"dark","statusBarStyle":"light"}
---

# Cellar Candlelight

A wine cellar at 12 °C, lit by one candle. The page falls from a near-black claret (#140A0A) to a deep oxblood (#241012). Cards are cream at 5% alpha, so they read as smoke on the stone rather than slabs. Every card has a brass hairline (#C8A165 at 15%). The header capsule picks up the stone through its glass, and the top-level brass `accentColor` warms it. Type is Didot throughout, which makes the readouts look like an engraved cellar book. Brass (#C8A165) is the only accent. Claret (#B0343F) is kept for alarms and nothing else: the fault badge and the top zone of each gauge. Motion is slow: toggles and segments use the `gentle` profile (easeInOut 0.6 s). Themes are Pro-only: without Pro the phone ignores the layout `theme` and shows the default look.

**When to use:** Wine cellars, humidor and pantry monitoring, slow evening dashboards.

**Light and dark:** Pinned to dark; theme.dark carries the scheme-sensitive colours.

Apply it by copying the `tokens` object into the layout `theme` (see [[theming]]) and the `appearance` object into the layout `appearance`. Rules that still apply to it are in [[style-rules]]. Themes need Connect+ Pro on the phone; without it the default glass look is drawn.
