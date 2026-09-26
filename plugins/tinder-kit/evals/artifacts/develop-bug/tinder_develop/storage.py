"""任务存储管理器，支持线程安全的文件读写。"""

from __future__ import annotations

import json
import threading
from pathlib import Path


class TaskStore:
    def __init__(self, filepath: str = ".tasks.json"):
        self.filepath = Path(filepath)
        self.lock = threading.Lock()
        if not self.filepath.exists():
            self._write([])

    def _read(self) -> list[dict]:
        return json.loads(self.filepath.read_text(encoding="utf-8"))

    def _write(self, data: list[dict]) -> None:
        self.filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_task(self, task_id: int) -> dict | None:
        with self.lock:
            tasks = self._read()
            for t in tasks:
                if t["id"] == task_id:
                    return t
            return None

    def update_status(self, task_id: int, new_status: str) -> dict:
        """更新指定任务状态。"""
        with self.lock:
            tasks = self._read()
            target = None
            for t in tasks:
                if t["id"] == task_id:
                    target = t
                    break
            if not target:
                raise KeyError(f"Task #{task_id} not found")

            if new_status not in ["PENDING", "WAITING", "RUNNING", "DONE"]:
                raise ValueError(f"Invalid status: {new_status}")

            target["status"] = new_status
            self._write(tasks)
            return target
