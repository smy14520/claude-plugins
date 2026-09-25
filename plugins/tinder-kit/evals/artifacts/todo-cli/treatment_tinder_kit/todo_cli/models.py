"""领域模型与领域查询 —— 术语严格对齐 .forge/CONTEXT.md（Task / Status / Tag / Priority / ID）。

本模块是核心接缝（seam）：纯领域逻辑、零 IO，测试在此钉死行为；
Tag 归一化与排序规则的唯一定义点，任何调用方（storage / CLI）都绕不过。
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Iterable


class Priority(str, enum.Enum):
    """Task 的紧急度档位，固定三档。"""

    high = "high"
    med = "med"
    low = "low"


PRIORITY_RANK: dict[Priority, int] = {
    Priority.high: 0,
    Priority.med: 1,
    Priority.low: 2,
}
"""list 排序用的档位秩：high → med → low。"""


class Status(str, enum.Enum):
    """Task 的完成状态，仅两态；"放弃"用 delete 表达，不存在第三状态。"""

    pending = "pending"
    done = "done"


def normalize_tag(raw: str) -> str:
    """Tag 规范化：内部空白折叠为单个连字符，再转小写。"""
    return "-".join(raw.split()).lower()


@dataclass
class Task:
    """一条待办事项：一个标题、零个或多个 Tag、一个 Priority、一个 Status。"""

    id: int
    title: str
    tags: list[str] = field(default_factory=list)
    priority: Priority = Priority.med
    status: Status = Status.pending

    @property
    def sort_key(self) -> tuple[int, int]:
        """list 排序键：Priority(high→med→low) 再 ID 升序。"""
        return (PRIORITY_RANK[self.priority], self.id)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "tags": list(self.tags),
            "priority": self.priority.value,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, raw: dict) -> "Task":
        return cls(
            id=int(raw["id"]),
            title=str(raw["title"]),
            tags=[str(t) for t in raw.get("tags", [])],
            priority=Priority(raw.get("priority", Priority.med.value)),
            status=Status(raw.get("status", Status.pending.value)),
        )


def select_tasks(
    tasks: Iterable[Task], wanted_tags: Iterable[str], include_done: bool
) -> list[Task]:
    """领域查询：默认仅 pending；多 Tag 为 AND；按 Task.sort_key 排序。"""
    wanted = [normalize_tag(t) for t in wanted_tags]
    visible = [
        t
        for t in tasks
        if (include_done or t.status is Status.pending)
        and all(w in t.tags for w in wanted)
    ]
    return sorted(visible, key=lambda t: t.sort_key)
