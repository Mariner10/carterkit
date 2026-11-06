"""Palette tokens + raw-colour lint (carter-m7s.16). Mirrors the app's
PaletteTokenTests: refs resolve in colour positions only, unknown refs drop, and a
raw colour equal to a token is a warning suggesting the `$name`."""

import copy
from pathlib import Path

from carterkit import catalog, palette, validate

CAT = catalog.build_catalog(Path(__file__).parent.parent / "carterkit" / "controldocs", include_theme=True)


def _layout():
    return {
        "schemaVersion": 2, "name": "Tokens", "version": 1,
        "theme": {"palette": {"brand": "#0A84FF", "leaf": "#34C759", "ink": "#101010"},
                  "accentColor": "$brand", "pageBackgroundGradient": ["$ink", "#202020"],
                  "dark": {"foregroundColor": "$leaf"}},
        "appearance": {"header": {"style": "color", "dark": "$ink"}},
        "tabs": [{"title": "A", "icon": "star", "grid": {"columns": 2, "rows": 4}, "children": [
            {"type": "gauge", "id": "c_inline", "label": "$brand", "position": [0, 0],
             "tint": "$leaf", "theme": {"trackColor": "$ink"},
             "sync": [{"method": "meshsocket", "event": "$brand"}]},
            {"type": "gauge", "id": "c_styled", "position": [1, 0]},
            {"type": "group", "id": "g_bed", "position": [2, 0], "grid": {"columns": 1, "rows": 2},
             "theme": {"accentColor": "$leaf"},
             "children": [{"type": "button", "id": "c_kid", "label": "Go", "position": [0, 0],
                           "tint": "$nope"}]},
        ]}],
        "styles": {"c_styled": {"tint": "$brand"}},
    }


def _kinds(findings, kind):
    return [f for f in findings if f["kind"] == kind]


def test_resolve_matches_the_app():
    out = palette.resolve(_layout())
    assert out["theme"]["accentColor"] == "#0A84FF"
    assert out["theme"]["pageBackgroundGradient"] == ["#101010", "#202020"]
    assert out["theme"]["dark"]["foregroundColor"] == "#34C759"
    assert out["appearance"]["header"]["dark"] == "#101010"
    kids = out["tabs"][0]["children"]
    assert kids[0]["tint"] == "#34C759" and kids[0]["theme"]["trackColor"] == "#101010"
    assert kids[0]["label"] == "$brand", "non-colour strings are never rewritten"
    assert kids[0]["sync"][0]["event"] == "$brand", "wire blocks are never rewritten"
    assert out["styles"]["c_styled"]["tint"] == "#0A84FF"
    assert kids[2]["theme"]["accentColor"] == "#34C759"
    assert "tint" not in kids[2]["children"][0], "unknown refs drop"
    assert out["theme"]["palette"]["brand"] == "#0A84FF"


def test_unknown_token_is_a_warning():
    findings = validate.validate_layout(_layout(), CAT)
    unknown = _kinds(findings, "unknown_token")
    assert [f["where"] for f in unknown] == ["tabs[0].children[2].children[0].tint"]
    assert all(f["severity"] == "warn" for f in unknown)
    assert not _kinds(findings, "palette_literal")


def test_raw_colour_equal_to_a_token_suggests_the_name():
    layout = _layout()
    layout["tabs"][0]["children"][1]["tint"] = "#0a84ff"          # inline, lower case
    layout["styles"]["c_styled"]["theme"] = {"trackColor": "#34C759FF"}  # opaque alpha
    layout["tabs"][0]["children"][0]["label"] = "#0A84FF"          # a label, not a colour
    findings = validate.validate_layout(layout, CAT)
    lit = {f["where"]: f for f in _kinds(findings, "palette_literal")}
    assert set(lit) == {"tabs[0].children[1].tint", "styles.c_styled.theme.trackColor"}
    assert "'$brand'" in lit["tabs[0].children[1].tint"]["detail"]
    assert "'$leaf'" in lit["styles.c_styled.theme.trackColor"]["detail"]
    assert all(f["severity"] == "warn" for f in lit.values())


