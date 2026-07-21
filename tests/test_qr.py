"""Structural tests for carterkit.qr — shape, quiet zone, error handling. Always
run, no dev-only dependency. The oracle comparison against the `qrcode` PyPI
package lives in test_qr_oracle.py (skipped when that package isn't installed)
so a missing dev dependency can't skip these too."""

import pytest

from carterkit import qr


# ── shape / structure ────────────────────────────────────────────────────

def test_size_matches_version_formula():
    for version, text in [(1, "a"), (2, "b" * 20)]:
        code = qr.encode(text, ecc="M")
        assert code.version >= version
        assert code.size == code.version * 4 + 17
        assert len(code.matrix) == code.size
        assert all(len(row) == code.size for row in code.matrix)


def test_finder_patterns_present_at_three_corners():
    code = qr.encode("hello", ecc="M")
    n = code.size

    def is_finder(r0, c0):
        # outer ring dark, inner ring light, 3x3 core dark — the classic
        # concentric-square finder pattern, at every version.
        for r in range(7):
            for c in range(7):
                dark = (r in (0, 6) or c in (0, 6)) or (2 <= r <= 4 and 2 <= c <= 4)
                if bool(code.matrix[r0 + r][c0 + c]) != dark:
                    return False
        return True

    assert is_finder(0, 0)
    assert is_finder(0, n - 7)
    assert is_finder(n - 7, 0)


def test_timing_pattern_alternates():
    code = qr.encode("hello", ecc="M")
    row = code.matrix[6][8:code.size - 8]
    assert row == [i % 2 == 0 for i in range(len(row))]


def test_higher_ecc_or_longer_data_needs_more_room():
    small = qr.encode("hi", ecc="L")
    bigger = qr.encode("hi" * 200, ecc="L")
    assert bigger.version > small.version
    same_data_more_ecc = qr.encode("x" * 100, ecc="M")
    same_data_less_ecc = qr.encode("x" * 100, ecc="L")
    assert same_data_more_ecc.version >= same_data_less_ecc.version


def test_deterministic_for_the_same_input():
    a = qr.encode("carterkit pairing payload", ecc="M")
    b = qr.encode("carterkit pairing payload", ecc="M")
    assert a.matrix == b.matrix and a.mask == b.mask and a.version == b.version


def test_empty_string_encodes():
    code = qr.encode("", ecc="M")
    assert code.version == 1


def test_unsupported_ecc_rejected():
    with pytest.raises(ValueError):
        qr.encode("x", ecc="Q")


def test_too_long_raises():
    cap = qr._byte_capacity(40, "L")
    with pytest.raises(qr.QRTooLong):
        qr.encode("x" * (cap + 1), ecc="L")


# ── quiet zone ───────────────────────────────────────────────────────────

def test_svg_quiet_zone_is_light_and_sized_correctly():
    code = qr.encode("hello", ecc="M")
    svg = code.svg(module_size=2, quiet_zone=4)
    expected_px = (code.size + 8) * 2
    assert f'width="{expected_px}"' in svg
    assert f'height="{expected_px}"' in svg
    # a light backing rect must be drawn before the dark modules, so a dark
    # page background never bleeds into the scan area
    assert svg.index('fill="#fff"') < svg.index("<g")


def test_ascii_quiet_zone_is_blank_border():
    code = qr.encode("hi", ecc="M")
    art = code.ascii(quiet_zone=3)
    lines = art.split("\n")
    # the top printed line is entirely quiet zone (3 blank module-rows,
    # packed 2-per-line) — must be all spaces
    assert lines[0].strip() == ""
    # first 3 columns of every line are quiet zone too
    assert all(line[:3] == "   " for line in lines)


def test_ascii_pairs_rows_into_half_block_chars():
    code = qr.encode("h", ecc="M")
    art = code.ascii(quiet_zone=0)
    lines = art.split("\n")
    assert len(lines) == (code.size + 1) // 2
    assert all(ch in " ▀▄█" for line in lines for ch in line)
