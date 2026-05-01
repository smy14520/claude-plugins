from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import load_package, save_package
from .package_lifecycle import find_task
from .schema import TASK_ID_RE
from .state import add_phase_history, recalculate_package_state

IMPL_RESULT_STATES = {"done", "done_with_concerns", "needs_context", "blocked"}
REVIEW_RESULT_STATES = {"approved", "approved_with_notes", "needs_rework", "brainstorm_drift"}


def _require_task_id(task_id: str) -> None:
    if not TASK_ID_RE.match(task_id):
        raise ArborError(f"Invalid task id '{task_id}'. Use T-001 format.")


def _state_label(state: str) -> str:
    return state.upper()


def record_impl_result(
    root: Path,
    name: str,
    task_id: str,
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
    _require_task_id(task_id)
    if not summary.strip():
        raise ArborError("Impl result summary is required.")
    pkg, data = load_package(root, name)
    task = find_task(data, task_id)
    old = task.get("state")
    task["state"] = state
    task["updated_at"] = timestamp
    task["last_impl_result"] = {
        "state": _state_label(state),
        "at": timestamp,
        "summary": summary.strip(),
        "acceptance": [item for item in acceptance if item],
        "commands": [item for item in commands if item],
        "concerns": [item for item in concerns if item],
    }
    recalculate_package_state(data)
    data["updated_at"] = timestamp
    add_phase_history(data, timestamp, "impl", task_id, old, state, actor, summary.strip())
    save_package(pkg, data)
    return {"package": name, "task_id": task_id, "state": state, "task": task, "next_action": data.get("next_action")}


def _append_review_entry(pkg: Path, task_id: str, state: str, summary: str, evidence: list[str], notes: list[str], actor: str, timestamp: str) -> None:
    lines = [
        "",
        f"## {timestamp} {task_id} {state}",
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
    task_id: str,
    state: str,
    summary: str,
    evidence: list[str],
    notes: list[str],
    actor: str,
    timestamp: str,
) -> dict[str, Any]:
    if state not in REVIEW_RESULT_STATES:
        raise ArborError(f"Invalid review state '{state}'.")
    _require_task_id(task_id)
    if not summary.strip():
        raise ArborError("Review summary is required.")
    pkg, data = load_package(root, name)
    task = find_task(data, task_id)
    old = task.get("state")
    task["state"] = state
    task["updated_at"] = timestamp
    task["last_review_result"] = {
        "state": _state_label(state),
        "at": timestamp,
        "summary": summary.strip(),
        "evidence": [item for item in evidence if item],
        "notes": [item for item in notes if item],
    }
    recalculate_package_state(data)
    data["updated_at"] = timestamp
    add_phase_history(data, timestamp, "review", task_id, old, state, actor, summary.strip())
    save_package(pkg, data)
    _append_review_entry(pkg, task_id, state, summary.strip(), [item for item in evidence if item], [item for item in notes if item], actor, timestamp)
    return {"package": name, "task_id": task_id, "state": state, "task": task, "next_action": data.get("next_action")}
