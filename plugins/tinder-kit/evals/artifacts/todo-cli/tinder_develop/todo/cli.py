"""展示层：argparse 解析与输出渲染；领域规则一律下沉 core/storage。"""

import argparse
import sys
from datetime import datetime, timezone

from todo import core, storage


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _render(todo: dict) -> str:
    mark = "✓ " if todo["status"] == "done" else ""
    tags = " ".join(f"#{tag}" for tag in todo["tags"])
    line = f"[{todo['id']}] {mark}[{todo['priority']}] {todo['title']}"
    if tags:
        line += f"  {tags}"
    return line


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo", description="本地 CLI Todo：Tag 过滤 + 本地持久化"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="添加 Todo")
    p_add.add_argument("title", help="标题")
    p_add.add_argument("--tags", default="", help="逗号分隔的 Tag，可挂多个")
    p_add.add_argument(
        "--priority", choices=list(core.PRIORITIES), default="med", help="三档优先级"
    )

    p_list = sub.add_parser("list", help="列出 Todo（默认只列未完成）")
    p_list.add_argument(
        "--tag", action="append", default=[], metavar="TAG", help="按 Tag 过滤，可重复（AND 语义）"
    )
    p_list.add_argument("--all", action="store_true", help="含已完成")

    p_done = sub.add_parser("done", help="标记 Todo 为已完成")
    p_done.add_argument("id", type=int, help="Todo 的 id")

    p_undo = sub.add_parser("undo", help="把已完成的 Todo 翻回未完成")
    p_undo.add_argument("id", type=int, help="Todo 的 id")

    p_rm = sub.add_parser("rm", help="删除 Todo")
    p_rm.add_argument("id", type=int, help="Todo 的 id")

    sub.add_parser("tags", help="列出所有在用的 Tag")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handler = HANDLERS[args.command]
    try:
        return handler(args)
    except storage.StorageError as e:
        print(f"错误：{e}", file=sys.stderr)
        return 1


def _cmd_add(args: argparse.Namespace) -> int:
    todos = storage.load()
    todo = {
        "id": core.next_id(todos),
        "title": args.title,
        "tags": core.parse_tags(args.tags),
        "status": "open",
        "priority": args.priority,
        "created_at": _now(),
        "completed_at": None,
    }
    todos.append(todo)
    storage.save(todos)
    print(f"已添加 Todo {todo['id']}：{todo['title']}")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    todos = storage.load()
    if not args.all:
        todos = [t for t in todos if t["status"] == "open"]
    todos = core.filter_by_tags(todos, args.tag)
    if not todos:
        print("无匹配 Todo" if args.tag or args.all else "清单是空的，先 add 一条 Todo")
        return 0
    for t in todos:
        print(_render(t))
    return 0


def _find_or_error(todos: list[dict], todo_id: int) -> dict | None:
    todo = next((t for t in todos if t["id"] == todo_id), None)
    if todo is None:
        print(f"错误：Todo {todo_id} 不存在", file=sys.stderr)
    return todo


def _cmd_done(args: argparse.Namespace) -> int:
    todos = storage.load()
    todo = _find_or_error(todos, args.id)
    if todo is None:
        return 1
    if todo["status"] == "done":
        print(f"错误：Todo {args.id} 已经是完成状态", file=sys.stderr)
        return 1
    todos[todos.index(todo)] = core.mark_done(todo, now=_now())
    storage.save(todos)
    print(f"已完成 Todo {args.id}：{todo['title']}")
    return 0


def _cmd_undo(args: argparse.Namespace) -> int:
    todos = storage.load()
    todo = _find_or_error(todos, args.id)
    if todo is None:
        return 1
    if todo["status"] == "open":
        print(f"错误：Todo {args.id} 本来就未完成", file=sys.stderr)
        return 1
    todos[todos.index(todo)] = core.mark_open(todo)
    storage.save(todos)
    print(f"已重开 Todo {args.id}：{todo['title']}")
    return 0


def _cmd_rm(args: argparse.Namespace) -> int:
    todos = storage.load()
    todo = _find_or_error(todos, args.id)
    if todo is None:
        return 1
    todos.remove(todo)
    storage.save(todos)
    print(f"已删除 Todo {args.id}：{todo['title']}")
    return 0


def _cmd_tags(args: argparse.Namespace) -> int:
    tags = sorted({tag for todo in storage.load() for tag in todo["tags"]})
    if not tags:
        print("（还没有任何 Tag）")
        return 0
    print(" ".join(tags))
    return 0


HANDLERS = {
    "add": _cmd_add,
    "list": _cmd_list,
    "done": _cmd_done,
    "undo": _cmd_undo,
    "rm": _cmd_rm,
    "tags": _cmd_tags,
}
