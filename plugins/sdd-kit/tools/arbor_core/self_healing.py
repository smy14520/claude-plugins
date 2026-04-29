from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *
from .map_contracts import contract_requests_list, next_contract_request_id
from .map_dispatch import assignment_context, normalize_worktree_root_ref, resolve_worktree_ref, worker_name_for_package
from .map_model import ensure_map_workspace
from .map_policy import normalize_modification_scope, normalize_parallel_policy, normalize_string_list
from .map_readiness import map_check, package_dependency_complete
from .map_runtime import append_parallel_runtime_event
from .map_sync import read_package_summary, sync_map_from_packages
from .package_artifacts import import_package_artifacts, safe_artifact_ref
from .package_context import add_context, repair_context_jsonl
from .package_execution import record_checkpoint, release_package
from .package_lifecycle import find_task
from .parallel_scheduler import parallel_schedule
from .schema import CHECKPOINT_KINDS, CONTEXT_KINDS, CONTEXT_TYPES, CONTRACT_REQUEST_STATUSES, SOURCE_TYPES
from .validation import validate_package


def _assignment_package(assignment_id: str) -> str:
    parts = assignment_id.split(":")
    if len(parts) < 3 or not parts[1]:
        raise ArborError("Invalid assignment id; expected round:<package>:<assignment_kind>.")
    validate_name(parts[1])
    return parts[1]


def _assignment_kind(assignment_id: str) -> str:
    parts = assignment_id.split(":")
    if len(parts) < 3 or not parts[2]:
        raise ArborError("Invalid assignment id; expected round:<package>:<assignment_kind>.")
    return parts[2]


def ensure_assignment_matches(package: str, assignment_id: str) -> None:
    assigned_package = _assignment_package(assignment_id)
    if assigned_package != package:
        raise ArborError(f"Assignment id package mismatch: {assigned_package} != {package}.")


def _candidate_from_active_claim(root: Path, initiative: str, package: str, assignment_id: str, check: dict[str, Any]) -> dict[str, Any] | None:
    kind = _assignment_kind(assignment_id)
    _, task_data = load_package(root, package)
    execution = task_data.get("execution") if isinstance(task_data.get("execution"), dict) else {}
    if execution.get("session") != assignment_id:
        return None
    active_item = next((item for item in check.get("active", []) if isinstance(item, dict) and item.get("name") == package), None)
    if active_item is None:
        return None
    map_data = sync_map_from_packages(root, initiative, execution.get("updated_at") or "")
    entry = next((item for item in map_data.get("packages", []) if isinstance(item, dict) and item.get("name") == package), {})
    summary = read_package_summary(root, package)
    deps = entry.get("depends_on", summary.get("depends_on", []))
    policy = normalize_parallel_policy(entry.get("parallel_policy") or summary.get("parallel_policy"), deps if isinstance(deps, list) else [], entry.get("boundary_reason") or "")
    scope = normalize_modification_scope(entry.get("modification_scope") or summary.get("modification_scope"), package, entry.get("boundary_reason"))
    if kind == "serial_integration_ready" and scope.get("integration_role") != "lead_serial":
        raise ArborError("Claimed assignment kind is serial_integration_ready but package is not lead_serial.")
    if kind not in {"execution_ready", "prep_ready", "serial_integration_ready"}:
        raise ArborError(f"Unsupported assignment kind '{kind}'.")
    active_item["assignment_kind"] = kind
    active_item["parallel_policy"] = policy
    active_item["modification_scope"] = scope
    active_item["contract_inputs"] = normalize_string_list(entry.get("contract_inputs") or summary.get("contract_inputs"))
    active_item["contract_outputs"] = normalize_string_list(entry.get("contract_outputs") or summary.get("contract_outputs"))
    active_item["allowed_until"] = "review"
    active_item["stop_before"] = policy.get("dependency_gate_phase") if kind == "prep_ready" else None
    active_item["dependency_gate"] = "active_claim"
    active_item["next_action"] = summary.get("next_action")
    return active_item


