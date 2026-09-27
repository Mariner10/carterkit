"""CarterClient.local_* (readback spec §6.1) against a scripted fake studio socket."""

import asyncio
import json

import pytest

from carterkit import CarterClient, LocalDataError, parse_local_event, validate_layout
from carterkit import localdata
from carterkit.cli import main as cli_main

from test_client import _FakeSock

PHONE = {"id": "phone-1", "name": "iPhone"}


class _StudioSock(_FakeSock):
    """_FakeSock with a get_nodes roster and a scripted route_msg responder:
    `script(verb, payload)` returns the device's reply for each routed call."""

    def __init__(self, script, roster=None):
        super().__init__()
        self.script = script
        self.roster = [{"id": "me", "name": "hub"}, PHONE] if roster is None else roster
        self.routed = []

    async def request(self, t, payload=None, timeout=5.0):
        self.sent.append(("REQ:" + t, payload))
        if t == "get_nodes":
            return {"clients": self.roster}
        assert t == "route_msg"
        self.routed.append((payload["target_id"], payload["type"], payload["payload"]))
        return self.script(payload["type"], payload["payload"])


class _Clock:
    """Injected clock + sleep: sleeping advances time, no real waiting."""

    def __init__(self):
        self.now = 0.0
        self.sleeps = 0

    def __call__(self):
        return self.now

    async def sleep(self, s):
        self.sleeps += 1
        self.now += s


def _client(script, *, can_route=True, can_monitor=True, roster=None):
    c = CarterClient("ws://x", "tok", "studio", role="controller", name="hub",
                     can_route=can_route, can_monitor=can_monitor)
    c._sock = _StudioSock(script, roster)
    clock = _Clock()
    c._local_clock = clock
    c._local_sleep = clock.sleep
    return c, clock


def run(coro):
    return asyncio.run(coro)


def test_describe_routes_studio_verb_to_first_peer():
    desc = {"ok": True, "consent": "none", "namespaces": []}
    c, _ = _client(lambda v, p: desc)
    assert run(c.local_describe()) == desc
    assert c._sock.routed == [("phone-1", "local.describe", {})]
    # plaintext route_msg, never the sealed CarterClient.request path
    assert c._sock.sent[0] == ("REQ:get_nodes", None)


def test_explicit_device_id_skips_roster():
    c, _ = _client(lambda v, p: {"ok": True, "consent": "none"})
    run(c.local_describe(device_id="dev-9"))
    assert c._sock.routed[0][0] == "dev-9"
    assert all(t != "REQ:get_nodes" for t, _ in c._sock.sent)


@pytest.mark.parametrize("kw,needle", [({"can_route": False}, "can_route"),
                                        ({"can_monitor": False}, "can_monitor")])
def test_missing_capabilities_raise_before_sending(kw, needle):
    c, _ = _client(lambda v, p: {"ok": True}, **kw)
    with pytest.raises(LocalDataError) as e:
        run(c.local_query("books"))
    assert e.value.code == "not-capable" and needle in e.value.reason
    assert c._sock.sent == []


def test_no_peer_raises_no_device():
    c, _ = _client(lambda v, p: {"ok": True}, roster=[{"id": "me", "name": "hub"}])
    with pytest.raises(LocalDataError) as e:
        run(c.local_describe())
    assert e.value.code == "no-device"


def test_timeout_reply_is_no_reply():
    c, _ = _client(lambda v, p: None)
    with pytest.raises(LocalDataError) as e:
        run(c.local_describe())
    assert e.value.code == "no-reply"


SPEC_CODES = ["bad-request", "no-layout", "no-local-source", "unknown-namespace",
              "unknown-collection", "denied", "busy", "invalid-stage", "limit",
              "schema", "remote-source", "validation", "store-error"]


@pytest.mark.parametrize("code", SPEC_CODES + ["consent-pending"])
def test_every_error_code_raises_local_data_error(code):
    assert code in localdata.ERROR_PROSE
    c, _ = _client(lambda v, p: {"error": code, "reason": "why " + code})
    with pytest.raises(LocalDataError) as e:
        run(c.local_describe())
    assert (e.value.code, e.value.reason) == (code, "why " + code)
    assert code in str(e.value)


