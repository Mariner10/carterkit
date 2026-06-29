import base64
from carterkit.e2ee import derive_key, E2EESession

K = bytes([1]) * 32
SESS = bytes([2]) * 16

def test_frozen_v2_key_vectors():
    assert base64.b64encode(derive_key(K, SESS, b"c2d v2")).decode() == "hE9w/2FmodiObkPZhOc4rHD3WCiHPpeji/23xfFdbkI="
    assert base64.b64encode(derive_key(K, SESS, b"d2c v2")).decode() == "XV0m6WgDihulvNPXqHH3XIs1vS4XdIYSIM/GxLd01og="

def test_frozen_v2_ciphertext_vectors():
    app = E2EESession(K, is_device_side=False, seal_salt=SESS)
    env = app.seal({"msg_type": "hello"})
    assert env["e2ee"] == 2 and env["s"] == base64.b64encode(SESS).decode() and env["n"] == 0
    assert env["ct"] == "+Nepe+TZfbf7rCjrPe7kS0SR8PGWxWwPv3/vnt+AWFoxPib+"
    hub = E2EESession(K, is_device_side=True, seal_salt=SESS)
    assert hub.seal({"msg_type": "hello"})["ct"] == "vJtIu68f/NhxkoiDMy3PoIJiSkDLJ4JRyJ3C9yB5DwrvjZ5m"

def test_cross_roundtrip_random_salts():
    app = E2EESession(K, is_device_side=False)
    hub = E2EESession(K, is_device_side=True)
    assert hub.open(app.seal({"a": 1})) == {"a": 1}
    assert app.open(hub.seal({"b": True})) == {"b": True}

def test_two_sessions_different_salts():
    s1 = E2EESession(K, is_device_side=False); s2 = E2EESession(K, is_device_side=False)
    assert s1.seal({"a": 1})["s"] != s2.seal({"a": 1})["s"]

def test_frozen_v2_group_vectors():
    # Symmetric "grp v2" room cipher — frozen, byte-identical to the app's group session.
    assert base64.b64encode(derive_key(K, SESS, b"grp v2")).decode() == "q6Mo+r3Ed3IFxfL3ASxtiBi9tcu9+PhzwktJg/PgSf8="
    s = E2EESession.group(K, seal_salt=SESS)
    assert s.seal({"msg_type": "hello"})["ct"] == "pFc43+GgSzwf+XW0owEzh57qjImojP74Q8LgUHZmL28yT+tl"

def test_group_multi_sender_roundtrip():
    # Any room member opens any other's envelope; independent per-session salts make it safe.
    a = E2EESession.group(K); b = E2EESession.group(K)
    assert b.open(a.seal({"a": 1})) == {"a": 1}
    assert a.open(b.seal({"b": True})) == {"b": True}
    assert a.seal({"x": 1})["s"] != b.seal({"x": 1})["s"]

def test_v1_envelope_rejected():
    assert not E2EESession.is_envelope({"e2ee": 1, "n": 0, "ct": "AAAA"})

if __name__ == "__main__":
    test_frozen_v2_key_vectors(); test_frozen_v2_ciphertext_vectors(); test_cross_roundtrip_random_salts()
    test_two_sessions_different_salts(); test_v1_envelope_rejected()
    print("ALL E2EE V2 INTEROP TESTS PASSED")
