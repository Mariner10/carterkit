# Tutorial hooks

What a tutorial step can bind to: the app's **targets** (where the spotlight goes), **signals** (what a step's
`expect: {signal}` waits for) and **facts** (what `expect: {fact}` reads). They moved here from the retired guide
engine's `CAR-TER/Support/` (aif-6jc0k.12); the Swift names keep their `Support` prefix (spec Decision 8).

| File | What it holds |
|---|---|
| `SupportTargets.swift` | Every target id: fixed ids, and patterns with `<param>` segments (`control.<id>`, `editor.chip.<chip>`). |
| `SupportTargetRegistry.swift` | `.supportTarget("…")`: views publish their window frame under an id; the step card's spotlight reads it. Also the founder's "Show target ids" labels. |
| `SupportRegistry.swift` | `SupportSignal` and `SupportFact`, with what each signal carries and each fact's type and comparators. |
| `SupportSignals.swift` | `AppState.signal(_:target:value:)`, the one emit point; it reaches `TutorialRunner.handle`. |
| `SupportObservation.swift` | The observation loop: screen transitions become signals (`picker.open`, `pane.open`, `layout.stale`…), and every change asks the runner to read its facts again. |
| `SupportFacts.swift` | One switch, one line per fact; nil means "cannot read this now" and the expect does not hold. |
| `SupportCoordinator.swift` | `AppState.support`: binds the above to the app, started once at launch. |
| `SupportTabBarProbe.swift` | `header.tabs` and `canvas.tab.<n>` from the UIKit tab bar. |
| `SupportCardPlacement.swift` | The step card's one screen-edge placement helper (never over the spotlight). |
| `SupportRegistryExport.swift` | `SupportRegistry.export()`: targets, signals, facts and the bold-word labels, as `registry.json`. |

## registry.json

`scripts/tutorials-lint.py` checks every tutorial's targets, signals, facts and bold words against `registry.json`.
After adding a target, signal or fact, regenerate it from a test run: run `SupportRegistryExportTests` with
`CARTER_SUPPORT_REGISTRY_OUT=<dir>` set, then copy `<dir>/<appVersion>.json` over `registry.json` and lint:

```bash
python3 scripts/tutorials-lint.py CAR-TER/Tutorials --caps CAR-TER/ControlDocs/capabilities.json --registry CAR-TER/Tutorials/Hooks/registry.json
```