@pytest.mark.parametrize("code", SPEC_CODES)
def test_error_codes_on_record_verbs(code):
    c, _ = _client(lambda v, p: {"error": code, "reason": "r"})
    with pytest.raises(LocalDataError) as e:
        run(c.local_upsert("books", [{"title": "Dune"}]))
    assert e.value.code == code


# ─── consent (§3.1) ──────────────────────────────────────────────────────────

def _consent_script(grant_after_polls, final):
    """First record call arms the sheet; describe reports pending for N polls, then
    `final`; the re-sent verb answers per `final`."""
    state = {"armed": False, "polls": 0}

    def script(verb, payload):
        if verb == "local.describe":
            state["polls"] += 1
            pending = state["polls"] <= grant_after_polls
            return {"ok": True, "consent": "pending" if pending else final}
        if not state["armed"]:
            state["armed"] = True
            return {"error": "consent-pending", "request_id": "r1"}
        if final == "granted":
            return {"ok": True, "collection": "books", "rows": [{"id": "a"}],
                    "count": 1, "total": 1, "cursor": None}
        return {"error": "denied", "reason": "user-denied"}
    return script, state


def test_consent_pending_polls_describe_then_resends():
    script, state = _consent_script(3, "granted")
    c, clock = _client(script)
    reply = run(c.local_query("books"))
    assert reply["rows"] == [{"id": "a"}]
    verbs = [v for _, v, _ in c._sock.routed]
    assert verbs == ["local.query"] + ["local.describe"] * 4 + ["local.query"]
    assert clock.sleeps == 4 and clock.now == 4.0      # 1 s poll, injected clock


def test_consent_denied_raises_denied():
    script, _ = _consent_script(1, "none")
    c, _ = _client(script)
    with pytest.raises(LocalDataError) as e:
        run(c.local_upsert("books", [{"title": "Dune"}]))
    assert (e.value.code, e.value.reason) == ("denied", "user-denied")


def test_consent_timeout_raises_denied_timeout():
    script, state = _consent_script(10_000, "granted")
    c, clock = _client(script)
    with pytest.raises(LocalDataError) as e:
        run(c.local_query("books", wait_consent=70.0))
    assert (e.value.code, e.value.reason) == ("denied", "timeout")
    assert clock.now == 70.0 and state["polls"] == 70
    assert [v for _, v, _ in c._sock.routed].count("local.query") == 1   # never re-sent


def test_describe_needs_no_consent_and_pending_is_an_error_there():
    c, _ = _client(lambda v, p: {"error": "consent-pending"})
    with pytest.raises(LocalDataError) as e:
        run(c.local_describe())
    assert e.value.code == "consent-pending"


# ─── upsert paging (§2.6) ────────────────────────────────────────────────────

def _upsert_script():
    store = {}

    def script(verb, payload):
        assert verb == "local.upsert"
        ids, ins, upd = [], 0, 0
        for i, rec in enumerate(payload["records"]):
            rid = rec.get("id") or f"gen-{len(store)}-{i}"
            if rid in store:
                upd += 1
            else:
                ins += 1
            store[rid] = rec["fields"]
            ids.append(rid)
        return {"ok": True, "collection": payload["collection"], "inserted": ins,
                "updated": upd, "ids": ids, "total": len(store)}
    return script, store


def test_upsert_250_records_is_three_calls_with_ids_in_input_order():
    script, store = _upsert_script()
    c, _ = _client(script)
    records = [{"id": f"r{i:03d}", "n": i} if i % 2 == 0 else {"fields": {"n": i}}
               for i in range(250)]
    res = run(c.local_upsert("books", records, namespace="book-logger"))
    calls = c._sock.routed
    assert [len(p["records"]) for _, _, p in calls] == [100, 100, 50]
    assert all(p["namespace"] == "book-logger" and p["mode"] == "upsert" for _, _, p in calls)
    assert len(res["ids"]) == 250 and res["pages"] == 3
    for i, rid in enumerate(res["ids"]):
        if i % 2 == 0:
            assert rid == f"r{i:03d}"
        assert store[rid] == {"n": i}
    assert res["inserted"] == 250 and res["updated"] == 0 and res["total"] == 250
    # flat records become the {id, fields} wire form
    assert calls[0][2]["records"][0] == {"id": "r000", "fields": {"n": 0}}


