---
type: theme-pack
label: Clinical Ward
icon: cross.case.fill
category: style
vibe: clinical, hospital, high contrast, colour-blind safe
accent: #0077C8
colorScheme: light
lightDarkNotes: Pinned to light with scheme-neutral values in the base theme.
whenToUse: Health and care readouts read at arm length, where status must never rely on colour alone
specimen: layout-library/playbook/themes/clinical-ward.specimen.json
themeFile: layout-library/playbook/themes/clinical-ward.theme.json
tokens: {"accentColor":"#0077C8","pageBackground":"#F5F8FA","surfacePrimary":"#FFFFFF","surfaceSecondary":"#EEF3F6","foregroundColor":"#0B1F2A","secondaryColor":"#0B1F2AA6","tertiaryColor":"#0B1F2A66","borderWidth":1,"borderColor":"#D5DEE5","cornerRadius":6,"controlPadding":10,"cardPadding":12,"fontDesign":"default","labelFontSize":14,"blurEnabled":false,"toggle":{"trackColor":"#DCE4EA","trackActiveColor":"#0077C8","knobColor":"#FFFFFF","knobShadow":true},"slider":{"trackColor":"#DCE4EA","trackActiveColor":"#0077C8","thumbColor":"#0077C8","thumbShadow":false},"segmented":{"trackColor":"#E6EDF2","selectedColor":"#0077C8","textColor":"#0B1F2AA6","selectedTextColor":"#FFFFFF","selectedShadow":false},"stepper":{"buttonColor":"#E3F0FA","iconColor":"#0077C8"}}
appearance: {"colorScheme":"light","statusBarStyle":"dark"}
---

# Clinical Ward

A hospital-grade light pack: a #F5F8FA page, #FFFFFF cards with a 1pt #D5DEE5 hairline, one clinical blue (#0077C8), and a status vocabulary that never relies on colour alone. It is built to be read at arm's length, at 3 a.m., by someone with red-green colour blindness. There are no gradients, no blur and no glow anywhere on the page. Its signature is a dashed #0077C8 "ECG rule" (a divider with a 12pt blue label) that names the next block on every tab, plus paired 2pt-bordered tinted slabs for actions. Themes are Pro-only: on a free phone the layout `theme` is ignored and the app default draws instead.

**When to use:** Health and care readouts read at arm length, where status must never rely on colour alone.

**Light and dark:** Pinned to light with scheme-neutral values in the base theme.

Apply it by copying the `tokens` object into the layout `theme` (see [[theming]]) and the `appearance` object into the layout `appearance`. Rules that still apply to it are in [[style-rules]]. Themes need Connect+ Pro on the phone; without it the default glass look is drawn.
