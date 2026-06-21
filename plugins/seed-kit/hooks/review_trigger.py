#!/usr/bin/env python3
"""review_trigger — slice 完成后自动触发 review。

触发条件：seed done 成功后，检查是否需要执行 review。
行为：返回 additionalContext 提醒 Claude 执行 /review。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

DONE_CMD_RE = re.compile(r"seed\s+done\s+(\S+)\s+--slice\s+(S-\d{3})")


def _tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    tool_input = payload.get("tool_input")
    return tool_input if isinstance(tool_input, dict) else {}


def _get_task_dir(payload: dict[str, Any]) -> Path | None:
    """从 payload 中提取项目根目录。"""
    cwd = payload.get("cwd")
    if cwd:
        return Path(cwd)
    return None


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    tool_name = str(payload.get("tool_name") or "")
    tool_input = _tool_input(payload)

    # 只在 Bash 工具执行后触发
    if tool_name != "Bash":
        return {}

    command = str(tool_input.get("command") or "")

    # 检查是否是 seed done 命令
    match = DONE_CMD_RE.search(command)
    if not match:
        return {}

    task = match.group(1)
    slice_id = match.group(2)

    # 获取项目根目录
    project_root = _get_task_dir(payload)
    if not project_root:
        return {}

    # 检查 review.md 是否存在最近的 review 记录
    review_path = project_root / ".arbor" / "tasks" / task / "review.md"
    if review_path.exists():
        content = review_path.read_text(encoding="utf-8")
        # 简单检查：是否有针对当前 slice 的 review
        # 实际可以更复杂，比如检查日期、检查 verdict 等
        if f"## Review" in content:
            # 已有 review 记录，不重复触发
            return {}

    # 返回 additionalContext 提醒 Claude 执行 review
    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                f"slice {slice_id} 已完成（seed done 成功）。"
                f"在执行下一个 slice 或 commit 之前，建议执行 /review 审计当前 slice 的实现。"
                f"review 会检查：偷懒签名、验证降级、交付面冒充、覆盖缺口等。"
                f"如果 review 发现问题，需要修复后重新跑 assert/judge，再次 seed done。"
            ),
        }
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = evaluate(payload)
    except Exception as exc:  # pragma: no cover - hook fails open softly
        result = {}

    # 输出 JSON 结果（Claude Code hook 协议）
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