def export_worker_context(root: Path, initiative: str, package: str, assignment_id: str, worktree_root_ref: str | None, actor: str, timestamp: str) -> dict[str, Any]:
    validate_name(initiative)
    validate_name(package)
    ensure_assignment_matches(package, assignment_id)
    normalized_worktree_root_ref = normalize_worktree_root_ref(root, worktree_root_ref)
    check = map_check(root, initiative, timestamp)
    candidate = None
    for key in ["execution_ready", "prep_ready", "integration_ready"]:
        for item in check.get(key, []):
            if isinstance(item, dict) and item.get("name") == package:
                candidate = item
                break
        if candidate is not None:
            break
    if candidate is None:
        candidate = _candidate_from_active_claim(root, initiative, package, assignment_id, check)
    if candidate is None:
        raise ArborError(f"Package '{package}' is not currently assignable or claimed for assignment '{assignment_id}' in initiative '{initiative}'.")
    if candidate.get("assignment_kind") != _assignment_kind(assignment_id):
        raise ArborError(f"Assignment id kind mismatch: {_assignment_kind(assignment_id)} != {candidate.get('assignment_kind')}.")
    round_id = assignment_id.split(":", 1)[0]
    assignment = assignment_context(root, initiative, candidate, check, round_id, normalized_worktree_root_ref)
    if assignment["assignment_id"] != assignment_id:
        raise ArborError(f"Assignment id mismatch: generated {assignment['assignment_id']} != {assignment_id}.")
    record = append_parallel_runtime_event(
        root,
        initiative,
        "self_heal_done",
        actor,
        timestamp,
        package=package,
        assignment_id=assignment_id,
        worker=assignment.get("worker_name"),
        reason="export_worker_context regenerated worker dispatch packet",
        detail={"action": "export_worker_context", "context_files": assignment["context_files"]},
    )
    return {"initiative": initiative, "package": package, "assignment": assignment, "runtime_event": record}


def reconcile_package(root: Path, initiative: str, package: str, assignment_id: str | None, worker: str | None, actor: str, timestamp: str, release_stale_claim: bool = False) -> dict[str, Any]:
    validate_name(initiative)
    validate_name(package)
    if assignment_id is not None:
        ensure_assignment_matches(package, assignment_id)
    data = sync_map_from_packages(root, initiative, timestamp)
    package_names = {entry.get("name") for entry in data.get("packages", []) if isinstance(entry, dict)}
    if package not in package_names:
        raise ArborError(f"Unknown package '{package}' for initiative '{initiative}'.")
    pkg, task_data = load_package(root, package)
    execution = task_data.get("execution") if isinstance(task_data.get("execution"), dict) else {}
    if worker and execution.get("owner") and execution.get("owner") != worker and not release_stale_claim:
        return {"initiative": initiative, "package": package, "status": "stand_down", "reason": f"package claimed by {execution.get('owner')}, not {worker}"}

    changed: list[str] = []
    check = map_check(root, initiative, timestamp)
    item = next((entry for entry in check.get("blocked", []) if isinstance(entry, dict) and entry.get("name") == package), None)
    if item and item.get("needs_reconcile"):
        tasks = task_data.get("tasks", []) if isinstance(task_data.get("tasks"), list) else []
        for task in tasks:
            if isinstance(task, dict) and task.get("state") == "needs_context":
                task["state"] = "ready"
                task["ready"] = True
                task["blockers"] = []
                task["updated_at"] = timestamp
                changed.append(f"task:{task.get('id')}:ready")
                task_data["state"] = "ready"
                task_data["current_phase"] = "task"
                task_data["active_task"] = None
                task_data["next_action"] = {"skill": "impl", "task_id": task.get("id"), "reason": "reconciled stale context blocker after dependency checkpoint"}
                break
    if release_stale_claim and execution.get("owner") and worker and execution.get("owner") != worker:
        execution["status"] = "unclaimed"
        execution["owner"] = None
        execution["released_at"] = timestamp
        execution["updated_at"] = timestamp
        execution["updated_by"] = actor
        changed.append("stale_claim_released")
    if changed:
        task_data["updated_at"] = timestamp
        save_package(pkg, task_data)
        append_parallel_runtime_event(root, initiative, "package_reconciled", actor, timestamp, package=package, assignment_id=assignment_id, worker=worker, reason="; ".join(changed), detail={"changed": changed})
        return {"initiative": initiative, "package": package, "status": "reconciled", "changed": changed}
    return {"initiative": initiative, "package": package, "status": "no_change", "changed": []}


