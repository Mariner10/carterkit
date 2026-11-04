---
type: theme-pack
label: Midnight
icon: moon.fill
category: style
vibe: navy, glass, steel labels, iOS blue, house dark
accent: #0A84FF
colorScheme: system
lightDarkNotes: Follows the device scheme; theme.light and theme.dark each set the page, surfaces, ink and border.
whenToUse: The house dark default and the reference every other pack is measured against
specimen: layout-library/playbook/themes/midnight.specimen.json
themeFile: layout-library/playbook/themes/midnight.theme.json
tokens: {"accentColor":"#0A84FF","cornerRadius":16,"fontDesign":"rounded","borderWidth":1,"controlPadding":10,"cardPadding":12,"blurEnabled":false,"dark":{"pageBackground":"#0A0F1E","pageBackgroundGradient":["#0A0F1E","#0E1A33"],"surfacePrimary":"#FFFFFF0F","surfaceSecondary":"#FFFFFF0A","borderColor":"#FFFFFF1A","foregroundColor":"#F2F5FA","secondaryColor":"#9FB3D1","tertiaryColor":"#9FB3D1A6"},"light":{"pageBackground":"#EEF2F8","pageBackgroundGradient":["#EEF2F8","#DCE5F2"],"surfacePrimary":"#FFFFFFD9","surfaceSecondary":"#FFFFFFB3","borderColor":"#0B12201F","foregroundColor":"#0B1220","secondaryColor":"#4A5F82","tertiaryColor":"#4A5F82B3"},"toggle":{"trackColor":"#9FB3D14D","trackActiveColor":"#0A84FF"},"slider":{"trackColor":"#9FB3D14D","trackActiveColor":"#0A84FF"},"segmented":{"trackColor":"#9FB3D12E","selectedColor":"#0A84FF","textColor":"#8A94A6","selectedTextColor":"#FFFFFF"},"stepper":{"buttonColor":"#0A84FF26","iconColor":"#0A84FF"}}
appearance: {"colorScheme":"system"}
---

# Midnight

Harbor at 2 a.m.: a navy page that is never black, glass cards at 6% white, one #0A84FF accent that carries every live value, and labels in a navy-tinted steel (#9FB3D1) instead of the default 60% white. Midnight is the house default and the reference every other pack is measured against. Themes are Pro-only: without Connect+ Pro a phone ignores the layout `theme` and draws the default look.

**When to use:** The house dark default and the reference every other pack is measured against.

**Light and dark:** Follows the device scheme; theme.light and theme.dark each set the page, surfaces, ink and border.

Apply it by copying the `tokens` object into the layout `theme` (see [[theming]]) and the `appearance` object into the layout `appearance`. Rules that still apply to it are in [[style-rules]]. Themes need Connect+ Pro on the phone; without it the default glass look is drawn.
