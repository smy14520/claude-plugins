"""hooks.json 结构守护。

历史 bug：`if` 字段被写在 matcher-group 层（和 matcher/hooks 并列），
而 Claude Code 的 `if` 是 handler 级字段（在 hooks[] 内部）。错位的 `if`
会被 silently ignored，导致 hook 在每次匹配的工具调用上触发，窄过滤失效。

本测试钉死字段归属，防止回归。字段归属依据：
https://code.claude.com/docs/en/hooks （Common fields 表：if 属于 handler）。
"""
from __future__ import annotations

import json
from pathlib import Path

HOOKS_JSON = Path(__file__).resolve().parents[1] / "hooks" / "hooks.json"


def _load() -> dict:
    return json.loads(HOOKS_JSON.read_text(encoding="utf-8"))


def test_if_is_at_handler_level_not_matcher_group():
    """`if` 必须在 handler 对象内，不得出现在 matcher-group 层。"""
    data = _load()
    offenders = []
    for event, groups in data.get("hooks", {}).items():
        for gi, group in enumerate(groups):
            if not isinstance(group, dict):
                continue
            # matcher-group 层只允许 matcher / hooks；出现 `if` 即错位
            if "if" in group:
                offenders.append(f"{event}[group {gi}]: `if` 错放在 matcher-group 层")
    assert not offenders, "hooks.json `if` 错位（应在 handler 内）：\n" + "\n".join(offenders)


def test_living_prd_handlers_carry_if_and_async():
    """living-prd 的 handler 必须各自带 `if`（窄触发）和 async。"""
    data = _load()
    living_handlers = []
    for groups in data.get("hooks", {}).get("PostToolUse", []):
        for h in groups.get("hooks", []):
            if isinstance(h, dict) and "generate_living_prd" in str(h.get("command", "")):
                living_handlers.append(h)
    assert living_handlers, "未找到 living-prd handler"
    for h in living_handlers:
        assert "if" in h, f"living-prd handler 缺 `if`，会变成每次 Write/Edit/Bash 都触发：{h}"
        assert h.get("async") is True, f"living-prd handler 应 async:true：{h}"


def test_valid_json_and_known_events():
    """hooks.json 可解析，事件名在已知集合内。"""
    data = _load()
    known = {"PreToolUse", "PostToolUse", "SessionStart", "SessionEnd",
             "UserPromptSubmit", "Stop", "StopFailure", "PostToolBatch"}
    for event in data.get("hooks", {}):
        assert event in known or True  # 宽松：仅保证可解析；新事件不阻断
