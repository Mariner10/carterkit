"""``carterkit start``: CLI registration and pairing payload, no network."""
import json

from carterkit import cli, start


class FakeConn:
    channel = "chan1"
    key = "k1"
    port = 8765

    def app_url(self):
        return "ws://127.0.0.1:8765"


class FakeHub:
    connection = FakeConn()

    def qr_json(self, *, role="controller"):
        return json.dumps({"channel": "chan1", "key": "k1"})


def test_start_subcommand_registered():
    args = cli.build_parser().parse_args(["start", "--fresh", "--no-repl", "--port", "9"])
    assert args.fn is cli._cmd_start
    assert args.fresh and args.no_repl and args.port == 9


def test_cmd_start_dispatches(monkeypatch):
    seen = {}
    monkeypatch.setattr(start, "main", lambda a: seen.setdefault("args", a) and 0)
    args = cli.build_parser().parse_args(["start"])
    assert cli.main(["start"]) == 0
    assert seen["args"].fresh is False and args.host is None


def test_pairing_lines_contain_payload_and_hint():
    lines = start.pairing_lines(FakeHub())
    text = "\n".join(lines)
    assert '"channel": "chan1"' in text
    assert start.SCAN_HINT in text
    assert "chan1" in lines[-1]
    assert "Reusing" not in text
    assert "Reusing" in "\n".join(start.pairing_lines(FakeHub(), reused=True))


def test_session_roundtrip(tmp_path):
    p = str(tmp_path / "d" / "session.json")
    assert start.load_session(p) is None
    start.save_session(FakeConn_holder(), p)
    assert start.load_session(p) == {"channel": "chan1", "key": "k1", "port": 8765}


def FakeConn_holder():
    return FakeConn()
