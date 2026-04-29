from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *
from .schema import *
from .state import add_phase_history, recalculate_package_state


def update_task_status(root: Path, name: str, task_id: str | None, state: str, actor: str, note: str, timestamp: str) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    if task_id:
        if state not in TASK_STATES:
            raise ArborError(f"Invalid task state '{state}'.")
        task = find_task(data, task_id)
        old = task.get("state")
        task["state"] = state
        task["updated_at"] = timestamp
        if state == "in_progress":
            task["attempts"] = int(task.get("attempts") or 0) + 1
        elif state in {"done", "done_with_concerns"}:
            task["last_impl_result"] = {
                "state": "DONE" if state == "done" else "DONE_WITH_CONCERNS",
                "at": timestamp,
                "summary": note,
                "acceptance": [],
                "concerns": [],
            }
        elif state == "needs_context":
            task["last_impl_result"] = {
                "state": "NEEDS_CONTEXT",
                "at": timestamp,
                "summary": note,
                "acceptance": [],
                "concerns": [],
            }
        elif state == "blocked":
            task["last_impl_result"] = {
                "state": "BLOCKED",
                "at": timestamp,
                "summary": note,
                "acceptance": [],
                "concerns": [],
            }
        elif state in {"approved", "approved_with_notes"}:
            task["last_review_result"] = {
                "state": "APPROVED" if state == "approved" else "APPROVED_WITH_NOTES",
                "at": timestamp,
                "summary": note,
                "evidence": [],
                "notes": [],
            }
        elif state == "needs_rework":
            task["last_review_result"] = {
                "state": "NEEDS_REWORK",
                "at": timestamp,
                "summary": note,
                "evidence": [],
                "notes": [],
            }
        elif state == "brainstorm_drift":
            task["last_review_result"] = {
                "state": "BRAINSTORM_DRIFT",
                "at": timestamp,
                "summary": note,
                "evidence": [],
                "notes": [],
            }
        elif state == "skipped":
            if data.get("active_task") == task_id:
                data["active_task"] = None
        recalculate_package_state(data)
        add_phase_history(data, timestamp, data.get("current_phase", "task"), task_id, old, state, actor, note)
    else:
        if state not in TOP_LEVEL_STATES:
            raise ArborError(f"Invalid top-level state '{state}'.")
        old = data.get("state")
        data["state"] = state
        add_phase_history(data, timestamp, data.get("current_phase", "task"), None, old, state, actor, note)
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data


def infer_sizing_phase(data: dict[str, Any], actor: str, phase: str | None) -> str:
    if phase:
        if phase not in PHASES:
            raise ArborError(f"Invalid package sizing phase '{phase}'.")
        return phase
    if actor in {"brainstorm", "map", "task"}:
        return actor
    current_phase = data.get("current_phase")
    return current_phase if current_phase in PHASES else "brainstorm"


def set_package_sizing(root: Path, name: str, status: str, actor: str, note: str, timestamp: str, decision: str | None, signals: list[str], recommended_packages: list[str], phase: str | None = None) -> dict[str, Any]:
    if status not in PACKAGE_SIZING_STATUSES:
        raise ArborError(f"Invalid package sizing status '{status}'.")
    pkg, data = load_package(root, name)
    sizing_phase = infer_sizing_phase(data, actor, phase)
    recommended: list[dict[str, Any]] = []
    for raw in recommended_packages:
        parts = raw.split(":", 2)
        package_name = parts[0].strip()
        if not NAME_RE.match(package_name):
            raise ArborError(f"Invalid recommended package name '{package_name}'.")
        depends_on = [item.strip() for item in parts[1].split(",") if item.strip()] if len(parts) >= 2 and parts[1].strip() else []
        for dep in depends_on:
            if not NAME_RE.match(dep):
                raise ArborError(f"Invalid recommended package dependency '{dep}'.")
        reason = parts[2].strip() if len(parts) == 3 else ""
        recommended.append({"name": package_name, "depends_on": depends_on, "reason": reason})
    old = data.get("package_sizing", {}).get("status") if isinstance(data.get("package_sizing"), dict) else None
    data["package_sizing"] = {
        "status": status,
        "decision": decision,
        "signals": signals,
        "recommended_packages": recommended,
        "decided_at": timestamp,
        "decided_by": actor,
        "note": note,
    }
    if status == "split_recommended":
        data["current_phase"] = "map"
        data["next_action"] = {"skill": "map", "task_id": None, "reason": "进入 task decomposition 前需要先由 map 明确 package graph"}
    data["updated_at"] = timestamp
    add_phase_history(data, timestamp, sizing_phase, None, old, f"package_sizing:{status}", actor, note)
    save_package(pkg, data)
    return data


