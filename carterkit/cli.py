"""Command-line interface: ``carterkit <command>`` (also ``python -m carterkit``).

Commands: catalog · doc · examples · validate · gen · explore · local · relay · version.
"""
from __future__ import annotations

import argparse
import json
import sys


def _cmd_catalog(args) -> int:
    import carterkit
    cat = carterkit.controls(types=[args.type] if args.type else None, include_theme=args.theme)
    if args.json:
        print(json.dumps(cat, indent=2))
    else:
        for t in sorted(cat):
            spec = cat[t]
            print(f"{t:18} {spec.get('label', ''):16} ({spec.get('category', '')})")
    return 0


def _cmd_doc(args) -> int:
    import carterkit
    md = carterkit.doc_markdown(args.control)
    if md is None:
        print(f"no doc for {args.control!r}", file=sys.stderr)
        return 1
    print(md)
    return 0


def _cmd_examples(args) -> int:
    import carterkit
    if args.name:
        from carterkit import catalog, controldocs_dir
        ex = catalog.find_example(controldocs_dir(), args.control, args.name)
        if not ex:
            print(f"no example {args.name!r} for {args.control!r}", file=sys.stderr)
            return 1
        print(ex["json"])
        return 0
    exs = carterkit.examples(args.control)
    if not exs:
        print(f"no examples for {args.control!r}", file=sys.stderr)
        return 1
    for ex in exs:
        print("•", ex["name"])
    return 0


def _cmd_validate(args) -> int:
    import carterkit
    with open(args.file) as f:
        layout = json.load(f)
    findings = carterkit.validate_layout(layout)
    print(carterkit.format_findings(findings))
    return 1 if any(f["severity"] == "error" for f in findings) else 0


def _cmd_gen(args) -> int:
    import carterkit
    with open(args.file) as f:
        layout = json.load(f)
    print(carterkit.codegen.generate_service_stub(layout, layout_path=args.file))
    return 0


def _cmd_explore(args) -> int:
    import asyncio
    import webbrowser
    from .explore import build_explorer

    overrides = {k: v for k, v in (("channel", args.channel), ("token", args.token))
                 if v is not None}
    explorer = build_explorer(args.source, device=args.device, port=args.port,
                              host="0.0.0.0" if args.lan else "127.0.0.1", **overrides)

    def ready(ex):
        url = f"http://127.0.0.1:{ex.port}"
        print(f"Layout Link → {url}")
        conn = ex.hub.connection
        if conn.kind in ("local", "selfhosted"):
            print(f"pair the phone (CAR-TER → Settings → Studio Session → scan):")
            payload = ex.hub.qr_json()
            from .qr import encode as qr_encode
            print(qr_encode(payload, ecc="M").ascii())
            print(f"  {payload}")
            if conn.is_loopback_relay():
                print("  (relay bound to 127.0.0.1 — a phone on the LAN cannot reach it; "
                      "pass --lan)", file=sys.stderr)
        if ex.pull is not None and ex.hub.layout is None:
            print("waiting for the phone to join — the layout appears the moment it does")
        if not args.no_open:
            webbrowser.open(url)

    try:
        asyncio.run(explorer.run(ready=ready))
    except KeyboardInterrupt:
        print("\nbye")
    return 0


def _load_json_arg(text_or_path, what):
    """A JSON value from inline text or `@path` / an existing file path."""
    import os
    if text_or_path is None:
        return None
    path = text_or_path[1:] if text_or_path.startswith("@") else text_or_path
    if text_or_path.startswith("@") or os.path.isfile(path):
        with open(path) as f:
            return json.load(f)
    try:
        return json.loads(text_or_path)
    except ValueError as e:
        raise SystemExit(f"{what}: not JSON and not a file ({e})")


def _local_client(args):
    """A studio-channel CarterClient for `carterkit local` (routes + reads the roster)."""
    from .client import CarterClient
    from .connection import Connection
    overrides = {k: v for k, v in (("channel", args.channel), ("token", args.token))
                 if v is not None}
    try:
        conn = Connection.parse(args.connection or None, **overrides)
    except ValueError as e:
        raise SystemExit(f"carterkit local: {e}")
    if conn.kind == "local":
        raise SystemExit("carterkit local needs the studio relay: pass its ws:// URL "
                         "(plus --channel/--token) or a pairing JSON file")
    kw = conn.client_kwargs(name=args.name)
    kw.update(can_route=True, can_monitor=True)
    return CarterClient(**kw)


