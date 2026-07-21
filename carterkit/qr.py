"""A compact, dependency-free QR Code encoder (ISO/IEC 18004), byte mode only.

Vendored so `carterkit explore`'s pairing card and `carterkit.cli`'s terminal QR
never need a runtime dependency. Versions 1-40, error correction L or M (the two
levels CAR-TER's pairing payloads need — Q/H aren't wired up). Auto-selects the
smallest version that fits the data, matches the standard mask-penalty rules for
mask selection, and is verified byte-for-byte against the `qrcode` PyPI package
(dev-only oracle, see `tests/test_qr.py`) for the same content/version/ecc/mask.

Public surface: :func:`encode` → :class:`QRCode` (``.matrix`` is a list of
``size`` rows of ``size`` bools, ``True`` = dark module).
"""
from __future__ import annotations

from dataclasses import dataclass

__all__ = ["encode", "QRCode", "QRTooLong"]


class QRTooLong(ValueError):
    """The data doesn't fit in any version 1-40 at the requested ECC level."""


@dataclass
class QRCode:
    version: int
    ecc: str
    mask: int
    size: int
    matrix: list[list[bool]]

    def svg(self, *, module_size: int = 8, quiet_zone: int = 4,
            dark: str = "#000", light: str = "#fff") -> str:
        """A self-contained SVG rendering, `light`-backed quiet zone included —
        handy standalone, though `explore_html`'s JS draws its own <rect>s from
        `.matrix` so the page controls colors/theme instead."""
        n = self.size + quiet_zone * 2
        px = n * module_size
        cells = []
        for r, row in enumerate(self.matrix):
            for c, dot in enumerate(row):
                if dot:
                    x = (c + quiet_zone) * module_size
                    y = (r + quiet_zone) * module_size
                    cells.append(f'<rect x="{x}" y="{y}" width="{module_size}" height="{module_size}"/>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {px} {px}" '
                f'width="{px}" height="{px}">'
                f'<rect width="{px}" height="{px}" fill="{light}"/>'
                f'<g fill="{dark}">{"".join(cells)}</g></svg>')

    def ascii(self, *, quiet_zone: int = 2) -> str:
        """Terminal rendering: two module-rows per printed line via Unicode
        half-block characters, so the whole code fits in a normal window."""
        n = self.size
        total = n + quiet_zone * 2

        def dark(r: int, c: int) -> bool:
            rr, cc = r - quiet_zone, c - quiet_zone
            return 0 <= rr < n and 0 <= cc < n and self.matrix[rr][cc]

        lines = []
        for r in range(0, total, 2):
            chars = []
            for c in range(total):
                top, bot = dark(r, c), dark(r + 1, c)
                chars.append("█" if top and bot else "▀" if top else "▄" if bot else " ")
            lines.append("".join(chars))
        return "\n".join(lines)


