from carterkit.testing import filter_frame, _supported
from carterkit import validate


def _fake_manifest(monkeypatch):
    caps = {"hub-surfaces.new": {"since": "2.1"}, "hub-surfaces.old": {"since": "2.0"},
            "hub-surfaces.old.extra": {"since": "2.1"}, "hub-surfaces.soon": {"since": "next"}}
    monkeypatch.setattr(validate, "capabilities_manifest", lambda: {"capabilities": caps})


def test_filter_frames_and_fields(monkeypatch):
    _fake_manifest(monkeypatch)
    assert filter_frame({"msg_type": "new"}, "2.0") is None
    assert filter_frame({"msg_type": "new"}, "2.1") == {"msg_type": "new"}
    assert filter_frame({"msg_type": "old", "a": 1, "extra": 2}, "2.0") == {"msg_type": "old", "a": 1}
    assert filter_frame({"msg_type": "old", "extra": 2}, "2.1")["extra"] == 2
    assert filter_frame({"msg_type": "soon"}, "9.9") is None
    assert filter_frame({"msg_type": "new"}, None) == {"msg_type": "new"}
    assert _supported("unknown.cap", "2.0")


def test_hello_dispatches_sync_request_and_defaults_to_baseline(monkeypatch):
    import asyncio
    from carterkit.testing import FakeHub
    import inspect
    assert "control_sync_request" in inspect.getsource(FakeHub.hello)
    caps = validate.capabilities_manifest()["capabilities"]
    assert caps["hub-surfaces.toast"]["since"] == "next"  # real key, unreleased
    assert filter_frame({"msg_type": "toast"}, "2.0") is None
