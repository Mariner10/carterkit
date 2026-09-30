"""Computed-field validation, matching Swift LocalCompute and LocalSourceSchema."""
import math


def lint_computed(collection, fields, types):
    out = []
    computed = {key for key, value in fields.items()
                if isinstance(value, dict) and value.get("compute") is not None}
    for key in sorted(computed):
        options = fields[key]
        prefix = f"collection {collection}: field {key} "
        def err(message):
            out.append(("error", prefix + message))
        if types.get(key) not in ("number", "integer"):
            err("compute needs a number field")
        if options.get("required") is True:
            err("is computed, so it can't be required")
        for option in ("default", "choices"):
            if options.get(option) is not None:
                err(f"is computed, so it can't have a {option}")
        try:
            inputs, dates = parse_compute(options["compute"])
        except ValueError as error:
            err(f"compute {error}")
            continue
        if not inputs:
            err("compute reads no field")
        for field in inputs:
            if field == key:
                err("compute reads itself")
            elif field not in types:
                err(f"compute reads undeclared field {field}")
            elif field in computed:
                err(f"compute reads computed field {field}")
            elif field in dates and types[field] != "date":
                err(f"compute: {field} is not a date")
            elif field not in dates and types[field] not in ("number", "integer", "bool"):
                err(f"compute: {field} is not a number")
    return out, computed


def parse_compute(formula):
    nodes = 0
    inputs, dates = [], set()
    def fail(reason):
        raise ValueError(reason)
    def walk(value, depth=1):
        nonlocal nodes
        nodes += 1
        if depth > 4:
            fail("nests deeper than 4")
        if nodes > 24:
            fail("has more than 24 parts")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if not math.isfinite(value):
                fail("has a number that is not finite")
            return None
        if not isinstance(value, dict) or len(value) != 1:
            fail("must be a number, {field} or one op")
        op, body = next(iter(value.items()))
        if op == "field":
            if not isinstance(body, str) or not body:
                fail("field must name a field")
            if body not in inputs:
                inputs.append(body)
            return body
        if op in ("add", "sub", "mul", "div"):
            if not isinstance(body, list) or not 2 <= len(body) <= 8:
                fail(f"{op} takes 2-8 inputs")
            for item in body:
                walk(item, depth + 1)
            return None
        if op in ("since", "until"):
            if not isinstance(body, dict) or "of" not in body or set(body) - {"of", "unit"}:
                fail(f"{op} takes {{of, unit}}")
            if body.get("unit", "days") not in ("seconds", "minutes", "hours", "days", "weeks"):
                fail(f"{op} unit must be seconds, minutes, hours, days or weeks")
            field = walk(body["of"], depth + 1)
            if field is None:
                fail(f"{op} reads one date field")
            dates.add(field)
            return None
        fail(f"has unknown op {op}")
    walk(formula)
    return inputs, dates