# ── standard tables (ISO/IEC 18004) ─────────────────────────────────────────
# Reed-Solomon block structure per version (index 0 = version 1), each entry a
# flat tuple of (block_count, total_codewords, data_codewords) groups — a
# version with two differently-sized block groups has two groups back to back.
_RS_BLOCKS_L: tuple[tuple[int, ...], ...] = (
    (1, 26, 19), (1, 44, 34), (1, 70, 55), (1, 100, 80), (1, 134, 108),
    (2, 86, 68), (2, 98, 78), (2, 121, 97), (2, 146, 116), (2, 86, 68, 2, 87, 69),
    (4, 101, 81), (2, 116, 92, 2, 117, 93), (4, 133, 107), (3, 145, 115, 1, 146, 116),
    (5, 109, 87, 1, 110, 88), (5, 122, 98, 1, 123, 99), (1, 135, 107, 5, 136, 108),
    (5, 150, 120, 1, 151, 121), (3, 141, 113, 4, 142, 114), (3, 135, 107, 5, 136, 108),
    (4, 144, 116, 4, 145, 117), (2, 139, 111, 7, 140, 112), (4, 151, 121, 5, 152, 122),
    (6, 147, 117, 4, 148, 118), (8, 132, 106, 4, 133, 107), (10, 142, 114, 2, 143, 115),
    (8, 152, 122, 4, 153, 123), (3, 147, 117, 10, 148, 118), (7, 146, 116, 7, 147, 117),
    (5, 145, 115, 10, 146, 116), (13, 145, 115, 3, 146, 116), (17, 145, 115),
    (17, 145, 115, 1, 146, 116), (13, 145, 115, 6, 146, 116), (12, 151, 121, 7, 152, 122),
    (6, 151, 121, 14, 152, 122), (17, 152, 122, 4, 153, 123), (4, 152, 122, 18, 153, 123),
    (20, 147, 117, 4, 148, 118), (19, 148, 118, 6, 149, 119),
)
_RS_BLOCKS_M: tuple[tuple[int, ...], ...] = (
    (1, 26, 16), (1, 44, 28), (1, 70, 44), (2, 50, 32), (2, 67, 43),
    (4, 43, 27), (4, 49, 31), (2, 60, 38, 2, 61, 39), (3, 58, 36, 2, 59, 37),
    (4, 69, 43, 1, 70, 44), (1, 80, 50, 4, 81, 51), (6, 58, 36, 2, 59, 37),
    (8, 59, 37, 1, 60, 38), (4, 64, 40, 5, 65, 41), (5, 65, 41, 5, 66, 42),
    (7, 73, 45, 3, 74, 46), (10, 74, 46, 1, 75, 47), (9, 69, 43, 4, 70, 44),
    (3, 70, 44, 11, 71, 45), (3, 67, 41, 13, 68, 42), (17, 68, 42), (17, 74, 46),
    (4, 75, 47, 14, 76, 48), (6, 73, 45, 14, 74, 46), (8, 75, 47, 13, 76, 48),
    (19, 74, 46, 4, 75, 47), (22, 73, 45, 3, 74, 46), (3, 73, 45, 23, 74, 46),
    (21, 73, 45, 7, 74, 46), (19, 75, 47, 10, 76, 48), (2, 74, 46, 29, 75, 47),
    (10, 74, 46, 23, 75, 47), (14, 74, 46, 21, 75, 47), (14, 74, 46, 23, 75, 47),
    (12, 75, 47, 26, 76, 48), (6, 75, 47, 34, 76, 48), (29, 74, 46, 14, 75, 47),
    (13, 74, 46, 32, 75, 47), (40, 75, 47, 7, 76, 48), (18, 75, 47, 31, 76, 48),
)
_RS_BLOCKS = {"L": _RS_BLOCKS_L, "M": _RS_BLOCKS_M}

# Alignment-pattern center coordinates per version (index 0 = version 1); a
# pattern sits at every (row, col) pair from this list's cross-product, minus
# the three already covered by finder patterns.
_ALIGNMENT: tuple[tuple[int, ...], ...] = (
    (), (6, 18), (6, 22), (6, 26), (6, 30), (6, 34), (6, 22, 38), (6, 24, 42),
    (6, 26, 46), (6, 28, 50), (6, 30, 54), (6, 32, 58), (6, 34, 62), (6, 26, 46, 66),
    (6, 26, 48, 70), (6, 26, 50, 74), (6, 30, 54, 78), (6, 30, 56, 82), (6, 30, 58, 86),
    (6, 34, 62, 90), (6, 28, 50, 72, 94), (6, 26, 50, 74, 98), (6, 30, 54, 78, 102),
    (6, 28, 54, 80, 106), (6, 32, 58, 84, 110), (6, 30, 58, 86, 114), (6, 34, 62, 90, 118),
    (6, 26, 50, 74, 98, 122), (6, 30, 54, 78, 102, 126), (6, 26, 52, 78, 104, 130),
    (6, 30, 56, 82, 108, 134), (6, 34, 60, 86, 112, 138), (6, 30, 58, 86, 114, 142),
    (6, 34, 62, 90, 118, 146), (6, 30, 54, 78, 102, 126, 150), (6, 24, 50, 76, 102, 128, 154),
    (6, 28, 54, 80, 106, 132, 158), (6, 32, 58, 84, 110, 136, 162), (6, 26, 54, 82, 110, 138, 166),
    (6, 30, 58, 86, 114, 142, 170),
)

_G15 = 0x537          # format-info BCH generator (x^10+x^8+x^5+x^4+x^2+x+1)
_G15_MASK = 0x5412
_G18 = 0x1F25          # version-info BCH generator
_ECC_INDICATOR = {"L": 0b01, "M": 0b00, "Q": 0b11, "H": 0b10}

_MODE_BYTE = 0b0100


# ── GF(256) for Reed-Solomon (primitive poly 0x11D, generator 2) ───────────
def _build_gf_tables() -> tuple[list[int], list[int]]:
    exp = [0] * 512
    log = [0] * 256
    x = 1
    for i in range(255):
        exp[i] = x
        log[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    for i in range(255, 512):
        exp[i] = exp[i - 255]
    return exp, log


_EXP, _LOG = _build_gf_tables()


def _gf_mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]


