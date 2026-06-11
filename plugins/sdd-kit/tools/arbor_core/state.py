from __future__ import annotations

from typing import Any


def default_execution(name: str) -> dict[str, Any]:
    return {
        "boundary": "package",
        "unit_path": f".arbor/tasks/{name}",
        "status": "unclaimed",
        "owner": None,
        "claimed_at": None,
        "released_at": None,
        "base_ref": None,
        "branch": {
            "base": None,
            "name": None,
            "upstream": None,
        },
        "worktree": {
            "path": None,
            "created_by": None,
        },
        "session": None,
        "pr": {
            "url": None,
            "number": None,
            "state": "none",
        },
        "agents": [],
        "checkpoints": [],
        "updated_at": None,
        "updated_by": None,
        "note": None,
    }


def ensure_execution(data: dict[str, Any]) -> dict[str, Any]:
    name = data.get("name")
    if not isinstance(name, str):
        name = ""
    execution = data.get("execution")
    if not isinstance(execution, dict):
        execution = default_execution(name)
        data["execution"] = execution
        return execution

    defaults = default_execution(name)
    execution.pop("child_task_scope", None)
    # Remove legacy plan field
    execution.pop("plan", None)
    for key, value in defaults.items():
        if key not in execution:
            execution[key] = value
    for key in ["branch", "worktree", "pr"]:
        if not isinstance(execution.get(key), dict):
            execution[key] = defaults[key]
        else:
            for child_key, child_value in defaults[key].items():
                execution[key].setdefault(child_key, child_value)
    if not isinstance(execution.get("agents"), list):
        execution["agents"] = []
    if not isinstance(execution.get("checkpoints"), list):
        execution["checkpoints"] = []
    return execution


def add_phase_history(data: dict[str, Any], timestamp: str, phase: str, from_state: str | None, to_state: str, actor: str, note: str) -> None:
    data.setdefault("phase_history", []).append(
        {
            "at": timestamp,
            "phase": phase,
            "from": from_state,
            "to": to_state,
            "actor": actor,
            "note": note,
        }
    )


def route_package_state(data: dict[str, Any], state: str, timestamp: str | None = None, actor: str | None = None, note: str | None = None) -> None:
    """Route package to one of 5 states: draft, ready, doing, done, reviewed."""
    # Map legacy states
    from .schema import LEGACY_STATE_MAP
    state = LEGACY_STATE_MAP.get(state, state)

    data["state"] = state
    execution = ensure_execution(data)

    if state == "draft":
        data["current_phase"] = "brainstorm"
        data["next_action"] = {"skill": "brainstorm", "reason": "PRD 尚未就绪"}
    elif state == "ready":
        data["current_phase"] = "brainstorm"
        data["next_action"] = {"skill": "impl", "reason": "PRD 已就绪，可以开始执行"}
    elif state == "doing":
        data["current_phase"] = "impl"
        data["next_action"] = {"skill": "impl", "reason": "正在执行"}
        execution["status"] = "in_progress"
    elif state == "done":
        data["current_phase"] = "impl"
        data["next_action"] = {"skill": "review", "reason": "执行完成，等待审计"}
        if execution.get("status") not in {"pr_open", "merged"}:
            execution["status"] = "done"
    elif state == "reviewed":
        data["current_phase"] = "review"
        data["next_action"] = {"skill": "none", "reason": "已通过审计"}
        if execution.get("status") not in {"pr_open", "merged"}:
            execution["status"] = "reviewed"
    elif state == "archived":
        data["current_phase"] = data.get("current_phase", "brainstorm")
        data["next_action"] = {"skill": "none", "reason": "已归档，不再推进"}

    if timestamp:
        data["updated_at"] = timestamp
        execution["updated_at"] = timestamp
    if actor:
        execution["updated_by"] = actor
    if note is not None:
        execution["note"] = note


# Backward-compatible import name for older modules during this migration.
def recalculate_package_state(data: dict[str, Any]) -> None:
    route_package_state(data, data.get("state", "draft"))
