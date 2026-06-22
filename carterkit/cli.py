"""Command-line interface: ``carterkit <command>`` (also ``python -m carterkit``).

Commands: catalog · doc · examples · validate · gen · relay · version.
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
    print(carterkit.codegen.generate_service_stub(layout))
    return 0


def _cmd_relay(args) -> int:
    import asyncio
    from socket_server import MeshServer  # bundled with meshsocket
    print(f"MeshSocket relay on ws://{args.host}:{args.port}", file=sys.stderr)
    asyncio.run(MeshServer(host=args.host, port=args.port).start())
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

    c = sub.add_parser("relay", help="run the bundled MeshSocket relay")
    c.add_argument("--host", default="0.0.0.0")
    c.add_argument("--port", type=int, default=8765)
    c.set_defaults(fn=_cmd_relay)

    c = sub.add_parser("version", help="print the carterkit version")
    c.set_defaults(fn=_cmd_version)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