def _rs_generator_poly(degree: int) -> list[int]:
    """The generator polynomial for `degree` EC codewords, coefficients
    highest-degree first, leading coefficient always 1."""
    poly = [1]
    for i in range(degree):
        poly.append(0)
        for j in range(len(poly) - 1, 0, -1):
            poly[j] ^= _gf_mul(poly[j - 1], _EXP[i])
    return poly


def _rs_encode(data: list[int], ec_count: int) -> list[int]:
    """Reed-Solomon error-correction codewords for one block of `data`."""
    gen = _rs_generator_poly(ec_count)
    remainder = data + [0] * ec_count
    for i in range(len(data)):
        coef = remainder[i]
        if coef == 0:
            continue
        for j, g in enumerate(gen):
            remainder[i + j] ^= _gf_mul(g, coef)
    return remainder[len(data):]


# ── bit stream ───────────────────────────────────────────────────────────
class _BitBuffer:
    def __init__(self) -> None:
        self.bits: list[int] = []

    def put(self, value: int, length: int) -> None:
        for i in range(length - 1, -1, -1):
            self.bits.append((value >> i) & 1)

    def __len__(self) -> int:
        return len(self.bits)


def _count_indicator_bits(version: int) -> int:
    return 8 if version <= 9 else 16


def _data_codewords(version: int, ecc: str) -> int:
    return sum(row[i + 2] * row[i] for row in (_RS_BLOCKS[ecc][version - 1],)
               for i in range(0, len(row), 3))


