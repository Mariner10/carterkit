"""carterkit.canonical — RFC 8785 JCS + layout contentDigest.

The RFC vectors below are independent of our implementation (straight from RFC
8785 §3.2.2/§3.2.3 and Appendix B). The golden fixture file is the cross-language
contract: CAR-TERTests/LayoutDigestTests.swift runs the very same file.
"""
import json
import re
from pathlib import Path

import pytest

from carterkit import canonical as c

FIXTURES = Path(__file__).parent / "fixtures" / "canonical-fixtures.json"


def _fixtures():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


# ── RFC 8785 vectors ─────────────────────────────────────────────────────────

def test_rfc8785_section_3_2_2_example():
    text = (r'{"numbers":[333333333.33333329,1E30,4.50,2e-3,0.000000000000000000000000001],'
            r'"string":"\u20ac$\u000F\u000aA' "'" r'\u0042\u0022\u005c\\\"\/",'
            r'"literals":[null,true,false]}')
    expected = ('{"literals":[null,true,false],"numbers":[333333333.3333333,1e+30,4.5,0.002,1e-27],'
                '"string":"€$\\u000f\\nA\'B\\"\\\\\\\\\\"/"}')
    assert c.canonical_json(c.loads(text)) == expected


def test_rfc8785_utf16_key_order():
    text = (r'{"€":"Euro Sign","\r":"Carriage Return","דּ":"Hebrew Letter Dalet With Dagesh",'
            r'"1":"One","😀":"Emoji: Grinning Face","\u0080":"Control",'
            r'"ö":"Latin Small Letter O With Diaeresis"}')
    keys = list(json.loads(c.canonical_json(c.loads(text))))
    assert keys == ["\r", "1", "\u0080", "ö", "€", "\U0001F600", "דּ"]


@pytest.mark.parametrize("value,expected", [
    (0.0, "0"), (-0.0, "0"), (1.0, "1"), (-1.0, "-1"), (100, "100"),
    (4.5, "4.5"), (0.002, "0.002"), (1e-27, "1e-27"), (1e30, "1e+30"),
    (1e21, "1e+21"), (1e20, "100000000000000000000"), (1e16, "10000000000000000"),
    (9007199254740992, "9007199254740992"), (5e-324, "5e-324"),
    (-5e-324, "-5e-324"), (1.7976931348623157e308, "1.7976931348623157e+308"),
    (0.000001, "0.000001"), (1e-7, "1e-7"), (123.456, "123.456"),
    (-1.5e-10, "-1.5e-10"), (333333333.33333329, "333333333.3333333"),
    (295147905179352830000, "295147905179352830000"),
    (1.2345e21, "1.2345e+21"), (0.1 + 0.2, "0.30000000000000004"),
])
def test_es6_number_serialization(value, expected):
    assert c.canonical_json(value) == expected


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf"), 10 ** 400])
def test_non_finite_numbers_are_errors(bad):
    with pytest.raises(ValueError):
        c.canonical_json(bad)


def test_nan_literal_rejected_on_parse():
    with pytest.raises(ValueError):
        c.loads('{"a": NaN}')


def test_bool_is_not_a_number():
    assert c.canonical_json([True, False, 1, 0]) == "[true,false,1,0]"


def test_string_escapes():
    assert c.canonical_json("\x00\x1f\b\t\n\f\r\"\\/é😀") == '"\\u0000\\u001f\\b\\t\\n\\f\\r\\"\\\\/é😀"'


# ── golden fixtures (shared with the app) ────────────────────────────────────

@pytest.mark.parametrize("case", _fixtures()["canonical"], ids=lambda k: k["name"])
def test_golden_canonical(case):
    assert c.canonical_json(c.loads(case["input"])) == case["output"]


@pytest.mark.parametrize("case", _fixtures()["digest"], ids=lambda k: k["name"])
def test_golden_digest(case):
    layout = c.loads(case["input"])
    assert c.canonical_json(c.digest_scope(layout)) == case["scope"]
    assert c.content_digest(layout) == case["digest"]
    assert c.content_digest(case["input"]) == case["digest"]
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", case["digest"])


def test_same_template_different_tokens_same_digest():
    groups = {}
    for case in _fixtures()["digest"]:
        if case.get("group"):
            groups.setdefault(case["group"], set()).add(c.content_digest(case["input"]))
    assert groups, "fixtures must carry at least one same-digest group"
    for name, digests in groups.items():
        assert len(digests) == 1, name


def test_different_content_different_digest():
    a = {"title": "Fern", "tabs": []}
    b = {"title": "Fern!", "tabs": []}
    assert c.content_digest(a) != c.content_digest(b)


def test_digest_scope_does_not_mutate_input():
    layout = {"connection": {"url": "wss://x", "token": "t"}, "provenance": {"parents": []},
              "extensions": {"editor": {"zoom": 2}, "other": 1}}
    before = json.dumps(layout, sort_keys=True)
    scope = c.digest_scope(layout)
    assert json.dumps(layout, sort_keys=True) == before
    assert scope == {"connection": {"url": "wss://x"}, "extensions": {"other": 1}}


def test_key_order_and_whitespace_do_not_matter():
    a = '{"b": 1, "a": [1.0, 2.50], "c": {"y": true, "x": null}}'
    b = '{"c":{"x":null,"y":true},"a":[1,2.5],"b":1}'
    assert c.content_digest(a) == c.content_digest(b)


# ── one implementation ───────────────────────────────────────────────────────

def test_no_other_canonical_json_in_carterkit():
    """sort_keys-style digests must not creep back in: the only JSON canonicalizer
    (and the only sha256-of-JSON) lives in carterkit/canonical.py."""
    pkg = Path(c.__file__).parent
    offenders = []
    for path in pkg.rglob("*.py"):
        if path.name == "canonical.py":
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"sort_keys\s*=\s*True|def\s+canonical_json|def\s+layout_hash", text):
            offenders.append(path.name)
    assert offenders == []
