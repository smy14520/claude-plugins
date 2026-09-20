#!/usr/bin/env python3
"""todo —— 本地 CLI Todo 工具（纯 stdlib：argparse + json）。

调用形态：``python3 todo.py <subcommand>``；四命令 add/list/done/delete。
存储路径 = ``$TODO_FILE`` 环境变量，否则用户主目录 ``~/.todos.json``。
``main(argv) -> int`` 返回进程退出码，供 pytest 进程内直接调用。
"""

from __future__ import annotations

import argparse
import os
import sys

import domain
import storage

DEFAULT_FILENAME = ".todos.json"


def storage_path() -> str:
    override = os.environ.get("TODO_FILE")
    if override:
        return override
    return os.path.join(os.path.expanduser("~"), DEFAULT_FILENAME)


def format_todo(todo: dict) -> str:
    """list 行格式：[id] [优先级] [状态] 文本 #标签…（无标签则省略尾段）。"""
    mark = "[x]" if todo.get("done") else "[ ]"
    tag_part = "".join(f" #{tag}" for tag in todo.get("tags", []))
    return f"[{todo['id']}] [{todo['priority']}] {mark} {todo['text']}{tag_part}"


def _not_found(id: int) -> int:
    print(f"错误: 找不到 id={id} 的 todo", file=sys.stderr)
    return 1


def cmd_add(args: argparse.Namespace) -> int:
    text, tags = domain.parse_text(args.text)
    path = storage_path()
    todos = storage.load(path)
    todo = domain.new_todo(todos, text, tags, args.priority)
    todos.append(todo)
    storage.save(path, todos)
    print(f"已添加 {format_todo(todo)}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    todos = storage.load(storage_path())
    picked = domain.filter_todos(todos, tags=args.tag or [], show_done=args.all)
    if not picked:
        print("（无匹配的 todo）")
        return 0
    for todo in picked:
        print(format_todo(todo))
    return 0


def cmd_done(args: argparse.Namespace) -> int:
    path = storage_path()
    todos = storage.load(path)
    for todo in todos:
        if todo.get("id") == args.id:
            if not todo.get("done"):  # 幂等：已完成则不再重复写盘
                todo["done"] = True
                storage.save(path, todos)
            print(f"已完成 {format_todo(todo)}")
            return 0
    return _not_found(args.id)


def cmd_delete(args: argparse.Namespace) -> int:
    path = storage_path()
    todos = storage.load(path)
    for index, todo in enumerate(todos):
        if todo.get("id") == args.id:
            todos.pop(index)
            storage.save(path, todos)
            print(f"已删除 {format_todo(todo)}")
            return 0
    return _not_found(args.id)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo", description="本地 Todo CLI（纯 stdlib，存储于单一 JSON 文件）"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="新增 todo，正文中 +tag 收为标签")
    p_add.add_argument("text", help='todo 正文，如 "买牛奶 +shopping +urgent"')
    p_add.add_argument(
        "--priority",
        choices=domain.PRIORITIES,
        default="med",
        metavar="high|med|low",
        help="优先级（缺省 med）",
    )
    p_add.set_defaults(handler=cmd_add)

    p_list = sub.add_parser("list", help="列出 todo（默认隐藏已完成）")
    p_list.add_argument(
        "--tag",
        action="append",
        default=None,
        metavar="TAG",
        help="按标签过滤，可重复出现，多标签为交集",
    )
    p_list.add_argument("--all", action="store_true", help="包含已完成项")
    p_list.set_defaults(handler=cmd_list)

    p_done = sub.add_parser("done", help="标记完成（幂等）")
    p_done.add_argument("id", type=int, help="todo id")
    p_done.set_defaults(handler=cmd_done)

    p_delete = sub.add_parser("delete", help="删除 todo")
    p_delete.add_argument("id", type=int, help="todo id")
    p_delete.set_defaults(handler=cmd_delete)

    return parser


def main(argv: list[str] | None = None) -> int:
    """进程内可调用的入口：解析 argv、分发子命令、返回退出码。"""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse 错误（非法 priority/未知命令等）
        code = exc.code
        if code is None:
            return 0
        return code if isinstance(code, int) else 2
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
