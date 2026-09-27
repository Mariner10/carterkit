# layout-ops goldens (snapshot)

Synced from the app's committed carter-c1n.8 (`origin/bead/carter-c1n.8` @ `1f34a8be`,
`CAR-TERTests/Fixtures/layout-ops/`, 27 files). **Re-sync when c1n.8 lands on master**
(copy from `CAR-TER/CAR-TERTests/Fixtures/layout-ops/`); do not hand-edit these files.

Shape: `{name, description, kit, input, batch{ops, base?, author}, expected | error,
minted?}`. `minted: {"#0": "<regex>"}` names an id the applier mints; `expected` writes it
as `"$#0"` and the runner substitutes the real id (as the app's `LayoutOpsTests` does).
`tests/test_patch.py` runs every file through `carterkit.patch.apply` (`kit: true` cases
must pass; known gaps are listed in `KNOWN_GAPS` there), checks the inverse restores the
input, and checks the differ round-trips `input` → `expected`.
