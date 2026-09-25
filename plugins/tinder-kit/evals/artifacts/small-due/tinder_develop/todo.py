#!/usr/bin/env python3
"""极简 Todo CLI 基础版本，存储在本地单一 .todos.json 中。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

DEFAULT_FILE = Path(".todos.json")


def parse_due(value: str) -> str:
    try:
        valid = datetime.strptime(value, "%Y-%m-%d").date().isoformat() == value
    except ValueError:
        valid = False
    if not valid:
        raise argparse.ArgumentTypeError(f"invalid --due value {value!r}, expected YYYY-MM-DD")
    return value


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


def add_todo(title: str, path: Path = DEFAULT_FILE, *, due: str | None = None) -> dict:
    todos = load_todos(path)
    new_id = max([t["id"] for t in todos], default=0) + 1
    new_todo = {"id": new_id, "title": title, "done": False}
    if due is not None:
        new_todo["due"] = due
    todos.append(new_todo)
    save_todos(todos, path)
    return new_todo


def list_todos(path: Path = DEFAULT_FILE) -> list[dict]:
    todos = load_todos(path)
    return [t for t in todos if not t.get("done", False)]


def is_overdue(todo: dict, on: date) -> bool:
    due = todo.get("due")
    if due is None:
        return False
    return date.fromisoformat(due) < on


def today() -> date:
    return date.today()


def format_todo(todo: dict, on: date) -> str:
    line = f"[{todo['id']}] {todo['title']}"
    if todo.get("due") is not None:
        line += f" (due: {todo['due']})"
    if is_overdue(todo, on=on):
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
    parser = argparse.ArgumentParser(prog="todo", description="Simple CLI Todo")
    sub = parser.add_subparsers(dest="cmd")

    add_parser = sub.add_parser("add", help="Add a todo")
    add_parser.add_argument("title", help="Todo title")
    add_parser.add_argument("--due", type=parse_due, help="Due date (YYYY-MM-DD)")

    sub.add_parser("list", help="List open todos")

    done_parser = sub.add_parser("done", help="Complete a todo")
    done_parser.add_argument("id", type=int, help="Todo ID")

    args = parser.parse_args(argv)
    if args.cmd == "add":
        item = add_todo(args.title, due=args.due)
        print(f"Added #{item['id']}: {item['title']}")
        return 0
    elif args.cmd == "list":
        on = today()
        for t in list_todos():
            print(format_todo(t, on))
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
