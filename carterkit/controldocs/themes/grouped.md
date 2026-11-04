---
type: theme-pack
label: Grouped
icon: list.bullet.rectangle.fill
category: style
vibe: Settings.app, iOS native, light, orange accent
accent: #FF6A00
colorScheme: light
lightDarkNotes: Pinned to light with scheme-neutral values in the base theme.
whenToUse: The house light pack: a layout that should feel shipped with iOS, counterpart to Midnight
specimen: layout-library/playbook/themes/grouped.specimen.json
themeFile: layout-library/playbook/themes/grouped.theme.json
tokens: {"accentColor":"#FF6A00","pageBackground":"#F2F2F7","surfacePrimary":"#FFFFFF","foregroundColor":"#1C1C1E","secondaryColor":"#3C3C43B3","tertiaryColor":"#3C3C4399","borderWidth":0,"borderColor":"#00000000","cornerRadius":14,"controlPadding":8,"cardPadding":12,"fontFamily":"Avenir Next","blurEnabled":false,"toggle":{"trackColor":"#E5E5EA","trackActiveColor":"#FF6A00"},"slider":{"trackColor":"#E5E5EA","trackActiveColor":"#FF6A00"},"segmented":{"trackColor":"#E5E5EA","selectedColor":"#FFFFFF","textColor":"#3C3C43B3","selectedTextColor":"#1C1C1E"},"stepper":{"buttonColor":"#FF6A0022","iconColor":"#FF6A00"}}
appearance: {"colorScheme":"light","statusBarStyle":"dark"}
---

# Grouped

Settings.app at noon: a #F2F2F7 page, opaque white cards with no stroke at all, Avenir Next, and one #FF6A00 accent that means "live" or "tap me". Grouped is the house light pack, the counterpart to Midnight, and the one to reach for when a layout should feel like it shipped with iOS. Themes are Pro-only: without Connect+ Pro a phone ignores the layout `theme` and draws the default look.

**When to use:** The house light pack: a layout that should feel shipped with iOS, counterpart to Midnight.

**Light and dark:** Pinned to light with scheme-neutral values in the base theme.

Apply it by copying the `tokens` object into the layout `theme` (see [[theming]]) and the `appearance` object into the layout `appearance`. Rules that still apply to it are in [[style-rules]]. Themes need Connect+ Pro on the phone; without it the default glass look is drawn.
