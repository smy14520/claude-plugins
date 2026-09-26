#!/usr/bin/env python3
"""极简 Todo CLI 基础版本，存储在本地单一 .todos.json 中。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import NoReturn

DEFAULT_FILE = Path(".todos.json")

EXIT_USAGE_ERROR = 42


class TodoArgumentParser(argparse.ArgumentParser):
    """参数校验失败一律 stderr 友好提示并 exit 42（ADR 0001），不保留默认的 2。"""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE_ERROR, f"{self.prog}: error: {message}\n")


def parse_due(text: str) -> date:
    """解析严格 YYYY-MM-DD 格式的截止日期，其余写法一律抛 ValueError。"""
    parsed = datetime.strptime(text, "%Y-%m-%d").date()
    if parsed.isoformat() != text:
        raise ValueError(f"not strict YYYY-MM-DD: {text!r}")
    return parsed


def load_todos(path: Path = DEFAULT_FILE) -> list[dict]:
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [_normalize_todo(t) for t in data.get("todos", [])]
    except Exception:
        return []


def _normalize_todo(item: dict) -> dict:
    """加载期归一化：due 缺失或损坏一律按 null 兼容，绝不让 list 崩溃。"""
    if not isinstance(item, dict):
        return item
    due_text = item.get("due")
    if due_text is not None:
        try:
            parse_due(due_text)
        except (TypeError, ValueError):
            item["due"] = None
    return item


def save_todos(todos: list[dict], path: Path = DEFAULT_FILE) -> None:
    data = {"todos": todos}
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def add_todo(title: str, path: Path = DEFAULT_FILE, due: date | None = None) -> dict:
    todos = load_todos(path)
    new_id = max([t["id"] for t in todos], default=0) + 1
    item = {"id": new_id, "title": title, "done": False}
    if due is not None:
        item["due"] = due.isoformat()
    todos.append(item)
    save_todos(todos, path)
    return item


def list_todos(path: Path = DEFAULT_FILE) -> list[dict]:
    todos = load_todos(path)
    return [t for t in todos if not t.get("done", False)]


def format_todo(item: dict, today: date) -> str:
    """渲染单行列表输出：DEADLINE 前缀标注截止日期，逾期追加 [OVERDUE]。"""
    line = f"[{item['id']}] {item['title']}"
    due_text = item.get("due")
    if due_text:
        line += f" (DEADLINE: {due_text})"
        if today > parse_due(due_text):
            line += " [OVERDUE]"
    return line


def done_todo(todo_id: int, path: Path = DEFAULT_FILE) -> bool:
    todos = load_todos(path)
    found = False
    for t in todos:
        if t["id"] == todo_id:
            t["done"] = True
            found = True
            break
    if found:
        save_todos(todos, path)
    return found


def main(argv: list[str] | None = None) -> int:
    parser = TodoArgumentParser(prog="todo", description="Simple CLI Todo")
    sub = parser.add_subparsers(dest="cmd")

    add_parser = sub.add_parser("add", help="Add a todo")
    add_parser.add_argument("title", help="Todo title")
    add_parser.add_argument("--due", help="Due date in YYYY-MM-DD format")

    sub.add_parser("list", help="List open todos")

    done_parser = sub.add_parser("done", help="Complete a todo")
    done_parser.add_argument("id", type=int, help="Todo ID")

    args = parser.parse_args(argv)
    if args.cmd == "add":
        due = None
        if args.due is not None:
            try:
                due = parse_due(args.due)
            except ValueError:
                print(
                    f"Error: Invalid due date '{args.due}' (expected YYYY-MM-DD)",
                    file=sys.stderr,
                )
                return EXIT_USAGE_ERROR
        item = add_todo(args.title, due=due)
        print(f"Added #{item['id']}: {item['title']}")
        return 0
    elif args.cmd == "list":
        items = list_todos()
        today = date.today()
        for it in items:
            print(format_todo(it, today))
        return 0
    elif args.cmd == "done":
        if done_todo(args.id):
            print(f"Done #{args.id}")
            return 0
        else:
            print(f"Error: Todo #{args.id} not found", file=sys.stderr)
            return 1
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