def update_phase(root: Path, name: str, phase: str, actor: str, note: str, task_id: str | None, timestamp: str) -> dict[str, Any]:
    if phase not in PHASES:
        raise ArborError(f"Invalid phase '{phase}'.")
    pkg, data = load_package(root, name)
    if task_id:
        find_task(data, task_id)
    old = data.get("current_phase")
    data["current_phase"] = phase
    data["updated_at"] = timestamp
    add_phase_history(data, timestamp, phase, task_id, old, phase, actor, note)
    save_package(pkg, data)
    return data


def update_prd_status(root: Path, name: str, status: str, actor: str, note: str, timestamp: str) -> dict[str, Any]:
    if status not in {"draft", "ready-for-task", "revising", "superseded"}:
        raise ArborError(f"Invalid PRD status '{status}'.")
    pkg, data = load_package(root, name)
    prd = data.setdefault("prd", {})
    old = prd.get("status")
    if status == "ready-for-task":
        sizing = data.get("package_sizing") if isinstance(data.get("package_sizing"), dict) else {}
        sizing_status = sizing.get("status")
        if sizing_status == "unchecked":
            raise ArborError("Cannot mark PRD ready-for-task before brainstorm/map records package sizing as fits_package or split_applied.")
        if sizing_status == "split_recommended":
            raise ArborError("Cannot mark PRD ready-for-task while package sizing recommends a map/package graph split.")
        if sizing_status not in {"fits_package", "split_applied"}:
            raise ArborError("Cannot mark PRD ready-for-task without resolved package sizing: expected fits_package or split_applied.")
    prd["status"] = status
    if status == "ready-for-task":
        prd["ready_for_task_at"] = timestamp
        data["state"] = "ready"
        data["current_phase"] = "task"
        data["next_action"] = {"skill": "task", "task_id": None, "reason": "executable package PRD 已就绪，可进入 task decomposition"}
    elif status in {"draft", "revising"}:
        data["current_phase"] = "brainstorm"
        data["next_action"] = {"skill": "brainstorm", "task_id": None, "reason": "PRD 尚未就绪，不能进入 task decomposition"}
    elif status == "superseded":
        data["state"] = "superseded"
        data["next_action"] = {"skill": "user", "task_id": None, "reason": "PRD 已被 superseded，需要用户确认下一步"}
    data["updated_at"] = timestamp
    add_phase_history(data, timestamp, data.get("current_phase", "brainstorm"), None, old, status, actor, note)
    save_package(pkg, data)
    return data


def freeze_definition(root: Path, name: str, actor: str, note: str, timestamp: str) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    definition = data.setdefault("definition", {})
    old = "frozen" if definition.get("frozen") else "draft"
    definition["task_md"] = definition.get("task_md") or "task.md"
    definition["frozen"] = True
    definition["version"] = int(definition.get("version") or 0) + 1
    definition["updated_at"] = timestamp
    data["state"] = "ready"
    data["current_phase"] = "task"
    recalculate_package_state(data)
    if not data.get("tasks"):
        data["next_action"] = {"skill": "user", "task_id": None, "reason": "task definition 已冻结，但没有 ready tasks"}
    data["updated_at"] = timestamp
    add_phase_history(data, timestamp, "task", None, old, "frozen", actor, note)
    save_package(pkg, data)
    return data


