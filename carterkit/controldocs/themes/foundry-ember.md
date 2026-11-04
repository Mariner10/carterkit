---
type: theme-pack
label: Foundry Ember
icon: flame.fill
category: style
vibe: molten, ember, industrial, monospaced, heat ramp
accent: #FF8A1F
colorScheme: dark
lightDarkNotes: Pinned to dark; theme.dark carries the scheme-sensitive colours.
whenToUse: Kilns, furnaces, 3D printers and any temperature-led machine panel
specimen: layout-library/playbook/themes/foundry-ember.specimen.json
themeFile: layout-library/playbook/themes/foundry-ember.theme.json
tokens: {"accentColor":"#FF8A1F","cornerRadius":8,"fontDesign":"monospaced","borderWidth":1,"controlPadding":10,"cardPadding":10,"blurEnabled":false,"tabBarTint":"#FF8A1F","labelFontSize":11,"valueFontWeight":"bold","foregroundColor":"#FFE8D6","secondaryColor":"#FFE8D699","tertiaryColor":"#FFE8D673","dark":{"pageBackground":"#0D0806","pageBackgroundGradient":["#0D0806","#2A1208"],"surfacePrimary":"#FF8A1F0D","surfaceSecondary":"#FF8A1F08","borderColor":"#FF8A1F26","foregroundColor":"#FFE8D6","secondaryColor":"#FFE8D699","tertiaryColor":"#FFE8D673","headerBackground":"#1A0C06","headerBackgroundGradient":["#1A0C06","#2A1208"],"tabBarBackground":"#1A0C06E6","tabBarTint":"#FF8A1F"},"toggle":{"trackColor":"#FF8A1F1F","trackActiveColor":"#FF8A1F","knobColor":"#FFE8D6"},"slider":{"trackColor":"#FF8A1F1F","trackActiveColor":"#FF8A1F","thumbColor":"#FFE8D6"},"segmented":{"trackColor":"#FF8A1F14","selectedColor":"#FF8A1F","textColor":"#FFE8D699","selectedTextColor":"#1A0A04"},"stepper":{"buttonColor":"#FF8A1F1F","iconColor":"#FF8A1F"}}
appearance: {"colorScheme":"dark","statusBarStyle":"light","header":{"style":"color","dark":["#1A0C06","#2A1208"],"light":["#1A0C06","#2A1208"]}}
---

# Foundry Ember

Molten metal on a cold floor. A near-black to dull-rust page, cards lit at 5% orange, an 8pt radius and monospaced numerals, with one accent: #FF8A1F, the colour of steel at about 1000 °C. Heat is the story, so every temperature arc is an in-theme heat ramp, cold iron `#7A3A12` (0 to 600 °C, below visible glow) to ember `#FF8A1F` (600 to 1225 °C, working heat) to over-temp `#FF3B30` (above 1225 °C), blended into one gradient (`colorBlend: 1`). No arc is ever green. The one probe that runs hot gets a red alarm card while its twin, on identical segment limits, stays in the house colours. The header capsule and tab bar are fired too: `#1A0C06` to `#2A1208`, never stock grey. Built for kilns, 3D printers, boilers, smokers and furnaces. Themes are Pro-only: without Pro the phone ignores the layout `theme` and draws the default look.

**When to use:** Kilns, furnaces, 3D printers and any temperature-led machine panel.

**Light and dark:** Pinned to dark; theme.dark carries the scheme-sensitive colours.

Apply it by copying the `tokens` object into the layout `theme` (see [[theming]]) and the `appearance` object into the layout `appearance`. Rules that still apply to it are in [[style-rules]]. Themes need Connect+ Pro on the phone; without it the default glass look is drawn.
