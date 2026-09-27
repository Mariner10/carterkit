# layout-ops goldens (snapshot)

Copied 2026-09-27 from the app's
`/Users/carter/Desktop/Programming/Swift/CAR-TER/.worktrees/bead-carter-c1n.8/CAR-TERTests/Fixtures/layout-ops/`
(carter-c1n.8, then uncommitted). **Re-sync when carter-c1n.8 commits** (copy from
`CAR-TER/CAR-TERTests/Fixtures/layout-ops/`); do not hand-edit these files.

Shape: `{name, description, kit, input, batch{ops, base?, author}, expected | error}`.
`tests/test_patch.py` runs every file through `carterkit.patch.apply` (`kit: true` cases
must pass; known gaps are listed in `KNOWN_GAPS` there) and checks the differ round-trips
`input` → `expected`.
