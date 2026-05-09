from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import package_dir, read_json
from .prd_slices import parse_prd_slices, validate_prd_slice_structure
from .schema import *


def parse_jsonl(path: Path, errors: list[str], required: set[str] | None = None) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not path.exists():
        errors.append(f"Missing file: {path}")
        return entries
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSONL at {path}:{line_no}: {exc}")
            continue
        if not isinstance(entry, dict):
            errors.append(f"JSONL entry must be an object at {path}:{line_no}")
            continue
        missing = required - entry.keys() if required else set()
        if missing:
            errors.append(f"Missing JSONL fields at {path}:{line_no}: {', '.join(sorted(missing))}")
        entries.append(entry)
    return entries


def validate_optional_string(value: Any, label: str, errors: list[str]) -> None:
    if value is not None and not isinstance(value, str):
        errors.append(f"{label} must be a string or null")


def validate_string_array(value: Any, label: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"{label} must be a string array")
        return []
    return value


def validate_prd_amendments(prd: dict[str, Any], errors: list[str]) -> set[str]:
    amendments = prd.get("amendments", [])
    if amendments is None:
        return set()
    if not isinstance(amendments, list):
        errors.append("prd.amendments must be an array")
        return set()

    amendment_ids: set[str] = set()
    for index, amendment in enumerate(amendments):
        label = f"prd.amendments[{index}]"
        if not isinstance(amendment, dict):
            errors.append(f"{label} must be an object")
            continue
        for field in ["id", "title", "wrong", "correct", "created_at", "created_by"]:
            value = amendment.get(field)
            if not isinstance(value, str) or not value:
                errors.append(f"{label}.{field} must be a non-empty string")
        amendment_id = amendment.get("id")
        if isinstance(amendment_id, str):
            if not AMENDMENT_ID_RE.match(amendment_id):
                errors.append(f"Invalid amendment id: {amendment_id}")
            elif amendment_id in amendment_ids:
                errors.append(f"Duplicate amendment id: {amendment_id}")
            else:
                amendment_ids.add(amendment_id)
        if "source" in amendment:
            validate_optional_string(amendment.get("source"), f"{label}.source", errors)
        if "affects" in amendment:
            validate_string_array(amendment.get("affects"), f"{label}.affects", errors)
    return amendment_ids


def validate_package_sizing(data: dict[str, Any], errors: list[str]) -> None:
    sizing = data.get("package_sizing")
    if sizing is None:
        return
    if not isinstance(sizing, dict):
        errors.append("package_sizing must be an object")
        return
    status = sizing.get("status")
    if status not in PACKAGE_SIZING_STATUSES:
        errors.append(f"Invalid package_sizing.status: {status}")
    if status == "fits_package" and not sizing.get("decision"):
        errors.append("package_sizing.status fits_package requires a non-empty decision")
    validate_optional_string(sizing.get("decision"), "package_sizing.decision", errors)
    validate_optional_string(sizing.get("decided_at"), "package_sizing.decided_at", errors)
    validate_optional_string(sizing.get("decided_by"), "package_sizing.decided_by", errors)
    validate_optional_string(sizing.get("note"), "package_sizing.note", errors)
    signals = sizing.get("signals", [])
    if not isinstance(signals, list) or not all(isinstance(item, str) for item in signals):
        errors.append("package_sizing.signals must be a string array")
    recommended = sizing.get("recommended_packages", [])
    if not isinstance(recommended, list):
        errors.append("package_sizing.recommended_packages must be an array")
    elif recommended:
        errors.append("package_sizing.recommended_packages is obsolete; use PRD ## Slices instead")


def validate_package_kind(data: dict[str, Any], errors: list[str]) -> None:
    kind = data.get("package_kind", "single")
    if kind not in PACKAGE_KINDS:
        errors.append(f"Invalid package_kind: {kind}")
    if data.get("parent") is not None:
        errors.append("parent metadata is obsolete; use PRD ## Slices inside the package")
    children = data.get("children")
    if children:
        errors.append("children metadata is obsolete; use PRD ## Slices inside the package")


