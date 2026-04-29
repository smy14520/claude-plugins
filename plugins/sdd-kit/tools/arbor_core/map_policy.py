from __future__ import annotations

from typing import Any

from .schema import *


def default_parallel_policy(depends_on: list[str], reason: str) -> dict[str, Any]:
    if depends_on:
        return {
            "independence": "contract_dependent",
            "can_prepare_without_dependencies": True,
            "can_implement_without_dependencies": False,
            "max_phase_before_dependencies": "task",
            "dependency_gate_phase": "impl",
            "reason": reason or "存在 package 依赖；依赖未完成前只允许先做 package-local brainstorm/task，进入 impl 前必须满足依赖 gate",
        }
    return {
        "independence": "independent",
        "can_prepare_without_dependencies": True,
        "can_implement_without_dependencies": True,
        "max_phase_before_dependencies": "review",
        "dependency_gate_phase": "none",
        "reason": reason or "没有 package 依赖；可独立推进到 review",
    }


def normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def normalize_modification_scope(value: Any, name: str, boundary_reason: str | None) -> dict[str, Any]:
    fallback = boundary_reason or name
    scope = {
        "summary": fallback,
        "owned_paths": [],
        "shared_paths": [],
        "integration_role": "package",
        "reason": boundary_reason or "该 package 边界由 map 声明",
    }
    if not isinstance(value, dict):
        return scope
    summary = value.get("summary")
    if isinstance(summary, str) and summary.strip():
        scope["summary"] = summary.strip()
    for field in ["owned_paths", "shared_paths"]:
        scope[field] = normalize_string_list(value.get(field))
    role = value.get("integration_role")
    if role in INTEGRATION_ROLES:
        scope["integration_role"] = role
    reason = value.get("reason")
    if isinstance(reason, str) and reason.strip():
        scope["reason"] = reason.strip()
    return scope


def normalize_parallel_policy(value: Any, depends_on: list[str], boundary_reason: str) -> dict[str, Any]:
    default = default_parallel_policy(depends_on, boundary_reason)
    if not isinstance(value, dict):
        return default
    policy = default.copy()
    independence = value.get("independence")
    if independence in PARALLEL_INDEPENDENCE:
        policy["independence"] = independence
    can_prepare = value.get("can_prepare_without_dependencies")
    if isinstance(can_prepare, bool):
        policy["can_prepare_without_dependencies"] = can_prepare
    can_implement = value.get("can_implement_without_dependencies")
    if isinstance(can_implement, bool):
        policy["can_implement_without_dependencies"] = can_implement
    max_phase = value.get("max_phase_before_dependencies")
    if max_phase in PARALLEL_MAX_PHASES:
        policy["max_phase_before_dependencies"] = max_phase
    gate_phase = value.get("dependency_gate_phase")
    if gate_phase in PARALLEL_GATE_PHASES:
        policy["dependency_gate_phase"] = gate_phase
    reason = value.get("reason")
    if isinstance(reason, str) and reason:
        policy["reason"] = reason
    if policy.get("independence") == "independent":
        policy["can_prepare_without_dependencies"] = True
        policy["can_implement_without_dependencies"] = True
        policy["max_phase_before_dependencies"] = "review"
        policy["dependency_gate_phase"] = "none"
    elif policy.get("independence") == "hard_dependent":
        policy["can_prepare_without_dependencies"] = False
        policy["can_implement_without_dependencies"] = False
    return policy
