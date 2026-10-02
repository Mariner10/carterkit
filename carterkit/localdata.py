"""Pure helpers for the studio-socket ``local.*`` readback/seed verbs.

The phone answers four routed verbs on the **studio** socket only (readback spec
``2026-09-24-local-readback-design.md`` §2): ``local.describe``, ``local.query``,
``local.upsert`` and ``local.delete``. This module holds everything that needs no
socket — request builders, reply unwrapping into :class:`LocalDataError`, paging and
reply merging, and the ``studio.event`` / ``local`` change-notice parser — so
``CarterClient.local_*`` and the MCP share one implementation of the wire contract.
"""
from __future__ import annotations

from dataclasses import dataclass, field

#: Routed verb names (the ``type`` inside ``route_msg``).
VERB_DESCRIBE = "local.describe"
VERB_QUERY = "local.query"
VERB_UPSERT = "local.upsert"
VERB_DELETE = "local.delete"

#: Records per routed ``local.upsert`` call (spec §2.6).
UPSERT_PAGE = 100
#: Ids per routed ``local.delete`` call (spec §2.7 "Rows cap: 1000 per call").
DELETE_PAGE = 1000
#: Default consent wait: the sheet times out at 60 s on the phone (§3.1); 70 s covers it.
WAIT_CONSENT = 70.0
#: How often ``local.describe`` is polled while the consent sheet is up (§3.1).
CONSENT_POLL = 1.0

UPSERT_MODES = ("upsert", "insert", "patch")

#: Every §2.3 device code, plus the client-side codes this library raises itself.
ERROR_PROSE = {
    "bad-request": "the request was malformed (missing/wrong-typed field or over a size cap)",
    "no-layout": "no layout is loaded on the phone (or the studio placeholder is showing)",
    "no-local-source": "the active layout declares no type:'local' source",
    "unknown-namespace": "that namespace is not declared by the active layout "
                         "(call local_describe for the exact strings)",
    "unknown-collection": "that collection is not declared by the active layout",
    "consent-pending": "the consent sheet is up on the phone; waiting for the owner's tap",
    "denied": "the owner declined, dismissed, or let the consent sheet time out",
    "busy": "another studio approval sheet is up on the phone (provision or local)",
    "invalid-stage": "the phone's store rejected the stage (where/groupBy/aggregate/having/orderBy/limit)",
    "limit": "a store cap was exceeded (50k rows per collection, 500 groups, 1000 records per upsert)",
    "schema": "the declared local schema failed validation on the phone",
    "remote-source": "that source is not a local store",
    "validation": "a record does not match the declared field types",
    "store-error": "the phone's store failed (SQLite error)",
    # client-side
    "no-reply": "the phone did not answer within the routed-reply window "
                "(an app without the local.* verbs times out — update CAR-TER)",
    "no-device": "no device is on the channel",
    "not-capable": "this CarterClient cannot send routed requests",
    "bad-reply": "the phone's reply did not match the local.* wire contract",
}


class LocalDataError(Exception):
    """A ``local.*`` verb failed. ``code`` is a §2.3 wire code (or a client-side code
    from :data:`ERROR_PROSE`); ``reason`` is the phone's (or this library's) detail."""

    def __init__(self, code: str, reason: str | None = None, *, reply: dict | None = None):
        self.code = code
        self.reason = reason
        self.reply = reply
        prose = ERROR_PROSE.get(code, "local data error")
        super().__init__(f"{code}: {prose}" + (f" ({reason})" if reason else ""))


def describe_error(code: str, reason: str | None = None) -> str:
    """Human prose for an error code (used by the CLI and the MCP)."""
    text = ERROR_PROSE.get(code, f"error {code!r}")
    return f"{text} — {reason}" if reason else text


