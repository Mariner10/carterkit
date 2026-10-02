# Derive conformance fixtures

Shared by the app (`CAR-TERTests/LayoutDeriveTests.swift`) and carterkit
(`tests/test_derive.py`, a byte-identical copy in `carterkit/tests/fixtures/derive/`).
Edit them here, in the app repo, then copy the folder to carterkit.

- `derive-eval-*.json`: `{"description", "cases": [{"name", "derive", "inputs", "now", "expected"}]}`.
  `derive` is a layout's top-level block, `inputs` maps control ids to displayed
  values, `now` is epoch seconds. `expected` maps derive ids to the value (number,
  label string or null). An id missing from `expected` must not be evaluated at
  all (it sits on a cycle or reads a missing derive). Numbers compare within
  1e-9 relative.
- `derive-problems.json`: `{"cases": [{"name", "derive", "controls", "consumers", "problems"}]}`.
  `problems` is the ordered `[id, reason]` list the decoder refuses the block with.