def finish_worker(
    root: Path,
    initiative: str,
    package: str,
    assignment_id: str,
    from_worktree: str,
    review_state: str,
    changed_artifacts: list[str],
    actor: str,
    timestamp: str,
    checkpoint_kind: str | None = None,
    sha: str | None = None,
    base_sha: str | None = None,
    branch: str | None = None,
    release: bool = False,
    worktree_root_ref: str | None = None,
) -> dict[str, Any]:
    validate_name(initiative)
    validate_name(package)
    ensure_assignment_matches(package, assignment_id)
    if review_state not in {"not_started", "ready_for_review", "reviewed"}:
        raise ArborError("Invalid review state.")
    artifacts = [safe_artifact_ref(item) for item in changed_artifacts] if changed_artifacts else []
    imported = import_package_artifacts(root, package, from_worktree, artifacts, actor, timestamp)
    repaired_context: list[dict[str, Any]] = []
    for context_type in ["impl", "review"]:
        repair = repair_context_jsonl(root, package, context_type, actor, timestamp)
        if repair["changed"]:
            repaired_context.append(repair)
    errors = validate_package(root, package)
    if errors:
        raise ArborError("Package validation failed after worker finish: " + "; ".join(errors))
    checkpoint = None
    if checkpoint_kind:
        if checkpoint_kind not in CHECKPOINT_KINDS:
            raise ArborError(f"Invalid checkpoint kind '{checkpoint_kind}'.")
        if not sha:
            raise ArborError("--sha is required when --checkpoint-kind is provided.")
        checkpoint = record_checkpoint(root, package, checkpoint_kind, sha, branch, base_sha, actor, f"finish-worker {review_state}", timestamp)
    if release:
        release_package(root, package, None, actor, "finish-worker release", timestamp, True)
    event = append_parallel_runtime_event(
        root,
        initiative,
        "worker_finished",
        actor,
        timestamp,
        package=package,
        assignment_id=assignment_id,
        worker=worker_name_for_package(package),
        reason=f"worker finished with review_state={review_state}",
        detail={"review_state": review_state, "changed_artifacts": imported["checked"], "imported": imported["imported"], "missing": imported["missing"], "repaired_context": repaired_context, "checkpoint_kind": checkpoint_kind},
    )
    schedule = parallel_schedule(root, initiative, 5, actor, timestamp, worktree_root_ref)
    return {"initiative": initiative, "package": package, "import": imported, "repaired_context": repaired_context, "checkpoint": checkpoint, "runtime_event": event, "next_schedule": schedule}


def _validate_context_entry(context_type: str, entry: dict[str, Any]) -> None:
    if context_type not in CONTEXT_TYPES:
        raise ArborError(f"Invalid context type '{context_type}'.")
    if context_type == "sources":
        required = ["id", "type", "location", "title", "why_it_matters"]
        missing = [field for field in required if not entry.get(field)]
        if missing:
            raise ArborError("sources context entry missing required fields: " + ", ".join(missing))
        if entry.get("type") not in SOURCE_TYPES:
            raise ArborError(f"Invalid source type '{entry.get('type')}'.")
    else:
        if not entry.get("summary"):
            raise ArborError("impl/review context entry requires summary.")
        if entry.get("kind") is not None and entry.get("kind") not in CONTEXT_KINDS:
            raise ArborError(f"Invalid context kind '{entry.get('kind')}'.")


