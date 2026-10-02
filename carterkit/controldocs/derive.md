---
type: derive
label: Derive
icon: function
category: system
fields:
  - name: control
    type: string
    description: "Argument: {control: id} reads whatever that control currently displays"
  - name: derive
    type: string
    description: "Argument: {derive: id} reads another derive entry's result"
  - name: clock
    type: bool
    description: "Argument: {clock: true} is now, as epoch seconds"
  - name: add
    type: array
    description: "Sum of the arguments; sum is an alias"
  - name: sub
    type: array
    description: First argument minus each of the rest
  - name: mul
    type: array
    description: Product of the arguments
  - name: div
    type: array
    description: First argument divided by each of the rest (nil on a zero divisor)
  - name: min
    type: array
    description: Smallest argument
  - name: max
    type: array
    description: Largest argument
  - name: avg
    type: array
    description: Mean of the arguments
  - name: coalesce
    type: array
    description: The first argument that is not nil (its value as-is, number or text)
  - name: abs
    type: object
    description: Absolute value of one argument
  - name: round
    type: object
    description: "{of, places}: round to places decimals (0-12, default 0); a bare argument rounds to a whole number"
  - name: clamp
    type: object
    description: "{of, min, max}: keep the value inside min..max (either bound may be omitted, not both)"
  - name: scale
    type: object
    description: "{of, from: [a, b], to: [c, d]}: linear map of a..b onto c..d (not clamped)"
  - name: band
    type: object
    description: "{of, stops, labels}: number to a label; labels[i] for the first stop the value is below, else the last label"
  - name: since
    type: object
    description: "{of, unit}: time elapsed since a date (epoch seconds or ISO-8601), in seconds/minutes/hours/days/weeks"
  - name: until
    type: object
    description: "{of, unit}: time remaining until a date, negative once it has passed"
---

Values the phone computes from other values, with no server and no code. A
layout's top-level `derive` object is keyed by id; each entry is a small JSON
op tree. A control shows one with a [[sync]] entry of `method: "derive"`.

## Definition

```json
"derive": {
  "watts":   { "mul": [ {"control": "volts"}, {"control": "amps"} ] },
  "avgC":    { "avg": [ {"control": "t1"}, {"control": "t2"}, {"control": "t3"} ] },
  "avgF":    { "scale": {"of": {"derive": "avgC"}, "from": [0, 100], "to": [32, 212]} },
  "tankPct": { "clamp": {"of": {"mul": [ {"div": [ {"control": "level"}, 180 ]}, 100 ]},
                         "min": 0, "max": 100} },
  "comfort": { "band": {"of": {"derive": "avgC"}, "stops": [18, 24],
                        "labels": ["cold", "ok", "warm"]} }
}
```

```json
{ "type": "gauge", "id": "wattsGauge", "min": 0, "max": 1800, "formatValue": "integer",
  "sync": [ { "method": "derive", "from": "watts" } ] }
```

Formulas are JSON structure, never strings. Each node is an object with exactly
one key: the op.

## Arguments

An argument is one of four things:

| Form | Reads |
|------|-------|
| `42` | a number literal |
| `{"control": "volts"}` | whatever control `volts` currently displays, from any transport (meshsocket, MQTT, HTTP, sensor, local store) or a user gesture |
| `{"derive": "watts"}` | another derive entry's result |
| a nested node | `{"div": [{"control": "level"}, 180]}` |

`{"clock": true}` is now, as epoch seconds.

## Ops

