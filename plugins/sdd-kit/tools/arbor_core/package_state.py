from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *
from .schema import *
from .state import add_phase_history, default_execution, ensure_execution, recalculate_package_state
from .templates import prd_template, review_template, task_template
from .validation import validate_package


def base_task_json(name: str, mode: str, title: str, timestamp: str, source_type: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "name": name,
        "title": title,
        "package_path": f".arbor/tasks/{name}",
        "created_at": timestamp,
        "updated_at": timestamp,
        "completed_at": None,
        "prd": {
            "file": "prd.md",
            "status": "draft",
            "source_type": source_type,
            "legacy_source": f".arbor/brainstorms/{name}.md" if source_type == "legacy-brainstorm" else None,
            "ready_for_task_at": None,
            "amendments": [],
        },
        "definition": {
            "task_md": "task.md",
            "frozen": False,
            "version": 0,
            "updated_at": None,
        },
        "package_sizing": {
            "status": "unchecked",
            "decision": None,
            "signals": [],
            "recommended_packages": [],
            "decided_at": None,
            "decided_by": None,
            "note": None,
        },
        "mode": mode,
        "state": "planned",
        "current_phase": "brainstorm",
        "active_task": None,
        "next_action": {
            "skill": "brainstorm",
            "task_id": None,
            "reason": "prd draft created",
        },
        "execution": default_execution(name),
        "tasks": [],
        "phase_history": [
            {
                "at": timestamp,
                "phase": "brainstorm",
                "task_id": None,
                "from": None,
                "to": "planned",
                "actor": "arbor",
                "note": "task package created",
            }
        ],
    }


def create_package(root: Path, name: str, mode: str, title: str | None, source_type: str, timestamp: str) -> dict[str, Any]:
    validate_name(name)
    if mode not in MODES:
        raise ArborError(f"Invalid mode '{mode}'. Expected one of: {', '.join(sorted(MODES))}.")
    if source_type not in {"new", "legacy-brainstorm", "ad-hoc", "map-split"}:
        raise ArborError("Invalid source type. Expected new, legacy-brainstorm, ad-hoc, or map-split.")

    title = title or name
    pkg = package_dir(root, name)
    context_dir = pkg / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    created_files: list[str] = []
    for rel, content in [
        ("prd.md", prd_template(name, title, timestamp)),
        ("task.md", task_template(name, mode, timestamp)),
        ("review.md", review_template(name, timestamp)),
        ("context/impl.jsonl", ""),
        ("context/review.jsonl", ""),
        ("context/sources.jsonl", ""),
    ]:
        if write_if_missing(pkg / rel, content):
            created_files.append(rel)

    task_path = task_json_path(pkg)
    if task_path.exists():
        data = read_json(task_path)
    else:
        data = base_task_json(name, mode, title, timestamp, source_type)
        write_json(task_path, data)
        created_files.append("task.json")

    return {"package": str(pkg), "created": created_files, "already_exists": not bool(created_files)}


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


def claim_package(root: Path, name: str, owner: str, actor: str, note: str, timestamp: str, force: bool, branch: str | None, base_branch: str | None, worktree: str | None, session: str | None) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    execution = ensure_execution(data)
    current_owner = execution.get("owner")
    if current_owner and current_owner != owner and not force:
        raise ArborError(f"Package already claimed by {current_owner}. Use --force to override.")
    execution["status"] = "claimed"
    execution["owner"] = owner
    execution["claimed_at"] = timestamp
    execution["released_at"] = None
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
    if session:
        execution["session"] = session
    if branch:
        execution["branch"]["name"] = branch
    if base_branch:
        execution["branch"]["base"] = base_branch
    if worktree:
        execution["worktree"]["path"] = worktree
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data


def release_package(root: Path, name: str, owner: str | None, actor: str, note: str, timestamp: str, force: bool) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    execution = ensure_execution(data)
    current_owner = execution.get("owner")
    if owner and current_owner and current_owner != owner and not force:
        raise ArborError(f"Package claimed by {current_owner}, not {owner}. Use --force to release.")
    execution["status"] = "unclaimed"
    execution["owner"] = None
    execution["released_at"] = timestamp
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data


def set_execution(root: Path, name: str, status: str | None, actor: str, note: str, timestamp: str, base_branch: str | None, branch: str | None, upstream: str | None, worktree: str | None, worktree_created_by: str | None) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    execution = ensure_execution(data)
    if status:
        if status not in EXECUTION_STATUSES:
            raise ArborError(f"Invalid execution status '{status}'.")
        execution["status"] = status
    if base_branch:
        execution["branch"]["base"] = base_branch
    if branch:
        execution["branch"]["name"] = branch
    if upstream:
        execution["branch"]["upstream"] = upstream
    if worktree:
        execution["worktree"]["path"] = worktree
    if worktree_created_by:
        execution["worktree"]["created_by"] = worktree_created_by
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data


def set_pr(root: Path, name: str, actor: str, note: str, timestamp: str, url: str | None, number: int | None, state: str | None) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    execution = ensure_execution(data)
    pr = execution.setdefault("pr", {"url": None, "number": None, "state": "none"})
    if url:
        pr["url"] = url
    if number is not None:
        pr["number"] = number
    if state:
        if state not in PR_STATES:
            raise ArborError(f"Invalid PR state '{state}'.")
        pr["state"] = state
        if state == "open":
            execution["status"] = "pr_open"
        elif state == "merged":
            execution["status"] = "merged"
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data


