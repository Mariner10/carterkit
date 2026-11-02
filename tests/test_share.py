import json
import urllib.request
import urllib.error

import pytest

from carterkit import share, cli


GOOD = {"name": "T", "version": 1, "tabs": []}


def _write(tmp_path, obj):
    p = tmp_path / "layout.json"
    p.write_text(json.dumps(obj))
    return str(p)


def test_import_link():
    assert share.import_link("http://1.2.3.4:5/layout.json") == \
        "carter://import?url=http://1.2.3.4:5/layout.json"


def test_serve_returns_body_and_404():
    srv, port = share.serve(b'{"a":1}', host="127.0.0.1")
    try:
        r = urllib.request.urlopen(f"http://127.0.0.1:{port}/layout.json")
        assert r.read() == b'{"a":1}'
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(f"http://127.0.0.1:{port}/x")
    finally:
        srv.shutdown(); srv.server_close()


def test_share_https_url_prints_link_and_qr(tmp_path):
    out = []
    rc = share.share(_write(tmp_path, GOOD), https_url="https://x.test/l.json", out=out.append)
    assert rc == 0
    assert out[-1] == "carter://import?url=https://x.test/l.json"
    assert len(out) == 2 and "\n" in out[0]


def test_share_serves_then_stops(tmp_path):
    out = []
    rc = share.share(_write(tmp_path, GOOD), seconds=0.05, out=out.append, ip="10.0.0.9")
    assert rc == 0
    assert out[1].startswith("carter://import?url=http://10.0.0.9:")
    assert out[1].endswith("/layout.json")


def test_share_rejects_invalid(tmp_path):
    out = []
    assert share.share(_write(tmp_path, {"tabs": "nope"}), out=out.append) == 1
    assert share.share(str(tmp_path / "missing.json"), out=out.append) == 1


def test_cli_registered():
    args = cli.build_parser().parse_args(["share", "a.json", "--https-url", "https://h/x"])
    assert args.fn is cli._cmd_share and args.https_url == "https://h/x"
