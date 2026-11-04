---
type: theme-pack
label: Darkroom Safelight
icon: camera.filters
category: style
vibe: red only, safelight, monochrome, glyph status
accent: #FF2A1A
colorScheme: dark
lightDarkNotes: Pinned to dark; theme.light and theme.dark are both set for the scheme-sensitive colours.
whenToUse: Photo workflows and night use where only red light is acceptable; status by glyph shape, not hue
specimen: layout-library/playbook/themes/darkroom-safelight.specimen.json
themeFile: layout-library/playbook/themes/darkroom-safelight.theme.json
tokens: {"accentColor":"#FF2A1A","cornerRadius":8,"fontDesign":"monospaced","borderWidth":1,"controlPadding":10,"cardPadding":10,"blurEnabled":false,"tabBarTint":"#FF2A1A","labelFontSize":11,"dark":{"pageBackground":"#070101","pageBackgroundGradient":["#070101","#160303"],"surfacePrimary":"#FF2A1A0A","surfaceSecondary":"#FF2A1A07","borderColor":"#FF2A1A1F","foregroundColor":"#FF9C8F","secondaryColor":"#FF9C8F80","tertiaryColor":"#FF9C8F66"},"light":{"pageBackground":"#070101","pageBackgroundGradient":["#070101","#160303"],"surfacePrimary":"#FF2A1A0A","surfaceSecondary":"#FF2A1A07","borderColor":"#FF2A1A1F","foregroundColor":"#FF9C8F","secondaryColor":"#FF9C8F80","tertiaryColor":"#FF9C8F66"},"toggle":{"trackColor":"#FF2A1A1F","trackActiveColor":"#FF2A1A","knobColor":"#FF9C8FB3","knobActiveColor":"#1A0000"},"slider":{"trackColor":"#FF2A1A1F","trackActiveColor":"#FF2A1A","thumbColor":"#FF9C8FB3"},"segmented":{"trackColor":"#FF2A1A14","selectedColor":"#FF2A1A","textColor":"#FF9C8F99","selectedTextColor":"#1A0000"},"stepper":{"buttonColor":"#FF2A1A1F","iconColor":"#FF2A1A"}}
appearance: {"colorScheme":"dark","statusBarStyle":"light"}
---

# Darkroom Safelight

Only red light reaches this page, the way only a #1 safelight reaches the paper. The page is near-black (#070101 to #160303), every card is red at 4% alpha, text is dim salmon ink (#FF9C8F), and nothing in the grid is white. Because every colour is red, hue carries no meaning: status is carried by glyph shape (check = done, dotted ring = running, ring = waiting, octagon-X = blocked). Use it where a bright pixel costs you something: fogged paper, lost dark adaptation, a woken baby. Themes are Pro-only; without Pro the phone ignores `theme` and shows the default white-on-black look, which is not darkroom-safe.

**When to use:** Photo workflows and night use where only red light is acceptable; status by glyph shape, not hue.

**Light and dark:** Pinned to dark; theme.light and theme.dark are both set for the scheme-sensitive colours.

Apply it by copying the `tokens` object into the layout `theme` (see [[theming]]) and the `appearance` object into the layout `appearance`. Rules that still apply to it are in [[style-rules]]. Themes need Connect+ Pro on the phone; without it the default glass look is drawn.
