"""单文件 Todo CLI：python3 todo.py add <title> | list | done <id> | export <path>"""

import csv
import json
import sys
import uuid
from pathlib import Path

DB = Path(".todos.json")


def load() -> list[dict]:
    if not DB.exists():
        return []
    return json.loads(DB.read_text(encoding="utf-8"))


def save(todos: list[dict]) -> None:
    DB.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding="utf-8")


def add(title: str) -> None:
    todos = load()
    todo_id = str(uuid.uuid4())
    todos.append({"id": todo_id, "title": title, "done": False})
    save(todos)
    print(f"[{todo_id}] {title}")


def list_todos() -> None:
    for t in load():
        if not t["done"]:
            print(f"[{t['id']}] {t['title']}")


def done(todo_id: str) -> None:
    todos = load()
    for t in todos:
        if str(t["id"]) == str(todo_id):
            t["done"] = True
            save(todos)
            return
    print(f"no such todo: {todo_id}", file=sys.stderr)
    sys.exit(1)


def export(path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "done"])
        for t in load():
            writer.writerow([t["id"], t["title"], t["done"]])


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:] or ["list"]
    if cmd == "add":
        add(" ".join(rest))
    elif cmd == "done":
        done(rest[0])
    elif cmd == "export":
        export(rest[0])
    else:
        list_todos()
