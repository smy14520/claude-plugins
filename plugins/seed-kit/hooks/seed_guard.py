#!/usr/bin/env python3
"""seed_guard — seed-kit 的窄底线 hook。

只守三条线，不做任何语义判断：
1. evidence/ 只能由 `seed run-check` 写入。
2. prd.md 的 slice checkbox 只能由 `seed done` 在证据齐备后勾选。
3. 拦截破坏性命令。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

PRD_RE = re.compile(r"(^|/)\.arbor/tasks/[^/]+/prd\.md$")
EVIDENCE_PATH_RE = re.compile(r"(^|/)\.arbor/tasks/[^/]+/evidence/")
EVIDENCE_REDIRECT_RE = re.compile(r"\.arbor/tasks/[^\s]*?/evidence/[^\s]*")
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
        if EVIDENCE_PATH_RE.search(path):
            return {
                "decision": "block",
                "reason": "evidence/ 只能由 `seed run-check` 写入；不要手工构造证据。",
            }
        if PRD_RE.search(path):
            if tool_name == "Edit":
                old = str(tool_input.get("old_string") or "")
                new = str(tool_input.get("new_string") or "")
                if _checked_count(new) > _checked_count(old):
                    return {
                        "decision": "block",
                        "reason": "slice checkbox 只能由 `seed done` 勾选（证据齐备后）；不要直接编辑 `### [ ]` → `### [x]`。",
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
                        "reason": "slice checkbox 只能由 `seed done` 勾选（证据齐备后）；不要整文件覆盖勾选。",
                    }

    if tool_name == "Bash":
        command = str(tool_input.get("command") or "")
        if DESTRUCTIVE_RE.search(command):
            return {
                "decision": "block",
                "reason": "检测到破坏性命令；换用范围更窄、更安全的方式。",
            }
        if EVIDENCE_REDIRECT_RE.search(command) and re.search(r"(>>?|\btee\b)", command):
            return {
                "decision": "block",
                "reason": "不要用 shell 重定向写 evidence/；用 `seed run-check` 真实执行并落盘。",
            }

    return {"decision": "allow"}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = evaluate(payload)
    except Exception as exc:  # pragma: no cover - hook fails open softly
        result = {"decision": "allow", "reason": f"seed_guard could not parse payload: {exc}"}
    if result.get("decision") == "block":
        print(result.get("reason", "Blocked by seed guard"), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
