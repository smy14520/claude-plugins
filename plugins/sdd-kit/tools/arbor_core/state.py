from __future__ import annotations

from typing import Any

from .schema import DEPENDENCY_COMPLETE_STATES, REVIEW_PASS_STATES


def default_execution(name: str) -> dict[str, Any]:
    return {
        "boundary": "package",
        "unit_path": f".arbor/tasks/{name}",
        "child_task_scope": "control_acceptance_review",
        "status": "unclaimed",
        "owner": None,
        "claimed_at": None,
        "released_at": None,
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


def add_phase_history(data: dict[str, Any], timestamp: str, phase: str, task_id: str | None, from_state: str | None, to_state: str, actor: str, note: str) -> None:
    data.setdefault("phase_history", []).append(
        {
            "at": timestamp,
            "phase": phase,
            "task_id": task_id,
            "from": from_state,
            "to": to_state,
            "actor": actor,
            "note": note,
        }
    )


def sorted_tasks(data: dict[str, Any], states: set[str] | None = None) -> list[dict[str, Any]]:
    tasks = data.get("tasks", []) if isinstance(data.get("tasks"), list) else []
    if states is not None:
        tasks = [task for task in tasks if task.get("state") in states]
    return sorted(tasks, key=lambda task: task.get("id", ""))


def dependencies_satisfied(task: dict[str, Any], states_by_id: dict[str, str]) -> bool:
    return all(states_by_id.get(dep) in DEPENDENCY_COMPLETE_STATES for dep in task.get("depends_on", []))


def recalculate_package_state(data: dict[str, Any]) -> None:
    tasks = sorted_tasks(data)
    if not tasks:
        return
    states_by_id = {task.get("id"): task.get("state") for task in tasks if isinstance(task.get("id"), str)}

    for state, package_state, phase, skill, reason in [
        ("brainstorm_drift", "brainstorm_drift", "review", "brainstorm", "package PRD 已过期或需求不正确"),
        ("needs_rework", "needs_rework", "review", "impl", "review 发现需要返工"),
        ("in_progress", "in_progress", "impl", "impl", "implementation 正在执行"),
        ("done", "impl_done", "impl", "review", "implementation 已完成，等待 semantic audit"),
        ("done_with_concerns", "impl_done", "impl", "review", "implementation 已完成但有 concerns，等待 semantic audit"),
        ("needs_context", "needs_context", "task", "task", "task-local context 缺失或冲突"),
        ("blocked", "blocked", data.get("current_phase", "task"), "user", "external blocker 需要用户处理"),
    ]:
        matches = sorted_tasks(data, {state})
        if matches:
            task_id = matches[0].get("id")
            data["state"] = package_state
            data["current_phase"] = phase
            data["active_task"] = task_id if state == "in_progress" else None
            data["next_action"] = {"skill": skill, "task_id": task_id, "reason": reason}
            if package_state in {"impl_done", "reviewed"}:
                execution = ensure_execution(data)
                if execution.get("status") not in {"in_progress", "pr_open", "merged"}:
                    execution["status"] = package_state
            return

    required_tasks = [task for task in tasks if task.get("state") != "skipped"]
    if required_tasks and all(task.get("state") in REVIEW_PASS_STATES for task in required_tasks):
        data["state"] = "reviewed"
        data["current_phase"] = "review"
        data["active_task"] = None
        data["next_action"] = {"skill": "none", "task_id": None, "reason": "所有 required package-local tasks 已通过 review"}
        execution = ensure_execution(data)
        if execution.get("status") not in {"in_progress", "pr_open", "merged"}:
            execution["status"] = "reviewed"
        return

    ready_tasks = [task for task in sorted_tasks(data, {"ready"}) if dependencies_satisfied(task, states_by_id)]
    if ready_tasks:
        task_id = ready_tasks[0].get("id")
        data["state"] = "ready"
        data["current_phase"] = "task"
        data["active_task"] = None
        data["next_action"] = {"skill": "impl", "task_id": task_id, "reason": "下一个 package-local ready task"}
        return