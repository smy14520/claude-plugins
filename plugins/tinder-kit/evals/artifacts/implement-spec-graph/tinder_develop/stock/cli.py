"""stock 命令行入口：python3 -m stock.cli [--db PATH] <command> ..."""

import argparse
import re
import sys
from pathlib import Path

from stock.store import Store


def parse_positive_int(raw: str) -> int | None:
    """把字符串解析为严格十进制正整数；含非 [0-9] 字符（符号、空白、下划线、全角）或 <= 0 时返回 None。"""
    if re.fullmatch(r"[0-9]+", raw) is None:
        return None
    qty = int(raw)
    if qty <= 0:
        return None
    return qty


def cmd_add(store: Store, args: argparse.Namespace) -> int:
    qty = parse_positive_int(args.qty)
    if qty is None:
        print(f"error: 数量必须是正整数: {args.qty}", file=sys.stderr)
        return 1
    items = store.load()
    items[args.name] = items.get(args.name, 0) + qty
    store.save(items)
    print(f"{args.name}: {items[args.name]}")
    return 0


def cmd_remove(store: Store, args: argparse.Namespace) -> int:
    qty = parse_positive_int(args.qty)
    if qty is None:
        print(f"error: 数量必须是正整数: {args.qty}", file=sys.stderr)
        return 1
    items = store.load()
    if args.name not in items:
        print(f"error: 商品不存在: {args.name}", file=sys.stderr)
        return 1
    if items[args.name] < qty:
        print(f"error: 库存不足: {args.name}", file=sys.stderr)
        return 1
    remaining = items[args.name] - qty
    if remaining == 0:
        del items[args.name]
    else:
        items[args.name] = remaining
    store.save(items)
    print(f"{args.name}: {remaining}")
    return 0


def format_items(items: dict[str, int]) -> str:
    return "\n".join(f"{name}: {qty}" for name, qty in sorted(items.items()))


def cmd_list(store: Store, args: argparse.Namespace) -> int:
    output = format_items(store.load())
    if not output:
        print("(empty)")
    else:
        print(output)
    return 0


def cmd_report(store: Store, args: argparse.Namespace) -> int:
    threshold = parse_positive_int(args.threshold)
    if threshold is None:
        print(f"error: 阈值必须是正整数: {args.threshold}", file=sys.stderr)
        return 1
    items = {name: qty for name, qty in store.load().items() if qty < threshold}
    output = format_items(items)
    if not output:
        print("nothing to restock")
    else:
        print(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stock")
    parser.add_argument("--db", default="stock.json", help="库存文件路径")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("add", help="入库：把数量累加到商品（不存在则新建）")
    p.add_argument("name", help="商品名")
    p.add_argument("qty", help="数量（正整数）")
    p.set_defaults(handler=cmd_add)

    p = sub.add_parser("remove", help="出库：扣减商品数量")
    p.add_argument("name", help="商品名")
    p.add_argument("qty", help="数量（正整数）")
    p.set_defaults(handler=cmd_remove)

    p = sub.add_parser("list", help="列出全部库存（按商品名排序）")
    p.set_defaults(handler=cmd_list)

    p = sub.add_parser("report", help="补货报告：列出数量严格小于阈值的商品")
    p.add_argument("--threshold", default="5", help="补货阈值（正整数，默认 5）")
    p.set_defaults(handler=cmd_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = Store(Path(args.db))
    return args.handler(store, args)


if __name__ == "__main__":
    sys.exit(main())
