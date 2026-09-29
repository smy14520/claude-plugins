"""单文件 Todo CLI：python3 todo.py add <title> | list | done <id> | export <path>"""

import json
import sys
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
    next_id = max((t["id"] for t in todos), default=0) + 1
    todos.append({"id": next_id, "title": title, "done": False})
    save(todos)
    print(f"[{next_id}] {title}")


def list_todos() -> None:
    for t in load():
        if not t["done"]:
            print(f"[{t['id']}] {t['title']}")


def done(todo_id: int) -> None:
    todos = load()
    for t in todos:
        if t["id"] == todo_id:
            t["done"] = True
            save(todos)
            return
    print(f"no such todo: {todo_id}", file=sys.stderr)
    sys.exit(1)


def export(path: str) -> None:
    data = [{"id": t["id"], "title": t["title"], "done": t["done"]} for t in load()]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:] or ["list"]
    if cmd == "add":
        add(" ".join(rest))
    elif cmd == "done":
        done(int(rest[0]))
    elif cmd == "export":
        export(rest[0])
    else:
        list_todos()
