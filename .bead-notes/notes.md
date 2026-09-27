# carter-0gj.10 — carterkit 0.14: local bindings, stage lint

Worktree: .worktrees/bead-carter-0gj.10, carterkit branch bead/carter-0gj.10.
Originally off main 605f2d9; REBASED 2026-09-27 onto main 4f83748 (= 0.13.1, after c1n.11 conformance
runner + 0.13.0 timer floors shipped to PyPI). Version is now 0.14.0 with its own CHANGELOG section.
B5 (CarterClient.local_*) and B6 (MCP) continue on THIS branch, not the description's feature/local-store.
(Dispatch note overrode the description's `carterkit-local-store` / `feature/local-store` worktree.)

## What landed
- carterkit/local.py (NEW): pure lint — lint_source / lint_stage / lint_op / fields_for + caps/enums.
  Deviation: the bead said "a new pure `_lint_stage` in validate.py"; it lives in its own module so
  B5 (CarterClient.local_*) and B6 (MCP) can reuse it. validate.py imports it.
- validate.py: `local` in _collect_source_refs, _ADDRESSED_METHODS, _validate_sources_defs (now
  returns a _SourceMap dict with `.local` schemas); _validate_local_sync; local branch in
  _validate_action_entry; second-local-source-needs-namespace + duplicate namespace checks.
  New finding kinds: bad_stage, unknown_collection. Local binding with no local source = error.
- bind.local / bind.local_op; Layout.source_local (shorthand {field:type} accepted).
- codegen (sync + action skip) and contract (appDirect in/out, address = collection / "op collection").
- ControlDocs re-vendored from .worktrees/local-store/CAR-TER/ControlDocs (feature/local-store @ 6d29b03c):
  +local-store.md; actions/index/sources/sync/privacy.md changed (privacy.md drift is from that branch, not A9).
- pyproject 0.14.0; CHANGELOG `## [0.14.0] — unreleased` (local store) above main's 0.13.1 / 0.13.0
  entries, which are untouched; README local-store paragraph.
- tests/test_local.py (73 tests), tests/local_eval.py (pure-Python stage evaluator, third engine),
  tests/fixtures/local-store.json (hand-built layout, lints clean).

## Verify
- python -m pytest -q  → 515 passed, 4 skipped after the rebase (498/2 before it). Skips are all
  env/path-adjacency: CARTER_CONFORMANCE_DIR unset (test_conformance) and app repo not adjacent
  (test_parity_acceptance). The local fixture-parity tests ran on all 11 A4 fixtures.
- carterkit validate tests/fixtures/local-store.json → exit 0; broken copy (namespace shared + limit 1001) → exit 1
- A8 sample .worktrees/bead-carter-0gj.8/CAR-TER/SampleLayouts/book-logger.json → "No issues found"
- Fixture parity: all 11 A4 fixtures / 84 stages: lint verdict matches (13 error cases flagged, 71 valid
  stages clean) and the evaluator reproduces every expected scalar/groups/rows result.

## Not done / follow-ups
- PyPI publish of 0.14.0 (Carter). Not pushed. `carterkit version` prints 0.10.0 because the venv's editable-install metadata
  is stale (pre-existing; pyproject is the source of truth).
