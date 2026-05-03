#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from typing import Any

CONTROL_STATE_RE = re.compile(r"(^|/)\.arbor/tasks/[^/]+/task\.json$")
CONTEXT_JSONL_RE = re.compile(r"(^|/)\.arbor/tasks/[^/]+/context/(impl|review|sources)\.jsonl$")
DESTRUCTIVE_RE = re.compile(r"\b(git\s+reset\s+--hard|git\s+clean\s+-|git\s+push\s+--force|rm\s+-rf)\b")


def _payload_path(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
    return str(tool_input.get("file_path") or tool_input.get("path") or "")


def _payload_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
    return str(tool_input.get("command") or "")


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    tool_name = str(payload.get("tool_name") or "")
    if tool_name in {"Edit", "Write", "NotebookEdit"}:
        path = _payload_path(payload)
        if CONTROL_STATE_RE.search(path):
            return {
                "decision": "block",
                "reason": "Use sdd-arbor helpers for .arbor control state instead of editing task.json directly.",
            }
        if CONTEXT_JSONL_RE.search(path):
            return {
                "decision": "block",
                "reason": "Use sdd-arbor add-context or add-context-batch for package context JSONL.",
            }
    if tool_name == "Bash":
        command = _payload_command(payload)
        if DESTRUCTIVE_RE.search(command):
            return {
                "decision": "block",
                "reason": "Destructive command detected; ask for explicit user authorization and prefer a safer helper if possible.",
            }
    return {"decision": "allow"}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = evaluate(payload)
    except Exception as exc:  # pragma: no cover - hook should fail closed softly
        result = {"decision": "allow", "reason": f"arbor_guard could not parse payload: {exc}"}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
