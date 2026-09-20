"""存储层（Seam 1）：单一 JSON 文件的读与原子写。

深模块要点：接口只有 load/save 两个函数，内部隐藏
「同目录临时文件 + fsync + 原子 rename」的防半写策略与 UTF-8 编码细节。
调用方（CLI / 测试）完全不感知临时文件的存在。
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def load(path) -> list[dict]:
    """读取 todo 列表；文件不存在时返回空列表。"""
    file = Path(path)
    if not file.exists():
        return []
    with file.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save(path, todos: list[dict]) -> None:
    """把 todos 落盘为 UTF-8 JSON 数组。

    采用「临时文件 + 原子 rename」：先写入目标文件所在目录的临时文件，
    冲刷并 fsync 后再 os.replace，保证任何时刻磁盘上不会出现半写状态。
    """
    target = Path(os.path.abspath(os.fspath(path)))
    fd, tmp_name = tempfile.mkstemp(
        prefix=target.name + ".", suffix=".tmp", dir=str(target.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(todos, fh, ensure_ascii=False, indent=2)
            fh.write("\
")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, target)  # 同目录内 rename，原子生效
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
