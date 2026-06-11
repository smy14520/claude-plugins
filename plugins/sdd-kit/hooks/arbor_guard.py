#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any

CONTROL_STATE_RE = re.compile(r"(^|/)\.arbor/tasks/[^/]+/task\.json$")
CONTEXT_JSONL_RE = re.compile(r"(^|/)\.arbor/tasks/[^/]+/context/(impl|review|sources)\.jsonl$")
CHECKS_DIR_RE = re.compile(r"(^|/)\.arbor/tasks/[^/]+/checks/")
PRD_FILE_RE = re.compile(r"(^|/)\.arbor/tasks/[^/]+/prd\.md$")
PRD_FROZEN_STATES = {"doing", "done"}
DESTRUCTIVE_RE = re.compile(r"\b(git\s+reset\s+--hard|git\s+push\s+--force|rm\s+-rf)\b|git\s+(checkout|restore)\s+(--\s+)?\.(?!\S)")


def _flag_chars(token: str) -> set[str]:
    if not token.startswith("-") or token.startswith("--"):
        return set()
    return set(token.lstrip("-"))


def _is_git_clean_destructive(tokens: list[str]) -> bool:
    if len(tokens) < 3 or tokens[0:2] != ["git", "clean"]:
        return False
    if "--dry-run" in tokens[2:]:
        return False
    flags = set().union(*(_flag_chars(token) for token in tokens[2:]))
    if "n" in flags:
        return False
    return "f" in flags and "d" in flags


def _is_mass_checkout_restore(tokens: list[str]) -> bool:
    if len(tokens) < 3 or tokens[0] != "git" or tokens[1] not in {"checkout", "restore"}:
        return False
    args = [token for token in tokens[2:] if token != "--"]
    return args == ["."]


def _is_rm_rf(tokens: list[str]) -> bool:
    if not tokens or tokens[0] != "rm":
        return False
    flags = set().union(*(_flag_chars(token) for token in tokens[1:]))
    return "r" in flags and "f" in flags


def _destructive_command(command: str) -> bool:
    if DESTRUCTIVE_RE.search(command):
        return True
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    return _is_git_clean_destructive(tokens) or _is_mass_checkout_restore(tokens) or _is_rm_rf(tokens)


def _prd_frozen(path: str) -> bool:
    """True when the package owning this prd.md is mid impl/review (state doing/done).

    Exception: when the package is routed back to brainstorm (e.g. impl
    recorded needs_context, which keeps state=doing), the PRD must stay
    editable — brainstorm's whole job at that point is to update it.
    Fail-open: any read/parse problem means no block.
    """
    try:
        task_json = Path(path).parent / "task.json"
        data = json.loads(task_json.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("state") not in PRD_FROZEN_STATES:
            return False
        next_action = data.get("next_action")
        next_skill = next_action.get("skill") if isinstance(next_action, dict) else None
        return next_skill != "brainstorm"
    except Exception:
        return False


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
                "reason": "Use sdd-arbor add-context for package context JSONL.",
            }
        if CHECKS_DIR_RE.search(path):
            return {
                "decision": "block",
                "reason": "Use sdd-arbor run-check or record-check to write check evidence; do not edit checks/ files directly.",
            }
        if PRD_FILE_RE.search(path) and _prd_frozen(path):
            return {
                "decision": "block",
                "reason": "PRD 在 impl/review 期间（state doing/done）冻结。需要修改需求：由 impl 记录 record-impl-result --state needs_context（回 brainstorm 后 PRD 解冻），或走 sdd-arbor add-amendment。",
            }
    if tool_name == "Bash":
        command = _payload_command(payload)
        if _destructive_command(command):
            return {
                "decision": "block",
                "reason": "Destructive command detected; use a narrower safer helper or command instead.",
            }
    return {"decision": "allow"}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = evaluate(payload)
    except Exception as exc:  # pragma: no cover - hook should fail closed softly
        result = {"decision": "allow", "reason": f"arbor_guard could not parse payload: {exc}"}
    if result.get("decision") == "block":
        print(result.get("reason", "Blocked by arbor guard"), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
