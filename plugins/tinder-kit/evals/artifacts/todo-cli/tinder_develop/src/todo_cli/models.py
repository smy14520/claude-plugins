"""核心领域模型（见 .forge/CONTEXT.md 统一语言）。"""

from dataclasses import dataclass, field


@dataclass
class Task:
    """任务：仅含 id、text、tags、done 四个字段。"""

    id: int
    text: str
    tags: list[str] = field(default_factory=list)
    done: bool = False
