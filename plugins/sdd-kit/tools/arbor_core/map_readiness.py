from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .fs import *
from .map_contracts import contract_blockers_for_consumer, open_contract_requests_for_package
from .map_sync import read_package_summary, sync_map_from_packages


def package_dependency_complete(summary: dict[str, Any]) -> bool:
    return summary.get("state") == "completed" or summary.get("execution_status") == "merged" or summary.get("pr_state") == "merged"


def package_active(summary: dict[str, Any]) -> bool:
    return summary.get("state") == "in_progress" or summary.get("execution_status") in {"in_progress", "pr_open"}


def package_assignable(summary: dict[str, Any]) -> bool:
    if not summary.get("exists"):
        return False
    if not summary.get("validation", {}).get("ok"):
        return False
    if package_dependency_complete(summary) or package_active(summary):
        return False
    if summary.get("state") in {"blocked", "needs_context", "superseded", "reviewed"}:
        return False
    next_action = summary.get("next_action") if isinstance(summary.get("next_action"), dict) else {}
    return next_action.get("skill") in {"brainstorm", "task", "impl", "review"}


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
    ready: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    active: list[dict[str, Any]] = []
    complete: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    for name in sorted(summaries, key=lambda item: wave_sort_key(package_entries.get(item, {"name": item}))):
        summary = summaries[name]
        entry = package_entries.get(name, {"name": name})
        deps = entry.get("depends_on", summary.get("depends_on", []))
        open_contract_requests = open_contract_requests_for_package(data, name)
        contract_blockers = contract_blockers_for_consumer(data, name)
        dependency_blockers: list[dict[str, Any]] = []
        for dep in deps if isinstance(deps, list) else []:
            dep_summary = summaries.get(dep) if dep in summaries else read_package_summary(root, dep)
            if not package_dependency_complete(dep_summary):
                dependency_blockers.append({
                    "name": dep,
                    "state": dep_summary.get("state"),
                    "exists": dep_summary.get("exists"),
                    "execution_status": dep_summary.get("execution_status"),
                })

        item = {
            "name": name,
            "path": summary.get("path"),
            "wave": entry.get("wave"),
            "state": summary.get("state"),
            "prd_status": summary.get("prd_status"),
            "execution_status": summary.get("execution_status"),
            "next_action": summary.get("next_action"),
            "depends_on": deps if isinstance(deps, list) else [],
            "open_contract_requests": open_contract_requests,
            "contract_blockers": contract_blockers,
            "validation": summary.get("validation"),
        }
        if not summary.get("exists"):
            item["reason"] = "package stub 缺失，需要先由 map materialize child package"
            missing.append(item)
        elif package_dependency_complete(summary):
            complete.append(item)
        elif package_active(summary):
            item["reason"] = "package 正在执行或已有 open PR"
            active.append(item)
        elif not summary.get("validation", {}).get("ok"):
            item["reason"] = "package validation 失败，需要先修复 task.json/结构问题"
            blocked.append(item)
        elif summary.get("state") in {"blocked", "needs_context", "superseded"}:
            state = summary.get("state")
            if dependency_blockers:
                item["blocked_by"] = dependency_blockers
            item["reason"] = f"package 当前 state={state}"
            blocked.append(item)
        elif summary.get("state") == "reviewed":
            item["reason"] = "package 已 reviewed；需要显式标记 completed 或合并 PR 后下游才能依赖"
            blocked.append(item)
        elif dependency_blockers:
            item["reason"] = "dependency 未完成"
            item["blocked_by"] = dependency_blockers
            blocked.append(item)
        elif contract_blockers:
            item["reason"] = "contract request 未解决"
            blocked.append(item)
        elif package_assignable(summary):
            ready.append(item)
        else:
            item["reason"] = "没有可执行的 next_action"
            blocked.append(item)

    return {
        "initiative": initiative,
        "map": parent_map_ref(initiative),
        "map_json": f".arbor/maps/{initiative}/map.json",
        "ready": ready,
        "blocked": blocked,
        "active": active,
        "complete": complete,
        "missing": missing,
    }
