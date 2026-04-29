from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from .errors import ArborError
from .map_dispatch import assignment_context, normalize_worktree_root_ref, resolve_worktree_ref, team_name_for_initiative
from .map_readiness import map_check
from .map_runtime import append_parallel_runtime_event
from .schema import PARALLEL_SELF_HEAL_ACTIONS, PARALLEL_STOP_REASONS


LANE_POLICY = {
    "default": "automatic_dynamic_progression",
    "confirm_lane_switches": False,
    "stop_only_for": [
        "product_decision",
        "permission_required",
        "destructive_action",
        "external_context",
        "unrecoverable_state",
    ],
}


def _lane_switch(lane: str, reason: str) -> dict[str, Any]:
    return {"lane": lane, "confirm": False, "reason": reason}


def _assignment(root: Path, initiative: str, item: dict[str, Any], check: dict[str, Any], round_id: str, worktree_root_ref: str, lane: str) -> dict[str, Any]:
    result = assignment_context(root, initiative, item, check, round_id, worktree_root_ref)
    result["lane"] = lane
    return result


def _recommended_self_healing(check: dict[str, Any]) -> list[dict[str, Any]]:
    recommended: list[dict[str, Any]] = []
    for item in check.get("blocked", []):
        if not isinstance(item, dict):
            continue
        if item.get("needs_reconcile"):
            recommended.append(
                {
                    "action": "reconcile_package",
                    "package": item.get("name"),
                    "reason": item.get("reason") or "package state can be reconciled from durable dependency checkpoints",
                }
            )
    return recommended


def _stop_reasons(check: dict[str, Any]) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []
    for item in check.get("missing", []):
        if isinstance(item, dict):
            reasons.append({"reason": "unrecoverable_state", "package": item.get("name"), "detail": item.get("reason")})
    for item in check.get("blocked", []):
        if not isinstance(item, dict):
            continue
        if item.get("needs_reconcile"):
            continue
        reason = "external_context" if item.get("state") in {"blocked", "needs_context"} else "unrecoverable_state"
        reasons.append({"reason": reason, "package": item.get("name"), "detail": item.get("reason")})
    return reasons


def _schedule_detail(schedule: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": schedule["mode"],
        "serial_critical_path_count": len(schedule["serial_critical_path"]),
        "parallel_execution_count": len(schedule["parallel_execution"]),
        "parallel_prep_count": len(schedule["parallel_prep"]),
        "serial_integration_count": len(schedule["serial_integration"]),
        "stop_reasons_count": len(schedule["stop_reasons"]),
        "self_healing_recommended_count": len(schedule["self_healing"]["recommended"]),
    }


