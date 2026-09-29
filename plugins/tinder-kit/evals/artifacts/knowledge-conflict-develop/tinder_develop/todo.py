"""单文件 Todo CLI：python3 todo.py add <title> | list | done <id> | export <path>

id 为 uuid；显示与 done 均可用其前 8 位短前缀。存量记录保留旧整数 id，done 同样接受。
"""

import csv
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB = Path(".todos.json")

# 存量记录没有 updated_at，修改时间未知：回填 epoch，视作从未修改，
# 避免 todo-sync 换用 updated_at 水位线后把全部老任务重推一遍。
EPOCH = "1970-01-01T00:00:00+00:00"


def load() -> list[dict]:
    if not DB.exists():
        return []
    todos = json.loads(DB.read_text(encoding="utf-8"))
    for t in todos:
        t.setdefault("updated_at", EPOCH)  # 只在内存回填，不改写文件（todo-sync 直接读它）
    return todos


def save(todos: list[dict]) -> None:
    DB.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding="utf-8")


def _short(todo_id) -> str:
    # uuid 取前 8 位短前缀；旧整数 id 原样显示
    return str(todo_id) if isinstance(todo_id, int) else str(todo_id)[:8]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def add(title: str) -> None:
    todos = load()
    new = {"id": str(uuid.uuid4()), "title": title, "done": False, "updated_at": _now()}
    todos.append(new)
    save(todos)
    print(f"[{_short(new['id'])}] {title}")


def list_todos() -> None:
    for t in load():
        if not t["done"]:
            print(f"[{_short(t['id'])}] {t['title']}")


def _resolve(todos: list[dict], key: str):
    # 先精确匹配（完整 uuid 或旧整数），再对 uuid 做唯一前缀匹配；旧整数 id 本就短，只接受完整输入
    for t in todos:
        if str(t["id"]) == key:
            return t
    matches = [t for t in todos if isinstance(t["id"], str) and t["id"].startswith(key)]
    if len(matches) > 1:
        print(f"ambiguous id: {key}", file=sys.stderr)
        for t in matches:
            print(f"  {t['id']}  {t['title']}", file=sys.stderr)
        sys.exit(1)
    return matches[0] if matches else None


def done(todo_id: str) -> None:
    todos = load()
    t = _resolve(todos, todo_id)
    if t is None:
        print(f"no such todo: {todo_id}", file=sys.stderr)
        sys.exit(1)
    if not t["done"]:
        t["done"] = True
        t["updated_at"] = _now()
        save(todos)


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