def validate_execution(data: dict[str, Any], errors: list[str]) -> None:
    execution = data.get("execution")
    if execution is None:
        return
    if not isinstance(execution, dict):
        errors.append("execution must be an object")
        return
    name = data.get("name")
    if execution.get("boundary") != "package":
        errors.append("execution.boundary must be package")
    expected_path = f".arbor/tasks/{name}" if isinstance(name, str) else None
    if execution.get("unit_path") != expected_path:
        errors.append(f"execution.unit_path must be {expected_path}")
    if "child_task_scope" in execution:
        errors.append("execution.child_task_scope is obsolete in PRD-first model")
    if execution.get("status") not in EXECUTION_STATUSES:
        errors.append(f"Invalid execution.status: {execution.get('status')}")
    for field in ["owner", "claimed_at", "released_at", "session", "updated_at", "updated_by", "note"]:
        validate_optional_string(execution.get(field), f"execution.{field}", errors)

    branch = execution.get("branch")
    if not isinstance(branch, dict):
        errors.append("execution.branch must be an object")
    else:
        for field in ["base", "name", "upstream"]:
            validate_optional_string(branch.get(field), f"execution.branch.{field}", errors)

    worktree = execution.get("worktree")
    if not isinstance(worktree, dict):
        errors.append("execution.worktree must be an object")
    else:
        for field in ["path", "created_by"]:
            validate_optional_string(worktree.get(field), f"execution.worktree.{field}", errors)

    pr = execution.get("pr")
    if not isinstance(pr, dict):
        errors.append("execution.pr must be an object")
    else:
        validate_optional_string(pr.get("url"), "execution.pr.url", errors)
        number = pr.get("number")
        if number is not None and not isinstance(number, int):
            errors.append("execution.pr.number must be an integer or null")
        if pr.get("state") not in PR_STATES:
            errors.append(f"Invalid execution.pr.state: {pr.get('state')}")

    if "agents" in execution and not isinstance(execution.get("agents"), list):
        errors.append("execution.agents must be an array when present")
    if "plan" in execution:
        errors.append("execution.plan is obsolete; use PRD ## Slices as the progress record")
    if "checkpoints" in execution and not isinstance(execution.get("checkpoints"), list):
        errors.append("execution.checkpoints must be an array when present")


