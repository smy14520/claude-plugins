#!/usr/bin/env python3
"""极简 Todo CLI 基础版本，存储在本地单一 .todos.json 中。"""

from __future__ import annotations

import argparse
import json
import sys
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


def add_todo(title: str, path: Path = DEFAULT_FILE) -> dict:
    todos = load_todos(path)
    new_id = max([t["id"] for t in todos], default=0) + 1
    item = {"id": new_id, "title": title, "done": False}
    todos.append(item)
    save_todos(todos, path)
    return item


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

    sub.add_parser("list", help="List open todos")

    done_parser = sub.add_parser("done", help="Complete a todo")
    done_parser.add_argument("id", type=int, help="Todo ID")

    args = parser.parse_args(argv)
    if args.cmd == "add":
        item = add_todo(args.title)
        print(f"Added #{item['id']}: {item['title']}")
        return 0
    elif args.cmd == "list":
        items = list_todos()
        for it in items:
            print(f"[{it['id']}] {it['title']}")
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
