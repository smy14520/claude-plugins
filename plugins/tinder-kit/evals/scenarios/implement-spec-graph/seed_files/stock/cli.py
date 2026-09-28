"""stock 命令行入口：python3 -m stock.cli [--db PATH] <command> ..."""

import argparse
import sys
from pathlib import Path

from stock.store import Store


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stock")
    parser.add_argument("--db", default="stock.json", help="库存文件路径")
    parser.add_subparsers(dest="command", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = Store(Path(args.db))
    return args.handler(store, args)


if __name__ == "__main__":
    sys.exit(main())
