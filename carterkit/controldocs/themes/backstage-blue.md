---
type: theme-pack
label: Backstage Blue-Light
icon: theatermasks.fill
category: style
vibe: blackout, stage, hooded blue light, OLED black
accent: #3D7BFF
colorScheme: dark
lightDarkNotes: Pinned to dark; theme.dark carries the scheme-sensitive colours.
whenToUse: Show calling, live-production prompt desks and any screen used in a dark room where light must not spill
specimen: layout-library/playbook/themes/backstage-blue.specimen.json
themeFile: layout-library/playbook/themes/backstage-blue.theme.json
tokens: {"accentColor":"#3D7BFF","cornerRadius":8,"fontDesign":"monospaced","borderWidth":1,"controlPadding":10,"cardPadding":10,"blurEnabled":false,"tabBarTint":"#3D7BFF","labelFontSize":12,"foregroundColor":"#C9D7FF","secondaryColor":"#C9D7FF80","tertiaryColor":"#C9D7FF66","pageBackground":"#000000","surfacePrimary":"#FFFFFF08","surfaceSecondary":"#FFFFFF05","borderColor":"#3D7BFF1F","dark":{"pageBackground":"#000000","surfacePrimary":"#FFFFFF08","surfaceSecondary":"#FFFFFF05","borderColor":"#3D7BFF1F","foregroundColor":"#C9D7FF","secondaryColor":"#C9D7FF80","tertiaryColor":"#C9D7FF66"},"toggle":{"trackColor":"#FFFFFF14","trackActiveColor":"#3D7BFF","knobColor":"#C9D7FF99","knobActiveColor":"#00081A"},"slider":{"trackColor":"#FFFFFF14","trackActiveColor":"#3D7BFF","thumbColor":"#C9D7FF"},"segmented":{"trackColor":"#FFFFFF0A","selectedColor":"#3D7BFF","textColor":"#C9D7FF99","selectedTextColor":"#00081A"},"stepper":{"buttonColor":"#3D7BFF1F","iconColor":"#3D7BFF"}}
appearance: {"colorScheme":"dark","statusBarStyle":"light"}
---

# Backstage Blue-Light

The prompt desk in the blackout. A stage manager calls the show from the wings with one hooded blue work-light over the book. The page is true black (`#000000`) because an OLED phone at the desk must not glow onto the set. Cards are white at 3%, just enough to catch the eye. Text is a cool ice-blue (`#C9D7FF`), never white. There are exactly two signal colours: work-light blue `#3D7BFF` means *go, live, ready*, and standby amber `#FFB000` means *standby, hold, about to happen*. A GO button stays hidden until you arm it, and it fires a heavy haptic, because a cue is a physical act. Themes are Pro-only: without Pro the phone ignores the layout `theme` and shows the default look.

**When to use:** Show calling, live-production prompt desks and any screen used in a dark room where light must not spill.

**Light and dark:** Pinned to dark; theme.dark carries the scheme-sensitive colours.

Apply it by copying the `tokens` object into the layout `theme` (see [[theming]]) and the `appearance` object into the layout `appearance`. Rules that still apply to it are in [[style-rules]]. Themes need Connect+ Pro on the phone; without it the default glass look is drawn.
