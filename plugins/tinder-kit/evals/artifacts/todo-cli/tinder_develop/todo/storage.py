"""持久化层：唯一允许接触存储文件的模块（见 .forge/wiki/decision/0001）。

单一 JSON 文件，整体读、整体写；写入经 tmp 文件 + 原子替换。
"""

import json
import os
from pathlib import Path

DEFAULT_FILENAME = ".todos.json"


class StorageError(Exception):
    """存储文件缺失、损坏或格式不符。"""


def storage_path() -> Path:
    """TODO_FILE 环境变量仅覆盖路径，不产生第二个数据文件。"""
    return Path(os.environ.get("TODO_FILE", DEFAULT_FILENAME))


def load() -> list[dict]:
    """读取全部 Todo；文件不存在视为空清单（首次使用）。"""
    path = storage_path()
    if not path.exists():
        return []
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise StorageError(f"存储文件 {path} 不是有效的 JSON：{e}") from e
    if not isinstance(data, list):
        raise StorageError(f"存储文件 {path} 格式错误：顶层应为 JSON 数组")
    return data


def save(todos: list[dict]) -> None:
    """整体写出全部 Todo；tmp + os.replace 保证不留半写状态。"""
    path = storage_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)