def _byte_capacity(version: int, ecc: str) -> int:
    """Max payload bytes this version/ecc can hold in byte mode."""
    usable_bits = _data_codewords(version, ecc) * 8 - 4 - _count_indicator_bits(version)
    return max(0, usable_bits // 8)


def _pick_version(nbytes: int, ecc: str, min_version: int) -> int:
    for v in range(max(1, min_version), 41):
        if _byte_capacity(v, ecc) >= nbytes:
            return v
    raise QRTooLong(f"{nbytes} bytes too long for any version at ECC {ecc}")


def _build_codewords(data: bytes, version: int, ecc: str) -> list[int]:
    buf = _BitBuffer()
    buf.put(_MODE_BYTE, 4)
    buf.put(len(data), _count_indicator_bits(version))
    for b in data:
        buf.put(b, 8)

    total_codewords = _data_codewords(version, ecc)
    total_bits = total_codewords * 8
    # Terminator: up to 4 zero bits, only as many as fit.
    buf.put(0, min(4, total_bits - len(buf)))
    # Pad to a byte boundary.
    while len(buf) % 8:
        buf.bits.append(0)
    # Pad codewords, alternating 0xEC/0x11, until the data capacity is filled.
    pad = (0xEC, 0x11)
    i = 0
    while len(buf) < total_bits:
        buf.put(pad[i % 2], 8)
        i += 1

    codewords = [int("".join(map(str, buf.bits[i:i + 8])), 2)
                 for i in range(0, len(buf.bits), 8)]

    # Split into RS blocks, compute EC codewords per block, interleave.
    blocks: list[tuple[list[int], list[int]]] = []
    idx = 0
    row = _RS_BLOCKS[ecc][version - 1]
    for i in range(0, len(row), 3):
        count, total_count, data_count = row[i:i + 3]
        ec_count = total_count - data_count
        for _ in range(count):
            block_data = codewords[idx:idx + data_count]
            idx += data_count
            blocks.append((block_data, _rs_encode(block_data, ec_count)))

    max_data = max(len(d) for d, _ in blocks)
    max_ec = max(len(e) for _, e in blocks)
    interleaved: list[int] = []
    for i in range(max_data):
        for d, _ in blocks:
            if i < len(d):
                interleaved.append(d[i])
    for i in range(max_ec):
        for _, e in blocks:
            if i < len(e):
                interleaved.append(e[i])
    return interleaved


# ── matrix construction ─────────────────────────────────────────────────
_FINDER_AT = lambda size: ((0, 0), (0, size - 7), (size - 7, 0))  # noqa: E731


def _place_finder(mat, reserved, r0, c0) -> None:
    for r in range(-1, 8):
        for c in range(-1, 8):
            rr, cc = r0 + r, c0 + c
            if not (0 <= rr < len(mat) and 0 <= cc < len(mat)):
                continue
            reserved[rr][cc] = True
            is_dark = (0 <= r <= 6 and c in (0, 6)) or (0 <= c <= 6 and r in (0, 6)) \
                or (2 <= r <= 4 and 2 <= c <= 4)
            mat[rr][cc] = is_dark


def _place_alignment(mat, reserved, r0, c0) -> None:
    for r in range(-2, 3):
        for c in range(-2, 3):
            rr, cc = r0 + r, c0 + c
            reserved[rr][cc] = True
            mat[rr][cc] = (r in (-2, 2) or c in (-2, 2) or (r == 0 and c == 0))


def _skeleton(version: int) -> tuple[list[list[bool]], list[list[bool]]]:
    size = version * 4 + 17
    mat = [[False] * size for _ in range(size)]
    reserved = [[False] * size for _ in range(size)]

    for r0, c0 in _FINDER_AT(size):
        _place_finder(mat, reserved, r0, c0)

    centers = _ALIGNMENT[version - 1]
    for r in centers:
        for c in centers:
            # A center already occupied (by a finder pattern, always) is the
            # only skip condition — matches the reference algorithm exactly,
            # rather than a proximity heuristic that can mis-skip at some
            # versions' alignment layouts.
            if reserved[r][c]:
                continue
            _place_alignment(mat, reserved, r, c)

    # timing patterns
    for i in range(8, size - 8):
        dark = i % 2 == 0
        if not reserved[6][i]:
            mat[6][i] = dark
            reserved[6][i] = True
        if not reserved[i][6]:
            mat[i][6] = dark
            reserved[i][6] = True

    # dark module: reserved now (kept out of masking/data), but left blank
    # until `_write_format` sets it — matching the reference implementation,
    # where it's part of the format-info write and so is blank during mask
    # search too. That's a real (if odd) quirk of the algorithm: getting it
    # right matters because close mask-score ties can flip on this one cell.
    dm_r = version * 4 + 9
    reserved[dm_r][8] = True

    # reserve format-info strips (written later, once the mask is chosen)
    for i in range(9):
        reserved[8][i] = True
        reserved[i][8] = True
    for i in range(8):
        reserved[8][size - 1 - i] = True
        reserved[size - 1 - i][8] = True

    # reserve version-info blocks (versions >= 7)
    if version >= 7:
        for r in range(6):
            for c in range(size - 11, size - 8):
                reserved[r][c] = True
                reserved[c][r] = True

    return mat, reserved


def _place_data(mat, reserved, codewords: list[int]) -> None:
    bits: list[int] = []
    for cw in codewords:
        for i in range(7, -1, -1):
            bits.append((cw >> i) & 1)
    size = len(mat)
    bit_i = 0
    col = size - 1
    upward = True
    while col > 0:
        if col == 6:            # timing column already placed
            col -= 1
        for i in range(size):
            row = (size - 1 - i) if upward else i
            for c in (col, col - 1):
                if reserved[row][c]:
                    continue
                bit = bits[bit_i] if bit_i < len(bits) else 0
                mat[row][c] = bool(bit)
                bit_i += 1
        upward = not upward
        col -= 2


# ── masking ──────────────────────────────────────────────────────────────
def _mask_fn(pattern: int):
    return [
        lambda r, c: (r + c) % 2 == 0,
        lambda r, c: r % 2 == 0,
        lambda r, c: c % 3 == 0,
        lambda r, c: (r + c) % 3 == 0,
        lambda r, c: (r // 2 + c // 3) % 2 == 0,
        lambda r, c: (r * c) % 2 + (r * c) % 3 == 0,
        lambda r, c: ((r * c) % 2 + (r * c) % 3) % 2 == 0,
        lambda r, c: ((r + c) % 2 + (r * c) % 3) % 2 == 0,
    ][pattern]


def _apply_mask(mat, reserved, pattern: int) -> list[list[bool]]:
    f = _mask_fn(pattern)
    size = len(mat)
    out = [row[:] for row in mat]
    for r in range(size):
        for c in range(size):
            if not reserved[r][c] and f(r, c):
                out[r][c] = not out[r][c]
    return out


def _penalty(mat) -> int:
    size = len(mat)
    score = 0

    # Rule 1: runs of 5+ same-color modules in a row/column.
    for line_i in range(size):
        for get in ((lambda i: mat[line_i][i]), (lambda i: mat[i][line_i])):
            run = 1
            prev = get(0)
            for i in range(1, size):
                v = get(i)
                if v == prev:
                    run += 1
                else:
                    if run >= 5:
                        score += 3 + (run - 5)
                    run = 1
                    prev = v
            if run >= 5:
                score += 3 + (run - 5)

    # Rule 2: 2x2 blocks of the same color.
    for r in range(size - 1):
        for c in range(size - 1):
            v = mat[r][c]
            if v == mat[r][c + 1] == mat[r + 1][c] == mat[r + 1][c + 1]:
                score += 3

    # Rule 3: the 1:1:3:1:1 finder-like pattern (with 4 light either side).
    patt_a = [True, False, True, True, True, False, True, False, False, False, False]
    patt_b = [False, False, False, False, True, False, True, True, True, False, True]
    for r in range(size):
        row = mat[r]
        for c in range(size - 10):
            window = row[c:c + 11]
            if window == patt_a or window == patt_b:
                score += 40
    for c in range(size):
        col = [mat[r][c] for r in range(size)]
        for r in range(size - 10):
            window = col[r:r + 11]
            if window == patt_a or window == patt_b:
                score += 40

    # Rule 4: overall dark-module ratio deviation from 50%, rated in 5% steps.
    dark = sum(1 for row in mat for v in row if v)
    percent = dark / (size * size)
    score += int(abs(percent * 100 - 50) / 5) * 10

    return score


def _bch_format(ecc: str, mask: int) -> int:
    data = (_ECC_INDICATOR[ecc] << 3) | mask
    val = data << 10
    g = _G15
    for i in range(4, -1, -1):
        if val & (1 << (i + 10)):
            val ^= g << i
    return ((data << 10) | val) ^ _G15_MASK


def _write_format(mat, size: int, bits: int) -> None:
    # Two copies: a vertical strip beside the top-left finder + a diagonal
    # continuation down column 8, and a horizontal strip along row 8.
    for i in range(15):
        bit = bool((bits >> i) & 1)
        if i < 6:
            mat[i][8] = bit
        elif i < 8:
            mat[i + 1][8] = bit
        else:
            mat[size - 15 + i][8] = bit
    for i in range(15):
        bit = bool((bits >> i) & 1)
        if i < 8:
            mat[8][size - i - 1] = bit
        elif i < 9:
            mat[8][15 - i] = bit
        else:
            mat[8][14 - i] = bit
    mat[size - 8][8] = True  # the fixed dark module, always on


def _bch_version(version: int) -> int:
    data = version
    val = data << 12
    g = _G18
    for i in range(5, -1, -1):
        if val & (1 << (i + 12)):
            val ^= g << i
    return (data << 12) | val


def _write_version(mat, size: int, version: int) -> None:
    if version < 7:
        return
    bits = _bch_version(version)
    for i in range(18):
        bit = bool((bits >> i) & 1)
        r, c = i // 3, i % 3 + size - 11
        mat[r][c] = bit        # top-right block
        mat[c][r] = bit        # bottom-left block (transpose of the above)


def encode(data: str | bytes, *, ecc: str = "M", min_version: int = 1) -> QRCode:
    """Encode `data` (byte mode) at error-correction level `ecc` ('L' or 'M'),
    auto-selecting the smallest fitting version >= `min_version`."""
    if ecc not in _RS_BLOCKS:
        raise ValueError(f"unsupported ecc {ecc!r}; use 'L' or 'M'")
    raw = data.encode("utf-8") if isinstance(data, str) else bytes(data)
    version = _pick_version(len(raw), ecc, min_version)
    codewords = _build_codewords(raw, version, ecc)

    skeleton, reserved = _skeleton(version)
    _place_data(skeleton, reserved, codewords)

    # Mask selection scores the matrix with format/version info still blank
    # (matching the reference algorithm) — those bits depend on the mask
    # that's about to be chosen, so they're written only onto the winner.
    best_mask, best_score = None, None
    for pattern in range(8):
        candidate = _apply_mask(skeleton, reserved, pattern)
        score = _penalty(candidate)
        if best_score is None or score < best_score:
            best_mask, best_score = pattern, score

    best_mat = _apply_mask(skeleton, reserved, best_mask)
    size = len(best_mat)
    _write_format(best_mat, size, _bch_format(ecc, best_mask))
    _write_version(best_mat, size, version)

    return QRCode(version=version, ecc=ecc, mask=best_mask, size=size, matrix=best_mat)
