# schema-v1 golden corpus (carter-m7s.8)

Inline (v1) documents that `LayoutSchemaCorpusTests` and carterkit's
`tests/test_schema_corpus.py` round-trip. Basenames are unique across all of
`Fixtures/` because the test target flattens its resources.

- `samples/` — snapshot of every `CAR-TER/SampleLayouts` file (`sample-` prefix). The
  live `SampleLayouts` folder also runs, so a new sample is covered at once.
- `library/` — snapshot of `layout-library/{beginner,intermediate,advanced,expert}`
  taken 2026-09-27 (`<tier>-` prefix; 39 of 56). Skipped: `playbook/` (drafts and
  chapter snippets, not finished layouts) and 17 layouts that no build decodes today
  (a `defaultValue` array, which `ControlValue` refuses; see the bug filed from
  carter-m7s.8): advanced-{ev-charger,film-set,hiking-companion,hospital-ward},
  expert-{factory-oee,film-post-pipeline,newsroom-live},
  intermediate-{baby-monitor,bike-trainer,car-diagnostics,dj-deck-lite,
  espresso-machine,greenhouse,podcast-studio,pool-spa,sprint-board,stream-deck}.
- `conformance/` — carter-c1n.11's accept set (v1 files, `conformance-` prefix).

`schema-v2/` holds the sectioned counterparts: carterkit `to_sectioned()` renditions
(`*-sectioned.json`, compared model-for-model with their v1 original) and c1n.11's two
v2 accept files. A new grammar adds one `schema-v<N>/` folder and one
`LayoutMigrator.Step`.
