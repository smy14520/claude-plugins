"""review_trigger hook 的单元测试。"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_SCRIPT = Path(__file__).resolve().parents[1] / "hooks" / "review_trigger.py"


def run_hook(payload: dict) -> dict:
    """运行 hook 脚本并返回解析后的 JSON 结果。"""
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def test_non_bash_tool_allowed():
    """非 Bash 工具应该被允许（返回空对象）。"""
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": "/some/file.py"},
    }
    result = run_hook(payload)
    assert result == {}


def test_bash_without_seed_done_allowed():
    """不包含 seed done 的 Bash 命令应该被允许（返回空对象）。"""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "echo hello"},
    }
    result = run_hook(payload)
    assert result == {}


def test_seed_done_triggers_review(tmp_path: Path):
    """seed done 成功后应该触发 review 提醒。"""
    # 创建项目结构
    task_dir = tmp_path / ".arbor" / "tasks" / "demo"
    task_dir.mkdir(parents=True)

    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "seed done demo --slice S-001"},
        "cwd": str(tmp_path),
    }
    result = run_hook(payload)
    assert "hookSpecificOutput" in result
    assert result["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert "additionalContext" in result["hookSpecificOutput"]
    assert "review" in result["hookSpecificOutput"]["additionalContext"].lower()
    assert "S-001" in result["hookSpecificOutput"]["additionalContext"]


def test_seed_done_with_existing_review_skipped(tmp_path: Path):
    """如果已有 review 记录，不应该重复触发（返回空对象）。"""
    # 创建项目结构和 review.md
    task_dir = tmp_path / ".arbor" / "tasks" / "demo"
    task_dir.mkdir(parents=True)
    review_file = task_dir / "review.md"
    review_file.write_text("## Review 2026-01-19\n\n结论：通过\n", encoding="utf-8")

    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "seed done demo --slice S-001"},
        "cwd": str(tmp_path),
    }
    result = run_hook(payload)
    # 已有 review，返回空对象
    assert result == {}


def test_malformed_payload_allowed():
    """格式错误的 payload 应该被允许（返回空对象，fail open）。"""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "seed done demo"},  # 缺少 --slice
    }
    result = run_hook(payload)
    assert result == {}
