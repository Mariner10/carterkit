"""Grid intelligence — pure occupancy math for a tab/group's child grid.

A CAR-TER grid is `columns` x `rows`; each child has `position: [row, col]` and
`span: [rowSpan, colSpan]` (default [1, 1]). These helpers let the editor place
controls without the LLM computing collisions by hand, and "see" the grid spatially.

Children are plain dicts in layout JSON form: {"id","type","position","span",...}.
"""

from __future__ import annotations

from typing import Optional


#: Never enumerate more cells than this for one child — a hostile `span` must not
#: turn a lint into a memory bomb. Anything larger is reported, not placed.
MAX_CELLS_PER_CHILD = 4096
#: Largest coordinate/span value the app could ever render; beyond it is a finding.
MAX_DIM = 10_000


def as_int(v) -> Optional[int]:
    """`v` as a grid integer, or None if it is not one (bool, float with a
    fraction, string, None, absurd magnitude). Never raises."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, int):
        return v if -MAX_DIM <= v <= MAX_DIM else None
    if isinstance(v, float):
        return int(v) if v == v and v not in (float("inf"), float("-inf")) \
            and v.is_integer() and -MAX_DIM <= v <= MAX_DIM else None
    return None


def child_span_or_none(child: dict) -> Optional[list[int]]:
    """`[rowSpan, colSpan]` if the child's span is well-formed (absent → [1, 1]),
    else None so the caller can report `bad_span` instead of guessing."""
    span = child.get("span")
    if span is None:
        return [1, 1]
    if not isinstance(span, list) or len(span) != 2:
        return None
    rs, cs = as_int(span[0]), as_int(span[1])
    if rs is None or cs is None:
        return None
    return [max(1, rs), max(1, cs)]


def child_span(child: dict) -> list[int]:
    """Lenient span: malformed → [1, 1]. Never raises."""
    return child_span_or_none(child) or [1, 1]


def child_position_or_none(child: dict) -> Optional[list[int]]:
    pos = child.get("position")
    if not isinstance(pos, list) or len(pos) != 2:
        return None
    r0, c0 = as_int(pos[0]), as_int(pos[1])
    if r0 is None or c0 is None:
        return None
    return [r0, c0]


def child_cells(child: dict) -> list[tuple[int, int]]:
    """The (row, col) cells a child occupies, given its position + span. Empty for
    a malformed position/span or a span too large to enumerate. Never raises."""
    pos = child_position_or_none(child)
    if pos is None:
        return []
    r0, c0 = pos
    rs, cs = child_span(child)
    if rs * cs > MAX_CELLS_PER_CHILD:
        return []
    return [(r, c) for r in range(r0, r0 + rs) for c in range(c0, c0 + cs)]


def occupancy(children: list[dict]) -> dict[tuple[int, int], str]:
    """Map of occupied cell -> the id of the (last) child occupying it."""
    cells: dict[tuple[int, int], str] = {}
    for child in children:
        cid = child.get("id", "?")
        for cell in child_cells(child):
            cells[cell] = cid
    return cells


def find_slot(children: list[dict], columns: int, rows: int,
              span: Optional[list[int]] = None) -> Optional[list[int]]:
    """First free [row, col] (row-major) where a `span`-sized block fits without
    overlap and within bounds. None if the grid has no room."""
    rs, cs = (span or [1, 1])
    rs, cs = max(1, as_int(rs) or 1), max(1, as_int(cs) or 1)
    taken = set(occupancy(children).keys())
    for r in range(0, rows - rs + 1):
        for c in range(0, columns - cs + 1):
            block = {(r + dr, c + dc) for dr in range(rs) for dc in range(cs)}
            if block.isdisjoint(taken):
                return [r, c]
    return None


def validate_placement(children: list[dict], columns: int, rows: int) -> list[dict]:
    """Structural placement issues: out-of-bounds and overlaps. Each issue is
    {"kind","ids"/"id","detail"}."""
    issues: list[dict] = []
    placeable: list[dict] = []
    # Out of bounds (and malformed geometry — reported, never raised)
    for child in children:
        if not isinstance(child, dict):
            continue
        cid = child.get("id", "?")
        pos = child_position_or_none(child)
        if pos is None:
            issues.append({"kind": "bad_position", "id": cid,
                           "detail": f"position must be [row, col] integers, got {child.get('position')!r}"})
            continue
        span = child_span_or_none(child)
        if span is None:
            issues.append({"kind": "bad_span", "id": cid,
                           "detail": f"span must be [rowSpan, colSpan] integers, got {child.get('span')!r}"})
            continue
        r0, c0 = pos
        rs, cs = span
        if r0 < 0 or c0 < 0 or r0 + rs > rows or c0 + cs > columns:
            issues.append({"kind": "out_of_bounds", "id": cid,
                           "detail": f"occupies rows {r0}-{r0+rs-1}, cols {c0}-{c0+cs-1} "
                                     f"but grid is {rows}x{columns}"})
            # A span larger than the whole grid several times over is not worth
            # enumerating for overlaps — it is already reported, and it may be hostile.
            if rs * cs > max(1, columns * rows) * 4 or rs * cs > MAX_CELLS_PER_CHILD:
                continue
        placeable.append(child)
    # Overlaps
    seen: dict[tuple[int, int], str] = {}
    reported: set[tuple[str, str]] = set()
    for child in placeable:
        cid = child.get("id", "?")
        for cell in child_cells(child):
            other = seen.get(cell)
            if other and other != cid:
                key = tuple(sorted((other, cid)))
                if key not in reported:
                    reported.add(key)
                    issues.append({"kind": "overlap", "ids": list(key),
                                   "detail": f"both occupy cell {list(cell)}"})
            else:
                seen[cell] = cid
    return issues


def _token(cid: str, width: int) -> str:
    cid = cid or "?"
    return cid[:width].ljust(width)


def render_grid(children: list[dict], columns: int, rows: int,
                cell_width: int = 6) -> str:
    """ASCII occupancy map. Each cell shows the id of its occupant (truncated),
    empty cells show dots. A child spanning multiple cells repeats its token."""
    grid_ids: dict[tuple[int, int], str] = occupancy(children)
    lines: list[str] = []
    header = "      " + " ".join(f"c{c}".ljust(cell_width) for c in range(columns))
    lines.append(header)
    for r in range(rows):
        row_cells = []
        for c in range(columns):
            cid = grid_ids.get((r, c))
            row_cells.append(_token(cid, cell_width) if cid else ("·" * cell_width))
        lines.append(f"r{r}".ljust(5) + " " + " ".join(row_cells))
    free = rows * columns - len(grid_ids)
    lines.append(f"\n({free} free cell(s) of {rows*columns})")
    return "\n".join(lines)