def _validate_result(value: Any, label: str, states: set[str], errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object or null")
        return
    if value.get("state") not in {state.upper() for state in states}:
        errors.append(f"Invalid {label}.state: {value.get('state')}")
    for field in ["at", "summary"]:
        if not isinstance(value.get(field), str) or not value.get(field):
            errors.append(f"{label}.{field} must be a non-empty string")


def validate_package(root: Path, name: str) -> list[str]:
    pkg = package_dir(root, name)
    errors: list[str] = []
    required_files = [
        "prd.md",
        "task.json",
        "review.md",
        "context/impl.jsonl",
        "context/review.jsonl",
        "context/sources.jsonl",
    ]
    for rel in required_files:
        if not (pkg / rel).exists():
            errors.append(f"Missing file: {pkg / rel}")
    if (pkg / "task.md").exists():
        errors.append("task.md is obsolete in PRD-first model; remove it")

    prd_text: str | None = None
    prd_slice_ids: set[str] | None = None
    prd_path = pkg / "prd.md"
    if prd_path.exists():
        prd_text = prd_path.read_text(encoding="utf-8")
        parsed_slices, parse_errors = parse_prd_slices(prd_text)
        if not parse_errors:
            prd_slice_ids = {item.id for item in parsed_slices}

    if not (pkg / "task.json").exists():
        return errors

    try:
        data = read_json(pkg / "task.json")
    except ArborError as exc:
        return errors + [str(exc)]

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"Unsupported schema_version: {data.get('schema_version')}")
    if data.get("name") != name:
        errors.append(f"task.json name '{data.get('name')}' does not match directory '{name}'")
    if "mode" in data:
        errors.append("mode is obsolete in PRD-first model")
    if data.get("state") not in TOP_LEVEL_STATES:
        errors.append(f"Invalid top-level state: {data.get('state')}")
    if data.get("current_phase") not in PHASES:
        errors.append(f"Invalid current_phase: {data.get('current_phase')}")
    next_action = data.get("next_action")
    if not isinstance(next_action, dict):
        errors.append("next_action must be an object")
    elif next_action.get("skill") not in NEXT_ACTION_SKILLS:
        errors.append(f"Invalid next_action.skill: {next_action.get('skill')}")
    elif "task_id" in next_action:
        errors.append("next_action.task_id is obsolete in PRD-first model")

    prd = data.get("prd")
    if not isinstance(prd, dict):
        errors.append("prd must be an object")
    else:
        validate_prd_amendments(prd, errors)
        if prd.get("file") != "prd.md":
            errors.append("prd.file must be prd.md")
        if prd.get("status") not in {"draft", "ready", "revising", "superseded"}:
            errors.append(f"Invalid prd.status: {prd.get('status')}")
        source_type = prd.get("source_type")
        if source_type not in {"new", "legacy-brainstorm", "ad-hoc", None}:
            errors.append(f"Invalid prd.source_type: {source_type}")
        if prd.get("status") == "ready":
            sizing = data.get("package_sizing") if isinstance(data.get("package_sizing"), dict) else {}
            if sizing.get("status") != "fits_package":
                errors.append("prd.status ready requires package_sizing.status fits_package")
            if prd_text is not None:
                errors.extend(f"prd.md: {error}" for error in validate_prd_slice_structure(prd_text))

    if "tasks" in data:
        errors.append("tasks[] is obsolete in PRD-first model; use PRD ## Slices instead")
    if "active_task" in data:
        errors.append("active_task is obsolete in PRD-first model")

    slices = data.get("slices")
    if slices is not None:
        if not isinstance(slices, list):
            errors.append("slices must be an array")
        else:
            seen_ids: set[str] = set()
            for index, entry in enumerate(slices):
                label = f"slices[{index}]"
                if not isinstance(entry, dict):
                    errors.append(f"{label} must be an object")
                    continue
                sid = entry.get("id")
                if not isinstance(sid, str) or not SLICE_ID_RE.match(sid):
                    errors.append(f"{label}.id must match S-NNN format")
                elif sid in seen_ids:
                    errors.append(f"Duplicate slice id: {sid}")
                else:
                    seen_ids.add(sid)
                    if prd_slice_ids is not None and sid not in prd_slice_ids:
                        errors.append(f"{label}.id {sid} is not defined in PRD ## Slices")
                if entry.get("status") not in SLICE_STATUSES:
                    errors.append(f"{label}.status must be one of {sorted(SLICE_STATUSES)}")

    validate_package_sizing(data, errors)
    validate_package_kind(data, errors)
    validate_execution(data, errors)
    _validate_result(data.get("impl_result"), "impl_result", {"done", "done_with_concerns", "needs_context", "blocked"}, errors)
    _validate_result(data.get("review_result"), "review_result", {"approved", "approved_with_notes", "needs_rework", "brainstorm_drift"}, errors)

    if data.get("state") == "doing" and isinstance(next_action, dict) and next_action.get("skill") not in {"impl", "brainstorm", "user"}:
        errors.append("top-level doing state should route to impl, brainstorm, or user")
    if data.get("state") == "reviewed" and isinstance(next_action, dict) and next_action.get("skill") != "none":
        errors.append("top-level reviewed state should have next_action.skill=none")

    impl_entries = parse_jsonl(pkg / "context" / "impl.jsonl", errors, {"at", "actor", "kind", "summary"})
    review_entries = parse_jsonl(pkg / "context" / "review.jsonl", errors, {"at", "actor", "kind", "summary"})
    source_entries = parse_jsonl(pkg / "context" / "sources.jsonl", errors, {"id", "type", "location", "title", "why_it_matters"})

    for path_label, entries in [("impl", impl_entries), ("review", review_entries)]:
        for entry in entries:
            if "task_id" in entry:
                errors.append(f"context/{path_label}.jsonl contains obsolete task_id field")
            if entry.get("kind") not in CONTEXT_KINDS:
                errors.append(f"context/{path_label}.jsonl has invalid kind: {entry.get('kind')}")
    source_ids: set[str] = set()
    for entry in source_entries:
        source_id = entry.get("id")
        if source_id in source_ids:
            errors.append(f"Duplicate source id: {source_id}")
        if isinstance(source_id, str):
            source_ids.add(source_id)
        if entry.get("type") not in SOURCE_TYPES:
            errors.append(f"sources.jsonl has invalid type for {source_id}: {entry.get('type')}")

    history = data.get("phase_history", [])
    if not isinstance(history, list):
        errors.append("phase_history must be an array")
    else:
        for index, item in enumerate(history):
            if not isinstance(item, dict):
                errors.append(f"phase_history[{index}] must be an object")
                continue
            for field in ["at", "phase", "from", "to", "actor", "note"]:
                if field not in item:
                    errors.append(f"phase_history[{index}] missing field: {field}")
            if item.get("phase") not in PHASES:
                errors.append(f"phase_history[{index}] has invalid phase: {item.get('phase')}")
            if "task_id" in item:
                errors.append(f"phase_history[{index}].task_id is obsolete in PRD-first model")

    return errors
