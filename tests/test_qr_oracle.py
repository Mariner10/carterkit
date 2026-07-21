"""Oracle test: carterkit.qr's matrix output vs. the `qrcode` PyPI package, for
the same content/version/ecc/mask. `qrcode` is a dev-only dependency (not
shipped with carterkit) — this whole module is skipped if it isn't installed,
so a CI environment without it still passes the rest of the suite."""

import random

import pytest

from carterkit import qr

qrcode = pytest.importorskip("qrcode", reason="dev-only oracle; not a runtime dependency")
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M  # noqa: E402
from qrcode.util import QRData, MODE_8BIT_BYTE  # noqa: E402

_ECC_VALUES = {"L": ERROR_CORRECT_L, "M": ERROR_CORRECT_M}


def _oracle(text: str, ecc_value: int):
    q = qrcode.QRCode(error_correction=ecc_value, border=0)
    # Force byte mode — `qrcode` auto-picks numeric/alphanumeric mode when the
    # content qualifies, which this encoder doesn't implement (byte mode only,
    # per spec), so an unforced comparison wouldn't be apples-to-apples.
    q.add_data(QRData(text.encode(), mode=MODE_8BIT_BYTE, check_data=False))
    q.make(fit=True)
    return q.version, q.get_matrix()


@pytest.mark.parametrize("ecc", ["L", "M"])
@pytest.mark.parametrize("text", [
    "", "a", "hello", "hello world",
    '{"url":"ws://192.168.1.5:8765","channel":"home","token":"abc123"}',
    "x" * 100, "A" * 300,
])
def test_matches_oracle_for_fixed_inputs(ecc, text):
    mine = qr.encode(text, ecc=ecc)
    oracle_version, oracle_matrix = _oracle(text, _ECC_VALUES[ecc])
    assert mine.version == oracle_version
    assert mine.matrix == oracle_matrix


@pytest.mark.parametrize("ecc", ["L", "M"])
def test_matches_oracle_for_random_inputs(ecc):
    rnd = random.Random(20260720)
    for _ in range(25):
        n = rnd.randint(0, 1200)
        text = "".join(chr(rnd.randint(32, 126)) for _ in range(n))
        mine = qr.encode(text, ecc=ecc)
        oracle_version, oracle_matrix = _oracle(text, _ECC_VALUES[ecc])
        assert mine.version == oracle_version, f"version mismatch for len={n}"
        assert mine.matrix == oracle_matrix, f"matrix mismatch for len={n}"


def test_matches_oracle_at_version_boundaries_with_alignment_and_version_info():
    # Versions >=7 add version-info blocks and multi-alignment-pattern grids —
    # exactly where this encoder's earlier drafts diverged from the oracle.
    for version, ecc in [(7, "L"), (27, "M"), (40, "L")]:
        cap = qr._byte_capacity(version, ecc)
        prev_cap = qr._byte_capacity(version - 1, ecc) if version > 1 else 0
        text = "Q" * (prev_cap + 1) if cap > prev_cap else "Q" * cap
        mine = qr.encode(text, ecc=ecc)
        oracle_version, oracle_matrix = _oracle(text, _ECC_VALUES[ecc])
        assert mine.version == oracle_version
        assert mine.matrix == oracle_matrix