def find_task(data: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            return task
    raise ArborError(f"Unknown task id: {task_id}")


def amendment_ids(data: dict[str, Any]) -> set[str]:
    prd = data.setdefault("prd", {})
    amendments = prd.setdefault("amendments", [])
    if not isinstance(amendments, list):
        raise ArborError("prd.amendments must be an array.")
    return {item.get("id") for item in amendments if isinstance(item, dict) and isinstance(item.get("id"), str)}


def next_amendment_id(data: dict[str, Any]) -> str:
    existing = amendment_ids(data)
    index = 1
    while True:
        candidate = f"AMD-{index:03d}"
        if candidate not in existing:
            return candidate
        index += 1


def add_amendment(root: Path, name: str, amendment_id: str | None, title: str, wrong: str, correct: str, affects_tasks: list[str], source: str, actor: str, timestamp: str) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    prd = data.setdefault("prd", {})
    amendments = prd.setdefault("amendments", [])
    if not isinstance(amendments, list):
        raise ArborError("prd.amendments must be an array.")
    amendment_id = amendment_id or next_amendment_id(data)
    if not AMENDMENT_ID_RE.match(amendment_id):
        raise ArborError(f"Invalid amendment id '{amendment_id}'. Use AMD-001 format.")
    if amendment_id in amendment_ids(data):
        raise ArborError(f"Amendment already exists: {amendment_id}")
    existing_task_ids = {task.get("id") for task in data.get("tasks", []) if isinstance(task, dict)}
    for task_id in affects_tasks:
        if not TASK_ID_RE.match(task_id):
            raise ArborError(f"Invalid affected task id '{task_id}'. Use T-001 format.")
        if task_id not in existing_task_ids:
            raise ArborError(f"Affected task does not exist: {task_id}")
    amendments.append({
        "id": amendment_id,
        "title": title,
        "wrong": wrong,
        "correct": correct,
        "affects_tasks": affects_tasks,
        "source": source,
        "created_at": timestamp,
        "created_by": actor,
    })
    prd["status"] = "ready-for-task"
    prd["ready_for_task_at"] = timestamp
    data["state"] = "ready"
    data["current_phase"] = "task"
    data["active_task"] = None
    data["next_action"] = {"skill": "task", "task_id": None, "reason": f"amendment {amendment_id} ready for task decomposition"}
    data["updated_at"] = timestamp
    add_phase_history(data, timestamp, "brainstorm", None, None, f"amendment:{amendment_id}", actor, title)
    save_package(pkg, data)
    return data


def add_child(root: Path, name: str, task_id: str, title: str, milestone: str, role: str, depends_on: list[str], ready: bool, blockers: list[str], timestamp: str, source_amendment: str | None = None, corrects: list[str] | None = None) -> dict[str, Any]:
    if not TASK_ID_RE.match(task_id):
        raise ArborError(f"Invalid task id '{task_id}'. Use T-001 format.")
    if role not in ROLES:
        raise ArborError(f"Invalid role '{role}'.")
    pkg, data = load_package(root, name)
    sizing = data.get("package_sizing") if isinstance(data.get("package_sizing"), dict) else {}
    if sizing.get("status") == "unchecked":
        raise ArborError("Package boundary sizing must be resolved by brainstorm/map before adding T-xxx tasks: expected fits_package or split_applied.")
    if sizing.get("status") == "split_recommended":
        raise ArborError("Package sizing routes this input to map; create the package graph and child package PRDs before adding package-local T-xxx tasks.")
    if sizing.get("status") not in {"fits_package", "split_applied"}:
        raise ArborError("Cannot add T-xxx tasks without resolved package sizing: expected fits_package or split_applied.")
    tasks = data.setdefault("tasks", [])
    existing_ids = {task.get("id") for task in tasks}
    if task_id in existing_ids:
        raise ArborError(f"Task already exists: {task_id}")
    for dep in depends_on:
        if dep and dep not in existing_ids:
            raise ArborError(f"Dependency does not exist: {dep}")
    if source_amendment:
        if not AMENDMENT_ID_RE.match(source_amendment):
            raise ArborError(f"Invalid source amendment '{source_amendment}'. Use AMD-001 format.")
        if source_amendment not in amendment_ids(data):
            raise ArborError(f"Unknown source amendment: {source_amendment}")
    corrects = corrects or []
    for corrected in corrects:
        if not TASK_ID_RE.match(corrected):
            raise ArborError(f"Invalid corrected task id '{corrected}'. Use T-001 format.")
        if corrected == task_id:
            raise ArborError("Task cannot correct itself.")
        if corrected not in existing_ids:
            raise ArborError(f"Corrected task does not exist: {corrected}")
    state = "ready" if ready and not blockers else "needs_context"
    task = {
        "id": task_id,
        "title": title,
        "milestone": milestone,
        "role": role,
        "state": state,
        "depends_on": [dep for dep in depends_on if dep],
        "ready": ready and not blockers,
        "blockers": blockers,
        "attempts": 0,
        "last_impl_result": None,
        "last_review_result": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    if source_amendment:
        task["source_amendment"] = source_amendment
    if corrects:
        task["corrects"] = corrects
    tasks.append(task)
    data["updated_at"] = timestamp
    recalculate_package_state(data)
    add_phase_history(data, timestamp, data.get("current_phase", "task"), task_id, None, state, "task", "child task added")
    save_package(pkg, data)
    return data
