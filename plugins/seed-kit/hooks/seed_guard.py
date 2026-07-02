#!/usr/bin/env python3
"""seed_guard — seed-kit 的窄底线 hook。

只守两条线，不做任何语义判断：
1. prd.md 的 slice checkbox 只能由 `seed done` 在硬事实通过后勾选。
2. 拦截破坏性命令。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

PRD_RE = re.compile(r"(^|/)\.arbor/tasks/[^/]+/prd\.md$")
DESTRUCTIVE_RE = re.compile(r"\b(git\s+reset\s+--hard|git\s+clean\s+-|git\s+push\s+--force|rm\s+-rf)\b")
CHECKED_HEADING_RE = re.compile(r"^### \[x\] ", re.MULTILINE)


def _tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    tool_input = payload.get("tool_input")
    return tool_input if isinstance(tool_input, dict) else {}


def _checked_count(text: str) -> int:
    return len(CHECKED_HEADING_RE.findall(text))


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    tool_name = str(payload.get("tool_name") or "")
    tool_input = _tool_input(payload)

    if tool_name in {"Edit", "Write", "NotebookEdit"}:
        path = str(tool_input.get("file_path") or tool_input.get("path") or "")
        if PRD_RE.search(path):
            if tool_name == "Edit":
                old = str(tool_input.get("old_string") or "")
                new = str(tool_input.get("new_string") or "")
                if _checked_count(new) > _checked_count(old):
                    return {
                        "decision": "block",
                        "reason": "slice checkbox 只能由 `seed done` 勾选；不要直接编辑 `### [ ]` → `### [x]`。",
                    }
            elif tool_name == "Write":
                content = str(tool_input.get("content") or "")
                try:
                    existing = Path(path).read_text(encoding="utf-8")
                except OSError:
                    existing = ""
                if _checked_count(content) > _checked_count(existing):
                    return {
                        "decision": "block",
                        "reason": "slice checkbox 只能由 `seed done` 勾选；不要整文件覆盖勾选。",
                    }

    if tool_name == "Bash":
        command = str(tool_input.get("command") or "")
        if DESTRUCTIVE_RE.search(command):
            return {
                "decision": "block",
                "reason": "检测到破坏性命令；换用范围更窄、更安全的方式。",
            }
        # 拦截通过 Bash 工具（sed/awk/perl/python -c 等）直接修改 prd.md checkbox
        if re.search(r"(sed|awk|perl)\s+.*\.arbor/tasks/.*prd\.md", command):
            return {
                "decision": "block",
                "reason": "不要用 shell 命令直接修改 prd.md；checkbox 只能由 `seed done` 勾选。",
            }
        if re.search(r"python\d?\s+-c\s+.*###\s*\[", command):
            return {
                "decision": "block",
                "reason": "不要用脚本直接修改 prd.md；checkbox 只能由 `seed done` 勾选。",
            }

    return {"decision": "allow"}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = evaluate(payload)
    except Exception:  # pragma: no cover - hook fails open softly
        result = {"decision": "allow", "reason": "seed_guard 无法解析 payload"}
    if result.get("decision") == "block":
        print(result.get("reason", "被 seed_guard 拦截"), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