def unwrap(reply, *, allow_pending: bool = False) -> dict:
    """Return a successful reply dict, else raise :class:`LocalDataError`.

    ``None`` (routed-request timeout) raises ``no-reply``. ``{error, reason}`` raises
    that code — except ``consent-pending`` when ``allow_pending`` is true, which is
    returned so the caller can start the consent poll."""
    if reply is None:
        raise LocalDataError("no-reply")
    if not isinstance(reply, dict):
        raise LocalDataError("bad-reply", f"expected an object, got {type(reply).__name__}")
    err = reply.get("error")
    if err:
        code = str(err)
        if code == "consent-pending" and allow_pending:
            return reply
        reason = reply.get("reason")
        raise LocalDataError(code, str(reason) if reason is not None else None, reply=reply)
    if reply.get("ok") is False:
        raise LocalDataError("bad-reply", "ok:false without an error code", reply=reply)
    return reply


def is_consent_pending(reply) -> bool:
    return isinstance(reply, dict) and reply.get("error") == "consent-pending"


# ─── request builders ────────────────────────────────────────────────────────

def _address(collection, namespace) -> dict:
    if not isinstance(collection, str) or not collection:
        raise LocalDataError("bad-request", "collection must be a non-empty string")
    req = {"collection": collection}
    if namespace is not None:
        if not isinstance(namespace, str) or not namespace:
            raise LocalDataError("bad-request", "namespace must be a non-empty string")
        req = {"namespace": namespace, **req}
    return req


def describe_request() -> dict:
    """Payload for ``local.describe`` (spec §2.4: ``{}``)."""
    return {}


def query_request(collection, stage=None, *, namespace=None, cursor=None) -> dict:
    """Payload for ``local.query`` (§2.5). ``stage`` is passed through untouched; the
    phone's store is the judge (``invalid-stage``)."""
    req = _address(collection, namespace)
    if stage is not None:
        if not isinstance(stage, dict):
            raise LocalDataError("bad-request", "stage must be an object")
        req["stage"] = stage
    if cursor is not None:
        if not isinstance(cursor, str):
            raise LocalDataError("bad-request", "cursor must be the opaque string from a reply")
        req["cursor"] = cursor
    return req


def normalize_record(rec, index: int = 0) -> dict:
    """Wire form ``{id?, fields}`` of one upsert record. Accepts the wire form itself
    (only ``id``/``fields`` keys, ``fields`` an object) or a flat ``{field: value}``
    dict whose optional ``id`` key becomes the record id."""
    if not isinstance(rec, dict):
        raise LocalDataError("bad-request", f"record {index} must be an object")
    if isinstance(rec.get("fields"), dict) and set(rec) <= {"id", "fields"}:
        out = {"fields": rec["fields"]}
        if rec.get("id") is not None:
            out = {"id": rec["id"], **out}
    else:
        flat = dict(rec)
        rid = flat.pop("id", None)
        out = {"fields": flat}
        if rid is not None:
            out = {"id": rid, **out}
    if "id" in out and not isinstance(out["id"], str):
        raise LocalDataError("bad-request", f"record {index}: id must be a string")
    return out


def upsert_request(collection, records, *, mode="upsert", namespace=None) -> dict:
    """Payload for one ``local.upsert`` call (§2.6, at most :data:`UPSERT_PAGE` records)."""
    if mode not in UPSERT_MODES:
        raise LocalDataError("bad-request", f"mode must be one of {list(UPSERT_MODES)}, got {mode!r}")
    if not isinstance(records, list):
        raise LocalDataError("bad-request", "records must be a list")
    if len(records) > UPSERT_PAGE:
        raise LocalDataError("bad-request", f"at most {UPSERT_PAGE} records per call (page them)")
    req = _address(collection, namespace)
    req["mode"] = mode
    req["records"] = [normalize_record(r, i) for i, r in enumerate(records)]
    return req


def delete_request(collection, ids=None, *, where=None, confirm_total=None,
                   namespace=None) -> dict:
    """Payload for ``local.delete`` (§2.7): by ``ids``, or by ``where`` plus
    ``confirm_total`` (the live count you just read). ``where`` without
    ``confirm_total`` is refused here, before anything is sent."""
    req = _address(collection, namespace)
    if (ids is None) == (where is None):
        raise LocalDataError("bad-request", "pass exactly one of ids or where")
    if ids is not None:
        if (not isinstance(ids, list) or not ids
                or not all(isinstance(i, str) and i for i in ids)):
            raise LocalDataError("bad-request", "ids must be a non-empty list of strings")
        if len(ids) > DELETE_PAGE:
            raise LocalDataError("bad-request", f"at most {DELETE_PAGE} ids per call (page them)")
        req["ids"] = list(ids)
        return req
    if not isinstance(where, dict):
        raise LocalDataError("bad-request", "where must be an object ({} = every record)")
    if confirm_total is None:
        raise LocalDataError(
            "bad-request", "delete by where needs confirm_total — read the collection's "
                           "live total first (local_query / local_describe) and pass it")
    if isinstance(confirm_total, bool) or not isinstance(confirm_total, int) or confirm_total < 0:
        raise LocalDataError("bad-request", "confirm_total must be a non-negative integer")
    req["where"] = where
    req["confirmTotal"] = confirm_total
    return req


