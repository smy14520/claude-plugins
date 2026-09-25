"""请求日志（Request Log）：每个收到的请求向 sink 输出一行人类可读记录。

格式（spec §5）：``[YYYY-MM-DD HH:MM:SS] <METHOD> <target> -> <status> (<N.N>ms)``，
404 追加 ``(no mock)``、405 追加 ``(method not allowed)`` 标记。
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import IO


def format_log_line(
    now: datetime,
    method: str,
    target: str,
    status: int,
    elapsed_ms: float,
    note: str | None = None,
) -> str:
    """渲染一行请求日志；时间戳由调用方给定（本地时间）。"""
    head = f"[{now:%Y-%m-%d %H:%M:%S}] {method} {target} -> {status}"
    if note is None:
        return f"{head} ({elapsed_ms:.1f}ms)"
    return f"{head} ({note}) ({elapsed_ms:.1f}ms)"


class RequestLog:
    """请求日志的 sink 抽象：默认写 stdout，测试注入 ``io.StringIO``。"""

    def __init__(self, sink: IO[str] | None = None) -> None:
        self.sink = sink if sink is not None else sys.stdout

    def log(
        self,
        method: str,
        target: str,
        status: int,
        elapsed_ms: float,
        note: str | None = None,
    ) -> None:
        """记录一次请求；时间戳取本地时间。"""
        print(format_log_line(datetime.now(), method, target, status, elapsed_ms, note), file=self.sink)
