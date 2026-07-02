#!/usr/bin/env python3
"""review_on_complete — Stop hook：task 完成（所有 slice [x]）时要求整体 review-loop 跑过。

声明/执行分离：impl SKILL 声明"所有 slice done 后跑整体 review-loop"（软），
本 hook 在 agent turn 结束时强制：所有 slice [x] 且无 task 级 review-loop.json
（由 `seed review-mark <task>` 落）→ exit 2 + 反馈，逼 agent 先跑整体
`/seed-kit:review-loop` 落 marker 再收尾（self-correcting）。

不拦：task 未完成（有 slice [ ]）、或 review-loop.json 已落（整体 review 跑过）。
fail open：解析异常放行（不阻断 agent）。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # fail open
    cwd = payload.get("cwd")
    if not cwd:
        sys.exit(0)
    tasks_root = Path(cwd).resolve() / ".arbor" / "tasks"
    if not tasks_root.is_dir():
        sys.exit(0)
    for task_dir in tasks_root.iterdir():
        if not task_dir.is_dir():
            continue
        prd = task_dir / "prd.md"
        if not prd.is_file():
            continue
        text = prd.read_text(encoding="utf-8")
        rows = re.findall(r"^### \[([ x])\] S-\d{3}", text, re.MULTILINE)
        if not rows or not all(r == "x" for r in rows):
            continue  # task 未完成，allow
        marker = task_dir / "review-loop.json"
        if marker.is_file():
            continue  # marker 有效，allow
        # task 完成 + 整体 review 没跑 → block
        print(
            f"⚠ task `{task_dir.name}` 所有 slice 已 done，但整体 review-loop 没跑。"
            f"先跑 `/seed-kit:review-loop`（不带 slice，审整个 task）到收敛，"
            f"再 `seed review-mark {task_dir.name} --verdict <terminal_reason>` 落 marker，再收尾。",
            file=sys.stderr,
        )
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
