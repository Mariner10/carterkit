---
type: theme-pack
label: Racing Livery
icon: flag.checkered
category: style
vibe: Gulf livery, graphite, orange and powder blue, carbon
accent: #7EC8E3
colorScheme: dark
lightDarkNotes: Pinned to dark; theme.dark carries the scheme-sensitive colours. Sibling variants: racing-livery-light.
whenToUse: Car, bike and sim telemetry; RPM hero in powder blue, action in orange; has a Paddock light variant
specimen: layout-library/playbook/themes/racing-livery.specimen.json
themeFile: layout-library/playbook/themes/racing-livery.theme.json
variants: layout-library/playbook/themes/racing-livery-light.theme.json
tokens: {"accentColor":"#FF6A00","cornerRadius":6,"fontFamily":"Avenir Next","borderWidth":1,"controlPadding":8,"cardPadding":10,"blurEnabled":false,"labelFontSize":12,"valueFontWeight":"heavy","tabBarTint":"#FF6A00","dark":{"pageBackground":"#0E0E10","pageBackgroundGradient":["#0E0E10","#18181C"],"surfacePrimary":"#FFFFFF0D","surfaceSecondary":"#FFFFFF08","borderColor":"#FFFFFF14","foregroundColor":"#F4F1EC","secondaryColor":"#F4F1EC99","tertiaryColor":"#F4F1EC4D"},"toggle":{"trackColor":"#FFFFFF1F","trackActiveColor":"#FF6A00"},"slider":{"trackColor":"#FFFFFF1F","trackActiveColor":"#FF6A00"},"segmented":{"trackColor":"#FFFFFF14","selectedColor":"#FF6A00","textColor":"#F4F1EC99","selectedTextColor":"#0E0E10"},"stepper":{"buttonColor":"#7EC8E326","iconColor":"#7EC8E3"}}
appearance: {"colorScheme":"dark","statusBarStyle":"light"}
---

# Racing Livery

A Gulf-style livery laid on carbon fibre. The page is a near-black #0E0E10 -> #18181C graphite gradient. Gulf orange #FF6A00 carries everything the driver acts on, and powder blue #7EC8E3 carries information and the normal operating band. The two colours meet on one surface on purpose: the RPM hero runs powder blue to 7000, Gulf orange through the 8200 shift band and red to the 9000 limiter, and a hairline orange-plus-blue stripe sits beside every tab title. Corners are cut tight at 6pt, and Avenir Next sets the type. The pack pins dark. A tested light sibling, Paddock, ships beside it for daylight pit boards. Themes are a Pro-only feature.

**When to use:** Car, bike and sim telemetry; RPM hero in powder blue, action in orange; has a Paddock light variant.

**Light and dark:** Pinned to dark; theme.dark carries the scheme-sensitive colours. Sibling variants: racing-livery-light.

Apply it by copying the `tokens` object into the layout `theme` (see [[theming]]) and the `appearance` object into the layout `appearance`. Rules that still apply to it are in [[style-rules]]. Themes need Connect+ Pro on the phone; without it the default glass look is drawn.
