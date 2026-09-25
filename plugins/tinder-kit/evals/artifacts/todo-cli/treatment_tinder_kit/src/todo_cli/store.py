"""Store：全部 Todo 与 ID 计数器的唯一持久化载体（ADR-0001 单一 JSON 文件）。"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator

from .model import Todo


class TodoNotFoundError(LookupError):
    """引用的 ID 在 Store 中不存在。"""


# list 主排序：high > med > low > 无优先级（变更周期 1）
PRIORITY_RANK = {"high": 0, "med": 1, "low": 2}
NO_PRIORITY = 3  # 无优先级排末位


def _now() -> str:
    """本地时区 ISO-8601 时间戳。"""
    return datetime.now().astimezone().isoformat(timespec="seconds")


class Store:
    def __init__(self, next_id: int = 1, todos: Iterable[Todo] = ()):
        self.next_id = next_id
        self._todos: dict[int, Todo] = {t.id: t for t in todos}

    def __iter__(self) -> Iterator[Todo]:
        return iter(self._todos.values())

    @classmethod
    def load(cls, path) -> "Store":
        p = Path(path)
        if not p.exists():
            return cls()  # 文件不存在 → 空 Store（next_id=1）
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls(next_id=data["next_id"], todos=map(Todo.from_dict, data["todos"]))

    def save(self, path) -> None:
        """原子写入：临时文件写同目录，os.replace 原子替换（ADR-0001）。"""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "next_id": self.next_id,
            "todos": [t.to_dict() for t in self],
        }
        fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=p.name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp, p)
        except BaseException:
            os.unlink(tmp)
            raise

    def add(self, text: str, tags: Iterable[str] = (), priority: str | None = None) -> Todo:
        if priority is not None and priority not in PRIORITY_RANK:
            raise ValueError(f"invalid priority {priority!r}: expected one of high/med/low")
        todo = Todo(
            id=self.next_id,
            text=text,
            tags=list(tags),
            status="open",
            created_at=_now(),
            priority=priority,
        )
        self._todos[todo.id] = todo
        self.next_id += 1
        return todo

    def _get(self, id: int) -> Todo:
        try:
            return self._todos[id]
        except KeyError:
            raise TodoNotFoundError(f"no Todo with id {id}") from None

    def done(self, id: int) -> Todo:
        todo = self._get(id)
        todo.status = "done"
        todo.done_at = _now()
        return todo

    def undo(self, id: int) -> Todo:
        todo = self._get(id)
        todo.status = "open"
        todo.done_at = None
        return todo

    def rm(self, id: int) -> None:
        self._get(id)
        del self._todos[id]  # ID 计数器不受影响：编号永不复用（ADR-0003）

    def list_todos(self, tags: Iterable[str] = (), show_all: bool = False) -> list[Todo]:
        """默认只显示 open；多个 Tag 为交集（AND）；主排序 Priority high>med>low>无，次排序 ID 升序。"""
        rows = [t for t in self if show_all or t.status == "open"]
        for tag in tags:
            rows = [t for t in rows if tag in t.tags]
        return sorted(rows, key=lambda t: (PRIORITY_RANK.get(t.priority, NO_PRIORITY), t.id))

    def tag_counts(self) -> dict[str, tuple[int, int]]:
        """每个 Tag 的 (open 数, done 数)，按 Tag 字典序。"""
        counts: dict[str, list[int]] = {}
        for todo in self:
            for tag in todo.tags:
                open_n, done_n = counts.get(tag, [0, 0])
                counts[tag] = [
                    open_n + (todo.status == "open"),
                    done_n + (todo.status == "done"),
                ]
        return {tag: (n[0], n[1]) for tag, n in sorted(counts.items())}
