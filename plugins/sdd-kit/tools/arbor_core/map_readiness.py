from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .fs import *
from .map_contracts import open_contract_requests_for_package
from .map_policy import normalize_modification_scope, normalize_parallel_policy, normalize_string_list
from .map_sync import read_package_summary, sync_map_from_packages


def package_dependency_complete(summary: dict[str, Any]) -> bool:
    return (
        summary.get("state") == "completed"
        or summary.get("execution_status") == "merged"
        or summary.get("pr_state") == "merged"
        or bool(summary.get("latest_lead_checkpoint"))
    )


def package_active(summary: dict[str, Any]) -> bool:
    return summary.get("state") == "in_progress" or summary.get("execution_status") in {"claimed", "worktree_ready", "in_progress", "pr_open"}


def package_assignable(summary: dict[str, Any]) -> bool:
    if not summary.get("exists"):
        return False
    if not summary.get("validation", {}).get("ok"):
        return False
    if package_dependency_complete(summary) or package_active(summary):
        return False
    if summary.get("state") in {"blocked", "needs_context", "superseded"}:
        return False
    next_action = summary.get("next_action") if isinstance(summary.get("next_action"), dict) else {}
    return next_action.get("skill") in {"brainstorm", "task", "impl", "review"}


def dependency_gate_satisfied(dependency_blockers: list[dict[str, Any]]) -> bool:
    return not dependency_blockers


def phase_before_dependency_allowed(skill: Any, max_phase: Any) -> bool:
    order = {"brainstorm": 1, "task": 2, "impl": 3, "review": 4}
    return isinstance(skill, str) and isinstance(max_phase, str) and order.get(skill, 999) <= order.get(max_phase, 0)


def package_prep_assignable(summary: dict[str, Any], policy: dict[str, Any], dependency_blockers: list[dict[str, Any]]) -> bool:
    if not package_assignable(summary) or not dependency_blockers:
        return False
    next_action = summary.get("next_action") if isinstance(summary.get("next_action"), dict) else {}
    skill = next_action.get("skill")
    return bool(policy.get("can_prepare_without_dependencies")) and skill in {"brainstorm", "task"} and phase_before_dependency_allowed(skill, policy.get("max_phase_before_dependencies"))


def package_execution_assignable(summary: dict[str, Any], policy: dict[str, Any], dependency_blockers: list[dict[str, Any]]) -> bool:
    if not package_assignable(summary):
        return False
    next_action = summary.get("next_action") if isinstance(summary.get("next_action"), dict) else {}
    skill = next_action.get("skill")
    if dependency_gate_satisfied(dependency_blockers):
        return skill in {"brainstorm", "task", "impl", "review"}
    return bool(policy.get("can_implement_without_dependencies")) and skill in {"impl", "review"} and phase_before_dependency_allowed(skill, policy.get("max_phase_before_dependencies"))


def wave_sort_key(entry: dict[str, Any]) -> tuple[int, str, str]:
    wave = entry.get("wave")
    if isinstance(wave, str):
        match = re.search(r"\d+", wave)
        if match:
            return (int(match.group()), wave, entry.get("name", ""))
    return (999, str(wave or ""), entry.get("name", ""))