def test_upsert_bad_mode_and_mismatched_ids_are_refused():
    c, _ = _client(lambda v, p: {"ok": True, "ids": []})
    with pytest.raises(LocalDataError) as e:
        run(c.local_upsert("books", [{"a": 1}], mode="merge"))
    assert e.value.code == "bad-request" and c._sock.sent == []
    with pytest.raises(LocalDataError) as e:
        run(c.local_upsert("books", [{"a": 1}]))
    assert e.value.code == "bad-reply"


# ─── query + cursor (§2.5) ───────────────────────────────────────────────────

def test_query_all_follows_cursor_until_null():
    pages = {None: (["a", "b"], "c1"), "c1": (["c", "d"], "c2"), "c2": (["e"], None)}

    def script(verb, payload):
        ids, nxt = pages[payload.get("cursor")]
        return {"ok": True, "collection": "books", "rows": [{"id": i} for i in ids],
                "count": len(ids), "total": 5, "cursor": nxt}
    c, _ = _client(script)
    rows = run(c.local_query_all("books", {"orderBy": "-finished"}))
    assert [r["id"] for r in rows] == ["a", "b", "c", "d", "e"]
    assert [p.get("cursor") for _, _, p in c._sock.routed] == [None, "c1", "c2"]
    assert all(p["stage"] == {"orderBy": "-finished"} for _, _, p in c._sock.routed)
    assert sum(1 for t, _ in c._sock.sent if t == "REQ:get_nodes") == 1


SCALAR = {"ok": True, "collection": "books", "value": 3}
GROUPS = {"ok": True, "collection": "books", "categories": ["2026-01", "2026-02"],
          "series": [{"name": "count", "values": [4, 7]}],
          "rows": [{"key": "2026-01", "value": 4}, {"key": "2026-02", "value": 7}]}


@pytest.mark.parametrize("reply,shape", [(SCALAR, "scalar"), (GROUPS, "groups"),
                                         ({"ok": True, "shape": "scalar", "value": None}, "scalar")])
def test_scalar_and_group_replies_pass_through_and_query_all_rejects(reply, shape):
    c, _ = _client(lambda v, p: dict(reply))
    assert run(c.local_query("books", {"aggregate": {"count": "*"}})) == reply
    assert localdata.reply_shape(reply) == shape
    with pytest.raises(LocalDataError) as e:
        run(c.local_query_all("books", {"aggregate": {"count": "*"}}))
    assert e.value.code == "bad-request" and shape in e.value.reason


def test_truncated_page_passes_through():
    r = {"ok": True, "collection": "books", "rows": [], "count": 0, "total": 9,
         "cursor": None, "truncated": True}
    c, _ = _client(lambda v, p: r)
    assert run(c.local_query("books"))["truncated"] is True


# ─── delete (§2.7) ───────────────────────────────────────────────────────────

def test_delete_where_without_confirm_total_is_refused_client_side():
    c, _ = _client(lambda v, p: {"ok": True, "deleted": 0, "total": 0})
    with pytest.raises(LocalDataError) as e:
        run(c.local_delete("books", where={}))
    assert e.value.code == "bad-request" and "confirm_total" in e.value.reason
    assert c._sock.sent == []
    with pytest.raises(LocalDataError):
        run(c.local_delete("books", ["a"], where={}))
    with pytest.raises(LocalDataError):
        run(c.local_delete("books"))


def test_delete_by_where_and_by_ids():
    c, _ = _client(lambda v, p: {"ok": True, "deleted": 3 if "where" in p else len(p["ids"]),
                                 "total": 0})
    res = run(c.local_delete("books", where={}, confirm_total=3))
    assert res == {"ok": True, "deleted": 3, "total": 0}
    assert c._sock.routed[-1][2] == {"collection": "books", "where": {}, "confirmTotal": 3}
    res = run(c.local_delete("books", [f"id{i}" for i in range(1500)]))
    assert res["deleted"] == 1500
    assert [len(p["ids"]) for _, v, p in c._sock.routed[1:]] == [1000, 500]


# ─── E2EE studio link ────────────────────────────────────────────────────────

