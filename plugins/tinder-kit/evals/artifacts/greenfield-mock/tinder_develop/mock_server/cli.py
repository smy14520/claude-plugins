"""Command line interface: the serve and check subcommands."""
from __future__ import annotations

import argparse
import sys

from .checker import check_file
from .config import ConfigError, load_config
from .server import serve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mock-server",
        description=(
            "Lightweight local HTTP API mock server driven by a single "
            "mocks.json contract (Python stdlib only)."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_contract_option(sub: argparse.ArgumentParser) -> None:
        sub.add_argument(
            "-f", "--file", default="mocks.json",
            help="path to the mocks.json contract (default: %(default)s)",
        )

    serve_parser = subparsers.add_parser("serve", help="serve the contract as a local HTTP mock")
    add_contract_option(serve_parser)
    serve_parser.add_argument("--host", default="127.0.0.1", help="bind address (default: %(default)s)")
    serve_parser.add_argument("--port", type=int, default=8000, help="bind port (default: %(default)s)")

    check_parser = subparsers.add_parser("check", help="statically check the contract")
    add_contract_option(check_parser)

    args = parser.parse_args(argv)

    errors = check_file(args.file)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        if args.command == "check":
            print(f"check failed: {len(errors)} error(s) in {args.file}", file=sys.stderr)
        else:
            print(
                f"refusing to start: fix {args.file} first (run `mock-server check`)",
                file=sys.stderr,
            )
        return 1

    if args.command == "check":
        print(f"OK: {args.file} is a valid contract")
        return 0

    try:
        routes = load_config(args.file)
    except ConfigError as exc:
        print(f"refusing to start: {exc}", file=sys.stderr)
        return 1
    serve(routes, args.host, args.port, args.file)
    return 0
