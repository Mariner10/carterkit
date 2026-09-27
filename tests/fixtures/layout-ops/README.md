# layout-ops goldens (snapshot)

Synced from the app's closed carter-c1n.8 (`bead/carter-c1n.8` @ `3c474dd0`,
`CAR-TERTests/Fixtures/layout-ops/`, 27 files; identical to 1f34a8be, where the
carter-60fd divergences were fixed app-side). Re-sync from app master once c1n.8 lands
there, or whenever `LayoutOps.swift` changes (deferred work: carter-kow5). Do not
hand-edit these files.

Shape: `{name, description, kit, input, batch{ops, base?, author}, expected | error,
minted?}`. `minted: {"#0": "<regex>"}` names an id the applier mints; `expected` writes it
as `"$#0"` and the runner substitutes the real id (as the app's `LayoutOpsTests` does).
`tests/test_patch.py` runs every file through `carterkit.patch.apply` (`kit: true` cases
must pass; known gaps are listed in `KNOWN_GAPS` there), checks the inverse restores the
input, and checks the differ round-trips `input` → `expected`.
