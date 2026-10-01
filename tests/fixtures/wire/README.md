# Wire golden fixtures

Shared golden cases for how a sync binding (`filter` + `valuePath`) treats one
incoming frame. `carterkit/wire.py` is the Python reference evaluator and
`tests/test_wire.py` runs every file here. The app's D1 refactor (carter-9dd.2)
copies this folder to `CAR-TERTests/Fixtures/wire/` and must pass the same cases,
so the MCP lint and the app can't drift.

One case per `NN-<name>.json`. Files are UTF-8; numbers keep their JSON spelling
(`1` vs `1.0` matters to Python, not to the app).

## Schema

```jsonc
{
  "name": "filter-msg-type-typo",          // unique, kebab-case (matches the file name)
  "note": "why this case exists",
  "frame": <any JSON>,                     // the decoded incoming payload
  "filter": <JSON or null>,                // optional; absent or null = no filter
  "valuePath": "a.b.0",                    // optional; absent = whole frame
  "expect": {
    "outcome": "delivered" | "filter_miss" | "path_miss" | "type_miss",
    "value": <any JSON>,                   // delivered / type_miss: value at the path
    "near": true,                          // filter_miss: worth reporting as a near miss
    "filterMisses": [                      // filter_miss: failing keys, sorted by key
      {"key": "msg_type", "expected": "telemetry",
       "present": true, "actual": "telemetery", "near": true}
    ],                                     // "actual" is omitted when present == false
    "pathMiss": {"segment": "-1", "index": 1, "reason": "bad_index"},
    "typeMiss": "null" | "object" | "array",
    "logSource": <any JSON>                // optional: logEntrySource(frame, valuePath)
  }
}
```

Keys absent from `expect` are not asserted.

## Rules the cases pin down

- **Order**: filter, then path, then (scalar controls) value type.
- **Filter** (`jsonMatches`): frame and filter must both be objects. Each
  top-level filter key must be present with an equal value; a filter key with a
  dot is a literal key. Equality is whole-value: objects by key set and values,
  arrays in order. Numbers are doubles (`1 == 1.0`); a bool is never a number
  (`true != 1`, `0 != false`); `"1" != 1`. `{}` matches any object frame.
- **Near miss**: a failing key that is present with another value. For
  `msg_type`, only when the two strings are within Levenshtein distance 2. An
  absent key is never near. The case is `near` overall when some miss is near
  and no `msg_type` miss is far (unrelated traffic is never promoted).
- **Path**: split on `.` and drop empty segments (`a..b`, `.a`, `a.`, `.` = no
  segments = whole frame). An object looks the segment up as a key (even `"0"`).
  An array parses it with Swift `Int(_:)`: ASCII digits, optional `+`/`-`, no
  whitespace or `_`, Int64 range; then `0 <= i < count`. `-0` parses to `0`.
- **pathMiss**: `index` is the 0-based position among the *non-empty* segments.
  `reason`: `missing_key` (object lacks it), `bad_index` (not an Int, or
  negative), `out_of_range`, `not_container` (scalar or null mid-walk).
- **Type**: a scalar control renders bool, number or string only.
- **logSource** (`logEntrySource`): the object/array at the path, else the whole
  frame (scalar result or failed walk both fall back).
