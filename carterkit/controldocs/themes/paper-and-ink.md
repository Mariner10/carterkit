---
type: theme-pack
label: Paper & Ink
icon: doc.richtext.fill
category: style
vibe: paper, ink, serif, editorial, pinned light
accent: #1F3A93
colorScheme: light
lightDarkNotes: Pinned to light with scheme-neutral values in the base theme. Sibling variants: paper-and-ink-night.
whenToUse: Reading-first layouts: notes, journals, finance summaries; has a rendered night sibling
specimen: layout-library/playbook/themes/paper-and-ink.specimen.json
themeFile: layout-library/playbook/themes/paper-and-ink.theme.json
variants: layout-library/playbook/themes/paper-and-ink-night.theme.json
tokens: {"accentColor":"#1F3A93","pageBackground":"#FAF7F0","surfacePrimary":"#FFFFFF","foregroundColor":"#1A1A1A","secondaryColor":"#1A1A1A99","tertiaryColor":"#1A1A1A4D","borderWidth":1,"borderColor":"#1A1A1A14","cornerRadius":6,"controlPadding":8,"cardPadding":12,"fontDesign":"serif","blurEnabled":false,"toggle":{"trackColor":"#E9E4D8","trackActiveColor":"#1F3A93"},"slider":{"trackColor":"#E9E4D8","trackActiveColor":"#1F3A93"},"segmented":{"trackColor":"#F1ECE1","selectedColor":"#FFFFFF","textColor":"#1A1A1A99","selectedTextColor":"#1F3A93"},"stepper":{"buttonColor":"#1F3A931A","iconColor":"#1F3A93"}}
appearance: {"colorScheme":"light","statusBarStyle":"dark"}
---

# Paper & Ink

This pack is pinned light (`appearance.colorScheme: "light"`), so `--scheme` changes nothing in its pixels: the light render below was made with `--scheme light`, and a system-dark phone draws the same paper. For night use it has a separate, rendered dark sibling, [`paper-and-ink-night.theme.json`](paper-and-ink-night.theme.json), shown in [Night desk](#night-desk) below with its own sheet.

**When to use:** Reading-first layouts: notes, journals, finance summaries; has a rendered night sibling.

**Light and dark:** Pinned to light with scheme-neutral values in the base theme. Sibling variants: paper-and-ink-night.

Apply it by copying the `tokens` object into the layout `theme` (see [[theming]]) and the `appearance` object into the layout `appearance`. Rules that still apply to it are in [[style-rules]]. Themes need Connect+ Pro on the phone; without it the default glass look is drawn.
