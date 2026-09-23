"""Second-pass hardening tests (desired behaviour). Each test FAILS on the current
code, confirming the weakness; it becomes the regression test for the fix."""
import base64
import pytest
from carterkit.e2ee import E2EESession

K = bytes([7]) * 32


def _env(**over):
    s = E2EESession.group(K)
    env = s.seal({"msg_type": "unlock"})
    env.update(over)
    return env


@pytest.mark.parametrize("bad", [
    {"n": -1},                 # struct.error today
    {"n": 1.5},                # struct.error today
    {"n": "0"},                # struct.error today
    {"n": 2 ** 64},            # struct.error today
    {"s": 12345},              # TypeError today
    {"ct": None},              # TypeError today
])
def test_open_rejects_malformed_envelope_with_valueerror(bad):
    env = _env(**bad)
    with pytest.raises(ValueError):
        E2EESession.group(K).open(env)


def test_open_missing_fields_is_valueerror_not_keyerror():
    env = _env()
    del env["ct"]
    with pytest.raises(ValueError):
        E2EESession.group(K).open(env)


def test_group_key_must_be_32_bytes():
    with pytest.raises(ValueError):
        E2EESession.group(b"\x01")            # 1-byte key derives and interops today
    with pytest.raises(ValueError):
        E2EESession(b"\x01" * 16, is_device_side=True)


def test_replay_of_same_envelope_is_rejected():
    a = E2EESession.group(K)
    b = E2EESession.group(K)
    env = a.seal({"msg_type": "unlock"})
    assert b.open(env) == {"msg_type": "unlock"}
    with pytest.raises(ValueError):
        b.open(env)                            # replays open fine today


def test_out_of_order_within_window_but_not_below_high_water():
    a = E2EESession.group(K)
    b = E2EESession.group(K)
    envs = [a.seal({"i": i}) for i in range(5)]
    assert b.open(envs[4]) == {"i": 4}
    assert b.open(envs[3]) == {"i": 3}          # small reordering is fine
    with pytest.raises(ValueError):
        b.open(envs[3])                         # but not twice
