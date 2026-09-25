"""单一 .todos.json 的读写（ADR-0001）。

- 路径跟随当前工作目录（Round 2 Q9 拍板）；
- 单进程场景：直接整体覆写，无锁、无原子替换；
- 结构：{"version": 1, "next_id": <int>, "tasks": [...]}；
- 领域规则（Tag 归一化、ID 分配）在写入路径强制执行，规则定义在 models.py。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .models import Priority, Task, normalize_tag

DATA_FILE = ".todos.json"
SCHEMA_VERSION = 1


class CorruptStoreError(RuntimeError):
    """数据文件存在但不是合法 JSON。"""


class Store:
    """cwd 下 .todos.json 的内存镜像。"""

    def __init__(self, tasks: list[Task], next_id: int) -> None:
        self.tasks = tasks
        self.next_id = next_id

    @classmethod
    def path(cls) -> Path:
        return Path.cwd() / DATA_FILE

    @classmethod
    def load(cls) -> "Store":
        if not cls.path().exists():
            return cls(tasks=[], next_id=1)
        try:
            raw = json.loads(cls.path().read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CorruptStoreError(f"{DATA_FILE} 不是合法 JSON：{exc}") from exc
        return cls(
            tasks=[Task.from_dict(raw_task) for raw_task in raw.get("tasks", [])],
            next_id=int(raw.get("next_id", 1)),
        )

    def save(self) -> None:
        payload = {
            "version": SCHEMA_VERSION,
            "next_id": self.next_id,
            "tasks": [t.to_dict() for t in self.tasks],
        }
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        self.path().write_text(text, encoding="utf-8")

    def add(self, title: str, tags: list[str], priority: Priority) -> Task:
        """创建 Task：分配自增 ID（永不复用）；Tag 经 normalize_tag 归一化并去重保序。"""
        seen: set[str] = set()
        unique = [
            t
            for t in (normalize_tag(raw) for raw in tags)
            if not (t in seen or seen.add(t))
        ]
        task = Task(id=self.next_id, title=title, tags=unique, priority=priority)
        self.next_id += 1
        self.tasks.append(task)
        return task

    def find(self, id: int) -> Optional[Task]:
        return next((t for t in self.tasks if t.id == id), None)

    def remove(self, id: int) -> bool:
        task = self.find(id)
        if task is None:
            return False
        self.tasks.remove(task)
        return True
