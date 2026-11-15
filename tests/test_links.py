import json
import os

import pytest

from carterkit import links, share, tutorials

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "links.json")
SIBLING = "/nas/home/Atlas/projects/CAR-TER-workspace/CAR-TER/contract/links.json"
URLS = {f["url"] for f in json.load(open(FIX))["fixtures"]}


def test_import_link_matches_fixtures():
    u = "http://192.168.1.20:8765/layout.json"
    assert share.import_link(u, 1900000000, scheme=True) == \
        "carter://import?url=http%3A%2F%2F192.168.1.20%3A8765%2Flayout.json&exp=1900000000"
    assert share.import_link(u, 1900000000, scheme=True) in URLS
    assert share.import_link("https://example.com/layout.json") == \
        "https://links.carterbeaudoin.net/import?url=https%3A%2F%2Fexample.com%2Flayout.json"
    assert share.import_link("https://example.com/layout.json") in URLS


def test_tutorial_and_beta():
    assert tutorials.web_link("first-layout") in URLS
    assert tutorials.app_link("first-layout", "2") in URLS
    assert tutorials.web_link("x", "2", beta=True) == "https://go-beta.carterbeaudoin.net/tutorial/x?step=2"
    assert links.app_link("handoff", "h_abc123", beta=True) in URLS
    assert links.app_link("handoff", "h_abc123", beta=True, scheme=True) in URLS
    assert links.app_link("join", query={"invite": "basecamp-crew"}, fragment="k=c2VjcmV0") in URLS


def test_share_link_has_exp(tmp_path):
    p = tmp_path / "l.json"
    p.write_text(json.dumps({"name": "T", "version": 1, "tabs": []}))
    out = []
    share.share(str(p), seconds=0.01, out=out.append, ip="10.0.0.9")
    assert out[1].startswith("https://links.carterbeaudoin.net/import?url=http%3A%2F%2F10.0.0.9%3A")
    assert "&exp=" in out[1]


@pytest.mark.skipif(not os.path.exists(SIBLING), reason="CAR-TER checkout not present")
def test_fixtures_match_contract_copy():
    assert json.load(open(SIBLING)) == json.load(open(FIX))
