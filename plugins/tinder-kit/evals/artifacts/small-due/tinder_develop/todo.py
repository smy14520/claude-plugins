#!/usr/bin/env python3
"""极简 Todo CLI 基础版本，存储在本地单一 .todos.json 中。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

DEFAULT_FILE = Path(".todos.json")


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
    """解析 YYYY-MM-DD 截止日期，非法输入（含非字符串）抛 ValueError。"""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid due date {value!r}, expected YYYY-MM-DD") from exc


def add_todo(title: str, path: Path = DEFAULT_FILE, *, due: str | None = None) -> dict:
    todos = load_todos(path)
    new_id = max([t["id"] for t in todos], default=0) + 1
    item = {"id": new_id, "title": title, "done": False}
    if due is not None:
        item["due"] = parse_due(due).isoformat()  # 校验失败在写盘前抛出，脏数据不落盘
    todos.append(item)
    save_todos(todos, path)
    return item


def is_overdue(todo: dict, today: date) -> bool:
    """未完成任务且当前日期已超过截止日期（截止当天不算逾期）。脏数据视为未逾期。"""
    if todo.get("done", False):
        return False
    due = todo.get("due")
    if not due:
        return False
    try:
        return today > parse_due(due)
    except ValueError:
        return False


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
    add_parser.add_argument("--due", default=None, help="Due date as YYYY-MM-DD (optional)")

    sub.add_parser("list", help="List open todos")

    done_parser = sub.add_parser("done", help="Complete a todo")
    done_parser.add_argument("id", type=int, help="Todo ID")

    args = parser.parse_args(argv)
    if args.cmd == "add":
        try:
            item = add_todo(args.title, due=args.due)
        except ValueError:
            print(f"Error: invalid --due {args.due!r}, expected YYYY-MM-DD", file=sys.stderr)
            return 1
        print(f"Added #{item['id']}: {item['title']}")
        return 0
    elif args.cmd == "list":
        items = list_todos()
        today = date.today()
        for it in items:
            line = f"[{it['id']}] {it['title']}"
            if is_overdue(it, today):
                line += " [OVERDUE]"
            print(line)
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
