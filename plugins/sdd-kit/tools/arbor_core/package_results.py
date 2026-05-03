from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import load_package, save_package
from .state import add_phase_history, route_package_state

IMPL_RESULT_STATES = {"done", "done_with_concerns", "needs_context", "blocked"}
REVIEW_RESULT_STATES = {"approved", "approved_with_notes", "needs_rework", "brainstorm_drift"}


def _state_label(state: str) -> str:
    return state.upper()


def record_impl_result(
    root: Path,
    name: str,
    state: str,
    summary: str,
    acceptance: list[str],
    commands: list[str],
    concerns: list[str],
    actor: str,
    timestamp: str,
) -> dict[str, Any]:
    if state not in IMPL_RESULT_STATES:
        raise ArborError(f"Invalid impl result state '{state}'.")
    if not summary.strip():
        raise ArborError("Impl result summary is required.")
    pkg, data = load_package(root, name)
    old = data.get("state")
    result = {
        "state": _state_label(state),
        "at": timestamp,
        "summary": summary.strip(),
        "acceptance": [item for item in acceptance if item],
        "commands": [item for item in commands if item],
        "concerns": [item for item in concerns if item],
    }
    data["impl_result"] = result
    if state in {"done", "done_with_concerns"}:
        route_package_state(data, "done", timestamp, actor, summary.strip())
    elif state == "needs_context":
        route_package_state(data, "doing", timestamp, actor, summary.strip())
        data["next_action"] = {"skill": "brainstorm", "reason": "impl 发现 PRD / technical framing 缺口，需要回 brainstorm 补齐"}
    elif state == "blocked":
        route_package_state(data, "doing", timestamp, actor, summary.strip())
        data["next_action"] = {"skill": "user", "reason": "impl 被环境、权限、依赖或外部因素阻塞，需要用户处理"}
    add_phase_history(data, timestamp, "impl", old, state, actor, summary.strip())
    save_package(pkg, data)
    return {"package": name, "state": state, "impl_result": result, "next_action": data.get("next_action")}


def _append_review_entry(pkg: Path, state: str, summary: str, evidence: list[str], notes: list[str], actor: str, timestamp: str) -> None:
    lines = [
        "",
        f"## {timestamp} {state}",
        "",
        f"- Actor: {actor}",
        f"- Summary: {summary}",
    ]
    for item in evidence:
        lines.append(f"- Evidence: {item}")
    for item in notes:
        lines.append(f"- Note: {item}")
    with (pkg / "review.md").open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def record_review(
    root: Path,
    name: str,
    state: str,
    summary: str,
    evidence: list[str],
    notes: list[str],
    actor: str,
    timestamp: str,
) -> dict[str, Any]:
    if state not in REVIEW_RESULT_STATES:
        raise ArborError(f"Invalid review state '{state}'.")
    if not summary.strip():
        raise ArborError("Review summary is required.")
    pkg, data = load_package(root, name)
    old = data.get("state")
    result = {
        "state": _state_label(state),
        "at": timestamp,
        "summary": summary.strip(),
        "evidence": [item for item in evidence if item],
        "notes": [item for item in notes if item],
    }
    data["review_result"] = result
    if state in {"approved", "approved_with_notes"}:
        route_package_state(data, "reviewed", timestamp, actor, summary.strip())
    elif state == "needs_rework":
        route_package_state(data, "doing", timestamp, actor, summary.strip())
        data["next_action"] = {"skill": "impl", "reason": "review 要求返工，回到 impl 继续执行"}
    elif state == "brainstorm_drift":
        route_package_state(data, "draft", timestamp, actor, summary.strip())
        data["next_action"] = {"skill": "brainstorm", "reason": "review 发现 PRD 漂移，需要回 brainstorm 修正需求"}
    add_phase_history(data, timestamp, "review", old, state, actor, summary.strip())
    save_package(pkg, data)
    _append_review_entry(pkg, state, summary.strip(), [item for item in evidence if item], [item for item in notes if item], actor, timestamp)
    return {"package": name, "state": state, "review_result": result, "next_action": data.get("next_action")}
