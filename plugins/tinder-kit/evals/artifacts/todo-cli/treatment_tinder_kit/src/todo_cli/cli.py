"""CLI 接缝：argparse 子命令 → Store 领域操作 → 纯文本输出（无 ANSI 颜色，D7）。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .model import Todo
from .store import PRIORITY_RANK, Store, TodoNotFoundError

DEFAULT_STORE_PATH = Path("~/.todo-cli.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description="本地 CLI Todo 工具：标签过滤 + 单文件 JSON 持久化",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="创建一条 Todo")
    p_add.add_argument("text", help="Todo 文案")
    p_add.add_argument("-t", "--tag", action="append", default=[], metavar="TAG",
                       help="Tag，可重复，每旗标一个")
    p_add.add_argument("--priority", choices=tuple(PRIORITY_RANK), default=None, metavar="PRIORITY",
                       help="Priority 三档：high/med/low，缺省无优先级")

    p_list = sub.add_parser("list", help="列出 Todo（默认只显示 open）")
    p_list.add_argument("--tag", action="append", default=[], metavar="TAG",
                        help="按 Tag 过滤，多个为交集（AND）")
    p_list.add_argument("--all", action="store_true", help="包含已完成的")

    for name, help_text in (("done", "标记完成"), ("undo", "重新打开")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("id", type=int, help="Todo 编号")
    p_delete = sub.add_parser("delete", aliases=["rm"], help="删除（ID 不复用）")
    p_delete.add_argument("id", type=int, help="Todo 编号")

    sub.add_parser("tags", help="列出全部 Tag 及 open/done 计数")
    return parser


def render(todo: Todo, text_width: int = 0, show_priority: bool = False) -> str:
    """`[x]   1  买牛奶  high  #shopping` 风格的行渲染（优先级列按需出现）。"""
    marker = "x" if todo.status == "done" else " "
    line = f"[{marker}] {todo.id:>3}  {todo.text:<{text_width}}"
    if show_priority:
        line += f"  {todo.priority or '':<4}"
    tags = " ".join(f"#{tag}" for tag in todo.tags)
    return f"{line}  {tags}" if tags else line.rstrip()


def main(argv: list[str] | None = None, store_path=None) -> int:
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:  # argparse 用法错误 / --help：透传其退出码
        return exc.code if isinstance(exc.code, int) else 1

    path = (Path(store_path) if store_path is not None else DEFAULT_STORE_PATH).expanduser()
    store = Store.load(path)
    changed = False
    try:
        if args.cmd == "add":
            todo = store.add(args.text, tags=args.tag, priority=args.priority)
            print(render(todo, show_priority=bool(todo.priority)))
            changed = True
        elif args.cmd == "list":
            rows = store.list_todos(tags=args.tag, show_all=args.all)
            width = max((len(t.text) for t in rows), default=0)
            any_priority = any(t.priority for t in rows)
            for todo in rows:
                print(render(todo, width, any_priority))
        elif args.cmd == "done":
            todo = store.done(args.id)
            print(render(todo, show_priority=bool(todo.priority)))
            changed = True
        elif args.cmd == "undo":
            todo = store.undo(args.id)
            print(render(todo, show_priority=bool(todo.priority)))
            changed = True
        elif args.cmd in ("delete", "rm"):
            store.rm(args.id)
            changed = True
        elif args.cmd == "tags":
            for tag, (open_n, done_n) in store.tag_counts().items():
                print(f"{tag:<12} open:{open_n}  done:{done_n}")
    except TodoNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if changed:  # 只读命令（list/tags）绝不写盘：Store 仅在首次真正写入时创建
        store.save(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
