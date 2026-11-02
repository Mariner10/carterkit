"""Hub/credential error messages, push_layout validation, identical-push skip."""
import asyncio
import logging

import pytest

from carterkit import Layout, HubError
from carterkit.client import CarterNotifyError, MissingCredentialError
from carterkit.connection import Connection
from tests.test_hub import _hub, _thermostat


def test_missing_credential_message():
    e = MissingCredentialError()
    assert "needs a credential: on the phone open Hubs -> Add Hub, then pass it to Hub(...)" in str(e)
    assert "carterbeaudoin.net" in str(e)
    assert isinstance(e, CarterNotifyError) and isinstance(e, ValueError)


def test_account_connection_raises_same_class():
    c = Connection.__new__(Connection)
    c.kind = "account"
    with pytest.raises(MissingCredentialError, match="Add Hub"):
        c.client_kwargs()


def _peer_hub(ui):
    hub = _hub(ui)
    s = hub.client._sock
    s.reply = {"ok": True}

    async def req(t, payload=None, timeout=5.0):
        s.sent.append(("REQ:" + t, payload))
        return {"clients": [{"id": "p1", "name": "phone"}]} if t == "get_nodes" else s.reply
    s.request = req
    return hub


def test_push_layout_rejects_duplicate_ids_before_sending():
    with Layout("X", cols=4, rows=4) as ui:
        ui.button("same", send="a")
        ui.button("same", send="b")
    hub = _peer_hub(ui)
    kids = hub.layout["tabs"][0]["children"]
    kids[1]["id"] = kids[0]["id"]
    with pytest.raises(HubError, match="duplicate_id"):
        asyncio.run(hub.push_layout())
    assert not [x for x in hub.client._sock.sent if x[0] == "REQ:route_msg"]


def test_identical_layout_push_skipped(caplog):
    ui, *_ = _thermostat()
    hub = _peer_hub(ui)
    asyncio.run(hub.push_layout())
    with caplog.at_level(logging.INFO):
        asyncio.run(hub.push_layout())
    sent = [x for x in hub.client._sock.sent if x[0] == "REQ:route_msg"]
    assert len(sent) == 1
    assert "skipped: identical to the last push" in caplog.text


def test_identical_value_push_skipped(caplog):
    ui, temp, *_ = _thermostat()
    hub = _hub(ui)
    asyncio.run(hub.push(temp, 1))
    with caplog.at_level(logging.INFO):
        asyncio.run(hub.push(temp, 1))
    assert len(hub.client._sock.sent) == 1
    assert "skipped: identical" in caplog.text