def _cmd_local(args) -> int:
    import asyncio
    from .localdata import LocalDataError

    if args.action == "seed":
        records = _load_json_arg("@" + args.file, "seed file")
        if not isinstance(records, list):
            print(f"{args.file}: expected a JSON array of records", file=sys.stderr)
            return 2
    stage = _load_json_arg(getattr(args, "stage", None), "--stage")

    async def run():
        async with _local_client(args) as client:
            common = {"device_id": args.device_id}
            if args.action == "describe":
                return await client.local_describe(**common)
            common.update(namespace=args.namespace, wait_consent=args.wait_consent)
            if args.action == "query":
                if args.all:
                    return await client.local_query_all(args.collection, stage, **common)
                return await client.local_query(args.collection, stage, **common)
            return await client.local_upsert(args.collection, records, mode=args.mode,
                                             **common)

    try:
        result = asyncio.run(run())
    except LocalDataError as e:
        print(f"local {args.action} failed: {e}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


def _cmd_relay(args) -> int:
    import asyncio
    from .relay import LocalRelay, lan_ip

    host = "0.0.0.0" if args.lan else args.host
    key = args.key
    if key is None and not args.insecure:
        import secrets
        key = secrets.token_urlsafe(24)
        print(f"relay key (pass as the pairing token): {key}", file=sys.stderr)
    if not key and not args.insecure:
        print("refusing to run an open relay: pass --key or --insecure", file=sys.stderr)
        return 2
    try:
        relay = LocalRelay(port=args.port, key=key or "", host=host, insecure=args.insecure)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    where = f"ws://{lan_ip()}:{args.port}" if host == "0.0.0.0" else f"ws://{host}:{args.port}"
    auth = "open — NO AUTH" if not key else "shared-key auth"
    print(f"MeshSocket relay on {where} ({auth})", file=sys.stderr)
    if host in ("127.0.0.1", "localhost", "::1"):
        print("bound to loopback: a phone on the LAN cannot reach it — add --lan "
              "(or Hub(host=\"0.0.0.0\") / CARTER_RELAY_HOST=0.0.0.0 in code)", file=sys.stderr)

    async def run():
        async with relay:
            await asyncio.Event().wait()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass
    return 0


def _cmd_version(args) -> int:
    import carterkit
    print(carterkit.__version__)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="carterkit", description="Build and drive CAR-TER layouts.")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("catalog", help="list the control catalog")
    c.add_argument("--type", help="restrict to one control type")
    c.add_argument("--theme", action="store_true", help="include per-control theme fields")
    c.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    c.set_defaults(fn=_cmd_catalog)

    c = sub.add_parser("doc", help="print a control's documentation")
    c.add_argument("control")
    c.set_defaults(fn=_cmd_doc)

    c = sub.add_parser("examples", help="list a control's examples, or print one with --name")
    c.add_argument("control")
    c.add_argument("--name", help="print the JSON of the named example")
    c.set_defaults(fn=_cmd_examples)

    c = sub.add_parser("validate", help="lint a layout JSON file (exit 1 on errors)")
    c.add_argument("file")
    c.set_defaults(fn=_cmd_validate)

    c = sub.add_parser("gen", help="generate a MeshSocket service stub from a layout file")
    c.add_argument("file")
    c.set_defaults(fn=_cmd_gen)

    c = sub.add_parser(
        "explore",
        help="serve a live, typed endpoint explorer for a layout (Layout Link)")
    c.add_argument("source", nargs="?",
                   help="a layout JSON to explore offline, a pairing/device JSON, "
                        "or a ws:// relay URL; omit for the zero-config local relay")
    c.add_argument("--device", nargs="?", const="current", default=None,
                   metavar="FILE_OR_NAME",
                   help="pull a layout off the paired phone: a saved layout's "
                        "file/name, or (bare) whatever is live right now")
    c.add_argument("--channel", help="mesh channel to join")
    c.add_argument("--token", help="relay auth token / shared key (visible in `ps`; "
                   "prefer a pairing/device JSON file)")
    c.add_argument("--port", type=int, default=8770, help="explorer web port")
    c.add_argument("--no-open", action="store_true",
                   help="don't auto-open the browser")
    c.add_argument("--lan", action="store_true",
                   help="bind the embedded relay on 0.0.0.0 so a phone on the LAN can pair")
    c.set_defaults(fn=_cmd_explore)

    c = sub.add_parser("local", help="read or seed the paired phone's local store "
                                     "(studio socket; the owner approves on the phone)")
    lsub = c.add_subparsers(dest="action", required=True)

    def _conn_flags(x):
        x.add_argument("connection", help="studio relay ws:// URL or a pairing JSON file")
        x.add_argument("--channel", help="studio mesh channel")
        x.add_argument("--token", help="relay auth token / shared key")
        x.add_argument("--name", default="carterkit-local", help="this client's mesh name")
        x.add_argument("--device-id", default=None,
                       help="route to this node id (default: the first other channel member)")

    def _coll_flags(x):
        x.add_argument("collection")
        x.add_argument("--namespace", default=None)
        x.add_argument("--wait-consent", type=float, default=70.0,
                       help="seconds to wait for the consent sheet (default 70)")

    x = lsub.add_parser("describe", help="collections, counts and consent state")
    _conn_flags(x)
    x = lsub.add_parser("query", help="read records (one page, or --all)")
    _conn_flags(x)
    _coll_flags(x)
    x.add_argument("--stage", default=None, help="stage JSON, or @file")
    x.add_argument("--all", action="store_true", help="follow the cursor to the end")
    x = lsub.add_parser("seed", help="upsert a JSON array file of records (100 per call)")
    _conn_flags(x)
    _coll_flags(x)
    x.add_argument("file", help="JSON array of records ({id?, fields} or flat)")
    x.add_argument("--mode", default="upsert", choices=["upsert", "insert", "patch"])
    c.set_defaults(fn=_cmd_local)

    c = sub.add_parser("relay", help="run the bundled MeshSocket relay (keyed, loopback by default)")
    c.add_argument("--host", default="127.0.0.1", help="bind address (default loopback)")
    c.add_argument("--lan", action="store_true", help="bind 0.0.0.0 so phones on the LAN can join")
    c.add_argument("--port", type=int, default=8765)
    c.add_argument("--key", default=None,
                   help="shared key clients must present (default: generated and printed once)")
    c.add_argument("--insecure", action="store_true",
                   help="run with NO key — anyone reaching the port joins every channel")
    c.set_defaults(fn=_cmd_relay)

    c = sub.add_parser("version", help="print the carterkit version")
    c.set_defaults(fn=_cmd_version)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