def record_checkpoint(root: Path, name: str, kind: str, sha: str, branch: str | None, base_sha: str | None, actor: str, note: str, timestamp: str) -> dict[str, Any]:
    if kind not in CHECKPOINT_KINDS:
        raise ArborError(f"Invalid checkpoint kind '{kind}'.")
    if not sha:
        raise ArborError("Checkpoint sha is required.")
    pkg, data = load_package(root, name)
    execution = ensure_execution(data)
    execution.setdefault("checkpoints", []).append(
        {
            "kind": kind,
            "sha": sha,
            "branch": branch,
            "base_sha": base_sha,
            "at": timestamp,
            "actor": actor,
            "note": note,
        }
    )
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data


def record_agent(root: Path, name: str, role: str, agent_name: str, status: str, summary: str, actor: str, note: str, timestamp: str, task_id: str | None) -> dict[str, Any]:
    if role not in AGENT_RECORD_ROLES:
        raise ArborError(f"Invalid agent role '{role}'.")
    if status not in AGENT_RECORD_STATUSES:
        raise ArborError(f"Invalid agent status '{status}'.")
    pkg, data = load_package(root, name)
    if task_id:
        find_task(data, task_id)
    execution = ensure_execution(data)
    execution.setdefault("agents", []).append(
        {
            "role": role,
            "name": agent_name,
            "status": status,
            "task_id": task_id,
            "at": timestamp,
            "summary": summary,
            "actor": actor,
            "note": note,
        }
    )
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
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
        data["next_action"] = {"skill": "map", "task_id": None, "reason": "package graph required before task decomposition"}
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
        data["next_action"] = {"skill": "task", "task_id": None, "reason": "executable package PRD ready for task decomposition"}
    elif status in {"draft", "revising"}:
        data["current_phase"] = "brainstorm"
        data["next_action"] = {"skill": "brainstorm", "task_id": None, "reason": "prd is not ready for task decomposition"}
    elif status == "superseded":
        data["state"] = "superseded"
        data["next_action"] = {"skill": "user", "task_id": None, "reason": "prd was superseded"}
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
        data["next_action"] = {"skill": "user", "task_id": None, "reason": "task definition frozen but no ready tasks"}
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


def add_context(root: Path, name: str, context_type: str, task_id: str | None, kind: str | None, summary: str | None, source: str | None, actor: str, timestamp: str, source_id: str | None, source_type: str | None, location: str | None, title: str | None, why: str | None) -> dict[str, Any]:
    if context_type not in CONTEXT_TYPES:
        raise ArborError(f"Invalid context type '{context_type}'.")
    pkg, data = load_package(root, name)
    if task_id:
        find_task(data, task_id)
    path = pkg / "context" / f"{context_type}.jsonl"
    if context_type == "sources":
        if not all([source_id, source_type, location, title, why]):
            raise ArborError("sources context requires --source-id, --source-type, --location, --title, and --why.")
        if source_type not in SOURCE_TYPES:
            raise ArborError(f"Invalid source type '{source_type}'.")
        entry = {
            "id": source_id,
            "type": source_type,
            "location": location,
            "title": title,
            "why_it_matters": why,
        }
    else:
        if not summary:
            raise ArborError("impl/review context requires --summary.")
        if kind and kind not in CONTEXT_KINDS:
            raise ArborError(f"Invalid context kind '{kind}'.")
        entry = {
            "at": timestamp,
            "actor": actor,
            "task_id": task_id,
            "kind": kind or "note",
            "source": source,
            "summary": summary,
        }
    append_jsonl(path, entry)
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return entry


def list_packages(root: Path) -> list[dict[str, Any]]:
    root_dir = tasks_root(root)
    if not root_dir.exists():
        return []
    result: list[dict[str, Any]] = []
    for pkg in sorted(path for path in root_dir.iterdir() if path.is_dir()):
        task_path = pkg / "task.json"
        if not task_path.exists():
            continue
        try:
            data = read_json(task_path)
        except ArborError:
            continue
        tasks = data.get("tasks", []) if isinstance(data.get("tasks"), list) else []
        execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
        branch = execution.get("branch") if isinstance(execution.get("branch"), dict) else {}
        worktree = execution.get("worktree") if isinstance(execution.get("worktree"), dict) else {}
        pr = execution.get("pr") if isinstance(execution.get("pr"), dict) else {}
        sizing = data.get("package_sizing") if isinstance(data.get("package_sizing"), dict) else {}
        result.append(
            {
                "name": pkg.name,
                "state": data.get("state"),
                "current_phase": data.get("current_phase"),
                "package_sizing": sizing.get("status"),
                "active_task": data.get("active_task"),
                "next_action": data.get("next_action"),
                "execution_status": execution.get("status"),
                "execution_owner": execution.get("owner"),
                "branch": branch.get("name"),
                "worktree": worktree.get("path"),
                "pr": pr.get("url") or pr.get("number"),
                "task_count": len(tasks),
                "ready_count": sum(1 for task in tasks if task.get("state") == "ready"),
                "blocked_count": sum(1 for task in tasks if task.get("state") in {"blocked", "needs_context"}),
            }
        )
    return result


def show_package(root: Path, name: str) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    errors = validate_package(root, name)
    tasks = data.get("tasks", []) if isinstance(data.get("tasks"), list) else []
    return {
        "name": name,
        "package": str(pkg),
        "state": data.get("state"),
        "current_phase": data.get("current_phase"),
        "active_task": data.get("active_task"),
        "next_action": data.get("next_action"),
        "execution": data.get("execution"),
        "package_sizing": data.get("package_sizing"),
        "prd": data.get("prd"),
        "tasks": tasks,
        "validation": {"ok": not errors, "errors": errors},
    }