def test_bad_palette_entries_are_reported():
    layout = _layout()
    layout["theme"]["palette"].update({"num": 7, "chain": "$brand", "bad name": "#00FF00"})
    findings = validate.validate_layout(layout, CAT)
    assert {f["where"] for f in _kinds(findings, "bad_palette")} == {
        "theme.palette.num", "theme.palette.chain", "theme.palette.bad name"}
    assert palette.palette(layout) == {"brand": "#0A84FF", "leaf": "#34C759", "ink": "#101010"}


def test_layouts_without_a_palette_get_no_palette_findings():
    plain = {
        "name": "Plain", "version": 1, "theme": {"accentColor": "#FF0000"},
        "tabs": [{"title": "A", "icon": "star", "grid": {"columns": 1, "rows": 2}, "children": [
            {"type": "gauge", "id": "c_a", "label": "$5 off", "position": [0, 0], "tint": "#FF0000",
             "theme": {"trackColor": "#101010"}}]}],
    }
    before = copy.deepcopy(plain)
    findings = validate.validate_layout(plain, CAT)
    assert not [f for f in findings if f["kind"] in {"palette_literal", "unknown_token", "bad_palette"}]
    assert palette.resolve(plain) == before


def test_role_pairs_are_not_bad_palette_entries():
    """Colour roles (app aif-5g98i.1): a role may be a {light, dark} pair; it is not a
    `$name` token, so `$primary` against a pair is an unknown token with its own hint."""
    layout = _layout()
    layout["theme"]["palette"].update({"primary": {"light": "#111111", "dark": "#EEEEEE"},
                                       "neutral": "#888888", "brand2": {"light": "#111111"}})
    layout["tabs"][0]["children"][1]["tint"] = "$primary"
    findings = validate.validate_layout(layout, CAT)
    bad = {f["where"] for f in _kinds(findings, "bad_palette")}
    assert "theme.palette.primary" not in bad
    assert "theme.palette.brand2" in bad, "only the four roles may be pairs"
    unknown = {f["where"]: f["detail"] for f in _kinds(findings, "unknown_token")}
    assert "light and dark" in unknown["tabs[0].children[1].tint"]
    tokens = palette.palette(layout)
    assert tokens["neutral"] == "#888888", "a plain role is still a token"
    assert "primary" not in tokens
    assert palette.is_role_pair("secondary", {"dark": "#00FF00"})
    assert not palette.is_role_pair("secondary", {"dark": "green"})


def test_control_colors_values_are_checked():
    """A control's `colors` (app aif-5g98i.1): roles, theme colour keys, `$name`s and hexes
    (each with an optional `@opacity`) pass; anything else warns, since the app draws the
    slot's default instead. A tab may carry its own `palette`."""
    layout = {
        "schemaVersion": 2, "name": "Roles", "version": 1,
        "theme": {"palette": {"primary": {"light": "#111111", "dark": "#EEEEEE"}}},
        "tabs": [{"title": "A", "icon": "star", "grid": {"columns": 2, "rows": 4},
                  "palette": {"secondary": "#00FF00"}, "children": [
            {"type": "gauge", "id": "c_ok", "label": "Ok", "position": [0, 0],
             "colors": {"arc": "secondary", "track": "neutral@0.2"}},
            # gauge's doc declares its slots (arc, track) since aif-5g98i.2: a theme colour key in a real slot
            {"type": "gauge", "id": "c_key", "label": "Key", "position": [1, 1],
             "colors": {"track": "secondaryColor"}},
            {"type": "gauge", "id": "c_bad", "label": "Bad", "position": [1, 0],
             "colors": {"arc": "blue", "track": "primary@2"}},
            {"type": "gauge", "id": "c_list", "label": "List", "position": [0, 1],
             "colors": ["primary", "#FF0000", 3]},
        ]}],
    }
    findings = validate.validate_layout(layout, CAT)
    assert not [f for f in findings if f["kind"] == "unknown_field"]
    bad = sorted(f["detail"].split(" = ")[0] for f in _kinds(findings, "bad_colors"))
    assert bad == ["gauge.colors", "gauge.colors.arc", "gauge.colors.track"]
    assert all(f["severity"] == "warn" for f in _kinds(findings, "bad_colors"))
    assert not _kinds(findings, "bad_palette")
