# carter-0gj.10 — carterkit 0.13: local bindings, stage lint

Worktree: .worktrees/bead-carter-0gj.10, carterkit branch bead/carter-0gj.10 (off main 605f2d9).
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
- pyproject 0.13.0; CHANGELOG [0.13.0] + [0.12.0] heading dated 2026-09-23; README local-store paragraph.
- tests/test_local.py (73 tests), tests/local_eval.py (pure-Python stage evaluator, third engine),
  tests/fixtures/local-store.json (hand-built layout, lints clean).

## Verify
- python -m pytest -q  → 498 passed, 2 skipped (was 425 before)
- carterkit validate tests/fixtures/local-store.json → exit 0; broken copy (namespace shared + limit 1001) → exit 1
- A8 sample .worktrees/bead-carter-0gj.8/CAR-TER/SampleLayouts/book-logger.json → "No issues found"
- Fixture parity: all 11 A4 fixtures / 84 stages: lint verdict matches (13 error cases flagged, 71 valid
  stages clean) and the evaluator reproduces every expected scalar/groups/rows result.

## Not done / follow-ups
- PyPI publish (Carter). `carterkit version` prints 0.10.0 because the venv's editable-install metadata
  is stale (pre-existing; pyproject is the source of truth).