def add_context_batch(root: Path, package: str, context_type: str, entries: list[dict[str, Any]], actor: str, timestamp: str) -> dict[str, Any]:
    validate_name(package)
    if not entries:
        raise ArborError("At least one context entry is required.")
    pkg, data = load_package(root, package)
    for entry in entries:
        if not isinstance(entry, dict):
            raise ArborError("Context batch entries must be JSON objects.")
        task_id = entry.get("task_id")
        if task_id:
            find_task(data, task_id)
        _validate_context_entry(context_type, entry)
    path = pkg / "context" / f"{context_type}.jsonl"
    written: list[dict[str, Any]] = []
    for entry in entries:
        if context_type == "sources":
            normalized = {
                "id": entry["id"],
                "type": entry["type"],
                "location": entry["location"],
                "title": entry["title"],
                "why_it_matters": entry["why_it_matters"],
            }
        else:
            normalized = {
                "at": entry.get("at") or timestamp,
                "actor": entry.get("actor") or actor,
                "task_id": entry.get("task_id"),
                "kind": entry.get("kind") or "note",
                "source": entry.get("source"),
                "summary": entry["summary"],
            }
        append_jsonl(path, normalized)
        written.append(normalized)
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return {"package": package, "type": context_type, "count": len(written), "entries": written}


def _normalized_request(value: str) -> str:
    return " ".join(value.strip().split()).casefold()


def upsert_contract(
    root: Path,
    initiative: str,
    consumer: str,
    producer: str,
    request: str,
    status: str,
    request_id: str | None,
    resolution: str | None,
    actor: str,
    timestamp: str,
) -> dict[str, Any]:
    validate_name(initiative)
    validate_name(consumer)
    validate_name(producer)
    if consumer == producer:
        raise ArborError("Contract request consumer and producer must be different packages.")
    if status not in CONTRACT_REQUEST_STATUSES:
        raise ArborError(f"Invalid contract request status '{status}'.")
    if not request.strip():
        raise ArborError("Contract request text is required.")
    ensure_map_workspace(root, initiative, timestamp)
    data = sync_map_from_packages(root, initiative, timestamp)
    package_names = {entry.get("name") for entry in data.get("packages", []) if isinstance(entry, dict)}
    for package_name, role in [(consumer, "consumer"), (producer, "producer")]:
        if package_name not in package_names:
            raise ArborError(f"Unknown {role} package '{package_name}' for initiative '{initiative}'.")
    requests = contract_requests_list(data)
    item = None
    if request_id:
        item = next((entry for entry in requests if entry.get("id") == request_id), None)
        if item is None:
            raise ArborError(f"Unknown contract request id '{request_id}'.")
    if item is None:
        normalized = _normalized_request(request)
        item = next(
            (
                entry
                for entry in requests
                if entry.get("consumer") == consumer
                and entry.get("producer") == producer
                and entry.get("status") in {"open", "accepted"}
                and _normalized_request(str(entry.get("request") or "")) == normalized
            ),
            None,
        )
    created = item is None
    if item is None:
        item = {
            "id": next_contract_request_id(requests),
            "consumer": consumer,
            "producer": producer,
            "request": request.strip(),
            "status": status,
            "resolution": resolution.strip() if isinstance(resolution, str) and resolution.strip() else None,
            "created_at": timestamp,
            "updated_at": timestamp,
            "created_by": actor,
            "updated_by": actor,
        }
        requests.append(item)
    else:
        item["consumer"] = consumer
        item["producer"] = producer
        item["request"] = request.strip()
        item["status"] = status
        if resolution is not None:
            item["resolution"] = resolution.strip() or None
        item["updated_at"] = timestamp
        item["updated_by"] = actor
    data["contract_requests"] = requests
    data["updated_at"] = timestamp
    data.setdefault("history", []).append({"at": timestamp, "actor": actor, "event": "contract_upserted", "id": item["id"], "consumer": consumer, "producer": producer, "status": status, "created": created})
    write_json(map_json_path(root, initiative), data)
    event = append_parallel_runtime_event(root, initiative, "contract_upserted", actor, timestamp, package=consumer, reason=f"{item['id']} {consumer}->{producer} {status}", detail={"id": item["id"], "created": created})
    return {"initiative": initiative, "map_json": f".arbor/maps/{initiative}/map.json", "contract_request": item, "created": created, "runtime_event": event}


def parse_entry_json(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ArborError(f"Invalid entry JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ArborError("Entry JSON must be an object.")
    return value


def parse_entries_json(raw: str) -> list[dict[str, Any]]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ArborError(f"Invalid entries JSON: {exc.msg}") from exc
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ArborError("Entries JSON must be an array of objects.")
    return value