def map_check(root: Path, initiative: str, timestamp: str) -> dict[str, Any]:
    data = sync_map_from_packages(root, initiative, timestamp)
    summaries = {entry["name"]: read_package_summary(root, entry["name"]) for entry in data.get("packages", []) if isinstance(entry, dict) and isinstance(entry.get("name"), str)}
    package_entries = {entry["name"]: entry for entry in data.get("packages", []) if isinstance(entry, dict) and isinstance(entry.get("name"), str)}
    execution_ready: list[dict[str, Any]] = []
    prep_ready: list[dict[str, Any]] = []
    integration_ready: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    active: list[dict[str, Any]] = []
    complete: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    for name in sorted(summaries, key=lambda item: wave_sort_key(package_entries.get(item, {"name": item}))):
        summary = summaries[name]
        entry = package_entries.get(name, {"name": name})
        deps = entry.get("depends_on", summary.get("depends_on", []))
        policy = normalize_parallel_policy(entry.get("parallel_policy") or summary.get("parallel_policy"), deps if isinstance(deps, list) else [], entry.get("boundary_reason") or "")
        modification_scope = normalize_modification_scope(entry.get("modification_scope") or summary.get("modification_scope"), name, entry.get("boundary_reason"))
        open_contract_requests = open_contract_requests_for_package(data, name)
        dependency_blockers: list[dict[str, Any]] = []
        for dep in deps if isinstance(deps, list) else []:
            dep_summary = summaries.get(dep) if dep in summaries else read_package_summary(root, dep)
            if not package_dependency_complete(dep_summary):
                dependency_blockers.append({
                    "name": dep,
                    "state": dep_summary.get("state"),
                    "exists": dep_summary.get("exists"),
                    "execution_status": dep_summary.get("execution_status"),
                    "latest_checkpoint": dep_summary.get("latest_checkpoint"),
                    "latest_lead_checkpoint": dep_summary.get("latest_lead_checkpoint"),
                })

        item = {
            "name": name,
            "path": summary.get("path"),
            "wave": entry.get("wave"),
            "state": summary.get("state"),
            "prd_status": summary.get("prd_status"),
            "execution_status": summary.get("execution_status"),
            "latest_checkpoint": summary.get("latest_checkpoint"),
            "latest_lead_checkpoint": summary.get("latest_lead_checkpoint"),
            "next_action": summary.get("next_action"),
            "depends_on": deps if isinstance(deps, list) else [],
            "parallel_policy": policy,
            "modification_scope": modification_scope,
            "contract_inputs": normalize_string_list(entry.get("contract_inputs") or summary.get("contract_inputs")),
            "contract_outputs": normalize_string_list(entry.get("contract_outputs") or summary.get("contract_outputs")),
            "open_contract_requests": open_contract_requests,
            "validation": summary.get("validation"),
        }
        if not summary.get("exists"):
            item["reason"] = "package stub 缺失，需要先由 map materialize child package"
            missing.append(item)
        elif package_dependency_complete(summary):
            complete.append(item)
        elif package_active(summary):
            item["reason"] = "package 已被 claim 或正在执行"
            active.append(item)
        elif not summary.get("validation", {}).get("ok"):
            item["reason"] = "package validation 失败，需要先修复 task.json/结构问题"
            blocked.append(item)
        elif modification_scope.get("integration_role") == "lead_serial" and package_execution_assignable(summary, policy, dependency_blockers) and dependency_gate_satisfied(dependency_blockers):
            item["assignment_kind"] = "serial_integration_ready"
            item["allowed_until"] = "review"
            item["stop_before"] = None
            item["dependency_gate"] = "satisfied"
            item["reason"] = "lead_serial integration scope 已满足依赖；派发一个 serial integration worker，lead 只审查/checkpoint"
            integration_ready.append(item)
        elif modification_scope.get("integration_role") == "lead_serial" and dependency_blockers:
            item["reason"] = "lead_serial integration 需等待依赖 package 的 mainline checkpoint"
            item["blocked_by"] = dependency_blockers
            blocked.append(item)
        elif summary.get("state") in {"blocked", "needs_context", "superseded"}:
            state = summary.get("state")
            if dependency_blockers:
                item["blocked_by"] = dependency_blockers
            if state == "needs_context" and not dependency_blockers:
                item["needs_reconcile"] = True
                item["reason"] = "package state=needs_context；lead 需要在依赖 checkpoint 后重新对齐 blocker/context"
            else:
                item["reason"] = f"package 当前 state={state}"
            blocked.append(item)
        elif summary.get("state") == "reviewed" or summary.get("execution_status") == "reviewed":
            item["reason"] = "package 已 reviewed；lead 必须先 integrate 并记录 lead checkpoint，下游才能依赖"
            blocked.append(item)
        elif package_execution_assignable(summary, policy, dependency_blockers):
            item["assignment_kind"] = "execution_ready"
            item["allowed_until"] = "review"
            item["stop_before"] = None
            item["dependency_gate"] = "satisfied" if dependency_gate_satisfied(dependency_blockers) else "implementation_allowed_by_policy"
            if dependency_blockers:
                item["blocked_by"] = dependency_blockers
            execution_ready.append(item)
        elif package_prep_assignable(summary, policy, dependency_blockers):
            item["assignment_kind"] = "prep_ready"
            item["allowed_until"] = policy.get("max_phase_before_dependencies") or "task"
            item["stop_before"] = policy.get("dependency_gate_phase") or "impl"
            item["dependency_gate"] = "planning-only"
            item["blocked_by"] = dependency_blockers
            prep_ready.append(item)
        elif dependency_blockers:
            item["reason"] = "dependency gate 未满足"
            item["blocked_by"] = dependency_blockers
            blocked.append(item)
        elif package_assignable(summary):
            item["reason"] = "当前 parallel_policy 不允许执行这个 next_action"
            blocked.append(item)
        else:
            item["reason"] = "没有可派发的 next_action"
            blocked.append(item)

    return {
        "initiative": initiative,
        "map": parent_map_ref(initiative),
        "map_json": f".arbor/maps/{initiative}/map.json",
        "execution_ready": execution_ready,
        "prep_ready": prep_ready,
        "integration_ready": integration_ready,
        "ready": execution_ready + prep_ready,
        "blocked": blocked,
        "active": active,
        "complete": complete,
        "missing": missing,
    }
