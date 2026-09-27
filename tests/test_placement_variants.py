"""carter-m7s.24 — landscape / regular placement variants and grid.reflow lint the way
the app renders them: well-formed variants (inline or in `placements`) are clean, a
malformed one is a warning (the app drops it and renders the default), never an error."""
import carterkit


def _layout(child, grid=None):
    return {"name": "L", "version": 1, "tabs": [{"title": "A", "grid": grid or {"columns": 4, "rows": 4},
                                                "children": [child]}]}


def _gauge(**extra):
    return {"type": "gauge", "id": "g", "position": [0, 0], "span": [2, 2], **extra}


def _findings(layout, *kinds):
    return [f for f in carterkit.validate_layout(layout) if f["kind"] in kinds]


def test_inline_variants_are_known_fields():
    layout = _layout(_gauge(landscape={"position": [0, 4], "span": [2, 4]}, regular={"hidden": True}))
    assert _findings(layout, "unknown_field", "bad_placement") == []


def test_group_variants_are_known_fields():
    group = {"type": "group", "id": "grp", "position": [0, 0], "span": [2, 4],
             "grid": {"columns": 2, "rows": 2}, "landscape": {"hidden": True}, "children": []}
    assert _findings(_layout(group), "unknown_field", "bad_placement") == []


def test_sectioned_variants_are_clean():
    layout = _layout(_gauge())
    layout["schemaVersion"] = 2
    layout["placements"] = {"g": {"landscape": {"position": [0, 4]}, "regular": {"span": [3, 2]}}}
    assert [f for f in carterkit.validate_layout(layout)
            if f["kind"] in ("unknown_field", "bad_placement", "bad_section")] == []


def test_malformed_variant_is_a_warning():
    layout = _layout(_gauge(landscape={"position": [0], "hidden": "yes", "cell": 1}, regular=[1, 2]))
    found = _findings(layout, "bad_placement", "unknown_field")
    assert {f["severity"] for f in found} == {"warn"}
    assert len([f for f in found if f["kind"] == "bad_placement"]) == 3
    assert any("cell" in f["detail"] for f in found)


def test_reflow_values():
    assert _findings(_layout(_gauge(), {"columns": 4, "rows": 4, "reflow": "stretch"}), "bad_grid") == []
    assert _findings(_layout(_gauge(), {"columns": 4, "rows": 4, "reflow": "auto"}), "bad_grid") == []
    bad = _findings(_layout(_gauge(), {"columns": 4, "rows": 4, "reflow": "sideways"}), "bad_grid")
    assert [f["severity"] for f in bad] == ["warn"]