| Op | Shape | Result |
|----|-------|--------|
| `add` / `sum` | `[a, b, ...]` | a + b + ... |
| `sub` | `[a, b, ...]` | a − b − ... |
| `mul` | `[a, b, ...]` | a × b × ... |
| `div` | `[a, b, ...]` | a ÷ b ÷ ...; nil when any divisor is 0 |
| `min` / `max` | `[a, b, ...]` | smallest / largest |
| `avg` | `[a, b, ...]` | mean |
| `coalesce` | `[a, b, ...]` | the first argument that is not nil, as-is (a number or a label) |
| `abs` | `a` or `[a]` | absolute value |
| `round` | `{"of": a, "places": 2}` or `a` | rounded to `places` decimals (0-12, default 0); half rounds away from zero |
| `clamp` | `{"of": a, "min": lo, "max": hi}` | a kept inside lo..hi; either bound may be omitted, not both; bounds may be arguments |
| `scale` | `{"of": a, "from": [0, 100], "to": [32, 212]}` | linear map, not clamped; nil when `from` has equal ends |
| `band` | `{"of": a, "stops": [20, 30], "labels": ["low", "ok", "high"]}` | `labels[i]` for the first `stops[i]` that a is below, else the last label; `labels` has one more entry than `stops`, stops strictly ascending |
| `since` | `{"of": date, "unit": "days"}` or `date` | time since `date`; unit `seconds` (default), `minutes`, `hours`, `days`, `weeks` |
| `until` | `{"of": date, "unit": "hours"}` or `date` | time until `date`, negative once it has passed |

The n-ary ops need at least one argument. `round` is for maths such as "whole
litres"; display formatting stays in `formatValue`. `band` pairs with
`colorMap` / `iconMap` to turn a raw number into a [[status-light]].

A `since` / `until` date is an ISO-8601 or `yyyy-MM-dd` string, or an epoch
number (seconds; milliseconds when larger than 10^11). Nodes that read the
clock are re-evaluated on a coarse tick only while the layout is open: every
second for `seconds` and `clock`, every 5 s for `minutes`, every minute
otherwise.

## Value rules

- **Coercion.** Numbers pass through, `true`/`false` count as 1/0, and numeric
  strings parse (`" 121.5 "` is 121.5). Anything else is unreadable.
- **Nil propagates.** An unreadable or missing input makes the node nil, and
  every node that reads it is nil too (except `coalesce`, which skips it). A
  control bound to a nil derive keeps its `defaultValue`.
- **Never infinite.** Division by zero, or any result that is not finite, is
  nil, never inf.
- **Unknown ops fail closed.** An op this app does not know evaluates to nil for
  that node and everything downstream. The layout still loads, so a newer layout
  degrades instead of failing. carterkit's validator flags it as an error.
- **No side effects.** A derive never fires an action, never builds a string
  beyond a `band` label, and never loops.

## Graph rules

A layout is refused at import (and an entry dropped when repaired from disk)
when:

- a derive id collides with a control id;
- a `{"control": id}` or `{"derive": id}` names something that does not exist;
- the graph has a cycle, including one through a binding: control X shows derive
  `d` and `d` reads X;
- it is over the caps: 256 op nodes in the whole block, 16 levels of nesting,
  32 arguments to one op.

A sync entry with `method: "derive"` needs `from`, naming a declared derive id.

## Where the value lives

- **Per device.** Derived values never go on the wire. Every device recomputes
  them from what it displays, so room members can briefly disagree while their
  inputs differ. Room snapshots and state sync leave derived consumers out.
- **What the user sees.** While an ack'd command is pending, the graph reads
  the optimistic on-screen value, so derived tiles never tear.
- **Relay alerts cannot see derived values.** Alerts are evaluated on the relay
  from server-readable frames; a derived value only exists on the phone.
- **Live Activities can disagree.** A server-pushed Live Activity (bridge
  notify) never passes through the phone's graph, so it can show a different
  number from the on-screen derived tile. Point [[glance]] slots at the
  consuming control so the app-driven surfaces stay in step.
- **Older apps** ignore `derive`; a consumer just shows its `defaultValue`.
  Pair a derive layout with `requires` (see [[layout-config]]).
- **E2EE rooms.** Evaluation happens after decryption on the device; the relay
  learns nothing new.

## Notes

- A derived value lives under its own id, so a visibility condition can watch it
  with `{"control": "watts"}` like any control (see
  [[visibility]]).
- carterkit ships a reference evaluator (`carterkit.derive`) and shared fixtures
  that the app's tests run too, so Python and Swift compute the same numbers.
