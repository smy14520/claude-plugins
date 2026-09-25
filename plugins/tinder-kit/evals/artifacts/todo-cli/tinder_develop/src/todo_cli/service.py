"""任务业务流转。

每个操作都是 读盘 → 变更 → 原子落盘 的完整事务：
CLI 是进程级语义（一命令一进程），不维护跨调用内存态。
"""

from dataclasses import replace

from .models import Task
from .storage import TodoStore


class TaskNotFound(LookupError):
    """引用了不存在的任务编号。"""


def _dedupe(tags: list[str]) -> list[str]:
    """去重且保留首次出现顺序。"""
    seen: set[str] = set()
    unique: list[str] = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique.append(tag)
    return unique


class TodoService:
    def __init__(self, store: TodoStore):
        self.store = store

    def add(self, text: str, tags: list[str]) -> Task:
        tasks, next_id = self.store.load()
        task = Task(id=next_id, text=text, tags=_dedupe(tags))
        self.store.save([*tasks, task], next_id + 1)
        return task

    def complete(self, task_id: int) -> Task:
        tasks, next_id = self.store.load()
        index = self._locate(tasks, task_id)
        tasks[index] = replace(tasks[index], done=True)
        self.store.save(tasks, next_id)
        return tasks[index]

    def remove(self, task_id: int) -> Task:
        tasks, next_id = self.store.load()
        removed = tasks.pop(self._locate(tasks, task_id))
        self.store.save(tasks, next_id)
        return removed

    @staticmethod
    def _locate(tasks: list[Task], task_id: int) -> int:
        """按编号定位任务下标；未命中即抛 TaskNotFound。"""
        for index, task in enumerate(tasks):
            if task.id == task_id:
                return index
        raise TaskNotFound(f"task {task_id} not found")

    def list_tasks(self, tags: list[str] | None = None, include_done: bool = False) -> list[Task]:
        """默认仅未完成(Open)；多标签为 AND 语义（须同时含全部指定标签）。"""
        wanted = set(tags or [])
        tasks, _ = self.store.load()
        return [
            t
            for t in tasks
            if (include_done or not t.done) and wanted <= set(t.tags)
        ]

    def tag_counts(self) -> dict[str, int]:
        """全量任务口径（含已完成）的标签计数。"""
        tasks, _ = self.store.load()
        counts: dict[str, int] = {}
        for task in tasks:
            for tag in task.tags:
                counts[tag] = counts.get(tag, 0) + 1
        return counts

    def _mutate(self, task_id: int, fn) -> Task:
        tasks, next_id = self.store.load()
        for i, task in enumerate(tasks):
            if task.id == task_id:
                tasks[i] = fn(task)
                self.store.save(tasks, next_id)
                return tasks[i]
        raise TaskNotFound(f"task {task_id} not found")
