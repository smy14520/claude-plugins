"""单一 JSON 文件持久化（ADR-0001）。

路径解析顺序：显式 path 参数 > TODO_FILE 环境变量 > ~/.todo/todos.json。
TODO_FILE 同时是测试接缝（注入 tmp_path），生产代码无需感知测试存在。
"""

import json
import os
import tempfile
from pathlib import Path

from .models import Task

DEFAULT_PATH = Path.home() / ".todo" / "todos.json"


class StorageError(RuntimeError):
    """存储文件损坏或不可读。绝不静默重置用户数据。"""


class TodoStore:
    def __init__(self, path: Path | None = None):
        env = os.environ.get("TODO_FILE")
        self.path = Path(path) if path is not None else (Path(env) if env else DEFAULT_PATH)

    def load(self) -> tuple[list[Task], int]:
        """返回 (tasks, next_id)。文件缺失 = 全新起始。"""
        if not self.path.exists():
            return [], 1
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StorageError(f"存储文件损坏，拒绝载入: {self.path} ({exc})") from exc
        if not isinstance(data, dict):
            raise StorageError(f"存储文件结构损坏（顶层应为对象）: {self.path}")
        try:
            tasks = [Task(**raw) for raw in data.get("tasks", [])]
            # 自愈手工编辑造成的 next_id 漂移，守住"ID 永不复用"契约
            next_id = max(int(data.get("next_id", 1)), max((t.id for t in tasks), default=0) + 1)
        except (TypeError, ValueError) as exc:
            raise StorageError(
                f"存储文件结构损坏（任务记录字段缺失/多余，或 next_id 不可解析）: {self.path} ({exc})"
            ) from exc
        return tasks, next_id

    def save(self, tasks: list[Task], next_id: int) -> None:
        """原子写入：同目录临时文件 + os.replace，杜绝半写损坏。"""
        data = {
            "next_id": next_id,
            "tasks": [
                {"id": t.id, "text": t.text, "tags": list(t.tags), "done": t.done}
                for t in tasks
            ],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=self.path.parent, prefix=self.path.name + ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_name, self.path)
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True)
            raise
