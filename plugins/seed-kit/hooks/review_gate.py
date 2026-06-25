#!/usr/bin/env python3
"""review_gate — `seed done` 的 PreToolUse 硬 gate：review-loop 未收敛不准勾选。

堵弱模型跳过 review-loop 直接 done 的路径（软提醒已被证明无效）。

为什么是 hook 而不是 cmd_done 里的检查：
- 职责分离——helper（cmd_done）守"声明义务证据齐备"（可移植、单测覆盖）；
  hook 守"review-loop 这道独立流程跑过且收敛"，是流程底线，不是证据形状。
- 直接调 seed.main（脚本/单测）绕过本 hook，义务 gate 照旧；只有 harness 里
  通过 Bash 调 `seed done` 才过这道 gate——正是要拦的弱模型路径。

放行条件（任一满足即 allow）：
1. 不是 `seed done <task> --slice <S>` 命令；
2. 该 slice 已是 [x]（无 unchecked→checked 迁移，幂等重跑不重复 gate）；
3. evidence/<slice>/review-loop.json 存在且 terminal_reason == converged。
否则 block，给出可执行的下一步（review-loop 熔断 = 真·未收敛，走卡住协议交人，不开后门）。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

DONE_RE = re.compile(r"\bseed\b.*?\bdone\s+(\S+)\s+--slice\s+(S-\d{3})\b")


def _tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    ti = payload.get("tool_input")
    return ti if isinstance(ti, dict) else {}


def _marker_path(root: Path, task: str, slice_id: str) -> Path:
    return root / ".arbor" / "tasks" / task / "evidence" / slice_id / "review-loop.json"


def _slice_already_done(root: Path, task: str, slice_id: str) -> bool:
    prd = root / ".arbor" / "tasks" / task / "prd.md"
    try:
        text = prd.read_text(encoding="utf-8")
    except OSError:
        return False
    # prd 索引行：`### [x] S-001 <title>`；slice_id 形如 S-001，无正则元字符
    return bool(re.search(rf"^### \[x\] {slice_id}(?:\s|$)", text, re.MULTILINE))


def _review_loop_ran_in_session(payload):
    """本会话是否真跑过 review-loop Workflow（subagents/workflows/*/journal.jsonl 有 ≥1 result）。
    返回 True/False；payload 缺 session_id/transcript_path 时返回 None（无法判定，不阻断）。"""
    transcript_path = payload.get("transcript_path")
    session_id = payload.get("session_id")
    if not transcript_path or not session_id:
        return None
    wf_dir = Path(transcript_path).parent / session_id / "subagents" / "workflows"
    if not wf_dir.is_dir():
        return False
    for journal in wf_dir.glob("*/journal.jsonl"):
        try:
            txt = journal.read_text(encoding="utf-8")
        except OSError:
            continue
        if '"type":"result"' in txt or '"type": "result"' in txt:
            return True
    return False


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    if str(payload.get("tool_name") or "") != "Bash":
        return {"decision": "allow"}
    command = str(_tool_input(payload).get("command") or "")
    m = DONE_RE.search(command)
    if not m:
        return {"decision": "allow"}

    task, slice_id = m.group(1), m.group(2)
    cwd = payload.get("cwd")
    root = Path(cwd).resolve() if cwd else Path.cwd()

    if _slice_already_done(root, task, slice_id):
        # 幂等放行；但 marker 缺失/异常时留 stderr 审计警告（防"一次伪造、永久信任"无痕）
        try:
            _d = json.loads(_marker_path(root, task, slice_id).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            _d = None
        _cur = _d.get("terminal_reason") if isinstance(_d, dict) else None
        if _cur != "converged":
            print(f"⚠ {slice_id} 已 done，但 review-loop marker 缺失/异常（terminal_reason={_cur}），建议人工复核。", file=sys.stderr)
        return {"decision": "allow"}

    marker = _marker_path(root, task, slice_id)
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = None

    if not isinstance(data, dict) or data.get("terminal_reason") != "converged":
        current = data.get("terminal_reason") if isinstance(data, dict) else None
        cur = f"（当前 terminal_reason={current}）" if current else "（无 review-loop marker）"
        return {
            "decision": "block",
            "reason": (
                f"{slice_id} 还不能 seed done：review-loop 未收敛{cur}。\n"
                f"先跑 `/seed-kit:review-loop {slice_id}` 到 converged，再用\n"
                f"  seed review-mark {task} --slice {slice_id} --verdict converged\n"
                f"落 marker，然后重试 seed done。\n"
                f"（review-loop 熔断/escalate = 真·未收敛——走卡住协议停下交人，不要硬推 done。）"
            ),
        }
    # #1 anti-forge: converged marker 必须对应本会话真跑过的 review-loop，否则疑为手敲伪造
    _ran = _review_loop_ran_in_session(payload)
    if _ran is False:
        return {
            "decision": "block",
            "reason": (
                f"{slice_id} 的 marker=converged，但本会话没有 review-loop workflow 的运行记录——疑似手敲 `seed review-mark --verdict converged` 伪造。"
                f"先真跑 `/seed-kit:review-loop {slice_id}` 到 converged，再 review-mark + seed done。"
            ),
        }
    return {"decision": "allow"}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = evaluate(payload)
    except Exception as exc:  # pragma: no cover - fail open softly
        result = {"decision": "allow", "reason": f"review_gate 解析失败，放行：{exc}"}
    if result.get("decision") == "block":
        print(result.get("reason", "被 review_gate 拦截"), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