def test_sealed_reply_is_opened():
    from carterkit.e2ee import E2EESession
    import base64
    key = base64.b64encode(bytes([7]) * 32).decode()
    phone = E2EESession(bytes([7]) * 32, is_device_side=True, channel="studio", sender="iPhone")
    c = CarterClient("ws://x", "tok", "studio", role="controller", name="hub",
                     e2ee_key=key, can_route=True, can_monitor=True)
    c._sock = _StudioSock(lambda v, p: phone.seal({"ok": True, "consent": "granted"}))
    assert run(c.local_describe())["consent"] == "granted"
    # the route_msg envelope itself goes out plaintext
    assert c._sock.sent[-1][1]["type"] == "local.describe"


# ─── mirror change-notice (§4) ───────────────────────────────────────────────

def test_parse_local_event():
    ev = parse_local_event({"msg_type": "studio.event", "event": "local",
                            "namespace": "book-logger", "collection": "books",
                            "op": "upsert", "ids": ["seed-dune"], "total": 3, "seq": 41})
    assert (ev.namespace, ev.collection, ev.op, ev.ids, ev.total, ev.seq) == \
        ("book-logger", "books", "upsert", ["seed-dune"], 3, 41)
    assert parse_local_event({"msg_type": "studio.event", "event": "layout"}) is None
    assert parse_local_event({"msg_type": "studio.event", "event": "local"}) is None
    assert parse_local_event("nope") is None


# ─── CLI ─────────────────────────────────────────────────────────────────────

def test_cli_seed_reads_json_array_file(tmp_path, monkeypatch, capsys):
    import carterkit.cli as cli
    script, store = _upsert_script()
    made = []

    def fake_client(args):
        c, _ = _client(script)
        made.append((args.connection, args.channel, args.token))

        async def noop():
            return None
        c.connect = noop
        c.close = noop
        return c
    monkeypatch.setattr(cli, "_local_client", fake_client)
    f = tmp_path / "books.json"
    f.write_text(json.dumps([{"id": "seed-dune", "title": "Dune"}, {"title": "Solaris"}]))
    rc = cli_main(["local", "seed", "ws://127.0.0.1:8899", "--channel", "studio",
                   "--token", "k", "books", str(f)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ids"][0] == "seed-dune" and out["inserted"] == 2
    assert made == [("ws://127.0.0.1:8899", "studio", "k")]
    f.write_text(json.dumps({"not": "an array"}))
    assert cli_main(["local", "seed", "ws://x", "books", str(f)]) == 2


def test_cli_reports_local_data_error(monkeypatch, capsys):
    import carterkit.cli as cli

    def fake_client(args):
        c, _ = _client(lambda v, p: {"error": "no-local-source", "reason": "none"})

        async def noop():
            return None
        c.connect = noop
        c.close = noop
        return c
    monkeypatch.setattr(cli, "_local_client", fake_client)
    assert cli_main(["local", "describe", "ws://x"]) == 1
    assert "no-local-source" in capsys.readouterr().err


def test_cli_refuses_embedded_relay():
    with pytest.raises(SystemExit):
        cli_main(["local", "describe", "", "--channel", "s"])


# ─── mirror lint ─────────────────────────────────────────────────────────────

def _layout(sources):
    return {"name": "L", "sources": sources,
            "tabs": [{"title": "T", "grid": {"columns": 2, "rows": 2, "children": []}}]}


def _mirror_errors(layout):
    return [f for f in validate_layout(layout)
            if f["severity"] == "error" and "mirror" in f["detail"]]


def test_mirror_lint():
    ok = {"db": {"type": "local", "collections": {
        "books": {"fields": {"title": "string"}, "mirror": True}}}}
    assert _mirror_errors(_layout(ok)) == []
    bad_type = {"db": {"type": "local", "collections": {
        "books": {"fields": {"title": "string"}, "mirror": "yes"}}}}
    assert len(_mirror_errors(_layout(bad_type))) == 1
    non_local = {"feed": {"type": "http", "baseURL": "https://x",
                          "collections": {"books": {"mirror": True}}}}
    assert len(_mirror_errors(_layout(non_local))) == 1
    on_source = {"db": {"type": "local", "mirror": True, "collections": {
        "books": {"fields": {"title": "string"}}}}}
    assert len(_mirror_errors(_layout(on_source))) >= 1
