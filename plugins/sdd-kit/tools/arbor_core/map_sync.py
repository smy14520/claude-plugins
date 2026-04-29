from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *
from .state import ensure_execution
from .validation import validate_package
from .map_model import ensure_map_workspace


def read_package_summary(root: Path, name: str) -> dict[str, Any]:
    pkg = package_dir(root, name)
    if not (pkg / "task.json").exists():
        return {
            "name": name,
            "path": f".arbor/tasks/{name}",
            "exists": False,
            "validation": {"ok": False, "errors": ["package task.json missing"]},
        }
    data = read_json(pkg / "task.json")
    errors = validate_package(root, name)
    tasks = data.get("tasks", []) if isinstance(data.get("tasks"), list) else []
    execution = ensure_execution(data)
    prd = data.get("prd") if isinstance(data.get("prd"), dict) else {}
    sizing = data.get("package_sizing") if isinstance(data.get("package_sizing"), dict) else {}
    next_action = data.get("next_action") if isinstance(data.get("next_action"), dict) else {}
    return {
        "name": name,
        "title": data.get("title") or name,
        "path": f".arbor/tasks/{name}",
        "exists": True,
        "state": data.get("state"),
        "current_phase": data.get("current_phase"),
        "prd_status": prd.get("status"),
        "package_sizing": sizing.get("status"),
        "depends_on": sizing.get("depends_on_packages", []) if isinstance(sizing.get("depends_on_packages", []), list) else [],
        "parent_initiative": prd.get("parent_initiative") or sizing.get("parent_initiative"),
        "next_action": {"skill": next_action.get("skill"), "task_id": next_action.get("task_id"), "reason": next_action.get("reason")},
        "execution_status": execution.get("status"),
        "execution_owner": execution.get("owner"),
        "pr_state": execution.get("pr", {}).get("state") if isinstance(execution.get("pr"), dict) else None,
        "task_count": len(tasks),
        "ready_count": sum(1 for task in tasks if task.get("state") == "ready"),
        "blocked_count": sum(1 for task in tasks if task.get("state") in {"blocked", "needs_context"}),
        "validation": {"ok": not errors, "errors": errors},
    }


def map_package_names(root: Path, initiative: str, data: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for entry in data.get("packages", []) if isinstance(data.get("packages"), list) else []:
        if isinstance(entry, dict) and isinstance(entry.get("name"), str) and entry["name"] not in names:
            names.append(entry["name"])
    root_dir = tasks_root(root)
    if root_dir.exists():
        for pkg in sorted(path for path in root_dir.iterdir() if path.is_dir()):
            task_path = pkg / "task.json"
            if not task_path.exists():
                continue
            try:
                task_data = read_json(task_path)
            except ArborError:
                continue
            prd = task_data.get("prd") if isinstance(task_data.get("prd"), dict) else {}
            sizing = task_data.get("package_sizing") if isinstance(task_data.get("package_sizing"), dict) else {}
            if initiative in {prd.get("parent_initiative"), sizing.get("parent_initiative")} and pkg.name not in names:
                names.append(pkg.name)
    return names


def sync_map_from_packages(root: Path, initiative: str, timestamp: str) -> dict[str, Any]:
    ensure_map_workspace(root, initiative, timestamp)
    json_path = map_json_path(root, initiative)
    data = read_json(json_path)
    existing_entries = data.get("packages", []) if isinstance(data.get("packages"), list) else []
    by_name: dict[str, dict[str, Any]] = {entry.get("name"): entry for entry in existing_entries if isinstance(entry, dict) and isinstance(entry.get("name"), str)}
    names = map_package_names(root, initiative, data)
    synced: list[dict[str, Any]] = []
    for name in names:
        entry = by_name.get(name, {"name": name, "path": f".arbor/tasks/{name}"})
        summary = read_package_summary(root, name)
        for legacy_key in ["parallel_policy", "modification_scope", "contract_inputs", "contract_outputs", "latest_checkpoint", "latest_lead_checkpoint"]:
            entry.pop(legacy_key, None)
        if summary.get("exists"):
            entry["title"] = summary.get("title") or entry.get("title") or name
            entry["path"] = summary.get("path")
            entry["materialized"] = True
            entry["depends_on"] = summary.get("depends_on", entry.get("depends_on", []))
            entry["prd_status"] = summary.get("prd_status")
            entry["task_state"] = summary.get("state")
            entry["current_phase"] = summary.get("current_phase")
            entry["execution_status"] = summary.get("execution_status")
            entry["execution_owner"] = summary.get("execution_owner")
            entry["next_action"] = summary.get("next_action")
            entry["task_count"] = summary.get("task_count")
            entry["ready_count"] = summary.get("ready_count")
            entry["blocked_count"] = summary.get("blocked_count")
            entry["validation"] = summary.get("validation")
        else:
            entry.setdefault("path", f".arbor/tasks/{name}")
            entry["materialized"] = False
            entry["validation"] = summary.get("validation")
        entry.setdefault("wave", None)
        entry.setdefault("boundary_reason", None)
        entry["updated_at"] = timestamp
        synced.append(entry)
    data["packages"] = synced
    if not isinstance(data.get("contract_requests"), list):
        data["contract_requests"] = []
    data["updated_at"] = timestamp
    write_json(json_path, data)
    return data