# ─── paging and merging ──────────────────────────────────────────────────────

def page_records(records, size: int = UPSERT_PAGE) -> list[list]:
    """Split ``records`` into consecutive pages of at most ``size`` (order kept)."""
    if size < 1:
        raise ValueError("page size must be >= 1")
    records = list(records)
    return [records[i:i + size] for i in range(0, len(records), size)]


def merge_upsert_replies(replies, page_sizes=None) -> dict:
    """Merge per-page ``local.upsert`` replies into one: counts summed, ``ids``
    concatenated in page order (so they line up with the input records), ``total`` from
    the last page. With ``page_sizes`` each reply's ``ids`` length is checked."""
    merged = {"ok": True, "inserted": 0, "updated": 0, "ids": [], "total": None,
              "pages": 0}
    for n, reply in enumerate(replies):
        ids = reply.get("ids")
        if not isinstance(ids, list):
            raise LocalDataError("bad-reply", f"upsert page {n} has no ids list", reply=reply)
        if page_sizes is not None and len(ids) != page_sizes[n]:
            raise LocalDataError("bad-reply", f"upsert page {n} returned {len(ids)} ids "
                                              f"for {page_sizes[n]} records", reply=reply)
        if "collection" in reply:
            merged["collection"] = reply["collection"]
        merged["inserted"] += int(reply.get("inserted") or 0)
        merged["updated"] += int(reply.get("updated") or 0)
        merged["ids"].extend(ids)
        if "total" in reply:
            merged["total"] = reply["total"]
        merged["pages"] += 1
    return merged


def reply_shape(reply: dict) -> str:
    """``'scalar'``, ``'groups'`` or ``'rows'`` for a ``local.query`` reply (§2.5;
    alignment row 27 — an explicit ``shape`` wins, else inferred from the keys)."""
    shape = reply.get("shape")
    if shape in ("scalar", "groups", "rows"):
        return shape
    if "categories" in reply or "series" in reply or "groups" in reply:
        return "groups"
    if "value" in reply and "rows" not in reply:
        return "scalar"
    return "rows"


# ─── mirror change-notice (§4) ───────────────────────────────────────────────

@dataclass(frozen=True)
class LocalChangeEvent:
    """A ``studio.event`` / ``event: local`` change notice: ids and the new total of a
    mirrored collection, never record fields. ``seq`` is per session and monotonic."""
    namespace: str
    collection: str
    op: str
    ids: list = field(default_factory=list)
    total: int | None = None
    seq: int | None = None


def parse_local_event(payload) -> LocalChangeEvent | None:
    """A :class:`LocalChangeEvent` for a studio mirror frame, else ``None`` (any other
    frame, or a malformed local notice)."""
    if not isinstance(payload, dict):
        return None
    if payload.get("msg_type") != "studio.event" or payload.get("event") != "local":
        return None
    ns, coll, op = payload.get("namespace"), payload.get("collection"), payload.get("op")
    if not (isinstance(ns, str) and isinstance(coll, str) and isinstance(op, str)):
        return None
    ids = payload.get("ids")
    ids = [i for i in ids if isinstance(i, str)] if isinstance(ids, list) else []
    total = payload.get("total")
    seq = payload.get("seq")
    return LocalChangeEvent(
        namespace=ns, collection=coll, op=op, ids=ids,
        total=total if isinstance(total, int) and not isinstance(total, bool) else None,
        seq=seq if isinstance(seq, int) and not isinstance(seq, bool) else None)
