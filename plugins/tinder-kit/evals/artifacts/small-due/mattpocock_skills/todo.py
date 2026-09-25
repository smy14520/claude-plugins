#!/usr/bin/env python3
"""极简 Todo CLI，支持可选截止日期（--due YYYY-MM-DD），存储在本地单一 .todos.json 中。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

DEFAULT_FILE = Path(".todos.json")

DUE_FORMAT = "%Y-%m-%d"


def load_todos(path: Path = DEFAULT_FILE) -> list[dict]:
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("todos", [])
    except Exception:
        return []


def save_todos(todos: list[dict], path: Path = DEFAULT_FILE) -> None:
    data = {"todos": todos}
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_due(value: str) -> date:
    """严格解析命令行输入的截止日期，非法输入给出友好报错。"""
    try:
        return datetime.strptime(value, DUE_FORMAT).date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"无效的截止日期 {value!r}：需要 YYYY-MM-DD 格式，例如 2026-09-30"
        ) from exc


def get_due(todo: dict) -> date | None:
    """读取存储的截止日期；缺失或畸形一律视为没有截止日期。"""
    raw = todo.get("due")
    if not raw:
        return None
    try:
        return datetime.strptime(raw, DUE_FORMAT).date()
    except ValueError:
        return None


def add_todo(title: str, path: Path = DEFAULT_FILE, due: date | None = None) -> dict:
    todos = load_todos(path)
    new_id = max([t["id"] for t in todos], default=0) + 1
    item = {"id": new_id, "title": title, "done": False}
    if due is not None:
        item["due"] = due.isoformat()
    todos.append(item)
    save_todos(todos, path)
    return item


def is_overdue(todo: dict, today: date | None = None) -> bool:
    """逾期：截止日期早于今天的本地日期，截止当天不算逾期。"""
    due = get_due(todo)
    if due is None:
        return False
    if today is None:
        today = date.today()
    return today > due


def format_todo(todo: dict, today: date | None = None) -> str:
    line = f"[{todo['id']}] {todo['title']}"
    due = get_due(todo)
    if due is not None:
        line += f" (due: {due.isoformat()})"
        if is_overdue(todo, today):
            line += " [OVERDUE]"
    return line


def list_todos(path: Path = DEFAULT_FILE) -> list[dict]:
    todos = load_todos(path)
    return [t for t in todos if not t.get("done", False)]


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
    parser = argparse.ArgumentParser(prog="todo", description="Simple CLI Todo")
    sub = parser.add_subparsers(dest="cmd")

    add_parser = sub.add_parser("add", help="Add a todo")
    add_parser.add_argument("title", help="Todo title")
    add_parser.add_argument(
        "--due", type=parse_due, default=None, help="截止日期，YYYY-MM-DD，可省略"
    )

    sub.add_parser("list", help="List open todos")

    done_parser = sub.add_parser("done", help="Complete a todo")
    done_parser.add_argument("id", type=int, help="Todo ID")

    args = parser.parse_args(argv)
    if args.cmd == "add":
        item = add_todo(args.title, due=args.due)
        print(f"Added #{item['id']}: {item['title']}")
        return 0
    elif args.cmd == "list":
        items = list_todos()
        for it in items:
            print(format_todo(it))
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
