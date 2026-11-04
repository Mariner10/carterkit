---
type: theme-pack
label: Arcade Vapor
icon: gamecontroller.fill
category: style
vibe: synthwave, neon, arcade, playful
accent: #FF4ECD
colorScheme: dark
lightDarkNotes: Pinned to dark; theme.dark carries the scheme-sensitive colours.
whenToUse: Game scoreboards, streaming overlays and anything meant to feel like a cabinet at night
specimen: layout-library/playbook/themes/arcade-vapor.specimen.json
themeFile: layout-library/playbook/themes/arcade-vapor.theme.json
tokens: {"accentColor":"#FF4ECD","cornerRadius":20,"fontDesign":"rounded","borderWidth":1,"controlPadding":10,"cardPadding":12,"blurEnabled":false,"labelFontSize":12,"valueFontWeight":"bold","tabBarTint":"#FF4ECD","dark":{"pageBackground":"#12021F","pageBackgroundGradient":["#12021F","#2A0645","#4A0B4F"],"surfacePrimary":"#FFFFFF14","surfaceSecondary":"#FFFFFF0A","borderColor":"#FF4ECD33","foregroundColor":"#FFF0FB","secondaryColor":"#FFF0FBB3","tertiaryColor":"#FFF0FB4D"},"toggle":{"trackColor":"#FFFFFF1F","trackActiveColor":"#FF4ECD"},"slider":{"trackColor":"#FFFFFF1F"},"segmented":{"trackColor":"#FFFFFF14","selectedColor":"#FF4ECD","textColor":"#FFF0FBB3","selectedTextColor":"#12021F"},"stepper":{"buttonColor":"#00E5FF26","iconColor":"#00E5FF"}}
appearance: {"colorScheme":"dark","statusBarStyle":"light"}
---

# Arcade Vapor

Synthwave arcade, kept legible. The page is the three-stop all-dark gradient from the brief, #12021F -> #2A0645 -> #4A0B4F, and no stop gets bright enough to wash out white ink. Hot pink #FF4ECD is the one accent and carries every action. Cyan #00E5FF is the second series and the "reading, not doing" colour. Corners are soft at 20pt, type is SF Rounded, and the two heroes are the pieChart `menu` radial pad and the curved "smile switch". Themes are Pro-only: on a free phone the layout theme is ignored and the page renders in the default look.

**When to use:** Game scoreboards, streaming overlays and anything meant to feel like a cabinet at night.

**Light and dark:** Pinned to dark; theme.dark carries the scheme-sensitive colours.

Apply it by copying the `tokens` object into the layout `theme` (see [[theming]]) and the `appearance` object into the layout `appearance`. Rules that still apply to it are in [[style-rules]]. Themes need Connect+ Pro on the phone; without it the default glass look is drawn.
