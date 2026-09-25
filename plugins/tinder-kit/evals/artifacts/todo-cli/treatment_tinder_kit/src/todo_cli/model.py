"""Todo 领域模型（词汇表见 .forge/CONTEXT.md）。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Todo:
    id: int
    text: str
    tags: list[str]
    status: str  # "open" | "done"，二态，无中间态
    created_at: str
    done_at: str | None = None
    priority: str | None = None  # "high" | "med" | "low" | None（变更周期 1）

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "tags": self.tags,
            "status": self.status,
            "created_at": self.created_at,
            "done_at": self.done_at,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Todo":
        return cls(
            id=data["id"],
            text=data["text"],
            tags=data["tags"],
            status=data["status"],
            created_at=data["created_at"],
            done_at=data.get("done_at"),
            priority=data.get("priority"),  # 旧文件缺键 → 无优先级
        )
