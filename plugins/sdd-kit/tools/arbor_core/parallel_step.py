from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .fs import load_package, validate_name
from .map_dispatch import resolve_worktree_ref
from .map_readiness import map_check
from .parallel_scheduler import parallel_schedule


DISPATCH_KEYS = ["serial_integration", "serial_critical_path", "parallel_execution", "parallel_prep"]


def _action_command(action: dict[str, Any]) -> list[str]:
    action_type = action.get("type")
    if action_type == "reconcile_package":
        command = ["sdd-arbor", "reconcile-package", action["initiative"], action["package"]]
        if action.get("assignment_id"):
            command.extend(["--assignment-id", action["assignment_id"]])
        if action.get("worker"):
            command.extend(["--worker", action["worker"]])
        command.append("--json")
        return command
    if action_type == "release_stale_claim":
        return [
            "sdd-arbor",
            "release-package",
            action["package"],
            "--owner",
            action["worker"],
            "--actor",
            "parallel",
            "--note",
            action["reason"],
        ]
    if action_type == "dispatch_worker":
        return [
            "sdd-arbor",
            "claim-package",
            action["package"],
            "--owner",
            action["worker"],
            "--branch",
            action["branch"],
            "--worktree",
            action["worktree_ref"],
            "--session",
            action["assignment_id"],
            "--actor",
            "parallel",
            "--note",
            f"parallel-step dispatch {action['lane']}",
        ]
    if action_type == "shutdown_team":
        return []
    return []


def _dispatch_action(assignment: dict[str, Any]) -> dict[str, Any]:
    action = {
        "type": "dispatch_worker",
        "initiative": assignment["initiative"],
        "package": assignment["package"],
        "lane": assignment["lane"],
        "assignment_id": assignment["assignment_id"],
        "worker": assignment["worker_name"],
        "team_name": assignment["team_name"],
        "branch": assignment["branch"],
        "worktree_ref": assignment["worktree_ref"],
        "resolved_worktree_path": assignment["resolved_worktree_path"],
        "worker_prompt": assignment["worker_prompt"],
        "reason": f"dispatch {assignment['lane']} assignment from parallel-schedule",
    }
    action["command"] = _action_command(action)
    return action


def _self_heal_action(initiative: str, item: dict[str, Any]) -> dict[str, Any]:
    action = {
        "type": item.get("action"),
        "initiative": initiative,
        "package": item.get("package"),
        "reason": item.get("reason"),
    }
    action["command"] = _action_command(action)
    return action


def _collect_dispatch_actions(schedule: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for key in DISPATCH_KEYS:
        for assignment in schedule.get(key, []):
            if isinstance(assignment, dict):
                actions.append(_dispatch_action(assignment))
    return actions


def _worktree_clean(path: Path) -> bool:
    if not path.exists():
        return False
    result = subprocess.run(["git", "-C", str(path), "status", "--short"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False)
    return result.returncode == 0 and result.stdout.strip() == ""


def _release_stale_claim_actions(root: Path, initiative: str, live_workers: set[str] | None, timestamp: str) -> list[dict[str, Any]]:
    if live_workers is None:
        return []
    actions: list[dict[str, Any]] = []
    check = map_check(root, initiative, timestamp)
    for item in check.get("active", []):
        if not isinstance(item, dict):
            continue
        package = item.get("name")
        if not isinstance(package, str):
            continue
        validate_name(package)
        _, task_data = load_package(root, package)
        execution = task_data.get("execution") if isinstance(task_data.get("execution"), dict) else {}
        worker = execution.get("owner")
        if not isinstance(worker, str) or worker in live_workers:
            continue
        worktree_ref = execution.get("worktree", {}).get("path") if isinstance(execution.get("worktree"), dict) else None
        if not isinstance(worktree_ref, str) or not _worktree_clean(resolve_worktree_ref(root, worktree_ref)):
            continue
        action = {
            "type": "release_stale_claim",
            "initiative": initiative,
            "package": package,
            "worker": worker,
            "worktree_ref": worktree_ref,
            "reason": "Release stale runtime claim after no live Team worker and clean worktree",
        }
        action["command"] = _action_command(action)
        actions.append(action)
    return actions


def parallel_step(root: Path, initiative: str, max_parallel: int, actor: str, timestamp: str, worktree_root_ref: str | None = None, live_workers: list[str] | None = None) -> dict[str, Any]:
    """Return a deterministic lead action plan for one orchestration step.

    This is intentionally a thin coordinator. It does not judge product semantics
    or inspect live Team processes. It converts durable scheduler state into the
    next mechanical actions the lead should execute.
    """
    schedule = parallel_schedule(root, initiative, max_parallel, actor, timestamp, worktree_root_ref)
    live_worker_set = set(live_workers) if live_workers is not None else None
    safe_actions: list[dict[str, Any]] = _release_stale_claim_actions(root, initiative, live_worker_set, timestamp)
    dispatch_actions = _collect_dispatch_actions(schedule)
    stop_reasons = schedule.get("stop_reasons", []) if isinstance(schedule.get("stop_reasons"), list) else []

    if safe_actions:
        mode = "continue"
        phase = "self_heal"
        dispatch_actions = []
    elif dispatch_actions:
        mode = "continue"
        phase = "dispatch"
    elif schedule.get("self_healing", {}).get("recommended"):
        mode = "continue"
        phase = "self_heal"
        safe_actions = [_self_heal_action(initiative, item) for item in schedule["self_healing"]["recommended"] if isinstance(item, dict)]
    elif schedule.get("mode") == "complete":
        mode = "complete"
        phase = "cleanup"
        safe_actions = [{"type": "shutdown_team", "initiative": initiative, "team_name": schedule.get("team_name"), "reason": "schedule complete and no dispatchable work", "command": []}]
    elif schedule.get("mode") == "stop":
        mode = "stop"
        phase = "blocked"
    else:
        mode = "wait"
        phase = "runtime_wait"

    return {
        "at": timestamp,
        "initiative": initiative,
        "round_id": schedule.get("round_id"),
        "team_name": schedule.get("team_name"),
        "mode": mode,
        "phase": phase,
        "schedule_mode": schedule.get("mode"),
        "source_check": schedule.get("source_check"),
        "safe_actions": safe_actions,
        "dispatch": dispatch_actions,
        "stop_reasons": stop_reasons,
        "schedule": schedule,
    }