def parallel_schedule(root: Path, initiative: str, max_parallel: int, actor: str, timestamp: str, worktree_root_ref: str | None = None) -> dict[str, Any]:
    if max_parallel < 1:
        raise ArborError("--max-parallel must be at least 1.")
    if max_parallel > 5:
        raise ArborError("--max-parallel must be 5 or less; keep the lead-owned worker pool bounded.")

    normalized_worktree_root_ref = normalize_worktree_root_ref(root, worktree_root_ref)
    check = map_check(root, initiative, timestamp)
    round_id = f"round-{uuid5(NAMESPACE_URL, f'arbor-schedule:{initiative}:{timestamp}').hex[:12]}"
    schedule: dict[str, Any] = {
        "at": timestamp,
        "round_id": round_id,
        "actor": actor,
        "initiative": initiative,
        "team_name": team_name_for_initiative(initiative),
        "runtime": "claude-code-agent-team",
        "lead": "main-session",
        "isolation": "team-enter-worktree-required",
        "worktree_root_ref": normalized_worktree_root_ref,
        "worktree_root_path": str(resolve_worktree_ref(root, normalized_worktree_root_ref)),
        "max_parallel": max_parallel,
        "mode": "continue",
        "lane_policy": LANE_POLICY.copy(),
        "lane_switches": [],
        "serial_critical_path": [],
        "parallel_execution": [],
        "parallel_prep": [],
        "serial_integration": [],
        "self_healing": {"recommended": _recommended_self_healing(check), "applied": []},
        "stop_reasons": [],
        "source_check": {
            "execution_ready_count": len(check.get("execution_ready", [])),
            "prep_ready_count": len(check.get("prep_ready", [])),
            "integration_ready_count": len(check.get("integration_ready", [])),
            "blocked_count": len(check.get("blocked", [])),
            "active_count": len(check.get("active", [])),
            "complete_count": len(check.get("complete", [])),
            "missing_count": len(check.get("missing", [])),
        },
    }

    integration_ready = check.get("integration_ready", [])
    execution_ready = check.get("execution_ready", [])
    prep_ready = check.get("prep_ready", [])
    active = check.get("active", [])
    complete = check.get("complete", [])
    missing = check.get("missing", [])
    blocked = check.get("blocked", [])

    if integration_ready:
        schedule["serial_integration"] = [_assignment(root, initiative, integration_ready[0], check, round_id, normalized_worktree_root_ref, "serial_integration")]
        schedule["lane_switches"].append(_lane_switch("serial_integration", "shared/global integration scope is ready; dispatch exactly one integration worker"))
    elif len(execution_ready) == 1:
        schedule["serial_critical_path"] = [_assignment(root, initiative, execution_ready[0], check, round_id, normalized_worktree_root_ref, "serial_critical_path")]
        schedule["lane_switches"].append(_lane_switch("serial_critical_path", "only one execution-ready package exists; keep lead/worker boundary with a single worker"))
    elif len(execution_ready) > 1:
        execution_slots = min(max_parallel, len(execution_ready))
        schedule["parallel_execution"] = [
            _assignment(root, initiative, item, check, round_id, normalized_worktree_root_ref, "parallel_execution")
            for item in execution_ready[:execution_slots]
        ]
        schedule["lane_switches"].append(_lane_switch("parallel_execution", "multiple independent execution-ready packages are available"))
        remaining_slots = max_parallel - len(schedule["parallel_execution"])
        if remaining_slots > 0 and prep_ready:
            schedule["parallel_prep"] = [
                _assignment(root, initiative, item, check, round_id, normalized_worktree_root_ref, "parallel_prep")
                for item in prep_ready[:remaining_slots]
            ]
            schedule["lane_switches"].append(_lane_switch("parallel_prep", "execution lane has spare capacity and dependency-safe prep work is available"))
    elif prep_ready:
        schedule["parallel_prep"] = [
            _assignment(root, initiative, item, check, round_id, normalized_worktree_root_ref, "parallel_prep")
            for item in prep_ready[:max_parallel]
        ]
        schedule["lane_switches"].append(_lane_switch("parallel_prep", "no execution-ready package is open, but dependency-safe prep work can proceed"))

    has_dispatch = any(schedule[key] for key in ["serial_critical_path", "parallel_execution", "parallel_prep", "serial_integration"])
    if not has_dispatch:
        if active:
            schedule["mode"] = "continue"
        elif complete and not blocked and not missing:
            schedule["mode"] = "complete"
            schedule["lane_switches"].append(_lane_switch("complete", "all known packages have stable completion checkpoints"))
        elif schedule["self_healing"]["recommended"]:
            schedule["mode"] = "continue"
            schedule["lane_switches"].append(_lane_switch("blocked", "only self-healable blocked packages remain; run recommended helpers before asking the user"))
        else:
            schedule["mode"] = "stop"
            schedule["stop_reasons"] = _stop_reasons(check)
            schedule["lane_switches"].append(_lane_switch("blocked", "no dispatchable package remains and at least one true blocker exists"))

    if schedule["mode"] == "stop" and not schedule["stop_reasons"]:
        schedule["stop_reasons"] = [{"reason": "unrecoverable_state", "detail": "no dispatchable package and no active worker"}]

    event = "scheduler_stop" if schedule["mode"] == "stop" else "scheduler_continue"
    append_parallel_runtime_event(root, initiative, event, actor, timestamp, reason=f"parallel-schedule mode={schedule['mode']}", detail=_schedule_detail(schedule))
    return schedule
